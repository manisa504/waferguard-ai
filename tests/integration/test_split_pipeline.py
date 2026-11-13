"""Synthetic end-to-end split contracts; real-source measurements are separate reports."""

import json
from collections import Counter

import pytest
import yaml

from waferguard.data.split import run


def test_pipeline_binds_processed_source_reproduces_and_refuses_changed_artifacts(
    tmp_path, monkeypatch
):
    raw = [
        {
            "source_row": i,
            "row_id": f"fixture:{i}",
            "lot": f"lot{i}",
            "label": ["Center", "Scratch"][i % 2],
            "map_hash": f"map{i}",
            "orbit_hash": f"orbit{i}",
        }
        for i in range(100)
    ]
    processed = [
        dict(row, input_row=i, input_hash=f"input{i}", input_orbit_hash=f"iorbit{i}")
        for i, row in enumerate(raw)
    ]
    receipt = {
        "records_sha256": "fixture-index",
        "labeled": len(raw),
        "identity": {"archive_sha256": "fixture-archive"},
        "label_counts": dict(Counter(row["label"] for row in raw)),
    }
    metadata = {
        "identity": {"index_sha256": "fixture-index", "size": 8},
        "artifacts_sha256": {"states.npy": "fixture-sha"},
    }
    monkeypatch.setattr("waferguard.data.split.read_index", lambda path: (raw, receipt))
    monkeypatch.setattr("waferguard.data.split.read_processed", lambda path: (processed, metadata))
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    (processed_dir / "processed.json").write_text(json.dumps(metadata))
    config = {
        "seed": 42,
        "attempts": 2,
        "fractions": {"train": 0.4, "validation": 0.2, "calibration": 0.2, "test": 0.2},
        "max_absolute_fraction_error": 0.05,
        "minimum_per_class": dict.fromkeys(["train", "validation", "calibration", "test"], 1),
        "image_size": 8,
    }
    config_path = tmp_path / "split.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))
    output, report = tmp_path / "splits", tmp_path / "audit.json"
    assert run(tmp_path, config_path, output, report, processed_dir)
    first = json.loads(report.read_text())
    assert first["leakage_audit"]["passed"]
    assert first["expanded_membership_audit"]["passed"]
    assert run(tmp_path, config_path, output, report, processed_dir)
    assert json.loads(report.read_text())["artifacts_sha256"] == first["artifacts_sha256"]
    original = (output / "train.jsonl").read_bytes()
    (output / "train.jsonl").write_bytes(original + b"{}\n")
    with pytest.raises(ValueError, match="Immutable"):
        run(tmp_path, config_path, output, report, processed_dir)
    assert (output / "train.jsonl").read_bytes() == original + b"{}\n"


def test_pipeline_rejects_processed_metadata_from_another_source(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "waferguard.data.split.read_index",
        lambda path: ([], {"records_sha256": "expected", "labeled": 0}),
    )
    monkeypatch.setattr(
        "waferguard.data.split.read_processed",
        lambda path: ([], {"identity": {"index_sha256": "different"}}),
    )
    with pytest.raises(ValueError, match="different source index"):
        run(tmp_path, tmp_path, tmp_path, tmp_path, tmp_path)
