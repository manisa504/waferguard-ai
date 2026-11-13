import { test } from 'node:test';
import assert from 'node:assert/strict';
import { App } from 'aws-cdk-lib';
import { Match, Template } from 'aws-cdk-lib/assertions';
import { FoundationStack } from '../stack';

test('private retained versioned storage, TLS and active/forecast budget warnings', () => {
  const stack = new FoundationStack(new App(), 'Test', { env: { region: 'us-east-2' } });
  const template = Template.fromStack(stack);
  template.resourceCountIs('AWS::S3::Bucket', 3);
  template.allResourcesProperties('AWS::S3::Bucket', {
    PublicAccessBlockConfiguration: { BlockPublicAcls: true, BlockPublicPolicy: true,
      IgnorePublicAcls: true, RestrictPublicBuckets: true },
    VersioningConfiguration: { Status: 'Enabled' },
    BucketEncryption: { ServerSideEncryptionConfiguration: [
      { ServerSideEncryptionByDefault: { SSEAlgorithm: 'AES256' } },
    ] },
  });
  template.allResources('AWS::S3::Bucket', { DeletionPolicy: 'Retain', UpdateReplacePolicy: 'Retain' });
  template.resourceCountIs('AWS::S3::BucketPolicy', 3);
  template.allResourcesProperties('AWS::S3::BucketPolicy', {
    PolicyDocument: { Statement: Match.arrayWith([Match.objectLike({
      Effect: 'Deny', Condition: { Bool: { 'aws:SecureTransport': 'false' } },
    })]) },
  });
  template.hasResourceProperties('AWS::Budgets::Budget', {
    Budget: { BudgetType: 'COST', TimeUnit: 'MONTHLY' },
    NotificationsWithSubscribers: Match.arrayWith([
      Match.objectLike({ Notification: Match.objectLike({ NotificationType: 'ACTUAL', Threshold: 80 }) }),
      Match.objectLike({ Notification: Match.objectLike({ NotificationType: 'FORECASTED', Threshold: 100 }) }),
    ]),
  });
  // Foundation must not provision compute before data verification.
  for (const kind of ['AWS::EC2::Instance', 'AWS::SageMaker::Endpoint', 'AWS::Lambda::Function']) {
    template.resourceCountIs(kind, 0);
  }
  assert.equal(stack.region, 'us-east-2');
});

test('security checker validates the foundation and detects an insecure control bucket', async () => {
  const { Validations, aws_s3: s3, Stack } = await import('aws-cdk-lib');
  const { AwsSolutionsChecks } = await import('cdk-nag');
  const app = new App({ autoSynth: false });
  const stack = new FoundationStack(app, 'Secure', { env: { region: 'us-east-2' } });
  Validations.of(stack.node.findChild('AccessLogs')).acknowledge({
    id: 'AwsSolutions-S1', reason: 'Dedicated logging sink must not recursively log itself.',
  });
  Template.fromStack(stack);
  const checks = new AwsSolutionsChecks(app);
  assert.deepEqual(checks.validateScope(app).violations, []);
  const unsafe = new Stack(app, 'UnsafeControl');
  new s3.Bucket(unsafe, 'NoTlsPolicy');
  const report = checks.validateScope(app);
  assert.equal(report.success, false);
  assert.ok(report.violations.some(v => v.ruleName === 'AwsSolutions-S10'));
});
