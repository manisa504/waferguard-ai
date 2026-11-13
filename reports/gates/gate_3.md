# Gate 3 — Baselines and first CNN

## Objective and authorization

Continue after the user authorized the next gate. Fit majority/classical baselines and
a first CNN on the audited real WM-811K training split. Store measured validation
metrics, model/config/input/code identity, raw local predictions and operational evidence.
Keep personal names out of content. No cloud deployment, reviewer application, model
promotion or automatic acceptance belongs to this gate.

## Environment / revision

Executed November 11, 2026, America/Los_Angeles. Local CPU with four training threads;
Python 3.12.13, NumPy 1.26.4, scikit-learn 1.9.1, PyTorch 2.15.0 and Matplotlib 3.11.2.
Dependencies are pinned in `uv.lock`; ML packages are optional under the `ml` extra.
Linux uses the explicit PyTorch CPU index rather than CUDA dependency packages.
No GPU or AWS training resource was rented. Hosted GitHub CI has not run.

The local main branch has no commit/remote. Experiment and gate source inventories
supply actual content hashes instead of an invented revision identifier. The experiment
receipt freezes source, config, dependency lock, class order, Gate 2 split evidence
and local model/prediction/feature artifacts. Gate 2 source metadata/config is preserved.

## Criteria and measured results

| Criterion | Result | Evidence |
|---|---|---|
| Train on audited real records only | PASS | 118,677 training representatives; original/encoded identity checks pinned to Gate 2 report |
| Majority reference fitted on training labels only | PASS | Validation macro-F1 0.1018; training majority class None |
| Classical feature baseline | PASS | 157 deterministic spatial features; unweighted 100-tree forest; validation macro-F1 0.7166 |
| First spatial CNN | PASS | 173,441 parameters; all eight full-data epochs completed; validation-selected epoch 4 |
| Actual raw classification measurements | PASS | All nine classes, per-class recall/precision/F1, confusion matrices, accuracy, balanced accuracy |
| Select checkpoints without held-out test feedback | PASS | Validation only; no calibration or test predictions computed |
| Reproducible experiment definition | PASS with replay limit | Pinned inputs/source/config, seed 42, CPU threads 4, deterministic algorithms; epoch-boundary state snapshots |
| Frozen model inference replay | PASS | CNN validation probabilities exact; forest differences <= 3.33e-16 with identical metrics |
| Source tests and integrity | PASS | 55 Python tests, lint and two CDK tests; guards reject test/calibration selection and changed completed model artifacts |
| Charts and model card | PASS | Actual validation comparison, confusion matrices and training curves; zero Scratch recall prominent |
| Model quality suitable for promotion/acceptance | NOT PASSED | Scratch recall 0/117; no calibration, selective-risk, robustness or final test evidence |

| Baseline | Validation macro-F1 | Balanced accuracy | Accuracy |
|---|---:|---:|---:|
| Majority | 0.1018 | 0.1111 | 0.8455 |
| Spatial-feature random forest | 0.7166 | 0.6629 | 0.9481 |
| Compact CNN, selected epoch 4 | 0.7707 | 0.7616 | 0.9666 |

All measurements use the same 17,021 validation records. The CNN's high aggregate
accuracy coexists with **zero correct Scratch predictions out of 117 validation cases**.
Of those Scratch cases, 89 were predicted as None. The forest recognizes only two.
This is an observed minority-class failure, not a solved detection problem. Near-full
recall is 14/15 for the CNN; the support is too small for a robust safety claim.

## Training procedure

The majority baseline uses training counts only. Classical features use per-grid local
occupancy/failure ratios, radial and angular densities, and spatial failure moments;
no label, lot ID or learned preprocessing statistic enters the feature vector. The
forest uses 100 trees, maximum depth 18, minimum leaf size two and no class weights.

The CNN has four stride-two convolution blocks with 12/24/48/64 channels, a spatial
128-unit classifier and dropout 0.1. AdamW, learning rate .001, weight decay .0001,
batch 256, seed 42, eight fixed epochs, unweighted cross-entropy and no augmentation.
Only training batches receive gradient updates. Validation macro-F1 selects the best
checkpoint; eight epochs were not chosen using test results. Calibration and held-out
test remain reserved for later stages. The final epoch had validation macro-F1 0.7521;
the checkpoint selection correctly retained epoch 4's 0.7707 instead.

## Commands and stored evidence

