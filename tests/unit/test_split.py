"""Synthetic grouping/race/coverage fixtures, never presented as wafer data."""

from copy import deepcopy

from waferguard.data.split import assign_groups, audit_splits, components, prepare


def row(number, lot, orbit, label="Center", component=None):
    result = {
        "source_row": number,
        "row_id": f"fixture:{number}",
        "lot": lot,
        "orbit_hash": orbit,
        "map_hash": f"map-{number}",
        "label": label,
    }
    if component is not None:
        result["component"] = component
    return result


def config():
    return {
        "seed": 42,
        "attempts": 8,
        "fractions": {"train": 0.4, "validation": 0.2, "calibration": 0.2, "test": 0.2},
        "max_absolute_fraction_error": 0.05,
        "minimum_per_class": dict.fromkeys(["train", "validation", "calibration", "test"], 1),
    }


def test_transitive_lot_and_transformed_copy_connections():
    records = [
        row(0, "lot1", "a"),
        row(1, "lot1", "b"),
        row(2, "lot2", "b"),
        row(3, "lot2", "c"),
        row(4, "lot3", "c"),
        row(5, "lot4", "d"),
    ]
    groups = components(records)
    assert sorted(map(len, groups.values())) == [1, 5]
    assert {r["lot"] for r in groups["lot1"]} == {"lot1", "lot2", "lot3"}


def test_dedup_does_not_discard_lot_bridges_and_conflicts_are_quarantined():
    records = [
        row(0, "lot1", "a"),
        row(1, "lot2", "a"),
        row(2, "lot2", "b"),
        row(3, "lot3", "conflict", "Scratch"),
        row(4, "lot4", "conflict", "None"),
        row(5, "lot3", "conflict", None),
        row(6, "lot5", "missing", None),
    ]
    kept, quarantine, details = prepare(records)
    assert [r["source_row"] for r in kept] == [0, 2]
    assert {r["component"] for r in kept} == {"lot1"}
    assert len(quarantine) == 2  # No labels invented for the two missing-label rows.
    assert details["summary"]["unlabeled_excluded"] == 2
    assert details["summary"]["duplicate_labeled_rows_removed"] == 1
    assert details["duplicates"][0]["component"] == "lot1"


def test_deterministic_group_assignment_and_independent_leakage_checks():
    records = [
        row(i, f"lot{i}", f"orbit{i}", ["Center", "Scratch"][i % 2], f"g{i}") for i in range(100)
    ]
    assignment, report = assign_groups(records, config())
    assert assignment is not None
    assert assignment == assign_groups(list(reversed(records)), config())[0]
    splits = {name: [] for name in config()["fractions"]}
    for record in records:
        splits[assignment[record["component"]]].append(record)
    assert audit_splits(splits, config())["passed"]
    bad = deepcopy(splits)
    bad["test"].append(dict(bad["train"][0], row_id="other-id", orbit_hash="different-orbit"))
    audit = audit_splits(bad, config())
    assert not audit["passed"]
    assert any("lot overlaps" in error for error in audit["errors"])
    assert any("map_hash overlaps" in error for error in audit["errors"])


def test_indivisible_giant_component_cannot_silently_fall_back_to_random_rows():
    records = [row(i, f"lot{i}", f"orbit{i}", component="giant") for i in range(90)]
    records += [row(i, f"lot{i}", f"orbit{i}", component=f"g{i}") for i in range(90, 100)]
    assignment, report = assign_groups(records, config())
    assert assignment is None
    assert report["largest_component_rows"] == 90
    assert "Indivisible" in report["failure"]


def test_insufficient_minority_component_support_fails_closed():
    records = [row(i, f"lot{i}", f"orbit{i}", component=f"g{i}") for i in range(100)]
    records += [row(101, "rare-lot", "rare", label="Near-full", component="rare")]
    assignment, report = assign_groups(records, config())
    assert assignment is None
    assert report["class_component_support"]["Near-full"] == 1


def test_postprocessing_collisions_quarantine_labels_and_preserve_transitive_links():
    records = [
        dict(row(0, "lot1", "a"), input_orbit_hash="resized"),
        dict(row(1, "lot2", "b"), input_orbit_hash="resized"),
        dict(row(2, "lot3", "b"), input_orbit_hash="other-resized"),
        dict(row(3, "lot4", "c", label="Scratch"), input_orbit_hash="other-resized"),
        dict(row(4, "lot5", "safe"), input_orbit_hash="safe-resized"),
    ]
    kept, quarantine, details = prepare(records)
    assert [record["source_row"] for record in kept] == [4]
    assert len(quarantine) == 4
    assert details["summary"]["original_conflicting_orbit_groups"] == 0
    assert details["summary"]["conflicting_equivalence_groups"] == 1


def test_processed_collision_across_splits_is_detected_independently():
    records = [
        dict(
            row(i, f"lot{i}", f"orbit{i}", component=f"g{i}"),
            input_hash=f"input{i}",
            input_orbit_hash=f"input-orbit{i}",
        )
        for i in range(100)
    ]
    assignment, _ = assign_groups(records, config())
    splits = {name: [] for name in config()["fractions"]}
    for record in records:
        splits[assignment[record["component"]]].append(record)
    splits["test"][0]["input_hash"] = splits["train"][0]["input_hash"]
    audit = audit_splits(splits, config())
    assert not audit["passed"]
    assert any("input_hash overlaps" in error for error in audit["errors"])
