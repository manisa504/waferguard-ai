"""Train-only reference classifiers."""

import numpy as np
from sklearn.ensemble import RandomForestClassifier


def majority_class(labels: np.ndarray, classes: int) -> int:
    if labels.ndim != 1 or not len(labels) or (labels < 0).any() or (labels >= classes).any():
        raise ValueError("Invalid training labels")
    return int(np.bincount(labels, minlength=classes).argmax())


def make_forest(config: dict, seed: int, threads: int) -> RandomForestClassifier:
    return RandomForestClassifier(**config, random_state=seed, n_jobs=threads, class_weight=None)
