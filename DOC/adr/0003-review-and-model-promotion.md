# ADR 0003 — Versioned evidence and server-side review

Status: target design only; not implemented.

The model produces classification evidence and cannot approve simulated disposition.
The deterministic policy defaults to review if calibration, evaluation or OOD evidence
is missing. Choose thresholds on validation data after calibration; no arbitrary default
threshold enables auto-accept. High-risk designation is a configurable simulated policy.

Authorize reviewers server-side using verified Cognito identity and scoped group claims.
Keep Step Functions callback tokens server-side. Resume requires current case/model/policy
versions, permission checks, unexpired single-use approval and a conditional state write.
Use idempotency records and transactional state/audit/outbox writes so replay, race and
partial callback failures cannot resume conflicting terminal cases. Enforce audit append
permissions; a database history field alone is not tamper-proof audit storage.

Reviewer corrections form versioned offline datasets. Promotion needs stored evaluation,
calibration, rollback and benchmark evidence. No online self-training or silent promotion.