```bash
uv sync --extra dev --extra ml --frozen
uv run --frozen --extra ml --extra dev waferguard-train
uv run --frozen --extra ml --extra dev python scripts/verify_gate3.py
uv run --frozen --extra ml --extra dev python scripts/plot_gate3.py
uv run --frozen --extra ml --extra dev pytest -q
uv run --frozen --extra ml --extra dev ruff check .
uv lock --check
python3 scripts/check_tracked_files.py
# Infrastructure regression checks:
cd infrastructure/cdk && npm test
```

- [Experiment receipt](../metrics/gate3-v1/experiment.json): exact config, source/lock/input/model hashes and validation selection.
- [Training log](../metrics/gate3-v1/training.log) and [epoch history](../metrics/gate3-v1/cnn-history.json): actual progress, loss, timing and metrics for every epoch.
- [Majority](../metrics/gate3-v1/majority-validation.json), [forest](../metrics/gate3-v1/forest-validation.json), [CNN](../metrics/gate3-v1/cnn-validation.json): raw aggregate classification metrics.
- [Replay](../metrics/gate3-v1/replay.json) and [verification log](../metrics/gate3-v1/verification.log): checksum-verified model reload and all validation predictions replayed.
- [Local inference measurement](../metrics/gate3-v1/local-inference.json): 100 warm batch-one requests after 20 warmups.
- [Test output](gate_3-tests.log) and [CDK output](gate_3-cdk-tests.log): actual passing checks.
- [Comparison figure](../figures/gate3-v1/model-comparison.png), [CNN confusion](../figures/gate3-v1/cnn-confusion.png), [forest confusion](../figures/gate3-v1/forest-confusion.png), [training history figure](../figures/gate3-v1/cnn-training.png): PNG and SVG exports from measured JSON, visually reviewed.
- [Model card](../../DOC/model_card.md), [experiment instructions](../../experiments/README.md), and [gate source inventory](gate_3-source-manifest.json).

Local artifacts under ignored `artifacts/experiments/gate3-v1/` include forest.joblib,
cnn-best.pt, optimizer/RNG resume state, feature matrices and per-case validation
predictions with true labels/row IDs. These are not committed or published. The default
completed run verifies hashes and refuses changed artifacts/config/source rather than
silently retraining under the same identity. Use a new run/report directory for a fresh
training repetition, as documented in experiments/README.md.

## Local runtime measurement and limits

CNN checkpoint size is 698,833 bytes; forest artifact is 6,223,991 bytes. Warm local
CPU inference from encoded 64×64 grids measured CNN p50 0.333 ms / p95 0.379 ms;
forest p50 15.895 ms / p95 16.695 ms. This includes one-hot conversion or feature
extraction and excludes raw-grid resizing, integrity verification, loading, network,
AWS cold starts and API overhead. It is neither a production/API benchmark nor a
cost-per-prediction claim. Small warm samples and host load limit generalization.

## Scientific, security and operational limitations

Full training was not repeated from scratch; empirically verified repeatability is
frozen-model validation inference plus synthetic save/reload contracts. Seeded/pinned
training and epoch-boundary checkpoints are provided; exact equivalence across
platforms, versions or hardware is not promised. This is one seed and one validation
partition, without statistical confidence intervals or independent final test results.

Models are uncalibrated. ECE/Brier analysis, temperature scaling, risk-coverage policies,
class weighting/sampling/augmentation and OOD/corruption analysis are Gate 4 work.
The Scratch failure blocks any acceptance claim. Uncertainty alone must not be assumed
to catch defects confidently predicted as None. The acceptance policy remains inactive.

Existing data provenance, approximate-duplicate, lot/temporal semantics and resolution
limitations remain. No human label correction or invented unlabeled ground truth was
introduced. Local forest joblib is loaded only after trusted receipt verification; do
not load arbitrary external joblib/pickle. CNN loading uses weights_only=True.

No AWS mutation, endpoint, registry promotion, frontend, authenticated review workflow,
GPU rental or GitHub publication occurred. Gate 0 cloud checks and the recorded CDK
advisory remain outstanding. CI now includes synthetic ML contracts with Linux CPU
packages, but no hosted CI or real-dataset training occurs in that job.

## Pass/fail and next-gate decision

**Gate 3 baseline implementation and stored measured validation evidence: PASS.**
**Promotion, calibrated confidence and automatic-accept readiness: NOT PASSED.**

Review before Gate 4, as outline section 10 requires “Stop for review between gates.”
Prioritize minority Scratch recall using controlled imbalance experiments, then fit
calibration on the reserved calibration split and select review policies using validation
evidence. Freeze candidate/model/policy choices before final held-out test evaluation.
No test-based tuning or silently enabling auto-accept is permitted.
