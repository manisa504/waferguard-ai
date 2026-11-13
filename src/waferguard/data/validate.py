"""Profile real WM-811K records without preprocessing, labeling, or splitting them.

The original is a legacy pandas pickle. Only a narrow, explicit set of reconstruction
symbols is allowed. This is defense in depth, not a sandbox: run trusted-source
archives in a resource-limited process without credentials or network access.
"""

import argparse
import hashlib
import json
import pickle
import time
import zipfile
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from pandas.compat.pickle_compat import Unpickler

from waferguard.data.acquire import check_archive, sha256, write_json

ALLOWED = {
    ("__builtin__", "slice"),
    ("builtins", "slice"),
    ("numpy", "dtype"),
    ("numpy", "ndarray"),
    ("numpy.core.multiarray", "_reconstruct"),
    ("numpy.core.multiarray", "scalar"),
    ("pandas.core.frame", "DataFrame"),
    ("pandas.core.internals", "BlockManager"),
    ("pandas.indexes.base", "Index"),
    ("pandas.indexes.base", "_new_Index"),
    ("pandas.indexes.range", "RangeIndex"),
    ("pandas.core.indexes.base", "Index"),
    ("pandas.core.indexes.base", "_new_Index"),
    ("pandas.core.indexes.range", "RangeIndex"),
}


class SourceUnpickler(Unpickler):
    def find_class(self, module, name):
        if (module, name) not in ALLOWED:
            raise pickle.UnpicklingError(f"Disallowed pickle global: {module}.{name}")
        return super().find_class(module, name)

    def persistent_load(self, pid):
        raise pickle.UnpicklingError("Persistent pickle references are forbidden")


def label_value(value) -> str | None:
    """Empty labels stay missing; lowercase source 'none' means the None class."""
    array = np.asarray(value)
    if array.size == 0:
        return None
    if array.size != 1:
        raise ValueError("Label must be empty or contain exactly one value")
    item = array.reshape(-1)[0]
    if item is None or pd.isna(item):
        return None
    if not isinstance(item, str):
        raise ValueError("Non-string label")
    return "None" if item.strip().lower() == "none" else item.strip()


def map_fingerprint(value: np.ndarray) -> str:
    """Hash dimensions plus categorical states, independent of integer storage dtype."""
    if value.ndim != 2 or 0 in value.shape or value.dtype.kind not in "biuf":
        raise ValueError("Expected nonempty, numeric two-dimensional wafer map")
    if not np.isin(value, [0, 1, 2]).all():
        raise ValueError("Unexpected die-state encoding")
    digest = hashlib.sha256(str(value.shape).encode("ascii"))
    digest.update(np.asarray(value, dtype=np.uint8, order="C").tobytes())
    return digest.hexdigest()


