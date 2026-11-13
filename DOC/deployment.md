# Deployment and cleanup

Status: **not deployed**. All application AWS services are future work. The foundation
stack only authors three private S3 buckets, bucket policies and AWS Budget warnings.
Default and deployed workload Region must be `us-east-2`; profile `awsnew`.

## Review prerequisites

The outline requires gate review before proceeding. Check identity and AWS Projects
home Region before diagnosing SCP denials; Ohio is the project default, and a regional
SCP denial does not establish a general service restriction. No cloud permissions have
been tested for this project. Do not change Region to evade account controls.

Review `npm audit`, `npm test`, strict synth and the CDK diff. Supply the owner's budget
recipient email. The suggested USD 25 monthly warning threshold is configurable and is
not a predicted bill. The budget is **account-wide**, including unrelated projects; it
avoids tag-activation gaps. Actual 80% and forecast 100% notifications are delayed
warnings, not hard caps. Confirm receipt and the deployed budget after creation.

## Local synthesis

```bash
./scripts/setup.sh
make check
make synth
```

Synthesis works without AWS credentials or recipient email because email is a required
CloudFormation parameter. `cdk-nag` v3 validation runs through CDK `Validations`; its
report lives in `infrastructure/cdk/cdk.out/validation-report.json`. S3 access-log delivery
uses bucket policy rather than ACLs. The log sink's S1 finding is acknowledged only on
that bucket because recursively logging the sink is inappropriate.

## Deployment after review

Authenticate profile `awsnew` using your established AWS login method, and inspect:

```bash
aws sts get-caller-identity --profile awsnew --region us-east-2
```

If bootstrapping is required, use a reviewed least-privilege CloudFormation execution
policy rather than CDK's unrestricted default. Substitute the actual account and
approved policy ARN; no bootstrap or IAM resources have been created in this change:

```bash
cd infrastructure/cdk
npm run cdk -- bootstrap aws://ACCOUNT_ID/us-east-2 --profile awsnew \
  --cloudformation-execution-policies APPROVED_EXECUTION_POLICY_ARN
cd ../..
ALERT_EMAIL=owner@example.com MONTHLY_BUDGET_USD=25 ./scripts/deploy.sh
```

The script runs strict synthesis, diff and standard CloudFormation deployment. It does
not disable CDK's IAM confirmation. The foundation requires S3, Budgets and applicable
CloudFormation permissions; no application or GitHub OIDC deployment role is created.
Future CI deployment must use repository/branch-scoped OIDC, short-lived credentials
and a protected GitHub environment after its dedicated IAM review.

Keep a deployment evidence file with actual stack outputs, Region, revision, template
hash, budget configuration and verification commands. Verify storage public access,
versioning, encryption and TLS behavior in AWS before claiming operational controls.
Raw data is not uploaded automatically. Model serving, CloudWatch runtime alarms,
CloudTrail configuration and promotion/rollback must be implemented in later gates.

## Teardown and retained resources

```bash
./scripts/teardown.sh
```

This lists the named stack's physical resources, disables its termination protection
and invokes CDK destroy with the normal interactive confirmation. Capture the printed
bucket names before deletion. All three buckets use **RETAIN**, so originals/artifacts
and their versions survive. The budget is removed with the stack; retained storage can
still incur costs after its warnings are removed. Maintain an account-level warning.

To completely remove retained storage after reviewing backup and provenance needs:

1. Inventory the exact retained bucket names from the stack resource listing.
2. List all object versions and delete markers using paginated `s3api list-object-versions`
   with `--profile awsnew --region us-east-2`. Review the inventory before deleting anything.
3. Delete every selected version and delete marker explicitly; `aws s3 rm --recursive`
   alone is insufficient for versioned storage. Then delete the exact empty buckets.
4. Inventory CDK bootstrap resources separately. They may be shared by other projects;
   never delete them as part of this stack's automatic cleanup.
5. Verify no stacks, buckets, retained data or project workloads remain, then inspect
   actual billing. Record any retained resources and costs instead of claiming zero cost.

No destructive bucket purge is included. Cloud teardown has not been run or tested;
there is currently no WaferGuard deployment to tear down. Rollback for this foundation
uses the prior reviewed template. Model registry rollback is future Gate 8 scope.
