"""Fixtures validate safe array loading and artifact integrity, not detection skill."""

import json

import numpy as np
import pytest

from waferguard.data.acquire import sha256
from waferguard.data.dataset import PreparedSplit


def fixture(tmp_path, monkeypatch):
    processed, splits = tmp_path / "processed", tmp_path / "splits"
    processed.mkdir()
    splits.mkdir()
    states = np.array([[[0, 1], [2, 1]]], dtype=np.uint8)
    np.save(processed / "states.npy", states, allow_pickle=False)
    metadata = {"shape": [1, 2, 2], "label_counts": {"Center": 1}}
    (processed / "processed.json").write_text(json.dumps(metadata))
    row = {"row_id": "synthetic:0", "input_row": 0, "label": "Center"}
    monkeypatch.setattr("waferguard.data.dataset.read_processed", lambda path: ([row], metadata))
    (splits / "train.jsonl").write_text(json.dumps(row) + "\n")
    evidence = {
        "split_created": True,
        "leakage_audit": {"passed": True},
        "expanded_membership_audit": {"passed": True},
        "processed_manifest_sha256": sha256(processed / "processed.json"),
        "artifacts_sha256": {"train.jsonl": sha256(splits / "train.jsonl")},
        "feasibility": {"split_counts": {"train": {"rows": 1}}},
    }
    report = tmp_path / "audit.json"
    report.write_text(json.dumps(evidence))
    return processed, splits, report


def test_loader_onehot_is_a_copy_and_cannot_mutate_original_states(tmp_path, monkeypatch):
    processed, splits, report = fixture(tmp_path, monkeypatch)
    dataset = PreparedSplit(processed, splits, report)
    item = dataset[0]
    assert item["label"] == "Center"
    assert item["image"].shape == (3, 2, 2)
    item["image"][:] = 99
    assert dataset[0]["image"].max() == 1
    assert not dataset.states.flags.writeable


def test_loader_rejects_tampered_split_before_returning_data(tmp_path, monkeypatch):
    processed, splits, report = fixture(tmp_path, monkeypatch)
    (splits / "train.jsonl").write_text("{}\n")
    with pytest.raises(ValueError, match="checksum"):
        PreparedSplit(processed, splits, report)


def test_failed_audit_cannot_be_consumed(tmp_path, monkeypatch):
    processed, splits, report = fixture(tmp_path, monkeypatch)
    evidence = json.loads(report.read_text())
    evidence["expanded_membership_audit"]["passed"] = False
    report.write_text(json.dumps(evidence))
    with pytest.raises(ValueError, match="not passed"):
        PreparedSplit(processed, splits, report)
