"""Internal Step Functions tasks; no public HTTP entry point."""

from waferguard.api.aws import workflow_event


def handler(event, context):
    return workflow_event(event)
