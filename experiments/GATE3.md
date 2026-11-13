# Gate 3 experiments — measured local baselines

Run: `gate3-v1`, completed locally November 11, 2026. Candidate selected on validation:
**CNN, epoch 4**. No calibration or held-out test evaluation occurred.
Known failure: **CNN recognized zero of 117 validation Scratch cases.**

| Model | Validation macro-F1 | Balanced accuracy | Accuracy |
|---|---:|---:|---:|
| majority | 0.1018 | 0.1111 | 0.8455 |
| forest | 0.7166 | 0.6629 | 0.9481 |
| cnn | 0.7707 | 0.7616 | 0.9666 |

- Majority chooses the most frequent training label only (None).
- Classical baseline: 100 unweighted random-forest trees, depth 18, minimum leaf 2,
  157 per-grid spatial die features: local occupancy/failure ratios, radial/angular
  densities and failure-location moments. No label or lot ID is an input feature.
- CNN: 173,441 parameters; four stride-two convolution stages with 12/24/48/64 channels,
  spatial dense layer, dropout 0.1, unweighted cross-entropy and AdamW. Eight full-data
  epochs, batch 256, learning rate .001, weight decay .0001, seed 42, CPU threads 4.
- Checkpoint selection uses validation macro-F1; hyperparameters were fixed in the run
  config before training. Neither calibration nor test predictions are used for selection.

## Reproduce

```bash
uv sync --extra dev --extra ml --frozen
# Requires the exact real dataset and passing Gate 2 artifacts:
make split
make train
# With completed local artifacts, replay inference and generate measured figures:
uv run --frozen --extra ml --extra dev python scripts/verify_gate3.py
uv run --frozen --extra ml --extra dev python scripts/plot_gate3.py
make check-ml
```

The default completed run is immutable and verifies artifact hashes before reuse.
To rerun training from scratch in a separate directory:

```bash
uv run --frozen --extra ml --extra dev waferguard-train \
  --run artifacts/experiments/gate3-reproduction \
  --reports reports/metrics/gate3-reproduction
```

Use the same config, dependency lock, CPU/thread settings, source and split hashes.
Epoch-boundary model/optimizer/RNG snapshots support resuming an interrupted compatible
run. A changed code/config/environment receipt requires a new run directory. Reloaded
CNN probabilities matched exactly on validation; forest differences were at floating-point
roundoff with identical classification metrics. Full retraining equivalence has not been
empirically tested, and cross-platform exact replay is not guaranteed.

## Evidence and artifact boundaries

[experiment.json](../reports/metrics/gate3-v1/experiment.json) contains code/config/lock,
class ordering, split evidence, model hashes and selected checkpoint.
[cnn-history.json](../reports/metrics/gate3-v1/cnn-history.json) stores each epoch's actual
loss and validation metrics. [replay.json](../reports/metrics/gate3-v1/replay.json) records
full validation inference replay; [local-inference.json](../reports/metrics/gate3-v1/local-inference.json)
records a small warm local benchmark with explicit scope. Raw per-case labels/probabilities,
features and model weights remain ignored under `artifacts/experiments/gate3-v1/`.
Only aggregate reports/figures and source are included in the repository.

Local `.joblib` loading is restricted to a locally trained, checksum-verified forest.
Never load arbitrary external joblib/pickle files. CNN replay uses `weights_only=True`.
The source data loader, encoded input hashes and observed grouping controls remain as
specified in [benchmark.md](../DOC/benchmark.md).

## Interpretation and next gate

The selected CNN improves validation macro-F1 over both baselines but misses every
Scratch case. The majority baseline's 84.55% validation accuracy illustrates imbalance;
accuracy alone is inadequate. No detection-safety, calibrated confidence, final test
performance, deployment or cost-improvement claim follows from these results.

Review Gate 3 before class-imbalance, calibration, selective-risk and robustness work at
Gate 4. Keep the calibration and test splits reserved. Maintain an inactive acceptance
policy until the corresponding evaluation and human-authorization gates pass.

Implementation references: [PyTorch reproducibility](https://docs.pytorch.org/docs/2.15/notes/randomness.html),
[RandomForestClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html),
[macro-F1 definition](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html).
