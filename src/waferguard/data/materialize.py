"""Materialize categorical inputs locally and audit identity after preprocessing."""

import argparse
import gzip
import io
import json
import os
import zipfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from waferguard.data.acquire import check_archive, sha256, write_json
from waferguard.data.index import implementation_hashes
from waferguard.data.preprocess import PREPROCESS_VERSION, encode_wafer, orbit_fingerprint
from waferguard.data.validate import SourceUnpickler, map_fingerprint


def materialize(index_dir: Path, archive: Path, output: Path, size: int) -> dict:
    receipt = json.loads((index_dir / "index.json").read_text())
    if receipt["identity"]["implementation_sha256"] != implementation_hashes():
        raise ValueError("Source index implementation changed")
    if sha256(index_dir / "records.jsonl.gz") != receipt["records_sha256"]:
        raise ValueError("Source index checksum mismatch")
    if sha256(archive) != receipt["identity"]["archive_sha256"]:
        raise ValueError("Original source checksum mismatch")
    identity = {
        "index_sha256": receipt["records_sha256"],
        "archive_sha256": receipt["identity"]["archive_sha256"],
        "version": PREPROCESS_VERSION,
        "size": size,
        "implementation_sha256": sha256(Path(__file__)),
        "preprocess_sha256": sha256(Path(__file__).with_name("preprocess.py")),
    }
    manifest_path = output / "processed.json"
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text())
        if previous["identity"] != identity:
            raise ValueError(
                "Processed identity changed; preserve artifacts and use a new directory"
            )
        for filename, digest in previous["artifacts_sha256"].items():
            if sha256(output / filename) != digest:
                raise ValueError("Processed artifact checksum mismatch")
        return previous
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("Unregistered files exist in processed directory; use a new directory")
    with gzip.open(index_dir / "records.jsonl.gz", "rt", encoding="utf-8") as stream:
        records = [row for line in stream if (row := json.loads(line))["label"] is not None]
    if len(records) != receipt["labeled"]:
        raise ValueError("Labeled source count mismatch")
    print(f"Encoding {len(records):,} labeled records; no labels are invented", flush=True)
    check_archive(archive)
    with zipfile.ZipFile(archive) as zipped, zipped.open("LSWMD.pkl") as stream:
        frame = SourceUnpickler(stream, encoding="latin1").load()
    temporary = output / "states.npy.tmp"
    states = np.lib.format.open_memmap(
        temporary, mode="w+", dtype=np.uint8, shape=(len(records), size, size)
    )
    counts = Counter()
    for position, record in enumerate(records):
        original = np.asarray(frame.iloc[record["source_row"]]["waferMap"])
        if map_fingerprint(original) != record["map_hash"]:
            raise ValueError("Source row does not match indexed identity")
        encoded = encode_wafer(original, size).argmax(axis=0).astype(np.uint8)
        states[position] = encoded
        record.update(
            {
                "input_row": position,
                "input_hash": map_fingerprint(encoded),
                "input_orbit_hash": orbit_fingerprint(encoded),
            }
        )
        counts[record["label"]] += 1
        if position and position % 25_000 == 0:
            print(f"Encoded {position:,} records", flush=True)
    states.flush()
    del states, frame
    os.replace(temporary, output / "states.npy")
    metadata = output / "records.jsonl.gz"
    with metadata.open("xb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as zipped:
            with io.TextIOWrapper(zipped, encoding="utf-8", newline="\n") as stream:
                for record in records:
                    stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    result = {
        "identity": identity,
        "total": len(records),
        "label_counts": dict(counts),
        "dtype": "uint8",
        "shape": [len(records), size, size],
        "channels_at_load": ["outside", "passing", "failing"],
        "created_at_utc": datetime.now(UTC).isoformat(),
        "artifacts_sha256": {
            name: sha256(output / name) for name in ("states.npy", "records.jsonl.gz")
        },
    }
    write_json(manifest_path, result)
    return result


def read_processed(directory: Path) -> tuple[list[dict], dict]:
    manifest = json.loads((directory / "processed.json").read_text())
    if manifest["identity"]["preprocess_sha256"] != sha256(
        Path(__file__).with_name("preprocess.py")
    ):
        raise ValueError("Preprocessing implementation differs from materialized inputs")
    for name, digest in manifest["artifacts_sha256"].items():
        if sha256(directory / name) != digest:
            raise ValueError("Materialized input checksum mismatch")
    with gzip.open(directory / "records.jsonl.gz", "rt", encoding="utf-8") as stream:
        records = [json.loads(line) for line in stream]
    if len(records) != manifest["total"]:
        raise ValueError("Materialized metadata count mismatch")
    return records, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=Path("data/processed/index-v1"))
    parser.add_argument("--archive", type=Path, default=Path("data/raw/wm811k-v1.zip"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/categorical-64-v1"))
    parser.add_argument("--size", type=int, default=64)
    args = parser.parse_args()
    print(json.dumps(materialize(args.index, args.archive, args.output, args.size), indent=2))


if __name__ == "__main__":
    main()
