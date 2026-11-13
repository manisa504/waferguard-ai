# Model card — first uncalibrated CNN baseline

**Status:** locally trained research baseline; not promoted or deployed. Model ID:
`gate3-v1-cnn-13a35b215f22`. **Known failure: Scratch recall is 0/117 on validation.** No automatic
acceptance is enabled. This model cannot authorize physical wafer release or real MES actions.

## Intended use and model identity

Educational nine-class WM-811K pattern classification and later simulated human review.
The selected candidate is a compact four-stage stride-two CNN with 173,441 parameters,
followed by a spatial classifier and dropout. It consumes categorical 64×64 one-hot
outside/pass/fail channels. Native source maps remain untouched; resizing can remove
small structures. Class order: Center, Donut, Edge-Loc, Edge-Ring, Loc, Near-full, None, Random, Scratch.

Local checkpoint: `artifacts/experiments/gate3-v1/cnn-best.pt`; SHA-256:
`13a35b215f2256e277eb7221fd0ad02d7bad228fdb9d38d0d83dcc5f68bd6709`. The experiment receipt pins source code, class order, training config,
dependency lock, split evidence and artifact hashes. Calibration version and validated
review-policy thresholds do not exist. Inference probabilities are uncalibrated.

## Training and measured scope

Trained on all 118,677 Gate 2 training representatives using CPU, four threads, seed 42,
AdamW and unweighted cross-entropy. Eight fixed epochs; checkpoint epoch
4 selected using validation macro-F1 only. No augmentation,
weighted loss, test-set model selection or online retraining. Validation has 17,021
records. Calibration and held-out test predictions were not computed.

| Model | Validation macro-F1 | Balanced accuracy | Accuracy |
|---|---:|---:|---:|
| majority | 0.1018 | 0.1111 | 0.8455 |
| forest | 0.7166 | 0.6629 | 0.9481 |
| cnn | 0.7707 | 0.7616 | 0.9666 |

These are validation measurements, not final held-out test results or production claims.
A high aggregate accuracy coexists with complete failure on Scratch; the model is not
suitable for automatic acceptance. Near-full validation support is only 15 records, so
its measured recall should not be generalized as a robust safety guarantee.

| Class | Validation support | Forest recall | CNN recall |
|---|---:|---:|---:|
| Center | 444 | 0.7140 | 0.8468 |
| Donut | 65 | 0.6923 | 0.8000 |
| Edge-Loc | 560 | 0.4411 | 0.7143 |
| Edge-Ring | 965 | 0.9347 | 0.9544 |
| Loc | 370 | 0.3649 | 0.7054 |
| Near-full | 15 | 0.8667 | 0.9333 |
| None | 14392 | 0.9998 | 0.9967 |
| Random | 93 | 0.9355 | 0.9032 |
| Scratch | 117 | 0.0171 | 0.0000 |

## Integrity, replay and local runtime

The frozen CNN replayed all 17,021 validation probability rows exactly. Forest replay
probabilities differed by at most 3.33e-16,
with identical aggregate classification metrics. Full training was not rerun from scratch;
seeded/pinned commands and epoch-boundary checkpoints are provided for repeatability.
Exact training equivalence across platforms/versions is not claimed.

Warm local CPU batch-one inference from an already encoded grid measured CNN p50
0.333 ms / p95 0.379 ms over 100 requests,
after 20 warmups. This includes one-hot conversion but excludes source resizing, integrity
checks, model loading, network and AWS cold starts. It is not an AWS/API latency or cost
benchmark. Checkpoint size: 698,833 bytes.

## Limitations and required next work

- Zero Scratch recall; uncertain/defect review behavior has not been validated.
- Severe class imbalance; weighted loss, sampling and controlled augmentation are next experiments.
- No temperature scaling, ECE/Brier analysis, risk-coverage policy, OOD or corruption validation yet.
- One training seed and one group-aware validation split; statistical confidence intervals and final test evaluation remain pending.
- Source/encoded exact and D4 grouping is audited; approximate duplicates and temporal/process independence remain limitations.
- Wafer geometry shortcuts and 64×64 representation loss have not been fully characterized.
- No registry promotion, deployed endpoint, authenticated reviewer workflow or automatic quality approval exists.

See [Gate 3 report](../reports/gates/gate_3.md), [measured experiments](../experiments/README.md),
[comparison figure](../reports/figures/gate3-v1/model-comparison.png) and
[raw CNN metrics](../reports/metrics/gate3-v1/cnn-validation.json). Gate 4 must address
imbalance and uncertainty before promotion is considered. Reviewer policies must be
assessed against errors, including defects confidently predicted as the None class.
