# WaferGuard AI — Full Project Outline

**Owner:** WaferGuard contributors  
**Project:** Uncertainty-Aware Semiconductor Wafer Defect Detection with Human-in-the-Loop Review  
**Repository:** `waferguard-ai`  
**Deployment:** AWS `us-east-2`  
**Status:** Planning — implementation and measured results pending  
**Focus:** Machine Learning Engineering, Computer Vision, MLOps, Responsible AI, AWS

## 1. Executive summary

WaferGuard AI is an end-to-end machine learning platform built around real WM-811K semiconductor wafer maps. It trains and evaluates models to identify wafer defect patterns, calibrates predictive uncertainty, routes uncertain or policy-sensitive predictions to qualified human reviewers, and resumes a controlled workflow with traceable decisions. It is a portfolio project for WaferGuard contributors, with emphasis on roughly 65% ML, 20% MLOps/infrastructure, and 15% approval-workflow engineering.

The project must distinguish **real wafer data** from **simulated engineering approval records and release policies**. It does not authorize real production wafer release or assert regulatory certification.

## 2. Business problem

Wafer defect pattern classification helps semiconductor manufacturers identify manufacturing process anomalies. Manual inspection can be time consuming and inconsistent; fully automated classifiers risk incorrect predictions, particularly for minority classes, ambiguous patterns, and out-of-distribution inputs.

**Key questions:**
1. What wafer defect pattern is present?
2. How reliable is this prediction?
3. Should the prediction be accepted or escalated to a human reviewer?

**Value proposition:** Demonstrate uncertainty-aware selective classification, measured tradeoffs between classification risk and review workload, reviewer-assisted correction, and auditable ML deployment.

## 3. Dataset and provenance

**Primary dataset:** WM-811K, public wafer map dataset.  
**Source:** https://www.kaggle.com/datasets/qingyi/wm811k-wafer-map

Publicly cited figures to verify at ingestion:
- Total wafer maps: 811,457
- Labeled wafer maps: 172,950
- Nine classes: None, Edge-Ring, Edge-Loc, Center, Loc, Scratch, Random, Donut, Near-full
- Published label counts commonly reported: None 147,431; Edge-Ring 9,680; Edge-Loc 5,189; Center 4,294; Loc 3,593; Scratch 1,193; Random 866; Donut 555; Near-full 149.

**Ingestion requirements:**
- Check source access and redistribution rights before acquisition or publishing samples.
- Preserve untouched originals, provenance, acquisition timestamp, hashes, and metadata.
- Exclude raw datasets from GitHub; commit manifests, scripts, source instructions, and permitted derived examples only.
- Profile missing labels, image sizes, die-state encodings, class imbalance, duplicates, and identifiers.
- Preserve original die-state meaning and avoid incorrect continuous-image transformations.
- Use group-aware splits only if reliable wafer/lot grouping identifiers actually exist; otherwise clearly document limitations and implement duplicate/leakage audits.
- Prevent copies or augmentations of samples crossing splits.
- Do not invent ground-truth labels for unlabeled data.
- Keep held-out test results separated from all hyperparameter and threshold selection.

## 4. ML workstreams

### Model experiments

| Experiment | Approach | Deliverable |
|---|---|---|
| E1 | Majority-class and classical ML baselines | Reference metrics and feature engineering |
| E2 | Custom PyTorch CNN | First spatial-pattern model |
| E3 | ResNet18 or lightweight CNN | Model comparison (accuracy, size, latency) |
| E4 | Weighted losses, sampling, controlled augmentation | Minority-class behavior |
| E5 | Temperature scaling and reliability diagrams | Calibrated class probabilities |
| E6 | Selective classification/abstention | Risk–coverage curves and reviewer workload |
| E7 | OOD/corruption stress tests | Robustness analysis |
| E8 | Reviewer-corrected labels for offline retraining | Controlled feedback study |

### Metrics

- **Primary:** macro-F1 and per-class recall, with focus on minority defects.
- Confusion matrix, macro precision, balanced accuracy.
- Calibration: expected calibration error (ECE), Brier score, reliability diagrams.
- Selective risk versus coverage; review/abstention rate; error on accepted predictions.
- OOD/corruption detection and behavior on invalid inputs.
- Inference p50/p95 latency, throughput, model size, and cost per prediction.
- Stratified confidence intervals where feasible.

