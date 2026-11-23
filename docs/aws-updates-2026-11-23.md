# AWS documentation updates - 2026-11-23

Total updates: 18

## api-gateway

- [API Portal](https://docs.aws.amazon.com/apigateway/latest/developerguide/history.html) — published 2026-11-23T19:00:00+00:00
  
  API Portal discovers the APIs running behind API Gateway REST APIs, Application Load Balancer, and CloudFront across your AWS account or your             organization in AWS Organizations, evaluates their security posture, and lets you publish documentation portals for them.             For more information, see <a href="https://docs.aws.amazon.com/apigateway/latest/developerguide/apiportal.html">API Portal</a>.


## bedrock

- [Web Search on Amazon Bedrock expands language support and country-aware search](https://aws.amazon.com/about-aws/whats-new/2026/11/web-search-amazon-bedrock/) — published 2026-11-21T00:17:00+00:00
  
  <p>Web Search on Amazon Bedrock, the tool that grounds AI agents and applications in cited, current web information, now supports five new languages, plus non-US English, on Amazon Bedrock AgentCore and Amazon Bedrock: Spanish, French, German, Italian, and Japanese.&nbsp; Agents serving users in these languages get results that draw on local-language sources.</p>  <p>We are also introducing a new optional country field that biases results toward sources from a specific country - just pass an ISO


## cloudformation

- [AWS CloudFormation Service-Managed StackSets adds custom execution roles with nested stacks support](https://aws.amazon.com/about-aws/whats-new/2026/11/stacksets-custom-execution-roles/) — published 2026-11-20T17:45:00+00:00
  
  <p><a href="https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stacksets-concepts.html" rel="noopener noreferrer" target="_blank">AWS CloudFormation StackSets</a> now supports custom execution roles for service-managed stack sets, which enables you to scope the permissions StackSets uses in each target AWS account. StackSets deploys the same infrastructure, such as networking and security settings, across thousands of accounts and Regions in one operation. With a custom execution rol

- [AWS CloudFormation increases the default stacks per account quota to 300,000](https://aws.amazon.com/about-aws/whats-new/2026/11/cloudformation-stacks-per-account-quota/) — published 2026-11-20T12:35:00+00:00
  
  <p>AWS CloudFormation now supports up to 300,000 stacks in each AWS account and Region by default (previously 2,000), which enables you to add stacks as your workloads grow without requesting a quota increase. CloudFormation manages related AWS resources as a stack that you create, update, and delete as one unit. Teams that deploy a separate stack for each customer, environment, or developer can now scale those patterns within a single account.</p>  <p>A higher default quota allows you to keep g


## cloudwatch

- [Increased maximum PromQL query time range](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/DocumentHistory.html) — published 2026-11-19T19:00:00+00:00
  
  CloudWatch increased the maximum time range for a PromQL query from 7 days to 30 days for           all accounts. The limit description now explains how the time range is measured. For           more information, see <a href="https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-PromQL.html#CloudWatch-PromQL-Limits">PromQL limits and restrictions</a>.

- [CloudWatchFullAccessV2 policy update](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/DocumentHistory.html) — published 2026-11-18T19:00:00+00:00
  
  CloudWatch updated the <code class="code">kms:DescribeKey</code> permission in the <a href="https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/managed-policies-cloudwatch.html#managed-policies-cloudwatch-CloudWatchFullAccessV2">CloudWatchFullAccessV2</a> managed policy so that you can also use it for requests           that CloudWatch makes on your behalf, in addition to requests from CloudWatch Logs. The permission still           applies only to keys in your own account. For more

- [OTel Container Insights changes in add-on version 7.0.0](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/DocumentHistory.html) — published 2026-11-12T19:00:00+00:00
  
  Version 7.0.0 of the Amazon CloudWatch Observability Amazon EKS add-on and Helm chart removes           duplicate series, deprecated attributes, and some generated labels from OTel Container           Insights metrics. For more information, see <a href="https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/container-insights-eks-otel.html#container-insights-eks-otel-upgrade-v7">Upgrading OTel Container Insights to version 7.0.0</a>.


## cognito

- [Amazon Cognito extends multi-Region replication to additional AWS Regions](https://aws.amazon.com/about-aws/whats-new/2026/11/cognito-mrr-opt-in-regions/) — published 2026-11-20T22:00:00+00:00
  
  <p><a href="https://aws.amazon.com/cognito/">Amazon Cognito</a> multi-Region replication (MRR) now supports additional AWS Regions, extending the resilience benefits of MRR to more workloads. Amazon Cognito helps you implement secure sign-in and access control for users, AI agents, and microservices in minutes, and MRR lets you synchronize user and machine identity data, including credentials, user pool configurations, and federation setups, to a secondary user pool in a standby Region you desig


## dynamodb

- [Auto scaling quota guidance](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DocumentHistory.html) — published 2026-11-17T19:00:00+00:00
  
  Added information about how throughput quotas affect DynamoDB auto scaling, so you can set table and index capacity within your per-table and account-level quotas. For more information, see <a href="https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/AutoScaling.html">Managing throughput capacity automatically with DynamoDB auto scaling</a>.

- [Secondary index quotas](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DocumentHistory.html) — published 2026-11-11T19:00:00+00:00
  
  Added information about secondary index quotas, including the maximum base table size for creating a global secondary index without additional allowlisting. For more information, see <a href="https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ServiceQuotas.html">Quotas in Amazon DynamoDB</a>.

- [DynamoDB bulk put items is now available](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DocumentHistory.html) — published 2026-11-05T19:00:00+00:00
  
  You can now use bulk put items to load data from Amazon S3 into an existing DynamoDB                     table without consuming read or write capacity on that table. Bulk put items                     offers two performance tiers, Standard and Accelerated, to match your workload                     requirements. For more information, see <a href="https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/BulkPutItems.HowItWorks.html">DynamoDB bulk put items: how it works</a>.

- [Bulk put items CloudTrail events](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DocumentHistory.html) — published 2026-11-05T19:00:00+00:00
  
  Added information about CloudTrail logging for bulk put items operations, which                     records the <code class="code">StartBulkPutItems</code> management event and                         <code class="code">BulkPutItems</code> data service events. For more information, see                         <a href="https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/BulkPutItems.Considerations.html">Bulk put items considerations, quotas, and permissions</a>.

- [Increased vector index quota](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DocumentHistory.html) — published 2026-10-26T19:00:00+00:00
  
  Updated documentation for the per-table vector index quota, which you can now                     increase to a maximum of 20 vector indexes per table. For more information, see                         <a href="https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ServiceQuotas.html">Quotas in                         Amazon DynamoDB</a>, <a href="https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ddb-strands-storage.html">Using                         DynamoDB as a stora


## ec2

- [T9g burstable performance instances](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/DocumentHistory.html) — published 2026-11-20T19:00:00+00:00
  
  Added documentation for T9g burstable performance instances, the latest-generation AWS Graviton5-based burstable instances. For more information, see <a href="https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/burstable-performance-instances.html">Burstable performance instances</a>, <a href="https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/burstable-credits-baseline-concepts.html">Key concepts for burstable performance instances</a>, <a href="https://docs.aws.amazon.com/AWSEC2/latest/UserGu

- [Capacity Manager supportability checks](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/DocumentHistory.html) — published 2026-10-28T19:00:00+00:00
  
  Updated documentation for Amazon EC2 Capacity Manager real-time supportability 					checks, fulfillment metrics, and capacity check quotas, including the 						<code class="code">--instance-requirements-with-metadata</code> attribute input. For more 					information, see <a href="https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/capacity-manager.html">EC2 Capacity 						Manager</a>.


## eventbridge

- [AWS Lambda now publishes Event Function state change events to Amazon EventBridge](https://aws.amazon.com/about-aws/whats-new/2026/11/aws-lambda-function-state-events/) — published 2026-11-20T22:40:00+00:00
  
  <p><a href="https://aws.amazon.com/lambda/" rel="noopener noreferrer" target="_blank">AWS Lambda</a>&nbsp;now publishes Event Function state change events to <a href="https://aws.amazon.com/eventbridge/" rel="noopener noreferrer" target="_blank">Amazon EventBridge</a>. Lambda emits an event each time an Event Function version changes state because of a customer action, such as creating, updating, publishing, or deleting a function. These events help platform and DevOps teams to trigger automatio


## lambda

- [Updated durable functions read quotas](https://docs.aws.amazon.com/lambda/latest/dg/lambda-releases.html) — published 2026-11-04T19:00:00+00:00
  
  Updated documentation for the read API request quotas for Lambda durable functions. For more information, see <a href="https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html">Lambda quotas</a>.


## rds

- [Amazon RDS reports snapshot storage charges at per-snapshot granularity](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/WhatsNew.html) — published 2026-11-01T19:00:00+00:00
  
  Amazon RDS now attributes snapshot storage charges to each snapshot individually 					in AWS Cost Explorer and your AWS Cost and Usage Report. The 					<code class="code">ResourceId</code> field shows the Amazon RDS snapshot ARN, or the Amazon RDS cluster 					snapshot ARN for Multi-AZ DB cluster snapshots. Your pricing and overall charges 					are unchanged. To group snapshot charges by instance, apply cost allocation tags to 					your snapshots. For more information, see <a href="https://docs.

