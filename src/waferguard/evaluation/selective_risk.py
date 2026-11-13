"""Empirical selective risk and explicit finite-sample uncertainty bounds."""

import numpy as np


def wilson_upper(errors, samples, z=1.96):
    if not samples:
        return 1.0
    proportion = errors / samples
    return float(
        (
            proportion
            + z * z / (2 * samples)
            + z * np.sqrt(proportion * (1 - proportion) / samples + z * z / (4 * samples * samples))
        )
        / (1 + z * z / samples)
    )


def selective_result(truth, probability, threshold, classes, policy, ood=None):
    predicted = probability.argmax(1)
    confidence = probability.max(1)
    ordered = np.sort(probability, axis=1)
    eligible = (confidence >= threshold) & (
        ordered[:, -1] - ordered[:, -2] >= policy["minimum_margin"]
    )
    critical = [classes.index(name) for name in policy["always_review"]]
    eligible &= ~np.isin(predicted, critical)
    if ood is not None:
        eligible &= ~ood
    wrong = predicted != truth
    accepted = int(eligible.sum())
    errors = int((eligible & wrong).sum())
    critical_errors = int((eligible & wrong & np.isin(truth, critical)).sum())
    return {
        "threshold": float(threshold),
        "accepted": accepted,
        "errors": errors,
        "coverage": accepted / len(truth),
        "review_rate": 1 - accepted / len(truth),
        "risk": errors / accepted if accepted else None,
        "wilson_upper_95": wilson_upper(errors, accepted),
        "critical_false_accepts": critical_errors,
    }


def select_threshold(truth, probability, classes, policy, ood=None):
    curve = [
        selective_result(truth, probability, threshold, classes, policy, ood)
        for threshold in np.r_[np.arange(0.50, 0.991, 0.01), 0.995, 0.999, 0.9999, 0.99999]
    ]
    feasible = [
        row
        for row in curve
        if row["accepted"] >= policy["minimum_accepted"]
        and row["risk"] <= policy["target_accepted_error"]
        and row["wilson_upper_95"] <= policy["maximum_wilson_upper"]
        and row["critical_false_accepts"] == 0
    ]
    selected = max(feasible, key=lambda row: row["coverage"]) if feasible else None
    return {
        "selected": selected,
        "curve": curve,
        "auto_accept_enabled": selected is not None,
        "limitation": "Validation-selected empirical rule, not a production safety guarantee",
    }
