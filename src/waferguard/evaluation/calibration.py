"""Temperature scaling fitted only on the reserved calibration partition."""

import numpy as np
from scipy.optimize import minimize_scalar


def probabilities(logits, temperature=1.0):
    logits = np.asarray(logits, dtype=np.float64)
    if logits.ndim != 2 or not np.isfinite(logits).all() or not 0.05 <= temperature <= 20:
        raise ValueError("Invalid logits or calibration temperature")
    shifted = logits / temperature
    shifted -= shifted.max(axis=1, keepdims=True)
    scores = np.exp(shifted)
    return scores / scores.sum(axis=1, keepdims=True)


def calibration_metrics(truth, probability, bins=15):
    truth = np.asarray(truth)
    probability = np.asarray(probability)
    if (
        probability.shape[0] != len(truth)
        or not np.isfinite(probability).all()
        or (probability < 0).any()
        or not np.allclose(probability.sum(1), 1)
    ):
        raise ValueError("Invalid calibration inputs")
    confidence = probability.max(1)
    correct = probability.argmax(1) == truth
    reliability = []
    for i in range(bins):
        selected = (confidence >= i / bins) & (confidence < (i + 1) / bins)
        if i == bins - 1:
            selected |= confidence == 1
        count = int(selected.sum())
        reliability.append(
            {
                "lower": i / bins,
                "upper": (i + 1) / bins,
                "count": count,
                "confidence": float(confidence[selected].mean()) if count else 0.0,
                "accuracy": float(correct[selected].mean()) if count else 0.0,
            }
        )
    target = np.eye(probability.shape[1])[truth]
    return {
        "ece": sum(
            row["count"] / len(truth) * abs(row["confidence"] - row["accuracy"])
            for row in reliability
        ),
        "brier": float(np.square(probability - target).sum(axis=1).mean()),
        "nll": float(-np.log(np.maximum(probability[np.arange(len(truth)), truth], 1e-15)).mean()),
        "reliability": reliability,
    }


def fit_temperature(logits, truth):
    result = minimize_scalar(
        lambda value: calibration_metrics(truth, probabilities(logits, np.exp(value)))["nll"],
        bounds=(np.log(0.05), np.log(20)),
        method="bounded",
        options={"xatol": 1e-7},
    )
    if not result.success:
        raise ValueError("Temperature fit failed")
    return float(np.exp(result.x))
