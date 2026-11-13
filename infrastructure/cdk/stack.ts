import {
  CfnOutput, CfnParameter, Duration, RemovalPolicy, Stack, StackProps, Tags,
  aws_budgets as budgets, aws_s3 as s3,
} from 'aws-cdk-lib';
import { Construct } from 'constructs';

/** Only foundation resources. All application services in the diagram are future work. */
export class FoundationStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);
    this.node.setContext('@aws-cdk/aws-s3:serverAccessLogsUseBucketPolicy', true);
    Tags.of(this).add('Project', 'WaferGuard');
    Tags.of(this).add('Owner', 'WaferGuard');
    Tags.of(this).add('Environment', 'portfolio');
    const alertEmail = new CfnParameter(this, 'AlertEmail', {
      type: 'String', description: 'Owner email for actual and forecast budget notifications',
      allowedPattern: '[^\\s@]+@[^\\s@]+\\.[^\\s@]+',
    });
    const budgetUsd = new CfnParameter(this, 'MonthlyBudgetUsd', {
      type: 'Number', minValue: 1, maxValue: 1000, default: 25,
      description: 'Account-wide monthly warning threshold; not a spending cap or cost forecast',
    });
    const logs = new s3.Bucket(this, 'AccessLogs', {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
      enforceSSL: true, versioned: true, removalPolicy: RemovalPolicy.RETAIN,
      lifecycleRules: [{ expiration: Duration.days(90),
        noncurrentVersionExpiration: Duration.days(90),
        abortIncompleteMultipartUploadAfter: Duration.days(7) }],
    });
    for (const name of ['RawData', 'Artifacts']) {
      const bucket = new s3.Bucket(this, name, {
        blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
        encryption: s3.BucketEncryption.S3_MANAGED,
        objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
        enforceSSL: true, versioned: true, removalPolicy: RemovalPolicy.RETAIN,
        serverAccessLogsBucket: logs, serverAccessLogsPrefix: `${name}/`,
        lifecycleRules: [{ abortIncompleteMultipartUploadAfter: Duration.days(7) }],
      });
      new CfnOutput(this, `${name}BucketName`, { value: bucket.bucketName });
    }
    new CfnOutput(this, 'AccessLogsBucketName', { value: logs.bucketName });
    new budgets.CfnBudget(this, 'MonthlyBudget', {
      budget: { budgetType: 'COST', timeUnit: 'MONTHLY',
        budgetLimit: { amount: budgetUsd.valueAsNumber, unit: 'USD' } },
      notificationsWithSubscribers: [
        { type: 'ACTUAL', threshold: 80 }, { type: 'FORECASTED', threshold: 100 },
      ].map(({ type, threshold }) => ({
        notification: { notificationType: type, comparisonOperator: 'GREATER_THAN',
          threshold, thresholdType: 'PERCENTAGE' },
        subscribers: [{ subscriptionType: 'EMAIL', address: alertEmail.valueAsString }],
      })),
    });
  }
}
