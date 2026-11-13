# Real dataset acquisition

Source: https://www.kaggle.com/datasets/qingyi/wm811k-wafer-map, version 1.
Source license metadata lists CC0: Public Domain. See ../DOC/data_rights_review.md.

`raw/wm811k-v1.zip` is local and ignored by Git. Never replace it with synthetic maps.
No dataset examples are redistributed. Only manifests and aggregate quality results
belong in the repository. `none` is a labeled class; empty failureType arrays stay unlabeled.

```bash
uv run --frozen waferguard-acquire --metadata data/manifests/kaggle-source-search.json --download
uv run --frozen waferguard-profile --archive data/raw/wm811k-v1.zip --manifest data/manifests/acquisition.json
```

Kaggle may require sign-in depending on source access policy. If download fails, obtain
the exact v1 archive through the source page; do not scrape other mirrors or embed
credentials. Do not load arbitrary pickles. The legacy restricted loader only supports
this pinned source and pandas/NumPy versions in uv.lock. The locally observed archive
hash must match the acquisition manifest. To audit changed source versions, create a
new manifest and preserve the original, then re-review before ingestion.

Gate 2 has created local processed data and split manifests after review; see below.

## Gate 2 artifacts

```bash
make index       # Original source, lot/wafer IDs, exact and D4 hashes; cached after verification.
make preprocess  # Encode labeled data as uint8 64x64 grids; no synthetic data or labels.
make split       # Verify inputs; quarantine conflicts; group lots and original/encoded duplicates.
```

The first index build and preprocessing pass can take several minutes and several GB
of memory for the original legacy table. The local categorical array is about 676 MiB;
all derived data stays under ignored `data/processed/`. Repeated runs verify hashes and
reuse unchanged artifacts. They refuse different existing split manifests.

`reports/data/split-audit.json` records the final benchmark and its leakage checks.
`source-grid-split-audit.json` is a preliminary original-grid-only assessment, not the
final encoded-input benchmark. `splits-v2` is the final manifest directory; `splits-v1`
was the preliminary assessment and is retained locally for traceability.

`waferguard.data.dataset.PreparedSplit` verifies processed artifacts and split evidence,
opens arrays read-only with `allow_pickle=False`, and returns one-hot image channels,
the original label, and stable source row ID. It never silently repairs labels or fits
statistics. Models, augmentation, confidence thresholds and model evaluation are later gates.
