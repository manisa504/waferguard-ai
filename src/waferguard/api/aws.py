"""Ohio-scoped AWS adapters. Callback tokens never enter public case responses."""

import json
import os
import time

import boto3
from boto3.dynamodb.conditions import Attr, Key
from botocore.config import Config

from waferguard.approval.authorization import Authorization
from waferguard.approval.store import Conflict
from waferguard.approval.workflow import TERMINAL, ReviewService, append_event


class DynamoStore:
    def __init__(self, table):
        self.table = table

    def get(self, scope, identity):
        response = self.table.get_item(
            Key={"pk": scope, "sk": "CASE#" + identity}, ConsistentRead=True
        )
        return json.loads(response["Item"]["payload"]) if "Item" in response else None

    def item(self, case):
        return {
            "pk": case["scope"],
            "sk": "CASE#" + case["id"],
            "version": case["version"],
            "payload": json.dumps(case, allow_nan=False),
            **({"ttl": int(time.time()) + 86400} if case["scope"].startswith("demo:") else {}),
        }

    def create(self, case):
        try:
            self.table.put_item(Item=self.item(case), ConditionExpression=Attr("pk").not_exists())
        except self.table.meta.client.exceptions.ConditionalCheckFailedException as error:
            raise Conflict("Case already exists") from error

    def replace(self, case, expected):
        try:
            self.table.put_item(
                Item=self.item(case), ConditionExpression=Attr("version").eq(expected)
            )
        except self.table.meta.client.exceptions.ConditionalCheckFailedException as error:
            raise Conflict("Case changed; refresh before deciding") from error

    def list(self, scope, limit=100):
        response = self.table.query(
            KeyConditionExpression=Key("pk").eq(scope) & Key("sk").begins_with("CASE#"),
            Limit=limit,
            ConsistentRead=True,
        )
        return [json.loads(item["payload"]) for item in response["Items"]]


class CallbackWorkflow:
    def __init__(self, client, store, auth, versions):
        self.client, self.store, self.auth, self.versions = client, store, auth, versions

    def start(self, scope, identity):
        self.client.start_execution(
            stateMachineArn=os.environ["REVIEW_STATE_MACHINE_ARN"],
            name="case-" + identity,
            input=json.dumps({"scope": scope, "case_id": identity}),
        )

    def resume(self, case, actor):
        if not case.get("_callback"):
            return  # Register callback will drain the durable decision outbox.
        self.auth.revalidate(actor)
        if actor["exp"] <= time.time() or case["expires_at"] <= time.time():
            raise Conflict("Approval expired before workflow resume")
        if self.versions() != case["decision"]["versions"]:
            raise Conflict("Release changed before workflow resume")
        try:
            self.client.send_task_success(
                taskToken=case["_callback"],
                output=json.dumps(
                    {"decision_id": case["decision"]["id"], "version": case["version"]}
                ),
            )
        except (
            self.client.exceptions.TaskDoesNotExist,
            self.client.exceptions.TaskTimedOut,
            self.client.exceptions.InvalidToken,
        ):
            latest = self.store.get(case["scope"], case["id"])
            if latest["state"] not in TERMINAL and latest["state"] != "REVALIDATING":
                raise Conflict("Callback no longer valid") from None
            # A consumed token is safe to replay: finalization is version/id-bound.


def decision_actor(case):
    decision = case["decision"]
    return {
        "sub": decision["actor"],
        "scope": case["scope"],
        "kind": decision["kind"],
        "exp": decision["actor_expires"],
        "cognito:groups": decision["groups"],
    }


def cloud_services(bundle):
    session = boto3.Session(region_name="us-east-2")
    config = Config(
        retries={"mode": "standard", "total_max_attempts": 3}, connect_timeout=3, read_timeout=10
    )
    table = session.resource("dynamodb", config=config).Table(os.environ["WAFERGUARD_TABLE"])
    store = DynamoStore(table)
    secret = session.client("secretsmanager", config=config).get_secret_value(
        SecretId=os.environ["SESSION_SECRET_ARN"]
    )["SecretString"]
    auth = Authorization(secret=secret, cognito=session.client("cognito-idp", config=config))
    workflow = CallbackWorkflow(
        session.client("stepfunctions", config=config), store, auth, bundle.versions
    )
    review = ReviewService(store, bundle.versions, auth.revalidate, workflow)
    return bundle, auth, review


def workflow_event(event):
    from waferguard.api.main import services

    _, _, review = services()
    scope, identity = event["scope"], event["case_id"]
    case = review.store.get(scope, identity)
    if not case:
        raise KeyError(identity)
    if event["action"] == "register":
        for _ in range(5):
            case = review.store.get(scope, identity)
            if case["state"] in TERMINAL:
                return {"terminal": case["state"]}
            previous = case["version"]
            case["_callback"] = event["token"]
            append_event(case, case["state"], "workflow", {"event": "Durable callback registered"})
            try:
                review.store.replace(case, previous)
                break
            except Conflict:
                continue
        else:
            raise Conflict("Unable to register callback concurrently")
        if case["state"] == "REVALIDATING":
            review.workflow.resume(case, decision_actor(case))
        return {"registered": True}
    if event["action"] == "finalize":
        case = review.finalize(
            decision_actor(case), identity, event["decision_id"], event["version"]
        )
        return {"state": case["state"], "case_id": identity}
    if event["action"] == "expire":
        if case["state"] not in TERMINAL:
            previous = case["version"]
            append_event(case, "EXPIRED", "workflow", {"reason": "Durable callback timeout"})
            review.store.replace(case, previous)
        return {"state": case["state"]}
    raise ValueError("Unknown workflow action")