**Evaluation rule:** No claims of accuracy, safety performance, cost improvement, or production success without stored measured evidence.

## 5. Uncertainty policy and human approval

A deterministic policy engine uses validated model outputs, calibration metadata, class-specific conditions, and case state. The model cannot grant approval by itself.

- Accept only when all configured, evaluated criteria pass.
- Abstain and escalate low-confidence, ambiguous, designated high-risk, or OOD cases.
- If required evidence/model metadata is unavailable, route to review rather than accepting.
- Only authorized reviewers may approve or correct classifications.
- Reviewer updates create versioned labels for separate offline training; no silent online self-training.
- Revalidate reviewer identity, permissions, case version, model version, and any state changes before resuming.
- Reject expired and replayed approvals; ensure idempotent execution and terminal state handling.
- Store a complete decision audit chain.

**Illustrative state machine:** DETECTED → ANALYZING → AUTO_ACCEPTED or AWAITING_REVIEW → REVALIDATING → ACCEPTED/CORRECTED/CLOSED, with rejected/expired/failed-safe branches.

The project supports classification approval and **simulated** quality disposition, not real MES release authorization.

## 6. AWS architecture

**Region:** `us-east-2` (AWS CLI profile `awsnew`; never hard-code credentials).

| Layer | Proposed service |
|---|---|
| Frontend | React + TypeScript on S3/CloudFront |
| REST API | FastAPI in Lambda container or ECS as benchmarking justifies |
| Inference | CPU Lambda container initially; evaluate SageMaker options when justified |
| Training | Reproducible local/remote training or SageMaker Training Jobs |
| Model registry | SageMaker Model Registry |
| Dataset/artifacts | S3 versioned buckets |
| Workflows | Step Functions Standard callback-token flow |
| Events | EventBridge + SQS and DLQ |
| Metadata/cases | DynamoDB by default; PostgreSQL if relational needs justify it |
| Authentication | Cognito + least-privilege IAM |
| Monitoring | CloudWatch; CloudTrail where appropriate |
| Infrastructure | AWS CDK |
| CI/CD | GitHub Actions + AWS OIDC (short-lived credentials) |

**Security:** Private S3, encryption at rest/in transit, least privilege, no exposed Step Functions task tokens, no secrets in repo, scoped reviewer roles, replay protection, audit retention policy, budgets/alarms, teardown procedures.

**Cost discipline:** Keep the public demonstration serverless and low-traffic. Use GPUs only for measured training requirements. Log actual cost; do not promise a specific bill without pricing/usage evidence.

## 7. Application pages

1. **Wafer Inspection:** Real held-out wafer map, model prediction, calibrated probability, per-class probabilities, model version, review routing explanation.
2. **Model Performance:** Confusion matrix, per-class metrics, risk–coverage curve, calibration diagram, model comparisons.
3. **Engineering Review Queue:** Authenticated approvals/corrections, evidence, role checks, case versioning, decision history.
4. **MLOps and Audit:** Model versions, drift monitoring, latency, traceable review records, deployment status, rollback evidence.

Provide safe public guest/demo mode and isolated scripted review cases; production review writes require authentication.

## 8. Proposed repository structure

```text
waferguard-ai/
├── README.md
├── LICENSE
├── pyproject.toml
├── Makefile
├── .github/
│   ├── workflows/{ci.yml,ml-evaluation.yml,deploy.yml}
│   └── PULL_REQUEST_TEMPLATE.md
├── configs/{data.yaml,train.yaml,evaluation.yaml,approval_policy.yaml}
├── data/{README.md,sample/}
├── src/waferguard/
│   ├── data/{acquire.py,validate.py,preprocess.py,split.py}
│   ├── features/wafer_features.py
│   ├── models/{baseline.py,cnn.py,resnet.py}
│   ├── training/{train.py,experiment.py}
│   ├── evaluation/{metrics.py,calibration.py,selective_risk.py,ood.py}
│   ├── inference/{predict.py,schemas.py}
│   ├── approval/{policy.py,workflow.py,authorization.py,audit.py}
│   └── api/main.py
├── frontend/{src/,package.json}
├── infrastructure/cdk/
├── tests/{unit/,integration/,security/,ml/,e2e/}
├── experiments/README.md
├── reports/{gates/,metrics/,figures/}
├── DOC/{index.html,architecture.drawio,data_card.md,model_card.md,threat_model.md,deployment.md}
└── scripts/{setup.sh,run_local.sh,deploy.sh,teardown.sh}
```

