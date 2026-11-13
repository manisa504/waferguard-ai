#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../infrastructure/cdk"
TASK_AWS_PROFILE="${AWS_PROFILE:-awsnew}"
export AWS_REGION=us-east-2
export AWS_DEFAULT_REGION=us-east-2
# Fail if the stack is absent or identity is unavailable; never search/delete other stacks.
aws sts get-caller-identity --profile "$TASK_AWS_PROFILE" --region us-east-2
aws cloudformation list-stack-resources --stack-name WaferGuardFoundation \
  --profile "$TASK_AWS_PROFILE" --region us-east-2
# This only disables protection on the named stack. All S3 buckets have RETAIN.
aws cloudformation update-termination-protection --no-enable-termination-protection \
  --stack-name WaferGuardFoundation --profile "$TASK_AWS_PROFILE" --region us-east-2
npm run cdk -- destroy WaferGuardFoundation --profile "$TASK_AWS_PROFILE"
echo 'Retained S3 buckets, versions, and CDK bootstrap resources can still incur charges.'
echo 'Use DOC/deployment.md to inventory them; no bucket contents were deleted by this script.'
