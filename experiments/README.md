# Measured experiment history

Current status: **Gate 4 evidence complete, release qualification failed**. No promotion
or live automatic acceptance is enabled. Keep individual gate reviews.

- [Gate 3 baselines and reproducibility](GATE3.md): historical validation-only run.
- [Gate 4 results and failure analysis](../DOC/uncertainty_results.md): imbalance trials,
  calibration, frozen test, stress checks and known limitations.
- [Current model card](../DOC/model_card.md).
- [Gate 4 report](../reports/gates/gate_4.md).

The balanced candidate's validation macro-F1 was .7881 and Scratch recall .7521. Its
frozen test macro-F1 was .7265 and Scratch recall .5556; four true Scratch cases were
falsely accepted by the unchanged offline candidate policy. Overall ECE improved but
minority-class precision/calibration remained poor. No settings were retuned on test.

The test set is now observed. Further modelling requires a reviewed evaluation protocol;
do not silently reshuffle data, tune against test, or describe it as untouched.

## Reproduce measurements

```bash
uv sync --extra dev --extra ml --extra api --frozen
# Existing real Gate 2 artifacts are required; no synthetic wafer substitutes.
uv run --frozen --extra ml --extra api --extra dev python -m waferguard.training.advanced
uv run --frozen --extra ml --extra api --extra dev python -m waferguard.training.refine
uv run --frozen --extra ml --extra api --extra dev python -m waferguard.training.balanced
uv run --frozen --extra ml --extra api --extra dev python -m waferguard.evaluation.advanced fit \
  --candidate artifacts/experiments/gate4-balanced-v1
uv run --frozen --extra ml --extra api --extra dev python -m waferguard.evaluation.advanced test
uv run --frozen --extra ml --extra api --extra dev python scripts/assess_gate4.py
uv run --frozen --extra ml --extra api --extra dev python scripts/plot_gate4.py
```

Preserve original configs/source snapshots: the first two completed training procedures
intentionally failed their recall-selection gates. Existing experiment identities and
frozen releases are protected; use new directories for a genuinely new reviewed run.
A stored frozen test is not rerun or used for selection. Raw per-case arrays, model
weights, original error logs and historical source snapshots remain ignored in artifacts/.
Source/config/lock hashes and aggregate metrics are provided; full retraining equivalence
was not empirically repeated.

Future review/API modules are drafts and not a passed Gate 5. The inference loader rejects
unqualified release manifests. No live AWS workload or human authorization is claimed.
