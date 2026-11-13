# Gate 2 — versioned data benchmark

Status: preprocessing, splits and measured integrity checks passed locally. Gate 3
now provides train/validation baseline measurements; see the [model card](model_card.md). Source: WM-811K v1; original archive SHA-256:
`0e4bd4316a110a04e475a88071f5e1c7fe4303b12ee53c851d2cae4d995a93e2`. Measured timestamp: `2026-11-11T01:32:06.416379+00:00`.

## Final cohort and class coverage

- Original source: 811,457 real records, including 638,507 unlabeled records excluded from supervision.
- Quarantine: 28 labeled records in 14 contradictory equivalence groups; no label voting or correction.
- Consistent copies removed: 3,263; the copy membership manifest preserves assignment and provenance.
- Final representatives: **169,659** across **10,113** indivisible lot/duplicate components.
- Largest final component: 9,423 representatives.

| Split | Rows | Center | Donut | Edge-Loc | Edge-Ring | Loc | Near-full | None | Random | Scratch |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| train | 118,677 | 2979 | 362 | 3518 | 6760 | 2482 | 96 | 101075 | 574 | 831 |
| validation | 17,021 | 444 | 65 | 560 | 965 | 370 | 15 | 14392 | 93 | 117 |
| calibration | 17,025 | 444 | 65 | 562 | 965 | 370 | 15 | 14391 | 96 | 117 |
| test | 16,936 | 419 | 63 | 503 | 965 | 350 | 15 | 14415 | 89 | 117 |

The requested proportions are 70/10/10/10; component sizes prevent exact stratification.
All actual split sizes pass the configured four-percentage-point tolerance. Every class
has at least 20 training and five records in each other split. These are dataset counts,
not predictions, model accuracy or evidence of industrial detection skill.

## Preprocessing and identities

Categorical nearest-neighbor sampling fits the aspect ratio in 64×64, with centered
outside-wafer padding. State meanings remain 0 outside, 1 pass, 2 fail. Original grids
are retained untouched; no fitted preprocessing, augmentation, or missing-label
imputation occurs. uint8 caches are converted to separate outside/pass/fail one-hot
float32 channels at load time. Small structures can be lost when downsampling; this
input size is a pilot engineering choice, not a validated optimum.

Two original maps may become identical after resizing. The preliminary original-grid
assessment retained 169,668 maps, while the final encoded-input-aware benchmark retains
169,659; **nine additional duplicate records** were removed. The preliminary
manifests are not the final benchmark. Source and encoded D4 identities (90-degree
rotations/reflections) are merged transitively before quarantine and lot grouping.

Deduplication occurs only after constructing all lot bridges. Source row IDs combine
the source archive hash and original row position. Original Training/Test annotations
remain available for provenance, but the original split is not used for this benchmark.

## Actual verification

[split-audit.json](../reports/data/split-audit.json) records zero observed cross-split
intersections for row IDs, lots, source hashes, original D4 hashes, components,
duplicate equivalence groups, encoded hashes and encoded D4 hashes. Expanded membership
also passes, including excluded consistent copies. These boundaries are checked
independently of the assignment search.

Two full split runs produced identical bytes/hashes for all six local manifests, as
recorded in [reproducibility.json](../reports/data/reproducibility.json). The real-data
loader passed first/last-record shape, dtype and one-hot checks for all four splits;
see [loader-smoke.json](../reports/data/loader-smoke.json). This bounded smoke check is
not a model evaluation or an exhaustive runtime transform test.

Arrays open read-only with `allow_pickle=False`. The loader verifies the processed
manifest, array and metadata hashes, selected split hash, counts and source identities
before returning a record. Synthetic tests cover tampering, lost lot bridges,
preprocessing-induced identity collisions, contradictory labels and immutable output
refusal; synthetic fixtures are never presented as real wafer maps.

## Reproduce and locate artifacts

```bash
./scripts/setup.sh
make index
make preprocess
make split
make verify-data
make check
```

All row-level artifacts remain local and ignored:

- `data/processed/index-v1/`: original source metadata index and integrity receipt.
- `data/processed/categorical-64-v1/`: `states.npy`, encoded metadata, processed receipt.
- `data/processed/splits-v2/`: train, validation, calibration, test, quarantine and copy-membership manifests.
- `data/processed/splits-v1/`: preliminary original-grid-only assignment, retained for traceability.

Publish only aggregate reports and artifact hashes. Changing configuration or encoded
inputs requires a new immutable artifact directory and a fresh audit. Cached inputs
are accepted only after their receipts and checksums match.

## Limitations and next gate

Lot identifiers are syntactically complete and source wafer IDs are unique, but their
process/temporal semantics are not independently authenticated. Exact/D4 checks do not
prove absence of noisy/cropped/approximate near-duplicates. Unlabeled records are excluded;
future semi-supervised training requires re-auditing all source relationships and exposure.
The source-wide component summary is descriptive, not the supervised grouping contract.

Class counts were used solely for deterministic split balancing and integrity checks.
Validation is reserved for hyperparameters/policy selection, calibration for probability
calibration, and held-out test for final model evaluation. No test predictions, model
metrics, threshold selection or training occurred at Gate 2. Gate 3 subsequently trained baselines using these fixed manifests; see the model card. AWS deployment and Gate 0 cloud checks remain pending.
