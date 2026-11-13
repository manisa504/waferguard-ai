# WaferGuard — Campaign brief

Evidence snapshot: November 13, 2026. Audience: Engineering managers hiring for applied ML, ML platform, data engineering, and cloud roles.

## Editorial guidance

Prepare this as a 12-day LinkedIn campaign for review. Do not publish or schedule until the account owner confirms the LinkedIn account, start date, posting timezone, cadence, and final text. Day numbers are relative sequence positions, not dates. This document does not grant account access or publishing permission.

Lead with business context, then technical evidence, then the engineering decision and architectural decision. Use plain language, short paragraphs, and one discussion question. Keep evidence links attached. Avoid invented ROI, savings, customer use, hiring claims, latency, cost, or production readiness. Do not add a personal name.

Model qualification FAILED. Promotion is blocked and operational automatic acceptance is disabled. API/review modules are drafts; Gate 5 is not passed. The AWS application is not deployed. The observed test must not be described as untouched. Historical validation metrics are not current test results. The 62.1% offline coverage is not achieved labor savings.

Use only aggregate evidence, committed plots, and labeled architecture diagrams. Never publish raw maps, trained weights, credentials, or synthetic wafer imagery presented as source data. The actual 90-second video and Vercel URL were not supplied. Keep these integrations pending; do not fabricate URLs or imply a live app.

## Content inventory

18 potential assets: 12 written posts, four six-slide carousel outlines, one 90-second video script, and one case-study brief. The last six are adaptations requiring production. Do not post all adaptations during the same twelve days without an approved cadence. No reach, engagement, or conversion forecast is claimed.

## Measurement plan

Record actual impressions, substantive comments, repository/site referrals, and qualified hiring conversations when available from authorized account analytics. There is no baseline or target forecast in this brief. Review responses after days 4, 8, and 12 to decide which subjects need clearer explanation. Do not add tracking identifiers or analytics credentials to public source.

## Day 1 — Start with the cost of a wrong decision

### LinkedIn copy

Start with the cost of a wrong decision

In a wafer-inspection workflow, a missed defect and an unnecessary review create different problems. A useful ML pilot must make those tradeoffs visible before anyone discusses automation. WaferGuard explores that decision using public wafer-pattern data; it does not measure factory yield or production savings.

The local pipeline audits WM-811K, trains pattern classifiers, calibrates confidence, and evaluates a frozen routing policy. The frozen test candidate achieved macro-F1 0.7265 and Scratch recall 55.6%; its offline policy falsely accepted four Scratch cases.

Engineering decision: Block model promotion and keep operational automatic acceptance disabled. These results do not justify a release.

Architectural decision: Separate prediction evidence, policy evaluation, and reviewer authorization. A model score must not itself authorize a quality disposition. The cloud review workflow remains a target design.

When reviewing an ML pilot, which failure would make you stop a release even if overall accuracy looked strong?

Evidence:

