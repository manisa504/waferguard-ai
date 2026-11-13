"""Categorical wafer transforms; no learned statistics and no interpolated die states."""

import numpy as np

from waferguard.data.validate import map_fingerprint

PREPROCESS_VERSION = "categorical-nearest-onehot-v1"


def orbit_fingerprint(wafer: np.ndarray) -> str:
    """Canonical identity across 90-degree rotations and reflections, including shape."""
    map_fingerprint(wafer)  # Validate before any cast; never round invalid die states.
    states = np.asarray(wafer, dtype=np.uint8)
    return min(
        map_fingerprint(np.rot90(view, turns))
        for view in (states, np.fliplr(states))
        for turns in range(4)
    )


def encode_wafer(wafer: np.ndarray, size: int = 64) -> np.ndarray:
    """Fit aspect ratio in a square using categorical nearest-neighbor sampling.

    Channels are outside/no-die, passing-die, failing-die. Padding is outside/no-die.
    Resampling can omit small structures; original grids are always retained separately.
    """
    map_fingerprint(wafer)
    if isinstance(size, bool) or not isinstance(size, int) or size < 2:
        raise ValueError("Output size must be an integer >= 2")
    height, width = wafer.shape
    scale = size / max(height, width)
    out_h, out_w = max(1, round(height * scale)), max(1, round(width * scale))
    rows = np.minimum(((np.arange(out_h) + 0.5) * height / out_h).astype(int), height - 1)
    cols = np.minimum(((np.arange(out_w) + 0.5) * width / out_w).astype(int), width - 1)
    canvas = np.zeros((size, size), dtype=np.uint8)
    top, left = (size - out_h) // 2, (size - out_w) // 2
    canvas[top : top + out_h, left : left + out_w] = wafer[np.ix_(rows, cols)]
    return np.eye(3, dtype=np.float32)[canvas].transpose(2, 0, 1).copy()
