# Project charter

Owner: WaferGuard contributors. Deliver an educational, reproducible wafer pattern classifier
with calibrated uncertainty and auditable, simulated human quality review. Follow the
65% ML / 20% MLOps / 15% workflow emphasis in the outline. Success requires stored
measured evaluation and a reproducible authorized reviewer scenario, not a passing
unit suite alone. No accuracy, cost, production release or certification claims exist.

The first change covers Gate 0 foundation and Gate 1 source verification only.
No frontend or rented GPU precedes data verification. Stop for owner review before
Gate 2. Future gates follow the outline sequentially with command evidence, limitations
and explicit next-gate decisions.

Data is real WM-811K. Workflow records and release policies will be simulated.
Ground truth is never invented for unlabeled records. Training and threshold selection
must be isolated from held-out test evaluation. All future predictions must pin model,
calibration, policy and case versions. Fail closed when evidence is unavailable.
