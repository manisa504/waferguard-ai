"""Spatial die-state features fit independently for each encoded grid."""

import numpy as np

FEATURE_VERSION = "spatial-die-features-v1"
FEATURE_NAMES = (
    ["occupancy", "failure_fraction"]
    + [f"patch_failure_{i}" for i in range(64)]
    + [f"patch_occupancy_{i}" for i in range(64)]
    + [f"radial_failure_{i}" for i in range(8)]
    + [f"angular_failure_{i}" for i in range(12)]
    + [
        "failure_x",
        "failure_y",
        "failure_var_x",
        "failure_var_y",
        "failure_cov_xy",
        "failure_mean_radius",
        "failure_std_radius",
    ]
)
AXIS = (np.arange(64, dtype=np.float64) + 0.5) / 32 - 1
XX, YY = np.meshgrid(AXIS, AXIS)
RADIUS = np.sqrt(XX**2 + YY**2)
RADIAL = np.minimum((RADIUS / np.sqrt(2) * 8).astype(int), 7)
ANGULAR = np.minimum(((np.arctan2(YY, XX) + np.pi) / (2 * np.pi) * 12).astype(int), 11)


def extract_features(states: np.ndarray) -> np.ndarray:
    if states.shape != (64, 64) or not np.isin(states, [0, 1, 2]).all():
        raise ValueError("Expected a categorical 64x64 grid")
    valid, failed = states > 0, states == 2
    count = int(failed.sum())
    patch_valid = valid.reshape(8, 8, 8, 8).sum(axis=(1, 3)).ravel()
    patch_failed = failed.reshape(8, 8, 8, 8).sum(axis=(1, 3)).ravel()
    values = [valid.mean(), count / max(int(valid.sum()), 1)]
    values.extend(patch_failed / np.maximum(patch_valid, 1))
    values.extend(patch_valid / 64)
    for bins, size in [(RADIAL, 8), (ANGULAR, 12)]:
        denominator = np.bincount(bins[valid], minlength=size)
        numerator = np.bincount(bins[failed], minlength=size)
        values.extend(numerator / np.maximum(denominator, 1))
    if count:
        x, y, radius = XX[failed], YY[failed], RADIUS[failed]
        values.extend(
            [
                x.mean(),
                y.mean(),
                x.var(),
                y.var(),
                ((x - x.mean()) * (y - y.mean())).mean(),
                radius.mean(),
                radius.std(),
            ]
        )
    else:
        values.extend([0.0] * 7)
    result = np.asarray(values, dtype=np.float32)
    if result.shape != (len(FEATURE_NAMES),) or not np.isfinite(result).all():
        raise ValueError("Invalid engineered feature vector")
    return result
