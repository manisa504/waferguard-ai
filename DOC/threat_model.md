# Threat model

Scope: local ingestion + authored S3/budget infrastructure. Future application controls
below are requirements, not deployed protections. Assets: original data, label provenance,
model/calibration versions, reviewer identity, private task tokens and audit records.
Trust boundaries: public source → local deserializer; developer/CI → AWS; public guest →
authenticated review API; API → durable workflow and state store.

| Threat | Foundation control / required future control | Evidence / status |
|---|---|---|
| Malicious or changed data archive | Pinned source, archive hash, exact member path/size, no extraction, reconstruction allowlist | Local tests; pickle allowlist is not a sandbox |
| Source substitution / unverified license | Source slug/license metadata captured; checksum origin limitation recorded | Acquisition manifest and rights review |
| Raw dataset or secret committed | Ignore raw/weights/env files plus tracked-file CI guard | Local guard; GitHub execution pending |
| Public S3 / plaintext access | Block public access, bucket-owner enforcement, TLS deny, encryption, versioning | CDK assertions + strict synth; not deployed |
| Unbounded infrastructure spending | No compute in foundation; budget actual/forecast warnings | Parameterized CDK; not deployed; warnings do not cap spend |
| Leaky train/test benchmark | Duplicate/conflicting-label and source-split audits | Gate 1 measurements; Gate 2 split controls pending |
| False confidence / invented performance | Inactive policy, measured validation metrics and explicit Scratch blind spot | Model card; future evaluation gates required |
| Unauthorized or replayed reviewer writes | Verified identity, server-side roles/tokens, expiry, version checks, idempotency, transactions | Design only, Gate 5 tests required |
| Audit tampering / partial resume | Append-only permissions, durable audit/outbox and callback reconciliation | Design only |
| Supply-chain compromise | Pinned locks, read-only CI permissions, dependency advisory recorded | Local dependency audit; action SHA pinning still pending |

Residual risks: third-party dataset provenance is not independently authenticated;
legacy deserialization consumes several GB of memory and may execute reconstruction
code from allowed libraries. Process only the documented source in an isolated environment
without credentials. Approximate duplicates, rotations and temporal/lot semantics are
not fully audited. Historical Gate 3 models have validation results and a zero Scratch recall baseline.
The Gate 4 candidate improved validation recall but failed frozen test qualification,
including four critical false accepts. Promotion and automatic acceptance are blocked. No reviewer application, registry, deployment or cloud audit
chain exists yet. Perform runtime security, authorization, replay and fault tests at later gates.

Gate 3 model persistence: CNN reload uses `weights_only=True`; the locally produced
forest joblib is loaded only after receipt checksum validation. Neither loader should
accept arbitrary external models. Versioned source/config/input/model hashes support
traceability, not authentication against a privileged local attacker. The acceptance
policy remains inactive; no calibrated confidence or defect-safety claim is established.
