"""Durable, version-bound review decisions and idempotent resumption."""

import hashlib
import json
import time
import uuid
from datetime import UTC, datetime

from waferguard.approval.policy import route
from waferguard.approval.store import Conflict

TERMINAL = {"AUTO_ACCEPTED", "ACCEPTED", "CORRECTED", "CLOSED", "EXPIRED", "FAILED_SAFE"}


def fingerprint(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def append_event(case, state, actor, details):
    previous = case["audit"][-1]["hash"] if case["audit"] else "0" * 64
    event = {
        "sequence": len(case["audit"]),
        "timestamp": datetime.now(UTC).isoformat(),
        "state": state,
        "actor": actor,
        "details": details,
        "previous_hash": previous,
    }
    event["hash"] = fingerprint(event)
    case["audit"].append(event)
    case["state"] = state
    case["version"] += 1


def public_case(case):
    return {key: value for key, value in case.items() if not key.startswith("_")}


class ReviewService:
    def __init__(self, store, release, revalidate, workflow=None, clock=time.time):
        self.store, self.release, self.revalidate = store, release, revalidate
        self.workflow, self.clock = workflow, clock

    def create(self, actor, sample_id, prediction, policy, key, force_review=False):
        scope = actor["scope"]
        identity = fingerprint([scope, key])[:32]
        request = fingerprint([sample_id, force_review])
        existing = self.store.get(scope, identity)
        if existing:
            if existing["_request"] != request:
                raise Conflict("Idempotency key reused for different evidence")
            return existing
        case = {
            "id": identity,
            "scope": scope,
            "sample_id": sample_id,
            "version": 0,
            "state": "DETECTED",
            "created_at": datetime.now(UTC).isoformat(),
            "expires_at": int(self.clock()) + 3600,
            "prediction": prediction,
            "policy_version": policy["version"],
            "audit": [],
            "decision": None,
            "_request": request,
            "_callback": None,
            "_outbox": None,
        }
        append_event(case, "DETECTED", actor["sub"], {"sample_id": sample_id})
        append_event(case, "ANALYZING", "system", {"evidence_hash": fingerprint(prediction)})
        decision = route(prediction, policy, force_review)
        case["routing_reasons"] = decision["reasons"]
        append_event(
            case,
            decision["state"],
            "policy",
            {
                "model_version": prediction["model_version"],
                "calibration_version": prediction["calibration_version"],
                "policy_version": policy["version"],
                "reasons": decision["reasons"],
            },
        )
        try:
            self.store.create(case)
        except Conflict:
            existing = self.store.get(scope, identity)
            if not existing or existing["_request"] != request:
                raise
            return existing
        if case["state"] == "AWAITING_REVIEW" and self.workflow:
            self.workflow.start(scope, identity)
        return case

    def get(self, actor, identity):
        case = self.store.get(actor["scope"], identity)
        if not case:
            raise KeyError(identity)
        if case["state"] not in TERMINAL and self.clock() >= case["expires_at"]:
            previous = case["version"]
            append_event(case, "EXPIRED", "system", {"reason": "Review time expired"})
            self.store.replace(case, previous)
        return case

    def decide(self, actor, identity, expected, versions, decision, label, note, key):
        self.revalidate(actor)
        case = self.get(actor, identity)
        payload = {
            "actor": actor["sub"],
            "expected": expected,
            "versions": versions,
            "decision": decision,
            "label": label,
            "note": note,
            "key": key,
        }
        digest = fingerprint(payload)
        if case["decision"] and case["decision"]["key"] == key:
            if case["decision"]["fingerprint"] != digest:
                raise Conflict("Replayed key contains a different decision")
            if case["state"] == "REVALIDATING" and self.workflow:
                self.workflow.resume(case, actor)
                return self.store.get(actor["scope"], identity)
            return case
        if case["state"] != "AWAITING_REVIEW" or case["version"] != expected:
            raise Conflict("Review is terminal, stale or already resuming")
        current = self.release()
        pinned = {
            "model": case["prediction"]["model_version"],
            "calibration": case["prediction"]["calibration_version"],
            "policy": case["policy_version"],
        }
        if versions != pinned or current != pinned:
            raise Conflict("Model, calibration or policy changed; inspect again")
        if decision not in {"approve", "correct", "reject"}:
            raise ValueError("Invalid decision")
        if decision == "correct" and label not in case["prediction"]["probabilities"]:
            raise ValueError("Correction must use a known class")
        if decision != "correct" and label is not None:
            raise ValueError("Only corrections carry a new label")
        case["decision"] = {
            **payload,
            "fingerprint": digest,
            "id": uuid.uuid4().hex,
            "actor_expires": actor["exp"],
            "kind": actor["kind"],
            "groups": actor.get("cognito:groups", []),
            "simulated": actor["kind"] == "demo",
        }
        append_event(
            case,
            "REVALIDATING",
            actor["sub"],
            {
                "decision": decision,
                "corrected_label": label,
                "note": note,
                "model_version": pinned["model"],
                "calibration_version": pinned["calibration"],
                "policy_version": pinned["policy"],
            },
        )
        case["_outbox"] = {
            "state": "pending",
            "decision_id": case["decision"]["id"],
            "version": case["version"],
        }
        self.store.replace(case, expected)
        if self.workflow:
            self.workflow.resume(case, actor)
            return self.store.get(actor["scope"], identity)
        return self.finalize(actor, identity, case["decision"]["id"], case["version"])

    def finalize(self, actor, identity, decision_id, expected):
        self.revalidate(actor)
        case = self.get(actor, identity)
        if case["state"] in {"ACCEPTED", "CORRECTED", "CLOSED"}:
            if case["decision"]["id"] == decision_id:
                return case
            raise Conflict("Different terminal decision")
        if case["state"] != "REVALIDATING" or case["version"] != expected:
            raise Conflict("Stale workflow resume")
        if (
            case["decision"]["id"] != decision_id
            or case["decision"]["actor"] != actor["sub"]
            or self.clock() >= case["decision"]["actor_expires"]
            or self.release() != case["decision"]["versions"]
        ):
            raise Conflict("Approval expired or evidence changed before resumption")
        decision = case["decision"]["decision"]
        state = {"approve": "ACCEPTED", "correct": "CORRECTED", "reject": "CLOSED"}[decision]
        case["approved_class"] = (
            case["decision"]["label"]
            if decision == "correct"
            else case["prediction"]["predicted_class"]
            if decision == "approve"
            else None
        )
        case["_outbox"]["state"] = "completed"
        append_event(
            case,
            state,
            actor["sub"],
            {"decision_id": decision_id, "simulated_quality_disposition": True},
        )
        self.store.replace(case, expected)
        return case
