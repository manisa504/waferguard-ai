"""Synthetic contract fixtures only; no classifier skill is measured here."""

import numpy as np
import pytest

from waferguard.data.preprocess import encode_wafer, orbit_fingerprint
from waferguard.data.validate import map_fingerprint


def test_orbit_hash_catches_transformed_copies_without_merging_different_patterns():
    wafer = np.array([[0, 1, 0], [1, 2, 2]])
    identity = orbit_fingerprint(wafer)
    for view in (wafer, np.fliplr(wafer)):
        for turns in range(4):
            assert orbit_fingerprint(np.rot90(view, turns)) == identity
    other = wafer.copy()
    other[1, 1] = 1
    assert orbit_fingerprint(other) != identity
    assert map_fingerprint(wafer) != map_fingerprint(np.rot90(wafer))


def test_one_hot_padding_is_outside_and_never_interpolates_states():
    wafer = np.array([[1, 2, 1, 2], [0, 1, 2, 0]])
    before = wafer.copy()
    result = encode_wafer(wafer, 8)
    assert result.shape == (3, 8, 8)
    assert result.dtype == np.float32
    assert set(np.unique(result)) == {0, 1}
    np.testing.assert_array_equal(result.sum(axis=0), np.ones((8, 8)))
    assert result[0, :2, :].all() and result[0, 6:, :].all()
    np.testing.assert_array_equal(wafer, before)
    assert result[2].sum() > 0


def test_same_size_encoding_preserves_all_die_states():
    wafer = np.array([[0, 1, 2], [2, 1, 0], [1, 2, 1]])
    np.testing.assert_array_equal(encode_wafer(wafer, 3).argmax(axis=0), wafer)


@pytest.mark.parametrize("wafer", [np.array([[0.2]]), np.array([[3]]), np.array([[np.nan]])])
def test_preprocessing_rejects_invalid_states_before_cast(wafer):
    with pytest.raises(ValueError):
        encode_wafer(wafer)
    with pytest.raises(ValueError):
        orbit_fingerprint(wafer)


@pytest.mark.parametrize("size", [0, 1, True, 4.5])
def test_preprocessing_rejects_invalid_size(size):
    with pytest.raises(ValueError):
        encode_wafer(np.ones((2, 3)), size)
