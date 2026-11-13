"""Synthetic mathematical contracts; these fixtures are not wafer performance evidence."""

import numpy as np
import pytest

pytest.importorskip("scipy")
from waferguard.evaluation.calibration import calibration_metrics, fit_temperature, probabilities
from waferguard.evaluation.ood import fit_guard, score
from waferguard.evaluation.selective_risk import select_threshold, wilson_upper


def test_temperature_fit_reduces_overconfident_nll_without_changing_argmax():
    logits = np.array([[10.0, 0.0], [10.0, 0.0], [10.0, 0.0], [0.0, 10.0]])
    truth = np.array([0, 0, 1, 1])
    temperature = fit_temperature(logits, truth)
    before = probabilities(logits)
    after = probabilities(logits, temperature)
    assert 0.05 <= temperature <= 20
    assert calibration_metrics(truth, after)["nll"] < calibration_metrics(truth, before)["nll"]
    np.testing.assert_array_equal(before.argmax(1), after.argmax(1))


def test_exact_ece_brier_values_and_last_bin_includes_probability_one():
    truth = np.array([0, 1])
    probability = np.array([[1.0, 0.0], [1.0, 0.0]])
    metrics = calibration_metrics(truth, probability)
    assert metrics["ece"] == pytest.approx(0.5)
    assert metrics["brier"] == pytest.approx(1.0)
    assert sum(row["count"] for row in metrics["reliability"]) == 2


def test_invalid_temperature_and_nonfinite_logits_are_rejected():
    with pytest.raises(ValueError):
        probabilities(np.array([[1.0, 2.0]]), 0)
    with pytest.raises(ValueError):
        probabilities(np.array([[np.nan, 2.0]]))


def policy():
    return {
        "minimum_margin": 0.2,
        "always_review": ["Scratch"],
        "minimum_accepted": 500,
        "target_accepted_error": 0.01,
        "maximum_wilson_upper": 0.02,
    }


def test_selective_rule_cannot_hide_a_critical_false_accept_in_global_accuracy():
    probability = np.tile([0.999, 0.001], (1000, 1))
    truth = np.zeros(1000, dtype=int)
    accepted = select_threshold(truth, probability, ["None", "Scratch"], policy())
    assert accepted["auto_accept_enabled"]
    assert accepted["selected"]["coverage"] == 1.0
    truth[0] = 1
    rejected = select_threshold(truth, probability, ["None", "Scratch"], policy())
    assert not rejected["auto_accept_enabled"]
    assert rejected["selected"] is None


def test_ood_and_critical_class_force_abstention():
    probability = np.tile([0.001, 0.999], (1000, 1))
    truth = np.ones(1000, dtype=int)
    assert not select_threshold(truth, probability, ["None", "Scratch"], policy())[
        "auto_accept_enabled"
    ]
    probability = probability[:, ::-1]
    assert not select_threshold(
        truth, probability, ["None", "Scratch"], policy(), np.ones(1000, dtype=bool)
    )["auto_accept_enabled"]


def test_wilson_bound_and_training_only_ood_guard():
    assert wilson_upper(0, 0) == 1
    assert wilson_upper(0, 1000) > 0.0
    assert wilson_upper(0, 1000) < 0.01
    data = np.linspace(0, 1, 1000)[:, None]
    guard = fit_guard(data)
    assert guard["fit_split"] == "train"
    assert score(np.array([100.0]), guard) > guard["threshold"]


def test_invalid_wafer_inputs_are_rejected_before_model_execution():
    pytest.importorskip("torch")
    from waferguard.inference.predict import ModelBundle

    model = ModelBundle.__new__(ModelBundle)
    for wafer in [
        np.zeros((64, 64), dtype=np.uint8),
        np.full((64, 64), 3),
        np.full((64, 64), np.nan),
        np.ones((257, 64)),
        np.ones(5),
    ]:
        with pytest.raises(ValueError):
            model.predict(wafer)


def test_release_gate_blocks_rare_class_errors_even_when_global_error_is_low():
    from waferguard.evaluation.release_gate import assess

    config = {
        "minimum_macro_f1": 0.75,
        "minimum_scratch_recall": 0.6,
        "policy": {"target_accepted_error": 0.01, "maximum_wilson_upper": 0.02},
    }
    validation = {"classification": {"macro_f1": 0.8, "per_class": {"Scratch": {"recall": 0.8}}}}
    test = {
        "classification": {"macro_f1": 0.8, "per_class": {"Scratch": {"recall": 0.8}}},
        "selective": {
            "coverage": 0.7,
            "risk": 0.005,
            "wilson_upper_95": 0.01,
            "critical_false_accepts": 1,
        },
        "policy_retuned_on_test": False,
    }
    decision = assess(validation, test, config)
    assert not decision["qualified_for_promotion"]
    assert not decision["automatic_acceptance_authorized"]
    assert "critical-class" in decision["failures"][0]


def test_unqualified_bundle_is_refused_before_weights_are_loaded(tmp_path):
    import json

    pytest.importorskip("torch")
    from waferguard.inference.predict import ModelBundle

    (tmp_path / "manifest.json").write_text(
        json.dumps({"qualification": {"qualified_for_promotion": False}})
    )
    with pytest.raises(ValueError, match="unqualified"):
        ModelBundle(tmp_path)