def profile(frame: pd.DataFrame, expected: dict) -> dict:
    required = {"waferMap", "failureType"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Missing required columns: {required - set(frame.columns)}")
    labels, shapes, states, source_splits = Counter(), Counter(), Counter(), Counter()
    hashes, conflicts = {}, set()
    duplicate_rows = invalid_maps = invalid_labels = missing_labels = 0
    missing_lots = duplicate_ids = 0
    lots, wafer_ids = set(), set()
    hash_lots = defaultdict(set)
    labeled_hash_counts = Counter()
    map_source_splits = defaultdict(set)
    lot_source_splits = defaultdict(set)
    conflict_details = defaultdict(set)
    has_lots = "lotName" in frame.columns
    has_ids = has_lots and "waferIndex" in frame.columns
    for position, row in enumerate(frame.itertuples(index=False, name=None)):
        record = dict(zip(frame.columns, row, strict=True))
        try:
            label = label_value(record["failureType"])
            if label is None:
                missing_labels += 1
            elif label not in expected["expected_counts"]:
                invalid_labels += 1
            else:
                labels[label] += 1
        except (ValueError, TypeError):
            label = "INVALID"
            invalid_labels += 1
        lot = record.get("lotName")
        if has_lots:
            if not isinstance(lot, str) or not lot.strip():
                missing_lots += 1
                lot = None
            else:
                lots.add(lot)
        if has_ids:
            index = record["waferIndex"]
            if lot is None or pd.isna(index):
                missing_lots += 1
            else:
                identity = (lot, index)
                duplicate_ids += identity in wafer_ids
                wafer_ids.add(identity)
        if "trianTestLabel" in record or "trainTestLabel" in record:
            source_split = record.get("trianTestLabel", record.get("trainTestLabel"))
            source_split_name = label_value(source_split) or "<missing>"
            source_splits[source_split_name] += 1
        else:
            source_split_name = "<missing>"
        try:
            wafer = np.asarray(record["waferMap"])
            fingerprint = map_fingerprint(wafer)
            shapes[f"{wafer.shape[0]}x{wafer.shape[1]}"] += 1
            values, counts = np.unique(wafer, return_counts=True)
            states.update({str(int(v)): int(n) for v, n in zip(values, counts, strict=True)})
            if fingerprint in hashes:
                duplicate_rows += 1
                prior = hashes[fingerprint]
                if prior != label and prior is not None and label is not None:
                    conflicts.add(fingerprint)
                    conflict_details[fingerprint].update([prior, label])
                if prior is None and label is not None:
                    hashes[fingerprint] = label
            else:
                hashes[fingerprint] = label
            if label in expected["expected_counts"]:
                labeled_hash_counts[fingerprint] += 1
            if source_split_name in {"Training", "Test"}:
                map_source_splits[fingerprint].add(source_split_name)
                if lot:
                    lot_source_splits[lot].add(source_split_name)
            if lot:
                hash_lots[fingerprint].add(lot)
        except (ValueError, TypeError):
            invalid_maps += 1
        if position and position % 100_000 == 0:
            print(f"Profiled {position:,} records", flush=True)
    counts_match = dict(labels) == expected["expected_counts"]
    validation_pass = (
        len(frame) == expected["expected_total"]
        and counts_match
        and sum(labels.values()) == expected["expected_labeled"]
        and invalid_maps == 0
        and invalid_labels == 0
    )
    cross_lot = sum(len(v) > 1 for v in hash_lots.values())
    return {
        "total": len(frame),
        "columns": list(frame.columns),
        "label_counts": dict(labels),
        "labeled": sum(labels.values()),
        "missing_labels": missing_labels,
        "invalid_labels": invalid_labels,
        "invalid_maps": invalid_maps,
        "shape_counts": dict(shapes),
        "die_state_counts": dict(states),
        "unique_maps": len(hashes),
        "unique_labeled_maps": len(labeled_hash_counts),
        "duplicate_labeled_map_rows": sum(n - 1 for n in labeled_hash_counts.values()),
        "conflicting_label_details": {k: sorted(v) for k, v in conflict_details.items()},
        "source_training_test_shared_map_groups": sum(
            len(v) > 1 for v in map_source_splits.values()
        ),
        "source_training_test_shared_lots": sum(len(v) > 1 for v in lot_source_splits.values()),
        "duplicate_map_rows": duplicate_rows,
        "conflicting_label_map_groups": len(conflicts),
        "unique_lots": len(lots),
        "missing_or_invalid_identifiers": missing_lots,
        "duplicate_wafer_ids": duplicate_ids,
        "duplicate_map_groups_across_lots": cross_lot,
        "source_split_counts": dict(source_splits),
        "expected_counts_match": counts_match,
        "validation_pass": validation_pass,
        "split_feasibility": {
            "lot_identifiers_present": has_lots,
            "wafer_identifiers_present": has_ids,
            "candidate_grouping": "lotName" if has_lots else "map_hash",
            "reliable_grouping_confirmed": False,
            "decision": "Gate 2 must audit identifiers, merge lot/duplicate connected components, "
            "quarantine conflicting labels, and verify class coverage before splitting.",
            "limitation": "Identifier presence is not proof of independence or temporal validity. "
            "No training/test split has been generated.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("configs/data.yaml"))
    parser.add_argument("--output", type=Path, default=Path("reports/data/quality.json"))
    args = parser.parse_args()
    start = time.monotonic()
    manifest = json.loads(args.manifest.read_text())
    if sha256(args.archive) != manifest["archive_sha256"]:
        parser.error("Archive hash does not match acquisition manifest")
    check_archive(args.archive)
    with zipfile.ZipFile(args.archive) as archive, archive.open("LSWMD.pkl") as stream:
        frame = SourceUnpickler(stream, encoding="latin1").load()
    if not isinstance(frame, pd.DataFrame):
        parser.error("Source must contain a pandas DataFrame")
    result = profile(frame, yaml.safe_load(args.config.read_text()))
    result.update(
        {
            "schema_version": 1,
            "measured_at_utc": datetime.now(UTC).isoformat(),
            "archive_sha256": manifest["archive_sha256"],
            "config_sha256": sha256(args.config),
            "duration_seconds": round(time.monotonic() - start, 3),
            "numpy_version": np.__version__,
            "pandas_version": pd.__version__,
        }
    )
    write_json(args.output, result)
    print(json.dumps({k: v for k, v in result.items() if k != "shape_counts"}, indent=2))
    if not result["validation_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
