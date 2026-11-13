import { App, Validations } from 'aws-cdk-lib';
import { AwsSolutionsChecks } from 'cdk-nag';
import { FoundationStack } from './stack';

const app = new App();
const stack = new FoundationStack(app, 'WaferGuardFoundation', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: 'us-east-2' },
  terminationProtection: true,
});
Validations.of(app).addPlugins(new AwsSolutionsChecks(app, { verbose: true }));
Validations.of(stack.node.findChild('AccessLogs')).acknowledge({
  id: 'AwsSolutions-S1',
  reason: 'Dedicated access log sink; logging this bucket to itself causes recursive logs.',
});
app.synth();
