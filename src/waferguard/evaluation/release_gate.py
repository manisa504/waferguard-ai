"""Qualification checks never adjust models or thresholds in response to test results."""


def assess(validation, test, config):
    failures = []
    for split, result in [("validation", validation), ("test", test)]:
        metrics = result["classification"]
        if metrics["macro_f1"] < config["minimum_macro_f1"]:
            failures.append(f"{split}: macro-F1 below declared minimum")
        if metrics["per_class"]["Scratch"]["recall"] < config["minimum_scratch_recall"]:
            failures.append(f"{split}: Scratch recall below declared minimum")
    if test["selective"].get("critical_false_accepts", 0) > 0:
        failures.append("test: critical-class cases were falsely accepted")
    if test["selective"].get("coverage", 0) > 0:
        if test["selective"]["risk"] > config["policy"]["target_accepted_error"]:
            failures.append("test: accepted error exceeds declared target")
        if test["selective"]["wilson_upper_95"] > config["policy"]["maximum_wilson_upper"]:
            failures.append("test: accepted risk bound exceeds declared maximum")
    if test.get("policy_retuned_on_test", True):
        failures.append("test: frozen-policy provenance unavailable")
    return {
        "qualified_for_promotion": not failures,
        "failures": failures,
        "automatic_acceptance_authorized": False,
        "decision": "MANUAL_MODEL_REVIEW_REQUIRED" if not failures else "PROMOTION_BLOCKED",
        "thresholds_retuned": False,
        "scope": "Technical benchmark gate; no certification or physical release authorization",
    }
