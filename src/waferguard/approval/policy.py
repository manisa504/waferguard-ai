"""Fail-closed routing; predictions never grant human authorization."""

import math


def route(prediction, policy, force_review=False):
    reasons = []
    if force_review:
        reasons.append("Manual review requested")
    if not policy.get("enabled") or not policy.get("evaluated"):
        reasons.append("Automatic acceptance is disabled or unevaluated")
    if not prediction.get("model_version") or not prediction.get("calibration_version"):
        reasons.append("Required model/calibration evidence unavailable")
    probability = prediction.get("probabilities", {})
    if (
        not probability
        or any(not math.isfinite(p) or p < 0 for p in probability.values())
        or abs(sum(probability.values()) - 1) > 1e-5
    ):
        reasons.append("Invalid probability evidence")
    confidence = prediction.get("confidence", 0)
    if not math.isfinite(confidence) or confidence < policy.get("threshold", 1.0):
        reasons.append("Confidence below evaluated threshold")
    ordered = sorted(probability.values(), reverse=True)
    if len(ordered) < 2 or ordered[0] - ordered[1] < policy.get("minimum_margin", 1.0):
        reasons.append("Ambiguous class probabilities")
    if prediction.get("ood", True):
        reasons.append("Out-of-distribution or missing input evidence")
    if prediction.get("predicted_class") in policy.get("always_review", ["Scratch", "Near-full"]):
        reasons.append("Designated class requires review")
    return {
        "state": "AWAITING_REVIEW" if reasons else "AUTO_ACCEPTED",
        "reasons": reasons or ["All evaluated simulated classification criteria passed"],
    }
