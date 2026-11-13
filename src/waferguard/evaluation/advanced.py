"""Fit calibration/select policy, freeze them, then evaluate held-out test once."""

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import torch
import yaml

from waferguard.approval.workflow import fingerprint
from waferguard.data.acquire import sha256, write_json
from waferguard.data.dataset import PreparedSplit
from waferguard.evaluation.calibration import calibration_metrics, fit_temperature, probabilities
from waferguard.evaluation.metrics import classification_metrics
from waferguard.evaluation.ood import fit_guard, score
from waferguard.evaluation.selective_risk import select_threshold, selective_result
from waferguard.features.wafer_features import extract_features
from waferguard.training.advanced import make_model
from waferguard.training.train import image_batches, labels_for

ROOT = Path("artifacts/release/gate4-v1")
REPORTS = Path("reports/metrics/gate4-final")
PROCESSED = Path("data/processed/categorical-64-v1")
SPLITS = Path("data/processed/splits-v2")
AUDIT = Path("reports/data/split-audit.json")
CONFIG = Path("configs/uncertainty.yaml")


def data(name):
    return PreparedSplit(PROCESSED, SPLITS, AUDIT, name)


def logits_for(model, dataset):
    model.eval()
    output = []
    with torch.inference_mode():
        for _, images in image_batches(dataset, 256, np.arange(len(dataset))):
            output.append(model(images).numpy())
    return np.concatenate(output)


def feature_cache(name):
    experiment = Path("artifacts/experiments/gate3-v1")
    receipt = json.loads((experiment / "experiment.json").read_text())
    path = experiment / f"{name}-features.npy"
    if sha256(path) != receipt["artifacts_sha256"][path.name]:
        raise ValueError("Prior training-feature cache changed")
    if receipt["identity"]["split_report_sha256"] != sha256(AUDIT):
        raise ValueError("Feature cache belongs to another split")
    return np.load(path, mmap_mode="r", allow_pickle=False)


def model_for(path):
    saved = torch.load(path, map_location="cpu", weights_only=True)
    model = make_model(saved["architecture"], len(saved["classes"]))
    model.load_state_dict(saved["state_dict"])
    model.eval()
    return model, saved["classes"]


def cluster_intervals(truth, probability, records, repetitions, seed):
    classes = probability.shape[1]
    groups, indices = np.unique([r["component"] for r in records], return_inverse=True)
    counts = np.zeros((len(groups), classes, classes), dtype=np.int64)
    np.add.at(counts, (indices, truth, probability.argmax(1)), 1)
    rng = np.random.default_rng(seed)
    f1, recall = [], []
    for _ in range(repetitions):
        weights = np.bincount(rng.integers(len(groups), size=len(groups)), minlength=len(groups))
        matrix = (counts * weights[:, None, None]).sum(0)
        diag = matrix.diagonal()
        f1.append(float(np.mean(np.divide(2 * diag, np.maximum(matrix.sum(0) + matrix.sum(1), 1)))))
        recall.append((diag / np.maximum(matrix.sum(1), 1)).tolist())
    return {
        "method": "connected-component cluster bootstrap",
        "repetitions": repetitions,
        "macro_f1_95": np.quantile(f1, [0.025, 0.975]).tolist(),
        "per_class_recall_95": np.quantile(recall, [0.025, 0.975], axis=0).T.tolist(),
        "scope": "Empirical interval on the observed benchmark, not industrial independence proof",
    }


def per_class_calibration(truth, probability, classes):
    return {
        name: {
            "samples": int((truth == i).sum()),
            **calibration_metrics(truth[truth == i], probability[truth == i]),
        }
        for i, name in enumerate(classes)
        if (truth == i).any()
    }


