# WaferGuard — high-level architecture

[Open the diagram page](architecture.html) · [Full-resolution PNG](architecture-target.drawio.png) ·
[Scalable SVG](architecture-target.drawio.svg) · [Editable draw.io source](architecture.drawio)

The first tab is the high-level target. The second tab shows the authored foundation.
Neither view describes a deployed AWS application. The public portfolio is on GitHub Pages.
Regional AWS services are planned for Ohio (`us-east-2`); CloudFront is global.

## Main user flow — planned

1. **Access:** an engineer or reviewer opens the web workspace, submits a map, and inspects
   evidence. The target serves frontend assets from private S3 through CloudFront.
2. **Analyze:** API Gateway and Lambda provide the prediction API. A versioned model and
   calibration transform supply class and confidence evidence; deterministic policy checks
   remain separate from reviewer authority.
3. **Decide:** an authorized reviewer records a decision through the application. Cognito
   supplies identity; application logic verifies authorization and current case versions.
   Step Functions Standard coordinates the planned pause/resume workflow. It does not
   itself perform the human judgment or replace the API's authorization checks.
4. **Record:** DynamoDB is the target store for case state, versions, and audit events.
   Conditional transitions, atomic state/audit/outbox writes, single-use decisions, and
   callback reconciliation still need complete end-to-end verification.

The arrows show the main business sequence, not every network call. Reviewer actions
return through the authenticated API; the browser never receives workflow callback tokens
or direct database access. No physical wafer release or MES integration is supported.

## Supporting capabilities

| Capability | Target service | Purpose and boundary |
|---|---|---|
| Reviewer identity | Cognito | Verify identity before server-side authorization |
| Versioned model evidence | S3 | Store model/calibration artifacts; serving requires release qualification |
| Operational visibility | CloudWatch | Future logs, metrics, and alarms; no live workload evidence yet |
| Cost warnings | AWS Budgets | Separate budget alerts; warnings do not cap spending |

Training and evaluation run locally today. The high-level diagram omits training jobs,
queues, retry plumbing, and network details to keep the user journey readable. Those
services remain future implementation work, not newly authorized architecture changes.

## Current scope

- **Implemented locally:** audited data, grouped partitions, baselines, imbalance experiments,
  calibration, frozen test evaluation, and a failed release qualification.
- **Authored infrastructure:** three private versioned S3 buckets for raw data, artifacts,
  and access logs; retention and budget warning definitions. No deployment has occurred.
- **Draft:** API and review modules. Gate 5 is not passed; there is no live reviewer service.
- **Public hosting:** static project and campaign pages on GitHub Pages, separate from AWS.
- **Release decision:** test macro-F1 0.7265, Scratch recall 55.6%, and four critical false
  accepts. Model promotion and operational automatic acceptance remain blocked.

See the [Gate 4 report](../reports/gates/gate_4.md),
[model card](model_card.md), [review ADR](adr/0003-review-and-model-promotion.md), and
[remaining AWS deployment work](PROJECT_STATUS_AND_AWS_PLAN.md).

## Rebuild the diagram

`python3 scripts/architecture.py` generates both editable tabs. Export tab 1 as
`architecture-target.drawio.png` and `architecture-target.drawio.svg`; export tab 2 as
`architecture.drawio.png`. The draw.io CLI uses **1-based** page indexes. Review exported
images after changes for label clipping, icon rendering, and connector overlap.
