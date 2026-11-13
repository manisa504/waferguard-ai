"""Audit connected components and create immutable supervised split manifests."""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import yaml

from waferguard.data.acquire import sha256, write_json
from waferguard.data.index import read_index
from waferguard.data.materialize import read_processed


class UnionFind:
    def __init__(self, keys):
        self.parent = {key: key for key in keys}

    def find(self, key):
        root = key
        while self.parent[root] != root:
            root = self.parent[root]
        while key != root:
            next_key = self.parent[key]
            self.parent[key] = root
            key = next_key
        return root

    def union(self, left, right):
        left, right = self.find(left), self.find(right)
        if left != right:
            self.parent[max(left, right)] = min(left, right)


def components(rows: list[dict]) -> dict[str, list[dict]]:
    """Lot and D4-equivalent maps are indivisible, even across different lots."""
    union = UnionFind({row["lot"] for row in rows})
    first_lot = {}
    for row in rows:
        previous = first_lot.setdefault(row.get("duplicate_group", row["orbit_hash"]), row["lot"])
        union.union(previous, row["lot"])
    grouped = defaultdict(list)
    for row in rows:
        grouped[union.find(row["lot"])].append(row)
    return dict(grouped)


def summarize_components(grouped: dict[str, list[dict]], classes: list[str]) -> dict:
    sizes = sorted((len(group) for group in grouped.values()), reverse=True)
    class_support = {
        label: sum(any(r["label"] == label for r in group) for group in grouped.values())
        for label in classes
    }
    largest = sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))[:10]
    return {
        "components": len(grouped),
        "rows": sum(sizes),
        "largest_component_rows": sizes[0] if sizes else 0,
        "class_component_support": class_support,
        "largest_components": [
            {
                "id": key,
                "rows": len(rows),
                "unique_lots": len({r["lot"] for r in rows}),
                "class_counts": dict(Counter(r["label"] for r in rows if r["label"] is not None)),
            }
            for key, rows in largest
        ],
    }


def prepare(rows: list[dict]) -> tuple[list[dict], list[dict], dict]:
    """Remove missing labels, quarantine entire conflicting orbits, retain one per orbit."""
    labeled = [row for row in rows if row["label"] is not None]
    equivalence = UnionFind({row["orbit_hash"] for row in labeled})
    original_labels = defaultdict(set)
    first_input = {}
    for row in labeled:
        original_labels[row["orbit_hash"]].add(row["label"])
        if "input_orbit_hash" in row:
            previous = first_input.setdefault(row["input_orbit_hash"], row["orbit_hash"])
            equivalence.union(previous, row["orbit_hash"])
    labels_by_orbit = defaultdict(set)
    labeled = [dict(row, duplicate_group=equivalence.find(row["orbit_hash"])) for row in labeled]
    for row in labeled:
        labels_by_orbit[row["duplicate_group"]].add(row["label"])
    conflicts = {key for key, labels in labels_by_orbit.items() if len(labels) > 1}
    eligible, quarantine, duplicates = [], [], []
    # Build components before deduplication: removed copies must still connect their lots.
    for row in labeled:
        if row["duplicate_group"] in conflicts:
            quarantine.append(row)
        else:
            eligible.append(row)
    grouped = components(eligible)
    representatives = []
    seen = set()
    for component, members in sorted(grouped.items()):
        for row in sorted(members, key=lambda r: r["source_row"]):
            assigned = dict(row, component=component)
            if row["duplicate_group"] in seen:
                duplicates.append(assigned)
            else:
                representatives.append(assigned)
                seen.add(row["duplicate_group"])
    summary = {
        "source_rows": len(rows),
        "unlabeled_excluded": sum(r["label"] is None for r in rows),
        "original_conflicting_orbit_groups": sum(len(v) > 1 for v in original_labels.values()),
        "conflicting_equivalence_groups": len(conflicts),
        "quarantined_labeled_rows": len(quarantine),
        "conflicting_labels": {k: sorted(labels_by_orbit[k]) for k in sorted(conflicts)},
        "consistent_labeled_rows": len(eligible),
        "deduplicated_rows": len(representatives),
        "duplicate_labeled_rows_removed": len(duplicates),
    }
    return (
        representatives,
        quarantine,
        {"summary": summary, "eligible_groups": grouped, "duplicates": duplicates},
    )


