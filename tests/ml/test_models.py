"""Synthetic mathematical/training contracts; no real model skill is measured here."""

import numpy as np
import pytest

pytest.importorskip("torch")
pytest.importorskip("sklearn")

import torch

from waferguard.evaluation.metrics import classification_metrics
from waferguard.features.wafer_features import FEATURE_NAMES, extract_features
from waferguard.models.baseline import majority_class
from waferguard.models.cnn import WaferCNN


def test_feature_regions_preserve_failure_locations_and_missing_die_semantics():
    states = np.ones((64, 64), dtype=np.uint8)
    states[:8, :8] = 2
    before = states.copy()
    vector = extract_features(states)
    assert vector.shape == (len(FEATURE_NAMES),)
    assert vector[0] == 1
    assert vector[1] == 1 / 64
    assert vector[2] == 1
    assert vector[3:66].sum() == 0
    np.testing.assert_array_equal(states, before)
    assert np.isfinite(extract_features(np.zeros_like(states))).all()


def test_features_never_cast_invalid_states_to_valid_categories():
    with pytest.raises(ValueError):
        extract_features(np.full((64, 64), 0.5))


def test_majority_is_based_on_training_counts_only():
    assert majority_class(np.array([2, 2, 2, 0, 1]), 3) == 2
    with pytest.raises(ValueError):
        majority_class(np.array([-1, 2]), 3)


def test_macro_metrics_keep_zero_recall_classes_in_the_average():
    truth = np.array([0, 0, 1, 2])
    probabilities = np.array([[1.0, 0.0, 0.0]] * 4)
    metrics = classification_metrics(truth, probabilities, ["None", "Scratch", "Donut"])
    assert metrics["accuracy"] == 0.5
    assert metrics["balanced_accuracy"] == pytest.approx(1 / 3)
    assert metrics["macro_f1"] == pytest.approx(2 / 9)
    assert metrics["per_class"]["Scratch"]["recall"] == 0
    assert metrics["confusion_matrix"] == [[2, 0, 0], [1, 0, 0], [1, 0, 0]]


@pytest.mark.parametrize(
    "probabilities", [np.array([[np.nan, 1]]), np.array([[-1.0, 2.0]]), np.array([[0.1, 0.1]])]
)
def test_invalid_probabilities_fail_closed(probabilities):
    with pytest.raises(ValueError):
        classification_metrics(np.array([0]), probabilities, ["a", "b"])


def test_cnn_learns_finite_gradients_and_has_stable_reload(tmp_path):
    torch.set_num_threads(2)
    torch.manual_seed(42)
    model = WaferCNN(9)
    batch = torch.rand(4, 3, 64, 64)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001)
    before = model.spatial[0].weight.detach().clone()
    loss = torch.nn.CrossEntropyLoss()(model(batch), torch.tensor([0, 1, 2, 3]))
    loss.backward()
    assert torch.isfinite(loss)
    assert all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None)
    optimizer.step()
    assert not torch.equal(before, model.spatial[0].weight)
    path = tmp_path / "model.pt"
    torch.save(model.state_dict(), path)
    restored = WaferCNN(9)
    restored.load_state_dict(torch.load(path, weights_only=True, map_location="cpu"))
    model.eval()
    restored.eval()
    with torch.inference_mode():
        torch.testing.assert_close(model(batch), restored(batch), rtol=0, atol=0)
    with pytest.raises(ValueError):
        model(torch.rand(4, 1, 32, 32))


@pytest.mark.parametrize("split", ["test", "calibration"])
def test_training_runner_refuses_reserved_splits_before_data_access(tmp_path, split):
    import yaml

    from waferguard.training.train import run

    config = {"stage": "gate_3", "device": "cpu", "validation_split": split}
    path = tmp_path / "train.yaml"
    path.write_text(yaml.safe_dump(config))
    with pytest.raises(ValueError, match="cannot be used"):
        run(path, tmp_path / "run", tmp_path / "reports")
    assert not (tmp_path / "run").exists()


def test_completed_experiment_cannot_silently_reuse_changed_model(tmp_path, monkeypatch):
    import json

    import yaml

    from waferguard.training.train import run

    config = {
        "stage": "gate_3",
        "device": "cpu",
        "validation_split": "validation",
        "seed": 42,
        "threads": 2,
        "split_report": "unused",
        "cnn": {"class_weights": None, "augmentation": False},
    }
    path = tmp_path / "train.yaml"
    path.write_text(yaml.safe_dump(config))
    monkeypatch.setattr("waferguard.training.train.provenance", lambda *args: {})
    root = tmp_path / "run"
    root.mkdir()
    (root / "cnn.pt").write_bytes(b"changed-local-model")
    (root / "experiment.json").write_text(
        json.dumps(
            {
                "identity": {"config": config},
                "status": "completed",
                "artifacts_sha256": {"cnn.pt": "0" * 64},
            }
        )
    )
    with pytest.raises(ValueError, match="artifact changed"):
        run(path, root, tmp_path / "reports")
