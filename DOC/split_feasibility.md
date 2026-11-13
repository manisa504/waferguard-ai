# Split feasibility and resulting decision

Gate 1 found 3,158 exact map groups spanning the source Training/Test assignments,
despite zero shared lot names. The source has 46,293 unique lot names and no duplicate
(lotName, waferIndex) IDs; these identifiers alone do not establish independence.

**Gate 2 result: a lot- and duplicate-component split is feasible.** No random-row
fallback was used. The benchmark joins original and encoded D4 identity connections
before removing consistent copies, preserving lot bridges. Conflicting groups are
quarantined, not relabeled. Unlabeled source records are not used for supervision.

The resulting 10,113 components contain 169,659 representatives;
the largest has 9,423 records. All nine classes occur in train,
validation, calibration and held-out test. Both representative and expanded-membership
boundary checks pass. Encoded-input auditing caught nine additional copies that an
original-grid-only audit would have missed.

See [benchmark.md](benchmark.md) for actual split/class counts, preprocessing contracts,
commands, hash-bound artifacts and residual limits. [split-audit.json](../reports/data/split-audit.json)
is the final machine-readable evidence. The earlier original-grid-only result is kept
as `reports/data/source-grid-split-audit.json` and is not the final training benchmark.

Group semantics, approximate duplicates and temporal independence remain limitations;
there is no claim of complete real-world independence. Future input transformations,
unlabeled-data exposure or human label corrections require a fresh versioned audit.

**Current state:** Gate 3 has trained baselines using these fixed manifests and measured
validation performance. No calibration or held-out test predictions were used for model
selection. See the [model card](model_card.md) for the Scratch failure and Gate 4 work.
