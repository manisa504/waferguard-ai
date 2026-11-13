# Model card — calibrated research candidate, release blocked

**Model version:** `b917a4d2c11c20510affb9c2197971c6c44ff8afae365ab398c1396382ff09e3`  
**Calibration version:** `6fc71d38ab18ac2d8a964441b127467539eca7bb46aab991c6752b4f8a977ab8`  
**Status:** not qualified for promotion; automatic acceptance disabled; not deployed.

The balanced compact CNN has 173,441 parameters, the same four-stage architecture as
the Gate 3 baseline, and uses the audited 64×64 categorical encoding. It was fine-tuned
from the sampled experiment with replacement sampling, D4 transforms and an unweighted
loss. Epoch 2 was selected on validation subject to Scratch recall >=60%.
Calibration uses only the separate calibration partition. All artifact and split hashes
are recorded in the frozen manifest. [Gate 3 historical card](model_card_gate3.md).

| Measurement | Validation | Held-out test |
|---|---:|---:|
| Macro-F1 | 0.7881 | 0.7265 |
| Scratch recall | 0.7521 | 0.5556 |
| Scratch precision | 0.1369 | 0.0994 |
| Overall ECE | 0.0145 | 0.0177 |

**Four true Scratch cases were falsely accepted by the unchanged candidate policy on test.**
The model failed the declared .75 macro-F1 and .60 Scratch-recall benchmarks out of sample.
Its roughly 10% test Scratch precision also means many false alarms. A low overall ECE
is dominated by the class mix and does not establish minority-class reliability.

Temperature scaling (T=0.875128) preserves class argmax and reduces validation
ECE; it does not solve confident critical errors. Predicted-Scratch test ECE is
0.5156. A training-feature-distance guard detects
engineered random grids but misses the tested mild die-state corruption. Inputs and
populations outside this benchmark have not been validated.

This model is for offline research and failure analysis. It cannot grant classification
approval, authorize physical wafer release or claim certification. The frozen policy
file is a **counterfactual evaluated candidate**, not an active authorization. The global
acceptance configuration stays disabled, and the draft inference loader refuses
unqualified release manifests. No reviewer application or production model is deployed.

The test set has been observed; no thresholds or models were retuned after its evaluation.
Further model investigation requires a reviewed evaluation protocol. Current figures and
metrics do not establish real-world generalization, cost savings, safety or calibrated
confidence across every class. No serving benchmark was run for this candidate; prior
Gate 3 latency belongs to its own recorded versions.

See [detailed results](uncertainty_results.md), [Gate 4 report](../reports/gates/gate_4.md),
[release assessment](../reports/metrics/gate4-final/qualification.json), and
[original benchmark](benchmark.md) for provenance, data limits, commands and raw evidence.
