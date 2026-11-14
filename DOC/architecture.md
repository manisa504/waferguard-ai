# WaferGuard — local app architecture

[Simple diagram page](architecture.html) · [Local app](app/) · [Screenshots](screenshots.html)

## The current local app

1. **Committed reports** supply aggregate measured model results and the failed qualification.
   The browser reads the JSON reports; it does not rerun evaluation or change thresholds.
2. **Grid input** is either a deterministic, labeled synthetic example or a user-uploaded
   rectangular categorical JSON grid. Input validation checks size, state values, shape,
   and presence of inside-wafer cells. Grids stay in memory and are never uploaded.
3. **Browser workspace** displays the evidence, draws the categorical grid, counts its states,
   and lets a researcher add a summary to the notebook. No model executes.
4. **Browser notebook** persists summaries and observations in localStorage. It contains
   no raw grid arrays and offers filtering, JSON export, and clearing. It is not a shared,
   authenticated, or tamper-proof review service and does not authorize dispositions.

![Local architecture](diagrams/local-app.svg)

[Explore](diagrams/local-app.html) · [PNG](diagrams/local-app.png) ·
[Editable specification](diagrams/local-app.json).

## The research decision

Audit data → separate evidence roles → freeze and evaluate → hold release.
The frozen candidate failed its declared criteria. The observed test must not be reused
for tuning, and operational automatic acceptance remains disabled.

![Research decision flow](diagrams/research-flow.svg)

[Explore](diagrams/research-flow.html) · [PNG](diagrams/research-flow.png) ·
[Editable specification](diagrams/research-flow.json).

## Scope and evidence

See the [local app guide](LOCAL_APP.md), [screenshot receipt](screenshots/receipt.json),
[diagram verification](diagrams/verification.json), and [Gate 4 report](../reports/gates/gate_4.md).
Two standalone architecture viewers passed nine artifact checks each, with zero composition
errors or warnings, automated four-viewport browser checks, and light/dark visual review.
Static PNG/SVG exports accompany the same typed specifications. The unlabelled research
edges intentionally avoid repeating the ordered steps; they carry no extra protocol facts.

The earlier AWS target is preserved in [draw.io source](architecture.drawio) and
[the deferred deployment plan](PROJECT_STATUS_AND_AWS_PLAN.md) as historical planning.
It is not required to run this app. No AWS deployment or model promotion was performed.
