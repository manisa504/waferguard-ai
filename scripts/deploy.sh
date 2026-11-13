#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../infrastructure/cdk"
: "${ALERT_EMAIL:?Set ALERT_EMAIL to the budget notification recipient}"
TASK_AWS_PROFILE="${AWS_PROFILE:-awsnew}"
export AWS_REGION=us-east-2
export AWS_DEFAULT_REGION=us-east-2
aws sts get-caller-identity --profile "$TASK_AWS_PROFILE" --region us-east-2
npm run synth
npm run cdk -- diff WaferGuardFoundation --profile "$TASK_AWS_PROFILE"
npm run cdk -- deploy WaferGuardFoundation --profile "$TASK_AWS_PROFILE" \
  --parameters "AlertEmail=$ALERT_EMAIL" \
  --parameters "MonthlyBudgetUsd=${MONTHLY_BUDGET_USD:-25}"