def assign_groups(rows: list[dict], config: dict) -> tuple[dict[str, str] | None, dict]:
    fractions = config["fractions"]
    names = list(fractions)
    weights = np.array(list(fractions.values()), dtype=float)
    if len(names) != 4 or set(names) != {"train", "validation", "calibration", "test"}:
        raise ValueError("Expected train, validation, calibration, test splits")
    if not np.isfinite(weights).all() or (weights <= 0).any() or not np.isclose(weights.sum(), 1):
        raise ValueError("Split fractions must be positive and sum to one")
    classes = sorted({row["label"] for row in rows})
    if len(classes) == 0:
        raise ValueError("No eligible labeled records")
    groups = defaultdict(list)
    for row in rows:
        groups[row["component"]].append(row)
    group_ids = sorted(groups)
    vectors = np.array(
        [
            [sum(r["label"] == label for r in groups[group]) for label in classes]
            for group in group_ids
        ],
        dtype=float,
    )
    totals = vectors.sum(axis=0)
    target = weights[:, None] * totals[None, :]
    minimum = np.array([config["minimum_per_class"][name] for name in names])[:, None]
    report = summarize_components(groups, classes)
    report["class_counts"] = dict(zip(classes, totals.astype(int).tolist(), strict=True))
    report["target_fractions"] = fractions
    tolerance = config["max_absolute_fraction_error"]
    if (
        report["largest_component_rows"] / len(rows) > weights.max() + tolerance
        or (totals < minimum.sum()).any()
        or min(report["class_component_support"].values()) < len(names)
    ):
        report["failure"] = "Indivisible components or class support prevent configured splits"
        return None, report
    best = None
    for attempt in range(config["attempts"]):
        rng = np.random.default_rng(config["seed"] + attempt)
        rarity = (vectors / totals).max(axis=1)
        tie_breaker = rng.random(len(group_ids))
        order = np.lexsort((tie_breaker, -rarity))
        counts = np.zeros_like(target)
        assignment = {}
        for index in order:
            vector = vectors[index]
            candidate_scores = []
            for split in range(len(names)):
                proposed = counts.copy()
                proposed[split] += vector
                class_error = np.square((proposed - target) / np.maximum(target, 1)).mean()
                size_error = np.square((proposed.sum(axis=1) / len(rows) - weights)).sum()
                candidate_scores.append(class_error + size_error)
            chosen = min(rng.permutation(len(names)), key=lambda s: candidate_scores[s])
            counts[chosen] += vector
            assignment[group_ids[index]] = names[chosen]
        observed = counts.sum(axis=1) / len(rows)
        valid = (counts >= minimum).all() and (abs(observed - weights) <= tolerance).all()
        score = np.square((counts - target) / np.maximum(target, 1)).mean()
        if valid and (best is None or score < best[0]):
            best = (float(score), assignment, counts, attempt)
    if best is None:
        report["failure"] = "Deterministic search found no assignment satisfying configured gates"
        return None, report
    _, assignment, counts, attempt = best
    report["assignment_attempt"] = attempt
    report["split_counts"] = {
        name: {
            "rows": int(counts[i].sum()),
            "class_counts": dict(zip(classes, counts[i].astype(int).tolist(), strict=True)),
        }
        for i, name in enumerate(names)
    }
    return assignment, report


def audit_splits(
    splits: dict[str, list[dict]], config: dict, require_unique_inputs: bool = True
) -> dict:
    """Fail closed on repeated IDs, lots, exact maps, transformations or components."""
    errors = []
    fields = ["row_id", "lot", "map_hash", "orbit_hash", "component"]
    for optional in ("duplicate_group", "input_hash", "input_orbit_hash"):
        if all(optional in row for records in splits.values() for row in records):
            fields.append(optional)
    if set(splits) != set(config["fractions"]):
        errors.append("Unexpected or missing split names")
    for field in fields:
        owner = {}
        for name, rows in splits.items():
            for row in rows:
                prior = owner.setdefault(row[field], name)
                if prior != name:
                    errors.append(f"{field} overlaps {prior}/{name}")
    total = sum(len(rows) for rows in splits.values())
    classes = {row["label"] for rows in splits.values() for row in rows}
    all_ids = [row["row_id"] for rows in splits.values() for row in rows]
    all_orbits = [row["orbit_hash"] for rows in splits.values() for row in rows]
    if len(all_ids) != len(set(all_ids)) or (
        require_unique_inputs and len(all_orbits) != len(set(all_orbits))
    ):
        errors.append("Representative row/orbit repeated")
    for name, fraction in config["fractions"].items():
        counts = Counter(row["label"] for row in splits.get(name, []))
        if None in counts:
            errors.append(f"{name}: missing ground-truth labels")
        if (
            total == 0
            or abs(len(splits.get(name, [])) / total - fraction)
            > config["max_absolute_fraction_error"]
        ):
            errors.append(f"{name}: size target violated")
        if any(counts[label] < config["minimum_per_class"][name] for label in classes):
            errors.append(f"{name}: class coverage violated")
    return {
        "passed": not errors,
        "errors": sorted(set(errors)),
        "checked_keys": fields,
        "transformed_duplicate_check": "Exact dihedral D4 rotations/reflections only",
        "approximate_duplicate_limit": "No guarantee against noise, crop or resize similarity",
    }


def encode_jsonl(rows: list[dict]) -> bytes:
    return "".join(
        json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
        for row in sorted(rows, key=lambda row: row["source_row"])
    ).encode()


