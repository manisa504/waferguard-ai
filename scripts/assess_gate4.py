"""Assess the frozen experiment and publish honest class-conditional diagnostics."""

import json
from pathlib import Path

import numpy as np
import yaml

from waferguard.data.acquire import sha256, write_json
from waferguard.data.dataset import PreparedSplit
from waferguard.evaluation.advanced import verify_frozen
from waferguard.evaluation.calibration import calibration_metrics
from waferguard.evaluation.ood import score
from waferguard.evaluation.release_gate import assess
from waferguard.features.wafer_features import extract_features

reports = Path("reports/metrics/gate4-final")
root = Path("artifacts/release/gate4-v1")
frozen = verify_frozen()
validation = json.loads((reports / "validation.json").read_text())
test = json.loads((reports / "test.json").read_text())
config = yaml.safe_load(Path("configs/uncertainty.yaml").read_text())
result = assess(validation, test, config)
result["test_report_sha256"] = sha256(reports / "test.json")
result["frozen_manifest_sha256"] = sha256(root / "frozen.json")
write_json(reports / "qualification.json", result)
write_json(Path("reports/gates/gate_4-release.json"), result)

diagnostics = {}
for split in ["validation", "test"]:
    with np.load(root / f"{split}.npz", allow_pickle=False) as arrays:
        truth = arrays["truth"]
        probability = arrays["probabilities"]
    predicted = probability.argmax(1)
    classes = frozen["classes"]
    diagnostics[split] = {
        name: {
            "predicted_samples": int((predicted == i).sum()),
            **calibration_metrics(truth[predicted == i], probability[predicted == i]),
        }
        for i, name in enumerate(classes)
        if (predicted == i).any()
    }

# Reconstruct the already frozen decision mask for failure analysis; do not optimize it.
dataset = PreparedSplit(
    Path("data/processed/categorical-64-v1"),
    Path("data/processed/splits-v2"),
    Path("reports/data/split-audit.json"),
    "test",
)
features = np.stack([extract_features(dataset.states[row["input_row"]]) for row in dataset.records])
guard = json.loads((root / "ood.json").read_text())
policy = json.loads((root / "policy.json").read_text())
ordered = np.sort(probability, axis=1)
accepted = (
    (probability.max(1) >= policy["threshold"])
    & (ordered[:, -1] - ordered[:, -2] >= policy["minimum_margin"])
    & ~np.isin(predicted, [classes.index(k) for k in policy["always_review"]])
    & (score(features, guard) <= guard["threshold"])
)
assert int(accepted.sum()) == test["selective"]["accepted"]
errors = accepted & (predicted != truth)
assert int(errors.sum()) == test["selective"]["errors"]
critical = {
    name: int((errors & (truth == classes.index(name))).sum()) for name in policy["always_review"]
}
write_json(
    reports / "diagnostics.json",
    {
        "predicted_class_calibration": diagnostics,
        "critical_false_accepts_by_true_class": critical,
        "frozen_threshold": policy["threshold"],
        "policy_retuned": False,
        "model_reselected": False,
    },
)
print(json.dumps(result, indent=2))
