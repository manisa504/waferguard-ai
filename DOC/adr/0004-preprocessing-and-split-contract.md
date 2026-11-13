# ADR 0004 — Categorical inputs and indivisible benchmark groups

Status: implemented at Gate 2; model training awaits gate review.

Preserve original source row identities and lot/wafer identifiers. An empty failureType
stays unlabeled. Labeled records alone enter this supervised benchmark. Never use the
original Training/Test annotations as a leakage-free benchmark: Gate 1 found identical
maps shared across those assignments.

Encode a pilot 64×64 square with aspect-preserving categorical nearest-neighbor sampling
and centered outside-wafer padding. Store uint8 states locally; expose separate float32
outside/passing/failing channels when loading a record. No interpolated grayscale, fitted
normalization, label imputation, or augmentation is performed. Native originals remain
untouched. Resampling can remove small features; 64×64 is an engineering starting point,
not an experimentally established optimum. Future size changes require versioned inputs
and a fresh identity/split audit before any benchmark comparison.

Identify duplicates using both original and encoded grids under exact 90-degree rotations
and reflections (D4). Merge these equivalence relations transitively. Quarantine all labeled
members of groups with contradictory annotations, without voting or inventing a label.
Before removing consistent copies, join lots through every duplicate connection. Choose
the first source row as each consistent group's reproducible representative. This avoids
losing a lot bridge when a nonrepresentative copy is removed.

Assign entire connected components with a seeded, deterministic class-balance search.
The proposed fractions are 70% train and 10% each validation, calibration and test. Size
fractions must be within four percentage points of their targets; every class must have
at least 20 training and five records in each other split. Save the actual class table,
not a claim of exact stratification. Fixed search attempts minimize a class/size balance
objective using label counts only, never model predictions or test performance.

Audit representatives and expanded membership separately. No lot, component, source map,
original D4 identity, encoded map or encoded D4 identity may cross boundaries. Keep
excluded copies in a separate membership manifest linked to the representative's split.
Local manifests and arrays are immutable by checksum; reruns must reproduce identical
manifest bytes, and changed existing artifacts must be refused.

All row-level indices, categorical arrays, quarantine and split manifests stay in ignored
`data/processed/`. Publish aggregate audits and hashes only. Unlabeled records are excluded,
so future semi-supervised training requires a fresh grouping/exposure audit; their hidden
links must not be assumed safe. Exact/D4 checks do not prove absence of noisy, cropped or
otherwise approximate near-duplicates, nor do identifiers establish temporal independence.

Validation is for hyperparameters and policy selection; calibration fits probability
calibration; the held-out test is reserved for final model evaluation. Gate 2 only inspects
class counts, identities and input integrity. No model is trained or evaluated here.