## 9. Aspect-driven development

Implement and test these cross-cutting aspects in every relevant gate:

1. Data lineage and provenance.
2. Modeling validity and anti-leakage.
3. Statistical calibration and uncertainty.
4. Workflow correctness and human authorization.
5. Reliability, idempotency, and fail-closed behavior.
6. Security, privacy, and least privilege.
7. Observability, reproducibility, and operational cost.
8. Documentation and verifiable claims.

## 10. Development gates

| Gate | Scope | Evidence required |
|---|---|---|
| 0 | Foundation | Charter, ADRs, architecture.drawio, threat model, CI, budget alarms |
| 1 | Real dataset acquisition | Documented acquisition, hashes, data card, verified label counts and quality report |
| 2 | Preprocessing | Reproducible preprocessing, split audits, no-leakage checks and unit tests |
| 3 | Baselines | Classical and first CNN models, repeatable experiments, saved raw metrics |
| 4 | Advanced ML | Class imbalance, calibration, selective risk, OOD and stress test results |
| 5 | Human review | Authenticated reviewer flow, durable pause/resume, revalidation, replay defense |
| 6 | AWS inference | Deployed versioned model, API contract, latency, cost and fault metrics |
| 7 | Frontend | Working inspection, evaluation, review, and audit pages |
| 8 | MLOps | Registry, release gating, drift instrumentation, rollback and CI evaluation |
| 9 | Production validation | E2E tests, fault injection, security tests, load and operational evidence |
| 10 | Portfolio release | Hosted showcase, DOC/index.html, reproducible demo, model card, honest metrics |

Every gate must save `reports/gates/gate_N.md` including objective, criteria, commands, environment/commit, actual evidence, pass/fail, limitations, and next-gate decision. Stop for review between gates. A passing test suite alone is not evidence of real-world detection skill.

## 11. Non-negotiable acceptance criteria

- No invented model performance or test evidence.
- No fabricated training data presented as real WM-811K samples.
- No leakage from preprocessing, duplicate records, or augmentation across splits.
- No hidden invented labels for unlabeled samples.
- No promotion without versioned evaluation and benchmark criteria.
- All predictions pinned to a model and calibration version.
- Uncertain and OOD cases cannot silently become auto-accepted.
- Unauthorized users cannot approve or alter state.
- Replayed, expired, conflicting, or stale approvals cannot execute.
- Decision history captures identity, timestamp, evidence, decision, policies, model version, and state version.
- Model regression gates and rollback must work.
- Deployments must include reproducible cleanup/teardown.

## 12. MVP and scope

**MVP:** dataset pipeline; baseline + CNN; calibration; abstention; authorized human review; AWS inference; basic UI; automated evaluation.

**Phase 2:** OOD detection; human-corrected offline retraining; active learning; registry promotion; drift alerts; shadow testing.

**Initially excluded:** multi-agent debate, gratuitous LLM reasoning, production factory integrations, physical wafer release, claims of certification.

## 13. Definition of done

A hiring manager can open the live AWS app, inspect a real held-out wafer, observe an actual trained model's prediction with calibrated uncertainty, trigger a review scenario, see an authorized human decision, inspect the audit trail, and review real reproducible training/evaluation reports. All public statements distinguish real data, simulated workflows, goals, and measured results.

## 14. First pull request

**PR 1: Gate 0 + Gate 1 only.** Create scaffold, architecture and ADRs, CI, security/cost controls, dataset acquisition and integrity scripts, source provenance, license/usage review, split feasibility assessment, data quality report, and gate reports. Do not build frontend or rent GPUs before verifying the data.

## 15. Suggested GitHub description

> Uncertainty-aware semiconductor wafer defect detection using real WM-811K data, calibrated computer vision, selective classification, AWS MLOps, and auditable human-in-the-loop review.

**Portfolio framing:** The project demonstrates how to design, train, evaluate, and deploy an industrial vision ML system with risk-based human review, robust MLOps, and verifiable experiment results.
