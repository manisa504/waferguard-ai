"""Build a local, hash-bound metadata index from the original trusted WM-811K archive."""

import argparse
import gzip
import io
import json
import os
import time
import zipfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from waferguard.data.acquire import check_archive, sha256, write_json
from waferguard.data.preprocess import orbit_fingerprint
from waferguard.data.validate import SourceUnpickler, label_value, map_fingerprint

INDEX_VERSION = "wm811k-metadata-d4-v1"


def implementation_hashes() -> dict:
    return {
        name: sha256(Path(__file__).with_name(name))
        for name in ("index.py", "preprocess.py", "validate.py")
    }


def build_index(archive: Path, acquisition: Path, config: Path, output: Path) -> dict:
    manifest = json.loads(acquisition.read_text())
    archive_hash = sha256(archive)
    if archive_hash != manifest["archive_sha256"]:
        raise ValueError("Archive hash differs from acquisition manifest")
    identity = {
        "version": INDEX_VERSION,
        "archive_sha256": archive_hash,
        "config_sha256": sha256(config),
        "implementation_sha256": implementation_hashes(),
    }
    output.mkdir(parents=True, exist_ok=True)
    destination, receipt = output / "records.jsonl.gz", output / "index.json"
    if receipt.exists():
        prior = json.loads(receipt.read_text())
        if prior["identity"] != identity or sha256(destination) != prior["records_sha256"]:
            raise ValueError("Existing index differs; preserve it and use a new output directory")
        return prior
    if destination.exists():
        raise ValueError("Unregistered index exists; use a new output directory")
    expected = yaml.safe_load(config.read_text())
    check_archive(archive)
    print("Loading original verified source archive", flush=True)
    start = time.monotonic()
    with zipfile.ZipFile(archive) as zipped, zipped.open("LSWMD.pkl") as source:
        frame = SourceUnpickler(source, encoding="latin1").load()
    if not isinstance(frame, pd.DataFrame) or len(frame) != expected["expected_total"]:
        raise ValueError("Unexpected source table or record count")
    required = {"waferMap", "failureType", "lotName", "waferIndex", "trianTestLabel"}
    if not required.issubset(frame.columns):
        raise ValueError("Required source identifiers/annotations missing")
    counts, missing = Counter(), 0
    identifiers = set()
    # Exclusive temporary creation prevents simultaneous writers for the same artifact.
    temporary = destination.with_suffix(".tmp")
    try:
        with temporary.open("xb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as compressed:
                with io.TextIOWrapper(compressed, encoding="utf-8", newline="\n") as stream:
                    for position, values in enumerate(frame.itertuples(index=False, name=None)):
                        row = dict(zip(frame.columns, values, strict=True))
                        label = label_value(row["failureType"])
                        if label is not None and label not in expected["expected_counts"]:
                            raise ValueError(f"Unknown label at source row {position}")
                        if label is None:
                            missing += 1
                        else:
                            counts[label] += 1
                        lot, wafer_index = row["lotName"], row["waferIndex"]
                        if (
                            not isinstance(lot, str)
                            or not lot.strip()
                            or not np.isfinite(wafer_index)
                            or wafer_index != int(wafer_index)
                            or wafer_index < 1
                        ):
                            raise ValueError(f"Invalid source identifier at row {position}")
                        identity_key = (lot, int(wafer_index))
                        if identity_key in identifiers:
                            raise ValueError(f"Duplicate wafer identity at row {position}")
                        identifiers.add(identity_key)
                        wafer = np.asarray(row["waferMap"])
                        record = {
                            "row_id": f"{archive_hash}:{position}",
                            "source_row": position,
                            "lot": lot,
                            "wafer_index": int(wafer_index),
                            "label": label,
                            "source_assignment": label_value(row["trianTestLabel"]),
                            "map_hash": map_fingerprint(wafer),
                            "orbit_hash": orbit_fingerprint(wafer),
                            "shape": list(wafer.shape),
                        }
                        stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")))
                        stream.write("\n")
                        if position and position % 100_000 == 0:
                            print(f"Indexed {position:,} records", flush=True)
        if dict(counts) != expected["expected_counts"]:
            raise ValueError("Observed label counts differ from expected source counts")
        os.replace(temporary, destination)
    except BaseException:
        # Only remove the temporary created by this process, never another writer's file.
        if "raw" in locals() and temporary.exists():
            temporary.unlink()
        raise
    result = {
        "identity": identity,
        "records_sha256": sha256(destination),
        "total": len(frame),
        "labeled": sum(counts.values()),
        "unlabeled": missing,
        "label_counts": dict(counts),
        "created_at_utc": datetime.now(UTC).isoformat(),
        "duration_seconds": round(time.monotonic() - start, 3),
    }
    write_json(receipt, result)
    return result


def read_index(directory: Path) -> tuple[list[dict], dict]:
    manifest = json.loads((directory / "index.json").read_text())
    source = directory / "records.jsonl.gz"
    if sha256(source) != manifest["records_sha256"]:
        raise ValueError("Index contents do not match their manifest")
    if manifest["identity"]["implementation_sha256"] != implementation_hashes():
        raise ValueError("Index implementation changed; regenerate in a new directory")
    with gzip.open(source, "rt", encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream]
    if len(rows) != manifest["total"]:
        raise ValueError("Index count mismatch")
    return rows, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path("data/raw/wm811k-v1.zip"))
    parser.add_argument("--acquisition", type=Path, default=Path("data/manifests/acquisition.json"))
    parser.add_argument("--config", type=Path, default=Path("configs/data.yaml"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/index-v1"))
    args = parser.parse_args()
    print(
        json.dumps(build_index(args.archive, args.acquisition, args.config, args.output), indent=2)
    )


if __name__ == "__main__":
    main()
