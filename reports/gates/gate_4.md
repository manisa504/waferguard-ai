# Gate 4 — Imbalance, calibration, selective classification and stress tests

## Decision

**Measured work complete; model release qualification FAILED. HOLD for individual gate review.**
No promotion, active automatic acceptance, deployment or further test-based tuning is authorized.

The frozen candidate scored test macro-F1 **0.7265**, Scratch recall **0.5556** and Scratch
precision **0.0994**. Its unchanged candidate policy falsely accepted **four true Scratch
cases**. These results fail the declared classification benchmarks and critical-case
requirement. Passing implementation tests does not overturn failed model qualification.

## Objective and scope

Investigate the Gate 3 Scratch failure using controlled imbalance experiments, compare a
second lightweight architecture, fit temperature scaling using calibration data, select
an abstention policy on validation, freeze scientific inputs and evaluate test once.
Measure limited engineered corruption/OOD behavior. Keep failed experiments and all
limitations visible. The user's latest preference explicitly retains review between gates.

Future API/review components were prepared as drafts while scope was being clarified.
They are not deployed, not Gate 5 completion evidence, and not an active reviewer service.

## Environment / revision

Measured November 12–13, 2026, America/Los_Angeles. Local CPU, four training threads;
Python 3.12.13, NumPy 1.26.4, PyTorch 2.15.0, scikit-learn 1.9.1 and SciPy 1.17.1.
The locked optional ML/API dependencies are in uv.lock. No paid GPU or AWS workload was
created. The local main branch has no commit or remote publication; content hashes,
source snapshots and artifact receipts supply revision evidence. See
[gate_4-source-manifest.json](gate_4-source-manifest.json).

## Criteria and actual evidence

| Criterion | Result | Evidence |
|---|---|---|
| Real audited data, no invented labels | PASS | Unchanged Gate 2 train/validation/calibration/test manifests and encoded data |
| Weighted loss, sampling, controlled augmentation | MEASURED | Four initial eight-epoch experiments; no initial candidate met 60% Scratch recall |
| Second lightweight architecture | MEASURED | Depthwise CNN comparison; validation macro-F1 0.7861, Scratch recall 0.2821 |
| Stronger weighting remedy | MEASURED; selection gate FAIL | Eight-epoch inverse-frequency fine-tune; maximum Scratch recall 0.5897 |
| Balanced sampling remedy | VALIDATION PASS | Equal-class replacement draws with D4 transforms; selected epoch 2 macro-F1 0.7881 / Scratch recall 0.7521 |
| Calibration partition separation | PASS | Temperature fitted on 17,025 calibration records only; validation selects policy |
| Calibration metrics and figures | MEASURED | Overall/per-class ECE, summed multiclass Brier, NLL, reliability data and figures |
| Frozen selective classification | MEASURED | Threshold .94, margin .20, critical predicted classes always reviewed, training-only OOD guard |
| Freeze before held-out evaluation | PASS | Model/calibration/policy/OOD plus scientific hashes frozen before test; no retuning |
| Held-out classification qualification | FAIL | Macro-F1 .7265 < .75; Scratch recall .5556 < .60 |
| Critical false-accept requirement | FAIL | Four true Scratch cases accepted by the frozen offline candidate |
| Limited OOD/corruption checks | MEASURED WITH LIMITS | Random OOD detected; mild categorical corruption not flagged by distance guard |
| Source/math/security tests | PASS | 70 Python tests; includes six preliminary review tests, not a live Gate 5 demonstration |
| Release enforcement | PASS | Qualification records promotion blocked; inference refuses unqualified manifests; global acceptance stays disabled |

## Actual classification and routing results

| Measurement | Validation | Test |
|---|---:|---:|
| Records | 17,021 | 16,936 |
| Macro-F1 | 0.7881 | 0.7265 |
| Balanced accuracy | 0.9036 | 0.8374 |
| Accuracy | 0.9275 | 0.9130 |
| Scratch recall | 0.7521 | 0.5556 |
| Scratch precision | 0.1369 | 0.0994 |
| Overall ECE after scaling | 0.0145 | 0.0177 |
| Offline candidate coverage | 0.6813 | 0.6212 |
| Offline accepted errors / accepted | 55 / 11,597 | 88 / 10,520 |
| Offline critical false accepts | 0 | 4 |

The test candidate's empirical accepted error was 0.8365%, with 95% Wilson upper bound
1.0294%. Although these aggregate figures pass the global configured limits, the critical
false accepts and classification criteria fail. Coverage is an offline counterfactual,
not active review savings. Operational acceptance remains disabled. Reviewing only
predictions labelled critical cannot catch every critical case labelled as another class.

## Experimental procedure

Initial experiments use the fixed audited train split, seed 43 and eight epochs each:
inverse-square-root loss weighting, inverse-square-root replacement sampling, weighted
categorical D4 augmentation, and a lightweight depthwise architecture. Their actual best
validation macro-F1 / Scratch recall pairs are .8074/.3590, .8209/.4701, .7921/.2308 and
.7861/.2821. All failed the predeclared 60% recall selection gate; results were not discarded.

An additional inverse-frequency weighted fine-tune from the sampled parent, seed 44,
optimizer reset and lower learning rate also failed after eight epochs. Its best macro-F1
was .7965 with .5128 Scratch recall; its maximum Scratch recall across epochs was .5897.

