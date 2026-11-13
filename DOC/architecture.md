# WaferGuard architecture

[Editable draw.io diagram](architecture.drawio) · [Foundation PNG](architecture.drawio.png) · [Future target PNG](architecture-target.drawio.png)

The Foundation tab shows authored Gate 0 resources; none are deployed. The Target tab
shows the future proposal, not implemented application capabilities.

1. Developer acquires the pinned real source, records metadata/hash and profiles it locally.
2. After deployment review, private versioned raw/artifact buckets hold immutable originals
   and versioned artifacts. Separate S3 access logs expire after 90 days.
3. AWS Budgets warns the owner at 80% actual / 100% forecast account-wide monthly threshold.
4. Future guests access React through S3/CloudFront; reviewers authenticate through Cognito.
5. API Gateway invokes FastAPI/Lambda CPU inference pinned to model/calibration artifacts.
6. A deterministic policy accepts eligible classification evidence or routes cases to
   Step Functions Standard review, storing versions/audit in DynamoDB.
7. Authorized reviewer decisions undergo state/permission/expiry checks before callbacks.
   EventBridge, SQS/DLQ and a durable outbox support eventual retries/reconciliation.
8. Offline training, evaluation, registry promotion and CloudWatch monitoring arrive in
   later gates once their measurable criteria are satisfied.

Only S3 and AWS Budgets are provisioned by current CDK. No frontend, API, identity pool,
Lambda, Step Functions, DynamoDB, queue, registry or monitoring runtime is implemented.
See ADRs for encryption/retention and approval/versioning decisions. Tokens never go to
browsers. No physical wafer release or real MES integration is supported.

Gate 3 now trains and verifies majority/forest/CNN baselines on local CPU using audited
inputs. Weights and per-case predictions remain local; the model registry, cloud serving,
review workflow and promotion are still future services. See the model card for the
uncalibrated CNN's zero Scratch recall.
