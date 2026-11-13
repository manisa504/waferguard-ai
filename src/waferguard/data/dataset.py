"""Read verified categorical splits without loading pickle or inventing labels."""

import json
from pathlib import Path

import numpy as np

from waferguard.data.acquire import sha256
from waferguard.data.materialize import read_processed


class PreparedSplit:
    def __init__(self, processed: Path, splits: Path, report: Path, name: str = "train"):
        if name not in {"train", "validation", "calibration", "test"}:
            raise ValueError("Unknown split")
        evidence = json.loads(report.read_text())
        if (
            not evidence.get("split_created")
            or not evidence["leakage_audit"]["passed"]
            or not evidence["expanded_membership_audit"]["passed"]
        ):
            raise ValueError("Split audit has not passed")
        if sha256(processed / "processed.json") != evidence["processed_manifest_sha256"]:
            raise ValueError("Preprocessing manifest differs from split evidence")
        records, metadata = read_processed(processed)
        filename = f"{name}.jsonl"
        path = splits / filename
        if sha256(path) != evidence["artifacts_sha256"][filename]:
            raise ValueError("Split manifest checksum mismatch")
        self.records = [json.loads(line) for line in path.read_text().splitlines()]
        if len(self.records) != evidence["feasibility"]["split_counts"][name]["rows"]:
            raise ValueError("Split row count differs from evidence")
        by_id = {record["row_id"]: record for record in records}
        for record in self.records:
            origin = by_id.get(record["row_id"])
            if origin is None or any(record.get(key) != value for key, value in origin.items()):
                raise ValueError("Split source identity differs from encoded input metadata")
        self.states = np.load(processed / "states.npy", mmap_mode="r", allow_pickle=False)
        if list(self.states.shape) != metadata["shape"] or self.states.dtype != np.uint8:
            raise ValueError("Encoded array does not match its manifest")
        self.classes = tuple(sorted(metadata["label_counts"]))
        self.name = name

    def __len__(self):
        return len(self.records)

    def __getitem__(self, position: int) -> dict:
        row = self.records[position]
        states = self.states[row["input_row"]]
        if not np.isin(states, [0, 1, 2]).all():
            raise ValueError("Invalid encoded die state")
        return {
            "image": np.eye(3, dtype=np.float32)[states].transpose(2, 0, 1).copy(),
            "label": row["label"],
            "row_id": row["row_id"],
        }
