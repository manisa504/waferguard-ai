"""Replay verified local models on validation and measure warm local CPU latency."""

import json
import time
from pathlib import Path

import joblib
import numpy as np
import torch

from waferguard.data.acquire import sha256, write_json
from waferguard.data.dataset import PreparedSplit
from waferguard.evaluation.metrics import classification_metrics
from waferguard.features.wafer_features import extract_features
from waferguard.models.cnn import WaferCNN
from waferguard.training.train import cnn_probabilities, labels_for

root = Path("artifacts/experiments/gate3-v1")
reports = Path("reports/metrics/gate3-v1")
receipt = json.loads((root / "experiment.json").read_text())
if receipt["status"] != "completed" or receipt["test_evaluated"] or receipt["calibration_used"]:
    raise ValueError("Expected a completed train/validation-only Gate 3 receipt")
for name, digest in receipt["artifacts_sha256"].items():
    if sha256(root / name) != digest:
        raise ValueError(f"Artifact changed: {name}")
config = receipt["identity"]["config"]
torch.set_num_threads(config["threads"])
torch.use_deterministic_algorithms(True)
dataset = PreparedSplit(
    Path(config["processed"]), Path(config["splits"]), Path(config["split_report"]), "validation"
)
y = labels_for(dataset)
classes = list(dataset.classes)
# joblib is accepted only for this locally produced model after receipt verification.
forest = joblib.load(root / "forest.joblib")
checkpoint = torch.load(root / "cnn-best.pt", map_location="cpu", weights_only=True)
assert checkpoint["classes"] == classes
cnn = WaferCNN(len(classes))
cnn.load_state_dict(checkpoint["state_dict"])
cnn.eval()
features = np.load(root / "validation-features.npy", mmap_mode="r", allow_pickle=False)
probabilities = {
    "forest": forest.predict_proba(features),
    "cnn": cnn_probabilities(cnn, dataset, config["cnn"]["batch_size"]),
}
verified = {}
for name, value in probabilities.items():
    with np.load(root / f"{name}-validation.npz", allow_pickle=False) as saved:
        np.testing.assert_array_equal(y, saved["truth"])
        np.testing.assert_array_equal(
            np.array([row["row_id"] for row in dataset.records]), saved["row_ids"]
        )
        difference = float(np.max(np.abs(value - saved["probabilities"])))
        np.testing.assert_allclose(value, saved["probabilities"], rtol=0, atol=1e-6)
    metrics = classification_metrics(y, value, classes)
    assert metrics == receipt["validation_results"][name]["metrics"]
    verified[name] = {
        "samples": len(dataset),
        "max_probability_absolute_difference": difference,
        "metrics_identical": True,
    }
write_json(
    reports / "replay.json",
    {
        "passed": True,
        "models": verified,
        "experiment_receipt_sha256": sha256(root / "experiment.json"),
        "scope": "Frozen-model validation inference replay; full retraining was not repeated",
        "test_evaluated": False,
        "calibration_used": False,
    },
)

rng = np.random.default_rng(42)
positions = rng.choice(len(dataset), size=120, replace=False)
grids = [
    np.array(dataset.states[dataset.records[int(position)]["input_row"]], copy=True)
    for position in positions
]


def forest_one(grid):
    return forest.predict_proba(extract_features(grid)[None, :])


def cnn_one(grid):
    state = torch.from_numpy(grid)
    image = (state[None, None, :, :] == torch.arange(3).view(1, 3, 1, 1)).float()
    with torch.inference_mode():
        return cnn(image).softmax(1)


measurements = {}
for name, function in [("forest", forest_one), ("cnn", cnn_one)]:
    for grid in grids[:20]:
        function(grid)
    durations = []
    for grid in grids[20:]:
        start = time.perf_counter_ns()
        function(grid)
        durations.append((time.perf_counter_ns() - start) / 1_000_000)
    artifact = root / ("forest.joblib" if name == "forest" else "cnn-best.pt")
    measurements[name] = {
        "samples": len(durations),
        "p50_ms": float(np.percentile(durations, 50)),
        "p95_ms": float(np.percentile(durations, 95)),
        "artifact_bytes": artifact.stat().st_size,
        "artifact_sha256": sha256(artifact),
        "batch_size": 1,
    }
write_json(
    reports / "local-inference.json",
    {
        "models": measurements,
        "device": "cpu",
        "threads": config["threads"],
        "warmup_requests": 20,
        "scope": "Warm local batch-one inference from already encoded 64x64 states; includes "
        "feature extraction or one-hot conversion, excludes source resizing, integrity "
        "verification, model loading, network and AWS cold starts",
        "production_or_aws_benchmark": False,
    },
)
print("Frozen model validation replay and warm local inference measurements passed")
