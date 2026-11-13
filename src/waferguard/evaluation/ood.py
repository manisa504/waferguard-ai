"""Training-only standardized feature-distance guard; no universal OOD claim."""

import numpy as np


def fit_guard(features):
    mean = np.asarray(features).mean(0)
    scale = np.maximum(np.asarray(features).std(0), 0.01)
    distance = np.sqrt(np.square((features - mean) / scale).mean(1))
    return {
        "mean": mean.tolist(),
        "scale": scale.tolist(),
        "threshold": float(np.quantile(distance, 0.995)),
        "quantile": 0.995,
        "fit_split": "train",
        "method": "standardized_feature_rms_v1",
    }


def score(features, guard):
    return np.sqrt(np.square((np.asarray(features) - guard["mean"]) / guard["scale"]).mean(axis=-1))
