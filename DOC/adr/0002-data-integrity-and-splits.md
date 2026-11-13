# ADR 0002 — Immutable source and duplicate-aware split design

Status: source ingestion implemented; splitting deferred to Gate 2 review.

Pin Kaggle qingyi/wm811k-wafer-map version 1. Save license/source metadata, acquisition
registration time, archive SHA-256, member size/CRC and dependency versions. Preserve
the original zip byte-for-byte, do not commit raw maps, and publish no example maps at
this stage. A local SHA-256 detects subsequent changes but is not a publisher signature.

Keep 0/1/2 die states categorical. `none` is a valid class; empty arrays are missing
labels. Unknown labels/invalid maps fail count validation. No reshaping, imputation,
augmentation, normalization or splitting occurs in this gate. Legacy pickle requires
a narrow symbol allowlist and a trusted source; compatibility never permits arbitrary globals.

Exact duplicates hash shape plus uint8 categorical content. Lot identifiers are present,
but duplicates cross lots and conflicting labels exist. Gate 2 must quarantine conflicting
maps, test lot identity semantics and use lot/duplicate connected components where feasible.
If connected components prevent representative class coverage, stop and document the
limitation rather than quietly choosing a leaky random split. Preserve official source
split annotations as evidence; assess overlap before adopting a benchmark split.