The final remedy uses seed 45, equal-class replacement sampling, unweighted cross-entropy,
D4 transforms, optimizer reset and learning rate .0003 from the sampled parent. It makes
118,677 training draws per epoch; history records actual class counts and unique source
rows. It does not claim every unique row is observed per epoch. All transforms remain
inside training. The combined intervention is not a single-factor causal ablation.
Maximum validation macro-F1 subject to Scratch recall >=.60 selects epoch 2 out of eight.
No calibration/test observations choose the checkpoint.

Temperature .875128 is fitted only on calibration data. Calibration NLL improves from
.244099 to .241033, and validation ECE changes from .029549 to .014472. Temperature
preserves class argmax. Overall calibration hides severe subgroup weakness: predicted-
Scratch conditional test ECE is .5156. Class-conditional diagnostics and low precision
must accompany the attractive global ECE.

The frozen threshold .94 requires margin >=.20, no training-distance OOD flag, and
mandatory review for predicted Scratch/Near-full. Validation selection required zero
observed critical false accepts, accepted error <=1%, Wilson upper <=2% and at least
500 accepted records. Scientific artifacts and implementation hashes are frozen before
test. Test macro-F1's connected-component-bootstrap 95% interval is [.6652,.8313] over
200 replicates; this is descriptive benchmark uncertainty, not industrial independence
or a significance claim. No new candidate/temperature/threshold was selected after test.

## Robustness and invalid-input evidence

The standardized feature-distance guard uses only training means/scales and a 99.5th
training percentile. All 256 engineered random OOD grids were flagged and routed to
review by the candidate policy, despite model mean confidence nearly one. None of 256
maps with 5% die-state flips were flagged by that guard; candidate review rate was
41.8%. This narrow stress behavior does not establish broad OOD/corruption detection.
No ground-truth labels were invented for altered or random inputs. Input-contract tests
reject empty/all-outside, illegal states, nonfinite states and oversized grids before
model execution. There is no deployed API validity claim.

## Commands and stored artifacts

```bash
uv run --frozen --extra ml --extra api --extra dev python -m waferguard.training.advanced
uv run --frozen --extra ml --extra api --extra dev python -m waferguard.training.refine
uv run --frozen --extra ml --extra api --extra dev python -m waferguard.training.balanced
uv run --frozen --extra ml --extra api --extra dev python -m waferguard.evaluation.advanced fit \
  --candidate artifacts/experiments/gate4-balanced-v1
uv run --frozen --extra ml --extra api --extra dev python -m waferguard.evaluation.advanced test
uv run --frozen --extra ml --extra api --extra dev python scripts/assess_gate4.py
uv run --frozen --extra ml --extra api --extra dev python scripts/plot_gate4.py
uv run --frozen --extra ml --extra api --extra dev pytest -q
uv run --frozen --extra ml --extra api --extra dev ruff check .
```

The first two training commands intentionally exit with failed selection gates after
completing their experiments. Preserve existing runs; modified config/source identities
need new run directories. Do not rerun an observed test to tune or replace this failure.
Historical training code snapshots are retained locally because later development changes
source files. Full retraining was not repeated. No fresh-model generalization guarantee
follows from seeded commands or reloaded weights.

- [Detailed results](../../DOC/uncertainty_results.md) and [model card](../../DOC/model_card.md).
- [Initial weighted](../metrics/gate4-v1/weighted.json), [sampled](../metrics/gate4-v1/sampled.json), [augmented](../metrics/gate4-v1/weighted_augmented.json), [lightweight](../metrics/gate4-v1/lite_weighted.json).
- [Failed stronger-weighting history](../metrics/gate4-refined-v1/history.json).
- [Balanced selection](../metrics/gate4-balanced-v1/result.json) and [all eight epochs](../metrics/gate4-balanced-v1/history.json).
- [Calibration](../metrics/gate4-final/calibration.json), [validation](../metrics/gate4-final/validation.json), [freeze](../metrics/gate4-final/frozen.json), [test](../metrics/gate4-final/test.json).
- [Stress](../metrics/gate4-final/stress.json), [class diagnostics](../metrics/gate4-final/diagnostics.json), [qualification](../metrics/gate4-final/qualification.json).
- [Release decision](gate_4-release.json) and [70 passing tests](gate_4-tests.log).
- [Recall/calibration](../figures/gate4-v1/recall-calibration.png), [risk/coverage](../figures/gate4-v1/risk-coverage.png), [test confusion](../figures/gate4-v1/test-confusion.png), with SVG exports.

Weights, per-case arrays, historical source and original failure logs stay ignored under
artifacts/. Public failure logs redact only local home paths; raw originals are retained
privately. No raw wafer examples or invented dataset labels are published.

## Gate decision, AWS and next review

**Gate 4 analysis/evidence: complete. Model release qualification: FAIL. Gate exit: HOLD.**
The global acceptance config stays disabled and an unqualified manifest is refused before
weights load. No model is promoted, no live acceptance policy is enabled and no AWS resource
was deployed. Do not treat successful tests or fitted temperature as approval evidence.

AWS sign-in for awsnew completed and was verified with STS. The profile default Region
is us-east-2. No resources were deployed. A complete budget-alert recipient remains
pending for a later deployment gate. No credentials or personal account details are
stored in public project files.

Keep individual gate reviews, as requested. The next decision is whether to investigate
modelling under a newly reviewed evaluation protocol or authorize a clearly marked,
manual-review-only research workflow. The test set is observed and must not be described
as untouched, silently reshuffled or used for test-driven tuning. Future API/review code
is draft preparation, not a passed Gate 5 or a production authorization system.
