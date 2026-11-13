# ADR 0001 — Ohio and serverless foundation

Status: accepted for implementation; cloud deployment pending review.

Use `us-east-2` and profile `awsnew`. Foundation creates only versioned private raw,
artifact and access-log buckets plus a parameterized account-wide monthly budget.
SSE-S3 and enforced TLS provide encryption without adding customer key operations at
this stage. Raw/artifact versions are retained indefinitely pending an explicit data
retention decision. Access-log versions expire after 90 days. No app roles, network,
compute or expensive training endpoints are provisioned before data validation.

Use termination protection and RETAIN for stateful storage. Teardown preserves data
and exposes retained resources for explicit follow-up. This trades automated cleanup
for preservation of originals. Accounts and recipient email are supplied at deployment;
credentials never enter source. Alerts do not prevent charges.

Future target services are proposals until their gates validate need, latency and cost.
Before interpreting an SCP regional denial, check the AWS Projects home Region.
