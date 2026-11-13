# Gate 1 — Real source acquisition and quality

## Objective

Acquire WM-811K from the named source, preserve provenance and originals, verify actual
counts/encodings, and assess label/duplicate/identifier quality and split feasibility.

## Environment / revision

Same uncommitted local foundation revision and dependency locks as Gate 0; see
[source-manifest.json](source-manifest.json). Measured at `2026-11-11T00:38:18.569851+00:00` UTC
(November 10, 2026 in America/Los_Angeles). NumPy 1.26.4, pandas
2.2.3. Original source version 1; exact archive SHA-256:
`0e4bd4316a110a04e475a88071f5e1c7fe4303b12ee53c851d2cae4d995a93e2`.

## Criteria and actual evidence

| Criterion | Result | Evidence |
|---|---|---|
| Named source access and usage review | PASS with provenance limitation | Kaggle metadata lists CC0; DOC/data_rights_review.md |
| Untouched originals and lineage | PASS | Ignored original zip; acquisition.json records hash, size, registration time, source/version and metadata hash |
| Verify totals / nine classes | PASS | 811,457 maps, 172,950 labeled; all expected class counts match |
| Preserve missing labels | PASS | 638,507 remain unlabeled; valid None class kept distinct |
| Profile die states and shapes | PASS | 632 distinct shapes, only 0/1/2 states; no invalid maps |
| Duplicate / annotation quality | FINDINGS RECORDED | 114,858 duplicate rows; 14 conflicting-label map groups |
| Identifier / split feasibility | ASSESSED; split NOT CREATED | 46,293 lots, zero missing/duplicate wafer IDs; cross-lot duplicates and source train/test overlap |
| No data redistribution | PASS | No raw or derived wafer examples tracked; only metadata and aggregate reports |

## Commands and measured artifacts

```bash
# Source metadata was fetched before downloading the original archive:
curl --fail --location 'https://www.kaggle.com/api/v1/datasets/list?search=wm811k-wafer-map' -o data/manifests/kaggle-source-search.json
uv run --frozen waferguard-acquire --metadata data/manifests/kaggle-source-search.json --download
uv run --frozen waferguard-profile --archive data/raw/wm811k-v1.zip --manifest data/manifests/acquisition.json
```

The initial transfer used the same pinned public download URL recorded in acquisition.json;
registration then preserved the existing bytes. An initial system-Python HTTPS certificate
error was resolved by using verified curl TLS, without disabling certificate checks.
The successful final profile completed in 85.298 seconds and exited 0.
[quality.json](../data/quality.json) and [profile-run.log](../data/profile-run.log) contain
actual results. [Data card](../../DOC/data_card.md) has the full class table; the original
source spelling `trianTestLabel` is preserved. Synthetic test fixtures are not real data
or model performance evidence.

Key leakage result: **3,158 exact map groups span source Training and Test,
despite zero shared lot names**. Across all maps 32,392 duplicate groups span lots.
Labeled data contains 169,698 unique maps and 3,252 duplicate rows.
Conflicting hashes/classes are saved for follow-up; no annotation is silently corrected.
The locally observed 46,293 lot names differ from the mirror's published 46,393 figure.

## Limitations

The mirror's license/provenance assertion and original-owner rights are not independently
verified. The local hash is not an independently authenticated publisher checksum.
The original legacy pickle is processed using a narrow reconstruction allowlist; this is
not a sandbox, and reconstruction should run isolated without credentials. No raw sample
publication occurred. Exact hashing does not find every transformed/approximate duplicate.
Identifier presence does not establish temporal/process independence. Source split overlap
and conflicting labels prevent treating these annotations as a ready-to-train benchmark.

## Pass/fail and next-gate decision

**Gate 1 acquisition, measured quality and feasibility assessment: PASS.** This is not a
claim of clean training data or model detection skill. **HOLD before Gate 2 for the review
required by outline section 10.** Follow DOC/split_feasibility.md: quarantine conflicts,
audit identifier semantics and lot/duplicate connected components, measure minority-class
coverage, then define immutable splits and leakage checks. Gate 2 and model training have
not started. Gate 0 live cloud checks remain outstanding as described in gate_0.md.
