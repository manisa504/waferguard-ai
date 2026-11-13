# Gate 4 — uncertainty and failed release qualification

**Status: analysis complete; promotion and operational automatic acceptance blocked.**
Measured November 12–13, 2026. The model met the validation selection constraints but
failed them on the frozen held-out test. No thresholds/model were retuned after testing.

## Classification and imbalance experiments

| Experiment | Validation macro-F1 | Validation Scratch recall |
|---|---:|---:|
| weighted | 0.8074 | 0.3590 |
| sampled | 0.8209 | 0.4701 |
| weighted_augmented | 0.7921 | 0.2308 |
| lite_weighted | 0.7861 | 0.2821 |
| balanced + D4, selected epoch 2 | 0.7881 | 0.7521 |

All use the fixed Gate 2 data. The first four experiments used seed 43 and eight epochs:
inverse-square-root class loss, inverse-square-root sampling, weighted D4 augmentation,
and a second lightweight depthwise CNN. No first-round candidate met 60% Scratch recall.
An eight-epoch inverse-frequency-loss fine-tune also failed that recall constraint;
its maximum observed recall was 58.97%. These failed results are preserved.

The selected additional run fine-tunes the sampled parent with equal-class sampling,
unweighted loss, D4 transforms, optimizer reset, lower learning rate .0003 and seed 45.
It draws 118,677 samples per epoch **with replacement**, rather than claiming that every
unique training row is seen in each epoch. Actual class exposure and unique-row counts
are stored in its history. The combined changes are a remedy, not a single-factor causal
ablation. Eight epochs were fixed; maximum validation macro-F1 subject to Scratch recall
>=60% selected epoch 2. Neither calibration nor test labels selected the checkpoint.

| Frozen model measurement | Validation | Held-out test |
|---|---:|---:|
| Records | 17,021 | 16,936 |
| Macro-F1 | 0.7881 | 0.7265 |
| Scratch recall | 0.7521 | 0.5556 |
| Scratch precision | 0.1369 | 0.0994 |
| Overall ECE after scaling | 0.0145 | 0.0177 |

Test macro-F1's connected-component bootstrap 95% interval is
[0.6652, 0.8313] (200 resamples).
This is a descriptive interval on the observed groups, not proof of industrial independence
or a statistically established cause for the point-estimate gap.

## Calibration and class-conditional limitations

Scalar temperature **0.875128** was fitted using only 17,025 calibration
records. Validation ECE fell from 0.0295 to
0.0145. Temperature scaling preserves predicted argmax classes.
Brier uses the mean sum of squared probability errors across all nine classes; ECE uses
15 equal-width top-confidence bins. Class-conditional statistics are also stored.

The low overall ECE hides a serious subgroup failure: among test predictions labelled
Scratch, precision is only 0.0994, and
predicted-Scratch conditional ECE is 0.5156.
Global calibration must not be interpreted as reliable confidence for every minority class.

## Frozen selective policy — analysis only, not authorized for use

The validation-selected confidence threshold was 0.94,
with minimum class margin .20, a training-only feature-distance OOD guard, and mandatory
review for predictions labelled Scratch or Near-full. Selection also required no observed
critical-class false accepts on validation. No test-based threshold selection occurred.

On test the **unchanged candidate** would accept 62.12% and review
37.88%. Among 10,520 accepted predictions it made
88 errors (0.84%; 95% Wilson upper bound
1.03%), including **four false accepts of true Scratch cases**.
A rule that reviews only predictions *labelled* critical cannot catch every critical case
confidently labelled as another class. Therefore the research candidate is **not promoted**,
and operational automatic acceptance stays disabled. These coverage numbers are offline
measurements, not live review savings, production success or a safety guarantee.

## Robustness checks

The feature-distance guard fits only training feature means/scales and a 99.5th-percentile
training threshold. It flagged all 256 engineered random OOD grids, although the model's
mean confidence on them was almost one. It flagged zero of 256 wafer maps with 5% die-state
flips; the candidate policy reviewed only 41.8% of those altered maps. This is a narrow
stress result, not universal OOD/corruption detection. No ground-truth class labels are
invented for these synthetic or altered inputs. Empty/all-outside, illegal-state and
oversized inputs are rejected before model execution, as covered by tests.

## Per-class recall and test precision

| Class | Validation recall | Test recall | Test precision |
|---|---:|---:|---:|
| Center | 0.9640 | 0.9642 | 0.8096 |
| Donut | 0.9385 | 0.9683 | 0.7531 |
| Edge-Loc | 0.8250 | 0.8588 | 0.6381 |
| Edge-Ring | 0.9772 | 0.9710 | 0.8668 |
| Loc | 0.7541 | 0.5886 | 0.4736 |
| Near-full | 1.0000 | 0.8000 | 0.8571 |
| None | 0.9324 | 0.9202 | 0.9937 |
| Random | 0.9892 | 0.9101 | 0.5510 |
| Scratch | 0.7521 | 0.5556 | 0.0994 |

## Integrity, reproducibility and next decision

The model, temperature, policy and OOD artifacts plus scientific implementation hashes
were frozen before test evaluation. [frozen.json](../reports/metrics/gate4-final/frozen.json)
and [test.json](../reports/metrics/gate4-final/test.json) bind the exact configuration.
The runner refuses changed frozen inputs and does not rerun or retune an already-recorded
test evaluation. Cluster-bootstrap intervals and class diagnostics are descriptive;
they do not change weights, temperature, candidate or threshold. Source training snapshots
and per-case arrays stay local and ignored. Public failure logs redact local home paths
only; originals are preserved privately, and measured epoch values are unchanged.

The test set is now observed and must not be represented as untouched in subsequent
experiments. Any additional model investigation needs an explicit evaluation protocol;
no reshuffling to erase this failure or test-driven threshold tuning is permitted.

Your instruction is to keep individual gate reviews. Review the failed qualification
before deciding whether to investigate modelling further or proceed with a clearly marked,
manual-review-only research workflow. Future review/API source modules are drafts, not
completed/deployed Gate 5 evidence. No live model, API, reviewer or AWS release is claimed.

[Gate report](../reports/gates/gate_4.md) · [qualification](../reports/metrics/gate4-final/qualification.json) ·
[recall/calibration figure](../reports/figures/gate4-v1/recall-calibration.png) ·
[risk-coverage figure](../reports/figures/gate4-v1/risk-coverage.png) ·
[test confusion matrix](../reports/figures/gate4-v1/test-confusion.png)
