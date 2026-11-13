"""Explicit class ordering, including zero-recall minority classes."""

import numpy as np
from sklearn.metrics import classification_report, confusion_matrix


def classification_metrics(
    truth: np.ndarray, probabilities: np.ndarray, classes: list[str]
) -> dict:
    if (
        truth.ndim != 1
        or probabilities.shape != (len(truth), len(classes))
        or not len(truth)
        or not np.isfinite(probabilities).all()
        or (probabilities < 0).any()
        or not np.allclose(probabilities.sum(axis=1), 1, atol=1e-5)
        or (truth < 0).any()
        or (truth >= len(classes)).any()
    ):
        raise ValueError("Invalid labels/probabilities or class ordering")
    prediction = probabilities.argmax(axis=1)
    report = classification_report(
        truth,
        prediction,
        labels=np.arange(len(classes)),
        target_names=classes,
        output_dict=True,
        zero_division=0,
    )
    per_class = {
        name: {
            key: float(value) if key != "support" else int(value)
            for key, value in report[name].items()
        }
        for name in classes
    }
    return {
        "samples": len(truth),
        "classes": classes,
        "accuracy": float((truth == prediction).mean()),
        "macro_f1": float(report["macro avg"]["f1-score"]),
        "macro_precision": float(report["macro avg"]["precision"]),
        "balanced_accuracy": float(np.mean([per_class[name]["recall"] for name in classes])),
        "per_class": per_class,
        "confusion_matrix": confusion_matrix(
            truth, prediction, labels=np.arange(len(classes))
        ).tolist(),
    }
