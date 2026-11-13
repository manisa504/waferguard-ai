# Dataset source and usage review

Reviewed 2026-11-10 America/Los_Angeles. Source: [Kaggle WM-811K](https://www.kaggle.com/datasets/qingyi/wm811k-wafer-map).
The source [metadata page](https://www.kaggle.com/qingyi/wm811k-wafer-map/metadata)
and saved Kaggle API metadata identify the source license as **CC0: Public Domain**.
The public v1 download was accessible without credentials during acquisition.
License/source evidence is saved in `data/manifests/kaggle-source-search.json`; its hash
is recorded with the archive hash in `data/manifests/acquisition.json`.

The source cites Wu, Ming-Ju; Jang, Jyh-Shing R.; Chen, Jui-Long, “Wafer Map Failure
Pattern Recognition and Similarity Ranking for Large-Scale Data Sets,” IEEE Transactions
on Semiconductor Manufacturing 28(1), 2015, pp. 1–12. Attribution is preserved for
provenance even though the mirror lists CC0.

Decision: acquire privately for this educational project and publish acquisition code,
metadata and aggregate quality statistics. Do not publish raw maps or derived examples
in this change. The uploader's license assertion has not been independently confirmed
with the original data owner; record that limitation and revisit source terms before
future sample redistribution or commercial use. Project MIT terms do not relicense data.
The source's published lot figure is descriptive metadata, not a verified ingestion count.