def fit(candidate):
    if (ROOT / "frozen.json").exists():
        raise ValueError("Release is already frozen; use its test phase or a new release directory")
    ROOT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    result = json.loads((candidate / "result.json").read_text())
    config = yaml.safe_load(CONFIG.read_text())
    if (
        result["validation"]["macro_f1"] < config["minimum_macro_f1"]
        or result["validation"]["per_class"]["Scratch"]["recall"] < config["minimum_scratch_recall"]
    ):
        raise ValueError("Candidate does not satisfy predeclared classification criteria")
    if sha256(candidate / "best.pt") != result["model_sha256"]:
        raise ValueError("Selected candidate changed")
    shutil.copyfile(candidate / "best.pt", ROOT / "model.pt")
    model, classes = model_for(ROOT / "model.pt")
    torch.set_num_threads(4)
    print("Fitting scalar temperature on reserved calibration data", flush=True)
    calibration = data("calibration")
    y_cal = labels_for(calibration)
    logits = logits_for(model, calibration)
    temperature = fit_temperature(logits, y_cal)
    cal = {
        "temperature": temperature,
        "method": "scalar-temperature-scaling",
        "fit_split": "calibration",
        "samples": len(calibration),
        "model_version": sha256(ROOT / "model.pt"),
        "before": calibration_metrics(y_cal, probabilities(logits)),
        "after": calibration_metrics(y_cal, probabilities(logits, temperature)),
    }
    cal["version"] = fingerprint(cal)
    write_json(ROOT / "calibration.json", cal)
    guard = fit_guard(feature_cache("train"))
    guard["failure_fraction_hist"] = np.histogram(
        feature_cache("train")[:, 1], bins=np.linspace(0, 1, 21)
    )[0].tolist()
    write_json(ROOT / "ood.json", guard)
    validation = data("validation")
    y_val = labels_for(validation)
    val_logits = logits_for(model, validation)
    probability = probabilities(val_logits, temperature)
    val_ood = score(feature_cache("validation"), guard) > guard["threshold"]
    selection = select_threshold(y_val, probability, classes, config["policy"], val_ood)
    chosen = selection["selected"]
    policy = {
        **config["policy"],
        "enabled": selection["auto_accept_enabled"],
        "evaluated": True,
        "threshold": chosen["threshold"] if chosen else 1.0,
        "model_version": sha256(ROOT / "model.pt"),
        "calibration_version": cal["version"],
        "selection_split": "validation",
        "critical_false_accept_requirement": 0,
        "scope": "Simulated classification review; no physical quality release",
    }
    policy["version"] = fingerprint(policy)
    write_json(ROOT / "policy.json", policy)
    evaluation = {
        "classification": classification_metrics(y_val, probability, classes),
        "calibration_before": calibration_metrics(y_val, probabilities(val_logits)),
        "calibration_after": calibration_metrics(y_val, probability),
        "per_true_class_calibration": per_class_calibration(y_val, probability, classes),
        "selective": selection,
        "ood_flag_rate": float(val_ood.mean()),
        "bootstrap": cluster_intervals(
            y_val, probability, validation.records, config["bootstrap_repetitions"], config["seed"]
        ),
    }
    write_json(REPORTS / "calibration.json", cal)
    write_json(REPORTS / "validation.json", evaluation)
    np.savez_compressed(
        ROOT / "validation.npz", truth=y_val, probabilities=probability, logits=val_logits
    )
    frozen = {
        "model_version": sha256(ROOT / "model.pt"),
        "calibration_version": cal["version"],
        "policy_version": policy["version"],
        "classes": classes,
        "candidate_result_sha256": sha256(candidate / "result.json"),
        "config_sha256": sha256(CONFIG),
        "split_report_sha256": sha256(AUDIT),
        "evaluation_code_sha256": sha256(Path(__file__)),
        "source_sha256": {
            name: sha256(Path(__file__).parents[1] / name)
            for name in [
                "models/cnn.py",
                "models/lite.py",
                "training/advanced.py",
                "training/train.py",
                "data/dataset.py",
                "data/materialize.py",
                "data/preprocess.py",
                "evaluation/calibration.py",
                "evaluation/metrics.py",
                "evaluation/ood.py",
                "evaluation/selective_risk.py",
            ]
        },
        "artifacts": {
            name: sha256(ROOT / name)
            for name in ["model.pt", "calibration.json", "policy.json", "ood.json"]
        },
        "selection_split": "validation",
        "test_evaluated": False,
    }
    write_json(ROOT / "frozen.json", frozen)
    write_json(REPORTS / "frozen.json", frozen)
    print(
        json.dumps(
            {
                "temperature": temperature,
                "validation_macro_f1": evaluation["classification"]["macro_f1"],
                "auto_accept_enabled": policy["enabled"],
                "test_evaluated": False,
            }
        )
    )


def verify_frozen():
    frozen = json.loads((ROOT / "frozen.json").read_text())
    if frozen["config_sha256"] != sha256(CONFIG) or frozen["split_report_sha256"] != sha256(AUDIT):
        raise ValueError("Frozen release inputs changed")
    if frozen["evaluation_code_sha256"] != sha256(Path(__file__)):
        raise ValueError("Evaluation implementation changed after release freezing")
    for name, digest in frozen["source_sha256"].items():
        if sha256(Path(__file__).parents[1] / name) != digest:
            raise ValueError("Scientific implementation changed after freezing")
    for name, digest in frozen["artifacts"].items():
        if sha256(ROOT / name) != digest:
            raise ValueError("Frozen release artifact changed")
    return frozen


