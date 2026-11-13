"""Verify split replay and sampled real-data loading; no model is trained or evaluated."""

import json
import subprocess
from pathlib import Path

import numpy as np

from waferguard.data.acquire import sha256, write_json
from waferguard.data.dataset import PreparedSplit

report = Path("reports/data/split-audit.json")
before = json.loads(report.read_text())
with Path("reports/data/split-replay.log").open("w") as log:
    subprocess.run(["waferguard-split"], stdout=log, stderr=subprocess.STDOUT, check=True)
after = json.loads(report.read_text())
assert before["artifacts_sha256"] == after["artifacts_sha256"]
assert before["config_sha256"] == after["config_sha256"]
assert before["split_implementation_sha256"] == after["split_implementation_sha256"]
write_json(
    Path("reports/data/reproducibility.json"),
    {
        "passed": True,
        "same_artifact_hashes": before["artifacts_sha256"],
        "config_sha256": after["config_sha256"],
        "split_implementation_sha256": after["split_implementation_sha256"],
        "comparison": "Two full runs reproduced identical split manifest bytes",
    },
)
result = {}
for name in ["train", "validation", "calibration", "test"]:
    dataset = PreparedSplit(
        Path("data/processed/categorical-64-v1"), Path("data/processed/splits-v2"), report, name
    )
    for index in [0, len(dataset) - 1]:
        item = dataset[index]
        assert item["image"].shape == (3, 64, 64)
        assert item["image"].dtype == np.float32
        assert item["label"] in dataset.classes
        assert set(np.unique(item["image"])) <= {0, 1}
        assert (item["image"].sum(axis=0) == 1).all()
    result[name] = {
        "records": len(dataset),
        "sampled_records": 2,
        "shape": [3, 64, 64],
        "dtype": "float32",
        "channels_one_hot": True,
        "states_read_only": not dataset.states.flags.writeable,
    }
write_json(
    Path("reports/data/loader-smoke.json"),
    {
        "passed": True,
        "splits": result,
        "split_report_sha256": sha256(report),
        "model_trained_or_evaluated": False,
    },
)
print("Real-data split replay and loader smoke checks passed")
