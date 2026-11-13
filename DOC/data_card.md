# WM-811K data card

Measured 2026-11-10T16:38:18.569851-08:00 (America/Los_Angeles), using NumPy 1.26.4 /
pandas 2.2.3. Source: [Kaggle WM-811K v1](https://www.kaggle.com/datasets/qingyi/wm811k-wafer-map).
[Rights review](data_rights_review.md) · [acquisition manifest](../data/manifests/acquisition.json) ·
[raw quality JSON](../reports/data/quality.json).

## Provenance and representation

Real wafer maps; no fabricated samples. Original zip retained locally without modification.
Archive bytes: 156,686,283; uncompressed `LSWMD.pkl`: 2,095,505,977 bytes.
Archive SHA-256: `0e4bd4316a110a04e475a88071f5e1c7fe4303b12ee53c851d2cae4d995a93e2`. No independent publisher checksum was available.
The mirror's metadata lists CC0; original-owner rights were not independently verified.
Raw maps and derived examples are excluded from Git and not redistributed.

Each map is a two-dimensional categorical die grid: 0 = outside/no die, 1 = passing die,
2 = failing die. Original columns: `waferMap`, `dieSize`, `lotName`, `waferIndex`, `trianTestLabel`, `failureType`.
The source spelling `trianTestLabel` is preserved. Arrays were neither resized nor interpolated.

## Measured quality

| Measurement | Observed |
|---|---:|
| Total maps | 811,457 |
| Labeled maps | 172,950 |
| Missing labels | 638,507 |
| Invalid maps / labels | 0 / 0 |
| Distinct shapes | 632 |
| Height range | 6–300 |
| Width range | 3–205 |
| Unique lot names | 46,293 |
| Missing/invalid identifiers | 0 |
| Duplicate (lotName, waferIndex) identifiers | 0 |
| Unique exact maps, all records | 696,599 |
| Duplicate map rows beyond first occurrence | 114,858 |
| Unique labeled maps | 169,698 |
| Duplicate labeled map rows | 3,252 |
| Map groups with conflicting non-missing labels | 14 |
| Duplicate map groups spanning lots | 32,392 |
| Shared Training/Test map groups | 3,158 |
| Shared Training/Test lots | 0 |

| Class | Labeled records |
|---|---:|
| Center | 4,294 |
| Donut | 555 |
| Edge-Loc | 5,189 |
| Edge-Ring | 9,680 |
| Loc | 3,593 |
| Near-full | 149 |
| None | 147,431 |
| Random | 866 |
| Scratch | 1,193 |

`none` maps to the named `None` class; an empty failureType array remains missing.
All nine measured class counts match the outline's expectations. The measured 46,293 lot
names differ from the source description's 46,393 lots; that discrepancy remains documented.
A quality validation pass confirms counts/encodings, not a leakage-free benchmark or
label correctness. Conflicting map hashes/classes are saved in the quality JSON.

## Usage limits and next gate

These annotations identify pattern classes; they do not authorize physical wafer release.
The None majority is substantial and Near-full has only 149 labels.
Use macro-F1 and per-class recall, not accuracy alone. Do not silently invent missing labels.
Approximate duplicates, lot semantics and temporal independence remain limitations.
Exact rotations/reflections are now audited at Gate 2.
Gate 2 now provides versioned train/validation/calibration/test splits after conflict
quarantine, duplicate grouping and encoded-input audits. Gate 3 now reports validation
measurements in the [model card](model_card.md); no raw sample map is published. See [benchmark](benchmark.md) and
[split feasibility](split_feasibility.md) for the final cohort and limitations.