def test_and_stress():
    verify_frozen()
    if (REPORTS / "test.json").exists():
        print("Held-out evaluation already recorded; no new selection or tuning performed")
        return
    config = yaml.safe_load(CONFIG.read_text())
    model, classes = model_for(ROOT / "model.pt")
    torch.set_num_threads(4)
    cal = json.loads((ROOT / "calibration.json").read_text())
    policy = json.loads((ROOT / "policy.json").read_text())
    guard = json.loads((ROOT / "ood.json").read_text())
    print("Evaluating held-out test against frozen model/calibration/policy", flush=True)
    dataset = data("test")
    truth = labels_for(dataset)
    logits = logits_for(model, dataset)
    probability = probabilities(logits, cal["temperature"])
    features = np.stack(
        [extract_features(dataset.states[row["input_row"]]) for row in dataset.records]
    )
    ood = score(features, guard) > guard["threshold"]
    report = {
        "freeze_sha256": sha256(ROOT / "frozen.json"),
        "classification": classification_metrics(truth, probability, classes),
        "calibration": calibration_metrics(truth, probability),
        "per_true_class_calibration": per_class_calibration(truth, probability, classes),
        "selective": selective_result(truth, probability, policy["threshold"], classes, policy, ood)
        if policy["enabled"]
        else {"coverage": 0.0, "review_rate": 1.0, "risk": None},
        "bootstrap": cluster_intervals(
            truth, probability, dataset.records, config["bootstrap_repetitions"], config["seed"]
        ),
        "policy_retuned_on_test": False,
    }
    write_json(REPORTS / "test.json", report)
    np.savez_compressed(ROOT / "test.npz", truth=truth, probabilities=probability)
    # These are clearly synthetic stress inputs, not claimed real OOD ground truth.
    rng = np.random.default_rng(config["seed"])
    positions = rng.choice(len(dataset), size=256, replace=False)
    grids = np.stack([dataset.states[dataset.records[int(i)]["input_row"]] for i in positions])
    stresses = {}
    corrupted = grids.copy()
    flip = (rng.random(corrupted.shape) < 0.05) & (corrupted > 0)
    corrupted[flip] = 3 - corrupted[flip]
    random_grids = rng.choice([0, 1, 2], size=grids.shape, p=[0.1, 0.45, 0.45]).astype(np.uint8)
    for name, states in [
        ("die_state_noise_5pct", corrupted),
        ("synthetic_random_ood", random_grids),
    ]:
        images = torch.from_numpy(
            (states[:, None] == np.arange(3)[None, :, None, None]).astype(np.float32)
        )
        with torch.inference_mode():
            altered = probabilities(model(images).numpy(), cal["temperature"])
        flags = (
            score(np.stack([extract_features(grid) for grid in states]), guard) > guard["threshold"]
        )
        confidence = altered.max(1)
        ordered = np.sort(altered, axis=1)
        critical = [classes.index(value) for value in policy["always_review"]]
        accepted = (
            (confidence >= policy["threshold"])
            & (ordered[:, -1] - ordered[:, -2] >= policy["minimum_margin"])
            & ~np.isin(altered.argmax(1), critical)
            & ~flags
        )
        stresses[name] = {
            "samples": len(states),
            "ood_flag_rate": float(flags.mean()),
            "mean_confidence": float(altered.max(1).mean()),
            "review_rate": float(1 - accepted.mean()) if policy["enabled"] else 1.0,
            "labels": "No ground-truth labels asserted for synthetic/altered inputs",
        }
    write_json(
        REPORTS / "stress.json",
        {
            "results": stresses,
            "scope": "Limited engineered stress, not universal OOD proof",
            "invalid_inputs": "Empty/all-outside/illegal states rejected by inference contract",
        },
    )
    print(
        json.dumps(
            {
                "test_macro_f1": report["classification"]["macro_f1"],
                "scratch_recall": report["classification"]["per_class"]["Scratch"]["recall"],
                "policy_retuned_on_test": False,
            }
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["fit", "test"])
    parser.add_argument(
        "--candidate", type=Path, default=Path("artifacts/experiments/gate4-balanced-v1")
    )
    args = parser.parse_args()
    if args.phase == "fit":
        fit(args.candidate)
    else:
        test_and_stress()


if __name__ == "__main__":
    main()
