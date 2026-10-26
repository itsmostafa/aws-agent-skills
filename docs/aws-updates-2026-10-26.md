# AWS documentation updates - 2026-10-26

Total updates: 11

## bedrock

- [Web Search on Amazon Bedrock now supports domain filtering and user location controls](https://aws.amazon.com/about-aws/whats-new/2026/10/bedrock-web-search-domain-user-location/) — published 2026-10-23T21:04:00+00:00
  
  <p>Web Search on&nbsp;Amazon Bedrock now supports two new controls that give you more precision over the results that ground a model's response: domain filtering and user location. Both are configured directly on the web_search tool in your existing OpenAI Responses API request.</p>  <p>With domain filtering, you can restrict Web Search results to a set of domains you choose. Using the filters parameter, you specify up to 100 allowed_domains to limit results to trusted sources, or up to 100 bloc

- [Amazon Bedrock Guardrails now supports Standard tier for contextual grounding checks](https://aws.amazon.com/about-aws/whats-new/2026/10/bedrock-guardrails-grounding-standard/) — published 2026-10-20T08:00:00+00:00
  
  <p>Amazon Bedrock Guardrails now offers a Standard tier for contextual grounding checks, which detect and filter hallucinations by checking whether a model response is grounded in your reference source and relevant to the user's query. The Standard tier is more robust than the Classic tier. It supports responses that include reasoning or conversational content, scores differently worded responses with the same meaning more consistently, and provides more comprehensive language support, matching

- [Amazon Bedrock Advanced Prompt Optimization now supports prompt shortening](https://aws.amazon.com/about-aws/whats-new/2026/10/bedrock-prompt-optimization-shortening/) — published 2026-10-20T08:00:00+00:00
  
  <p>Amazon Bedrock Advanced Prompt Optimization now supports prompt shortening, an optional setting that reduces the length of your prompt while maintaining or improving your evaluation scores. Advanced Prompt Optimization optimizes prompts for any model on Amazon Bedrock against your own evaluation criteria. Until now, optimization focused on quality alone. Optimized prompts were often longer than the original. Longer prompts raise input token costs and can increase time to first token, which ma

- [Grok 4.7 is now available on Amazon Bedrock in AWS GovCloud (US)](https://aws.amazon.com/about-aws/whats-new/2026/10/amazon-bedrock-grok-4-7-govcloud/) — published 2026-10-19T13:00:00+00:00
  
  <p>Amazon Bedrock now supports SpaceXAI Grok 4.7, a frontier model built for coding, agentic tasks, and knowledge work in AWS GovCloud (US).</p>  <p>Grok 4.7 builds on Grok 4.6 with better mixed-document handling, more dependable repo-scale coding with planning and error recovery, and enhanced browser-use agents for form fills and portal navigation. &nbsp;</p>  <p>Get started with Grok 4.7 in the<a href="https://console.amazonaws-us-gov.com/bedrock/"> Amazon Bedrock console</a> or programmatical

- [Web Search on Amazon Bedrock AgentCore expands to AWS GovCloud and 3 Regions](https://aws.amazon.com/about-aws/whats-new/2026/10/amazon-bedrock-agentcore/) — published 2026-10-15T20:40:00+00:00
  
  <p>Web Search on Amazon Bedrock AgentCore is now available in four additional AWS Regions: US East (Ohio), US West (Oregon), Asia Pacific (Sydney), and AWS GovCloud (US-West). Web Search is a fully managed tool that provides AI agents with current grounding from the web, enabling more accurate and up-to-date responses for tasks such as research, summarization, and question answering.</p>  <p>With this expansion, customers can build agents that retrieve web information closer to their application


## cloudwatch

- [CloudWatchFullAccessV2 policy update](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/DocumentHistory.html) — published 2026-10-20T19:00:00+00:00
  
  To let you create log groups that are encrypted with your own keys, CloudWatch added the             <code class="code">kms:DescribeKey</code> permission to the <a href="https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/managed-policies-cloudwatch.html#managed-policies-cloudwatch-CloudWatchFullAccessV2">CloudWatchFullAccessV2</a> managed policy. CloudWatch Logs requires this permission from the           caller to create a log group with a customer managed AWS KMS key, or to associa


## cognito

- [Amazon Cognito extends multi-Region replication to AWS GovCloud (US) Regions](https://aws.amazon.com/about-aws/whats-new/2026/10/cognito-multi-region-us-govcloud/) — published 2026-10-21T17:00:00+00:00
  
  <p>Amazon Cognito multi-Region replication (MRR) now supports AWS GovCloud (US) Regions, extending the resilience benefits of MRR to more workloads. MRR lets you synchronize user and machine identity data, including credentials, user pool configurations, and federation setups, to a secondary user pool in a standby Region you designate, in near real-time. With user data in the standby Region, you can redirect traffic and keep authentication available if there is a disruption in your primary Regio


## ec2

- [New ImdsV1Enabled CloudWatch metric](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/viewing_metrics_with_cloudwatch.html#ec2-cloudwatch-metrics) — published 2026-10-22T19:00:00+00:00
  
  Amazon EC2 now publishes the <code class="code">ImdsV1Enabled</code> CloudWatch metric, which 					indicates whether an instance is configured to allow IMDSv1, even when no 					IMDSv1 calls are being made. Use this metric to find instances that still 					allow IMDSv1 and to track your migration to IMDSv2 across your 					accounts and Regions.


## s3

- [S3 Tables increases the default table bucket quota](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WhatsNew.html) — published 2026-09-30T19:00:00+00:00
  
  The default quota for the number of Amazon S3 table buckets you can create per AWS Region in an account increased from 10 to 100. For more information, see <a href="https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-tables-regions-quotas.html">S3 Tables Regions, endpoints, and service quotas</a>.


## step-functions

- [3 new AWS SDK service integrations](https://docs.aws.amazon.com/step-functions/latest/dg/awssdk-release-history.html) — published 2026-10-14T19:00:00+00:00
  
  Added AWS Network Security Manager, Amazon CloudWatch Omni, Amazon EventBridge V2.

- [5 new AWS SDK service integrations](https://docs.aws.amazon.com/step-functions/latest/dg/awssdk-release-history.html) — published 2026-09-25T19:00:00+00:00
  
  Added AWS Agent Registry, AWS Agent Registry Control, AWS IAM Account Access Manager, AWS IAM Toolbox, AWS Pricing Plan Manager.

