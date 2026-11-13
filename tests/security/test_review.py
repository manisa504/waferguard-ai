"""Synthetic review records test authorization, races, expiry and replay defenses."""

from concurrent.futures import ThreadPoolExecutor

import pytest

pytest.importorskip("jwt")
from waferguard.approval.authorization import Authorization, Forbidden
from waferguard.approval.store import Conflict, SQLiteStore
from waferguard.approval.workflow import ReviewService, fingerprint, public_case


@pytest.fixture
def system(tmp_path):
    current = {"model": "m1", "calibration": "c1", "policy": "p1"}
    actor = {"sub": "reviewer:fixture", "scope": "demo:fixture", "kind": "demo", "exp": 2000}
    now = [1000]

    def authorize(user):
        if user["sub"] != actor["sub"] or user["exp"] <= now[0]:
            raise Forbidden("Unauthorized")

    store = SQLiteStore(tmp_path / "review.sqlite")
    service = ReviewService(store, lambda: dict(current), authorize, clock=lambda: now[0])
    prediction = {
        "predicted_class": "None",
        "confidence": 0.8,
        "probabilities": {"None": 0.8, "Scratch": 0.2},
        "ood": False,
        "model_version": "m1",
        "calibration_version": "c1",
    }
    policy = {"version": "p1", "enabled": False, "evaluated": False, "threshold": 0.99}
    case = service.create(actor, "real-fixture-id", prediction, policy, "inspection-fixture")
    return service, actor, case, current, now


def decide(system, key="decision-fixture", **kwargs):
    service, actor, case, current, _ = system
    return service.decide(
        actor,
        case["id"],
        case["version"],
        dict(current),
        kwargs.get("decision", "correct"),
        kwargs.get("label", "Scratch"),
        "Synthetic review fixture",
        key,
    )


def test_durable_correction_and_identical_retry_are_idempotent(system):
    result = decide(system)
    assert result["state"] == "CORRECTED"
    assert result["approved_class"] == "Scratch"
    assert decide(system) == result
    assert system[0].store.get(system[1]["scope"], result["id"]) == result
    previous = "0" * 64
    for event in result["audit"]:
        content = {k: v for k, v in event.items() if k != "hash"}
        assert event["previous_hash"] == previous
        assert fingerprint(content) == event["hash"]
        previous = event["hash"]
    assert "_callback" not in public_case(result)


def test_conflicting_replay_and_new_terminal_decision_are_rejected(system):
    decide(system)
    with pytest.raises(Conflict):
        decide(system, label="None")
    with pytest.raises(Conflict):
        decide(system, key="new-decision")


def test_unauthorized_subject_and_cross_namespace_cannot_approve(system):
    service, actor, case, versions, _ = system
    with pytest.raises(Forbidden):
        service.decide(
            dict(actor, sub="intruder"),
            case["id"],
            case["version"],
            versions,
            "approve",
            None,
            "Bad actor",
            "other-key",
        )
    with pytest.raises(KeyError):
        service.get(dict(actor, scope="another-visitor"), case["id"])


def test_stale_release_and_expired_case_fail_closed(system):
    system[3]["model"] = "changed"
    with pytest.raises(Conflict, match="changed"):
        decide(system)
    system[3]["model"] = "m1"
    system[4][0] = 5000
    with pytest.raises(Forbidden):
        decide(system)
    assert system[0].get(system[1], system[2]["id"])["state"] == "EXPIRED"


def test_two_competing_decisions_have_one_winner(system):
    def attempt(index):
        try:
            return decide(system, key=f"decision-{index}")["state"]
        except Conflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        result = list(pool.map(attempt, [1, 2]))
    assert result.count("CORRECTED") == 1
    assert result.count("conflict") == 1


def test_identity_issuance_is_isolated_and_prohibited_in_lambda(monkeypatch):
    monkeypatch.delenv("WAFERGUARD_LOCAL_AUTH", raising=False)
    auth = Authorization(secret="test-secret-long-enough-for-fixtures")
    with pytest.raises(Forbidden):
        auth.issue("local")
    demo = auth.authenticate(auth.issue("demo"))
    assert demo["scope"].startswith("demo:")
    with pytest.raises(Forbidden):
        auth.authenticate("forged-token")
    monkeypatch.setenv("WAFERGUARD_LOCAL_AUTH", "1")
    monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "fixture")
    with pytest.raises(RuntimeError):
        Authorization()
