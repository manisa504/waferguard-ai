"""Synthetic fixtures exercise data contracts only; these are not WM-811K samples."""

import numpy as np
import pandas as pd
import pytest

from waferguard.data.validate import label_value, map_fingerprint, profile


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ([], None),
        (np.empty((0, 0)), None),
        (np.array([["none"]]), "None"),
        ([["Scratch"]], "Scratch"),
        ([[None]], None),
    ],
)
def test_missing_labels_are_distinct_from_none_class(raw, expected):
    assert label_value(raw) == expected


def test_multi_labels_rejected():
    with pytest.raises(ValueError):
        label_value(["Center", "Donut"])


@pytest.mark.parametrize(
    "bad",
    [
        np.array([[0, 3]]),
        np.array([[np.nan]]),
        np.array([[0.5]]),
        np.array([1, 2]),
        np.empty((0, 2)),
        np.array([["1"]]),
    ],
)
def test_invalid_maps_rejected(bad):
    with pytest.raises(ValueError):
        map_fingerprint(bad)


def test_hashes_use_shape_and_categorical_content():
    assert map_fingerprint(np.array([[0, 1]], dtype="uint8")) == map_fingerprint(
        np.array([[0, 1]], dtype="int64")
    )
    assert map_fingerprint(np.array([[0, 1]])) != map_fingerprint(np.array([[0], [1]]))


def test_duplicate_conflicts_and_identifiers_are_reported():
    wafer = np.array([[0, 1], [2, 1]])
    frame = pd.DataFrame(
        {
            "waferMap": [wafer, wafer, wafer],
            "failureType": [[["Center"]], [["Scratch"]], []],
            "lotName": ["lot1", "lot2", "lot2"],
            "waferIndex": [1, 1, 1],
            "trianTestLabel": [[["Training"]], [["Test"]], [["Test"]]],
        }
    )
    result = profile(
        frame,
        {
            "expected_total": 3,
            "expected_labeled": 2,
            "expected_counts": {"Center": 1, "Scratch": 1},
        },
    )
    assert result["validation_pass"]
    assert result["missing_labels"] == 1
    assert result["duplicate_map_rows"] == 2
    assert result["conflicting_label_map_groups"] == 1
    assert result["duplicate_map_groups_across_lots"] == 1
    assert result["duplicate_wafer_ids"] == 1
    assert result["source_training_test_shared_map_groups"] == 1
    assert result["source_training_test_shared_lots"] == 0
    assert result["unique_labeled_maps"] == 1
    assert result["duplicate_labeled_map_rows"] == 1
    assert not result["split_feasibility"]["reliable_grouping_confirmed"]


def test_counts_drift_fails_validation():
    frame = pd.DataFrame({"waferMap": [np.array([[1]])], "failureType": [[["Center"]]]})
    result = profile(
        frame,
        {"expected_total": 811457, "expected_labeled": 172950, "expected_counts": {"Center": 4294}},
    )
    assert not result["validation_pass"]