def run(
    index_dir: Path, config_path: Path, output: Path, report_path: Path, processed_dir: Path
) -> bool:
    print("Verifying source and processed artifacts", flush=True)
    rows, manifest = read_index(index_dir)
    processed, processed_manifest = read_processed(processed_dir)
    if processed_manifest["identity"]["index_sha256"] != manifest["records_sha256"]:
        raise ValueError("Processed inputs belong to a different source index")
    by_id = {row["row_id"]: row for row in processed}
    if len(by_id) != manifest["labeled"] or len(processed) != len(by_id):
        raise ValueError("Processed input identities do not cover the labeled source exactly")
    for position, row in enumerate(rows):
        if row["label"] is not None:
            encoded = by_id.pop(row["row_id"])
            if any(encoded[key] != row[key] for key in row):
                raise ValueError("Processed metadata differs from original source identity")
            rows[position] = encoded
    if by_id:
        raise ValueError("Unknown processed source rows")
    print("Quarantining conflicts and forming indivisible components", flush=True)
    config = yaml.safe_load(config_path.read_text())
    if config["image_size"] != processed_manifest["identity"]["size"]:
        raise ValueError("Split configuration differs from materialized image size")
    classes = sorted(manifest["label_counts"])
    representatives, quarantine, preparation = prepare(rows)
    report = {
        "measured_at_utc": datetime.now(UTC).isoformat(),
        "source_archive_sha256": manifest["identity"]["archive_sha256"],
        "processed_manifest_sha256": sha256(processed_dir / "processed.json"),
        "processed_artifacts_sha256": processed_manifest["artifacts_sha256"],
        "index_sha256": manifest["records_sha256"],
        "config_sha256": sha256(config_path),
        "split_implementation_sha256": sha256(Path(__file__)),
        "preparation": preparation["summary"],
        "all_source_components": summarize_components(components(rows), classes),
        "eligible_before_dedup_components": summarize_components(
            preparation["eligible_groups"], classes
        ),
    }
    if sorted({row["label"] for row in representatives}) != classes:
        assignment, feasibility = None, {"failure": "Quarantine removed an expected class"}
    else:
        print("Searching deterministic class-balanced component assignments", flush=True)
        assignment, feasibility = assign_groups(representatives, config)
    report["feasibility"] = feasibility
    report["split_created"] = assignment is not None
    if assignment is None:
        report["next_decision"] = "Review component findings; do not fall back to random row splits"
        write_json(report_path, report)
        print(json.dumps(report, indent=2))
        return False
    splits = {name: [] for name in config["fractions"]}
    for row in representatives:
        splits[assignment[row["component"]]].append(row)
    report["leakage_audit"] = audit_splits(splits, config)
    expanded = {name: list(records) for name, records in splits.items()}
    for row in preparation["duplicates"]:
        expanded[assignment[row["component"]]].append(row)
    expanded_config = dict(config, max_absolute_fraction_error=1.0)
    # Balance applies to representatives. Expanded membership enforces identity boundaries.
    report["expanded_membership_audit"] = audit_splits(
        expanded, expanded_config, require_unique_inputs=False
    )
    if not report["expanded_membership_audit"]["passed"]:
        raise ValueError(report["expanded_membership_audit"]["errors"])
    if not report["leakage_audit"]["passed"]:
        raise ValueError(report["leakage_audit"]["errors"])
    output.mkdir(parents=True, exist_ok=True)
    content = {f"{name}.jsonl": encode_jsonl(records) for name, records in splits.items()}
    content["quarantine.jsonl"] = encode_jsonl(quarantine)
    duplicate_records = [
        dict(row, assigned_split=assignment[row["component"]]) for row in preparation["duplicates"]
    ]
    content["duplicate-membership.jsonl"] = encode_jsonl(duplicate_records)
    for filename, data in content.items():
        path = output / filename
        if path.exists() and path.read_bytes() != data:
            raise ValueError(
                "Immutable split differs; preserve it and choose a new output directory"
            )
    for filename, data in content.items():
        path = output / filename
        if not path.exists():
            with path.open("xb") as stream:
                stream.write(data)
    report["artifacts_sha256"] = {
        name: hashlib.sha256(data).hexdigest() for name, data in content.items()
    }
    report["next_decision"] = "Gate 2 review required before model training"
    write_json(report_path, report)
    print(json.dumps(report, indent=2))
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=Path("data/processed/index-v1"))
    parser.add_argument("--config", type=Path, default=Path("configs/split.yaml"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/splits-v2"))
    parser.add_argument("--report", type=Path, default=Path("reports/data/split-audit.json"))
    parser.add_argument("--processed", type=Path, default=Path("data/processed/categorical-64-v1"))
    args = parser.parse_args()
    if not run(args.index, args.config, args.output, args.report, args.processed):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