- [reports/gates/gate_4.md](https://github.com/manisa504/waferguard-ai/blob/main/reports/gates/gate_4.md)
- [DOC/adr/0003-review-and-model-promotion.md](https://github.com/manisa504/waferguard-ai/blob/main/DOC/adr/0003-review-and-model-promotion.md)

### Production note (not post copy)

A decision flow: prediction → policy → review or blocked release. Mark cloud components as planned.

## Day 2 — Count usable evidence before counting training rows

### LinkedIn copy

Count usable evidence before counting training rows

A large dataset can create a false sense of readiness. Before investing in training, a team needs to know how much of the data has usable labels and where provenance or consistency is uncertain.

The source audit counted 811,457 maps: 172,950 labeled and 638,507 unlabeled. It also found 114,858 duplicate map rows and 14 conflicting-label groups. Those are quality measurements, not detection results.

Engineering decision: Exclude unlabeled records from supervised training and quarantine contradictory groups instead of inventing labels or resolving disagreements by a silent vote.

Architectural decision: Preserve source identity and acquisition receipts separately from versioned derived data. Publish aggregate evidence and hashes while keeping raw maps and row-level artifacts outside Git.

What is the first data-quality result you want to see before approving a training budget?

Evidence:

- [DOC/data_card.md](https://github.com/manisa504/waferguard-ai/blob/main/DOC/data_card.md)
- [DOC/data_rights_review.md](https://github.com/manisa504/waferguard-ai/blob/main/DOC/data_rights_review.md)
- [reports/gates/gate_1.md](https://github.com/manisa504/waferguard-ai/blob/main/reports/gates/gate_1.md)

### Production note (not post copy)

An explicitly labeled count breakdown: total, labeled, and unlabeled records. Do not use stock wafer images as dataset evidence.

## Day 3 — A clean split is part of the product claim

### LinkedIn copy

A clean split is part of the product claim

An evaluation can overstate value when training and test sets contain versions of the same example. That can lead a team to fund a system whose apparent performance depends on familiarity with the benchmark.

The source train/test annotations shared 3,158 exact map groups. WaferGuard rebuilt the benchmark using connected lot and duplicate relationships, including rotations and reflections. The final cohort contains 169,659 consistent representatives across four splits.

Engineering decision: Use the audited splits-v2 benchmark rather than the original source partition. Keep duplicate-copy membership so excluded rows cannot hide cross-split relationships.

Architectural decision: Construct identity components before assigning partitions. Store immutable split manifests, then run a separate audit over row, lot, source-map, encoded-map, and component identities. This does not rule out every approximate near-duplicate.

Does your evaluation review ask how examples are related, or only how many rows each split contains?

Evidence:

- [DOC/split_feasibility.md](https://github.com/manisa504/waferguard-ai/blob/main/DOC/split_feasibility.md)
- [DOC/benchmark.md](https://github.com/manisa504/waferguard-ai/blob/main/DOC/benchmark.md)
- [reports/data/split-audit.json](https://github.com/manisa504/waferguard-ai/blob/main/reports/data/split-audit.json)

### Production note (not post copy)

A component diagram showing related rows staying together. Label it as a schematic, not an actual wafer map.

## Day 4 — Preprocessing can change what counts as a duplicate

### LinkedIn copy

Preprocessing can change what counts as a duplicate

A model sees transformed inputs. If an audit checks only source files, it can miss collisions introduced by the production representation and weaken the meaning of a test result.

WaferGuard encodes categorical die states into a 64×64 representation using nearest-neighbor sampling and outside-wafer padding. The encoded-input audit found nine additional duplicate records beyond the preliminary original-grid-only benchmark.

Engineering decision: Replace the preliminary benchmark with the encoded-input-aware version. Treat downsampling as a pilot choice: small structures can be lost, and a new representation requires a new audit.

Architectural decision: Include both source and encoded identities in the grouping graph. Verify processed-array and split hashes before loading training records; preserve native originals separately.

Which transformations in your pipeline could make two distinct source records indistinguishable to a model?

Evidence:

- [DOC/benchmark.md](https://github.com/manisa504/waferguard-ai/blob/main/DOC/benchmark.md)
- [DOC/adr/0004-preprocessing-and-split-contract.md](https://github.com/manisa504/waferguard-ai/blob/main/DOC/adr/0004-preprocessing-and-split-contract.md)
- [src/waferguard/data/dataset.py](https://github.com/manisa504/waferguard-ai/blob/main/src/waferguard/data/dataset.py)

### Production note (not post copy)

A categorical-grid transformation schematic with a clear warning that resizing may erase small features.

## Day 5 — A stronger average can hide a failed defect class

### LinkedIn copy

A stronger average can hide a failed defect class

An inspection tool needs to detect the patterns that matter to its workflow. Choosing a model on an aggregate score alone can hide failures in a rare class that drives the review decision.

At Gate 3, validation macro-F1 rose from 0.1018 for the majority baseline to 0.7166 for the spatial-feature random forest and 0.7707 for the compact CNN. That CNN still missed all 117 validation Scratch cases. These are historical validation results, not the final test candidate.

Engineering decision: Do not promote the best aggregate baseline. Investigate minority-class performance and introduce a Scratch-recall selection constraint before evaluating a later candidate.

Architectural decision: Keep simple baselines, per-class metrics, confusion matrices, configuration, and experiment receipts together. Model selection needs an inspectable evidence bundle.

Would your model-selection process catch a complete miss on one class when the headline metric improves?

Evidence:

- [reports/gates/gate_3.md](https://github.com/manisa504/waferguard-ai/blob/main/reports/gates/gate_3.md)
- [DOC/model_card_gate3.md](https://github.com/manisa504/waferguard-ai/blob/main/DOC/model_card_gate3.md)
- [reports/figures/gate3-v1/model-comparison.png](https://github.com/manisa504/waferguard-ai/blob/main/reports/figures/gate3-v1/model-comparison.png)

### Production note (not post copy)

Use the committed Gate 3 comparison plot and explicitly label it validation-only.

## Day 6 — Keep the experiments that did not work

### LinkedIn copy

Keep the experiments that did not work

A hiring manager needs to see how an engineer handles weak results, not only the final chart. Preserving failed experiments makes the next investment decision easier to assess.

Gate 4 compared weighting, replacement sampling, augmentation, and a lightweight architecture. None of the four initial experiments met the 60% validation Scratch-recall selection gate. A stronger-weighting refinement also fell short. A later balanced-sampling refinement selected a checkpoint with validation Scratch recall 75.2% and macro-F1 0.7881.

Engineering decision: Preserve the failed runs and select the later checkpoint using validation evidence. Do not describe the combined sampling-and-augmentation remedy as proof of one intervention's causal effect.

Architectural decision: Use distinct versioned experiment directories and stored histories. Separate checkpoint selection from calibration and frozen test evaluation.

What evidence makes an experiment history useful enough for another engineer to continue the work?

Evidence:

- [reports/gates/gate_4.md](https://github.com/manisa504/waferguard-ai/blob/main/reports/gates/gate_4.md)
- [reports/metrics/gate4-balanced-v1/result.json](https://github.com/manisa504/waferguard-ai/blob/main/reports/metrics/gate4-balanced-v1/result.json)
- [experiments/README.md](https://github.com/manisa504/waferguard-ai/blob/main/experiments/README.md)

### Production note (not post copy)

An experiment timeline showing failed selection gates alongside the validation-selected candidate.

## Day 7 — Confidence needs its own evaluation

### LinkedIn copy

Confidence needs its own evaluation

If confidence influences which cases receive human attention, confidence quality becomes part of workflow design. A confident prediction is still a prediction, and average calibration can hide a weak subgroup.

Temperature scaling was fitted on a separate calibration partition of 17,025 records. Overall validation expected calibration error improved from about 0.0295 to 0.0145. On the frozen test, predicted-Scratch conditional ECE was about 0.5156 despite overall ECE of about 0.0177.

Engineering decision: Report conditional diagnostics alongside global calibration. The attractive overall number does not establish reliable confidence for Scratch predictions, and temperature scaling does not change the predicted class.

Architectural decision: Keep training, validation, calibration, and test roles separate. Version the calibration identity with model and policy evidence so a confidence score can be traced to its fitted transform.

If confidence drives a review queue, do you inspect calibration for the classes that create the most operational risk?

Evidence:

- [DOC/uncertainty_results.md](https://github.com/manisa504/waferguard-ai/blob/main/DOC/uncertainty_results.md)
- [reports/metrics/gate4-final/calibration.json](https://github.com/manisa504/waferguard-ai/blob/main/reports/metrics/gate4-final/calibration.json)
- [reports/metrics/gate4-final/diagnostics.json](https://github.com/manisa504/waferguard-ai/blob/main/reports/metrics/gate4-final/diagnostics.json)

### Production note (not post copy)

Use the measured recall/calibration plot; pair overall ECE with the predicted-Scratch conditional result.

## Day 8 — Review coverage is not a savings claim

### LinkedIn copy

Review coverage is not a savings claim

Routing fewer cases to humans sounds attractive, but coverage is valuable only if the accepted cases meet the workflow's error requirements. An offline routing calculation cannot establish actual labor savings.

The frozen candidate policy required confidence at least 0.94, a margin of at least 0.20, no training-distance OOD flag, and mandatory review for predicted Scratch or Near-full. On test it would have accepted 10,520 of 16,936 cases, with 88 errors, including four true Scratch cases.

Engineering decision: Keep operational automatic acceptance disabled. Reviewing every predicted critical class does not catch critical examples that the model labels as something else. The offline 62.1% coverage is not an achieved reduction in review workload.

Architectural decision: Apply deterministic policy after prediction and retain a release gate above both. Evaluate false accepts using true labels during qualification, rather than relying on predicted labels alone.

Which error breakdown would you require before treating abstention coverage as a business benefit?

Evidence:

- [reports/metrics/gate4-final/test.json](https://github.com/manisa504/waferguard-ai/blob/main/reports/metrics/gate4-final/test.json)
- [reports/metrics/gate4-final/qualification.json](https://github.com/manisa504/waferguard-ai/blob/main/reports/metrics/gate4-final/qualification.json)
- [configs/approval_policy.yaml](https://github.com/manisa504/waferguard-ai/blob/main/configs/approval_policy.yaml)

### Production note (not post copy)

A routing funnel labeled offline counterfactual, with the four critical false accepts visible.

## Day 9 — A failed release can be an engineering result

### LinkedIn copy

A failed release can be an engineering result

A release process earns its place when it can stop an attractive demo from becoming an unsupported operational claim. WaferGuard's current outcome is a documented hold, not a production success story.

The frozen test missed the declared macro-F1 and Scratch-recall criteria and produced four critical false accepts. The recorded 70 passing Python implementation tests do not overturn that result. The test set has now been observed.

Engineering decision: Block promotion, preserve the failure, and require review before further modeling. Do not tune thresholds on the observed test or relabel it untouched. Future modeling needs an explicitly reviewed evaluation protocol.

Architectural decision: Store a machine-readable qualification decision. The draft inference loader rejects an unqualified manifest before loading weights, and the global acceptance configuration remains disabled. This is local enforcement, not a verified live service.

Can your release machinery represent a useful experiment that is still unqualified for deployment?

Evidence:

- [reports/gates/gate_4.md](https://github.com/manisa504/waferguard-ai/blob/main/reports/gates/gate_4.md)
- [reports/metrics/gate4-final/qualification.json](https://github.com/manisa504/waferguard-ai/blob/main/reports/metrics/gate4-final/qualification.json)
- [src/waferguard/inference/predict.py](https://github.com/manisa504/waferguard-ai/blob/main/src/waferguard/inference/predict.py)

### Production note (not post copy)

An evidence checklist with classification FAIL, critical false accepts FAIL, and promotion BLOCKED.

## Day 10 — A passing stress test has a boundary

### LinkedIn copy

A passing stress test has a boundary

A robustness claim should help an operator understand where protection ends. A detector that catches obvious nonsense may still miss smaller changes in otherwise familiar inputs.

A training-feature-distance guard flagged all 256 engineered random grids in a limited stress check. It flagged none of 256 maps with 5% die-state flips. The candidate routed 41.8% of the altered maps to review through its combined policy. No labels were invented for the synthetic or altered inputs.

Engineering decision: Publish both findings and limit the claim to the tested conditions. Do not call the guard a general corruption detector or assign detection accuracy to unlabeled altered inputs.

Architectural decision: Keep input-contract validation separate from statistical OOD checks and policy routing. Each control has a different purpose and needs separate evidence.

What nearby failure case would you test after a detector passes an obvious out-of-distribution example?

Evidence:

- [reports/metrics/gate4-final/stress.json](https://github.com/manisa504/waferguard-ai/blob/main/reports/metrics/gate4-final/stress.json)
- [DOC/threat_model.md](https://github.com/manisa504/waferguard-ai/blob/main/DOC/threat_model.md)
- [tests/security/test_ingestion.py](https://github.com/manisa504/waferguard-ai/blob/main/tests/security/test_ingestion.py)

### Production note (not post copy)

Two measured outcomes: random grids 256/256 flagged; mild corruption 0/256 flagged. Label both engineered stress checks.

## Day 11 — Human review needs a state model

### LinkedIn copy

Human review needs a state model

A review button is useful only if the resulting decision belongs to the right case and authorized reviewer. Duplicate clicks, stale screens, and delayed callbacks can otherwise create conflicting outcomes.

WaferGuard has draft API and review modules, with six preliminary review tests included in the recorded 70-test run. Gate 5 is not passed, and there is no live reviewer service. Restart durability, callback reconciliation, and end-to-end authorization still need verification.

Engineering decision: Keep model output separate from reviewer authority. Require current versions, permission checks, single-use unexpired decisions, and conflict handling before treating the workflow as complete.

Architectural decision: The target uses Cognito identity, conditional DynamoDB state/audit/outbox writes, and a Step Functions Standard callback workflow with tokens held server-side. These cloud services remain planned, not deployed.

What happens in your review workflow if the same case is approved twice from two browser tabs?

Evidence:

- [DOC/adr/0003-review-and-model-promotion.md](https://github.com/manisa504/waferguard-ai/blob/main/DOC/adr/0003-review-and-model-promotion.md)
- [DOC/architecture.md](https://github.com/manisa504/waferguard-ai/blob/main/DOC/architecture.md)
- [tests/security/test_review.py](https://github.com/manisa504/waferguard-ai/blob/main/tests/security/test_review.py)

### Production note (not post copy)

A planned sequence for authorization, conditional transition, audit/outbox, and callback reconciliation.

## Day 12 — Show the boundary between authored and operated

### LinkedIn copy

Show the boundary between authored and operated

A portfolio architecture should show what an engineer can defend today and what still needs operational evidence. A diagram alone cannot establish cost, reliability, or deployment readiness.

The authored CDK foundation defines private versioned S3 storage, access logging, retention, and budget warnings in us-east-2. The full application stack is not implemented or deployed. Live latency, cloud costs, authentication behavior, and rollback remain unmeasured.

Engineering decision: Review the failed model gate and choose the next scope before deployment. Resolve the recorded tooling advisory, confirm the budget recipient, and review the infrastructure diff. Budget alerts are warnings, not spending caps.

Architectural decision: Keep the foundation diagram separate from the target application: CloudFront delivery, Cognito, API Gateway, Lambda, DynamoDB, Step Functions, and monitoring. Require deployment and teardown evidence before making operational claims.

When reviewing a cloud portfolio project, which evidence helps you distinguish a design from an operated system?

Evidence:

- [DOC/PROJECT_STATUS_AND_AWS_PLAN.md](https://github.com/manisa504/waferguard-ai/blob/main/DOC/PROJECT_STATUS_AND_AWS_PLAN.md)
- [DOC/deployment.md](https://github.com/manisa504/waferguard-ai/blob/main/DOC/deployment.md)
- [reports/gates/gate_0.md](https://github.com/manisa504/waferguard-ai/blob/main/reports/gates/gate_0.md)

### Production note (not post copy)

Use the two committed architecture diagrams with explicit authored-foundation and future-target labels.

## Four carousel adaptations

### What a wafer ML pilot must prove

1. Business question: when should a prediction influence inspection review?
2. Data scope: public WM-811K patterns, no factory deployment or savings measurement.
3. Baseline warning: Gate 3 CNN validation macro-F1 0.7707, Scratch recall zero.
4. Frozen Gate 4 test: macro-F1 0.7265, Scratch recall 55.6%, four critical false accepts.
5. Decision: promotion blocked; operational automatic acceptance disabled.
6. Hiring discussion: separate attractive scores, error consequences, and release authority.

Evidence comes from days 1, 5, 9.

### Leakage checks before model selection

1. Business question: would performance survive genuinely different examples?
2. Audit source labels, contradictions, and duplicate relationships.
3. Find 3,158 exact map groups shared by source train/test.
4. Group lots, originals, rotations/reflections, and encoded identities before splitting.
5. Encoding reveals nine additional duplicate records; final cohort is 169,659 representatives.
6. Boundary: exact/D4 checks do not exclude all approximate near-duplicates. Link the audit.

Evidence comes from days 2, 3, 4.

### Confidence is a workflow input

1. Business question: which cases can safely receive less human attention?
2. Fit temperature on calibration data; choose routing on validation.
3. Global test ECE 0.0177 coexists with predicted-Scratch conditional ECE 0.5156.
4. Offline coverage 62.1% still includes four critical false accepts; no achieved labor savings.
5. Random-grid stress passes, but 5% die-state corruption is not flagged by the distance guard.
6. Decision: keep acceptance disabled and communicate the limits of every control.

Evidence comes from days 7, 8, 10.

### From evidence to a planned cloud workflow

1. Business question: who can authorize a disposition, and what evidence supports it?
2. Local now: audited data, measured experiments, failed qualification, and draft review code.
3. Authored foundation: private versioned S3, logging, retention, and budget warnings.
4. Target only: Cognito → API Gateway/Lambda → DynamoDB and Step Functions review.
5. Review correctness needs current versions, scoped authority, single-use decisions, and reconciliation.
6. Next gate: review scope, finish workflow verification, then review deployment evidence. No live AWS app claim.

Evidence comes from days 9, 11, 12.

## 90-second walkthrough script

90-second project walkthrough — script, not an existing recording

### 0–15s — Readable title and business question

A wafer-inspection model can look promising while missing the defect pattern that matters. WaferGuard asks a practical question: what evidence should a team require before a prediction influences a review decision?

### 15–30s — Dataset counts and split audit

I started with public WM-811K data: more than eight hundred thousand maps. I audited labels, contradictions, and duplicates, then built partitions that keep related lots and original or encoded map identities together.

### 30–45s — Historical Gate 3 plot, validation label visible

The first CNN beat simpler baselines on validation macro-F1 but missed every validation Scratch case. That changed model selection. I preserved failed experiments and selected a later candidate with an explicit minority-class constraint.

### 45–60s — Calibration plot, then frozen test results

Calibration and validation had separate roles. After freezing the candidate and routing policy, the test still showed Scratch recall of fifty-five point six percent and four critical false accepts. The release gate failed.

### 60–75s — Promotion-blocked state beside target architecture

The decision was to block promotion and keep automatic acceptance disabled. The target architecture separates predictions, review policy, and authorization. AWS application services are planned; the foundation is authored, and the review API remains a draft.

### 75–90s — Repository, gate report, and next decision

This project demonstrates data auditing, controlled evaluation, and explicit release decisions. It does not claim factory savings or a deployed inspection system. The repository includes the evidence and the next review gate. That is the work I would want a hiring team to inspect.

Target duration only; record and verify final timing. Use real committed plots and captions. Label diagrams as authored foundation or future target. Generated decorative media must not masquerade as measured results.

## One-page case-study brief

### An ML inspection pilot that did not qualify for release

### Business context

Explore whether public wafer-pattern classification can support a review workflow, while making critical misses and review errors visible. Production yield, customer impact, throughput, and savings were not measured.

### Technical work

Audited source provenance and data quality; built encoded-input-aware grouped splits; compared majority, random-forest, and CNN baselines; ran imbalance experiments; calibrated on a dedicated split; froze and tested a candidate routing policy.

### Measured outcome and decision

Gate 4 test macro-F1 0.7265, Scratch recall 55.6%, Scratch precision 9.9%, and four critical false accepts. Promotion blocked; operational automatic acceptance disabled. Tests establish bounded implementation behavior, not model qualification.

### Architectural decision

Local evidence pipeline and authored S3/budget foundation. Planned cloud application separates model evidence, deterministic routing, identity, case state, human authority, and audit. Draft review modules are not a completed or deployed service.

### Next gate

Review the failed gate, choose a manual-review-only research scope or a newly reviewed modeling protocol, finish review correctness, then separately validate infrastructure, deployment, costs, and teardown. Do not tune on the observed test.

## Handoff fields still pending

- LinkedIn account, campaign start date, timezone, cadence, and publication approval.
- Actual video URL/file and captions; current deliverable is a script.
- Actual Vercel application URL and a verified description of what it demonstrates.
- Visual production for the four carousel outlines.

## Source of truth

- [Repository](https://github.com/manisa504/waferguard-ai)
- [Gate 4 qualification](https://github.com/manisa504/waferguard-ai/blob/main/reports/gates/gate_4.md)
- [Current model card](https://github.com/manisa504/waferguard-ai/blob/main/DOC/model_card.md)
- [AWS plan](https://github.com/manisa504/waferguard-ai/blob/main/DOC/PROJECT_STATUS_AND_AWS_PLAN.md)
