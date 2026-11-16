# AWS documentation updates - 2026-11-16

Total updates: 12

## bedrock

- [Amazon Bedrock adds bedrock-runtime endpoint support for Daybreak models](https://aws.amazon.com/about-aws/whats-new/2026/11/openai-gpt-daybreak-on-amazon-bedrock-runtime/) — published 2026-11-10T10:14:00+00:00
  
  <p>Eligible customers can now access OpenAI’s specialized cybersecurity models Daybreak Red: GPT-5.6 Cyber and Daybreak Blue: GPT-5.6 Sol through the bedrock-runtime endpoint on Amazon Bedrock.<br /> <br /> Daybreak Blue is the starting point for most security teams across defensive workflows, including vulnerability discovery, detection engineering, and incident response. Daybreak Red is designed for advanced, authorized tasks such as vulnerability research, exploit reproduction, and mitigation

- [Amazon Bedrock AgentCore now offers a Web Search API](https://aws.amazon.com/about-aws/whats-new/2026/11/amazon-bedrock-agentcore-web-search-api/) — published 2026-11-10T00:00:00+00:00
  
  <p>Today, AWS announces the general availability of the Web Search API on Amazon Bedrock AgentCore, which lets you search the web with a single API call. Web Search on AgentCore has been available as an MCP tool through AgentCore Gateway. The new InvokeWebSearch API gives applications, custom agent loops, and data pipelines search results with no resources to create.</p>  <p>The API returns ranked results from the Amazon-operated web index behind Web Search on AgentCore. Each result includes a t

- [Amazon Bedrock now offers Claude Mythos 5.2 to Eligible Customers in AWS GovCloud (US)](https://aws.amazon.com/about-aws/whats-new/2026/11/bedrock-claude-mythos-5-2-govcloud/) — published 2026-11-09T18:30:00+00:00
  
  <p>Amazon Bedrock, the platform for building generative AI applications and agents at production scale, now offers Claude Mythos 5.2 to eligible customers in AWS GovCloud (US). Claude Mythos 5.2 is Anthropic's most advanced AI model to date for use cases across cybersecurity, software coding, and complex reasoning tasks. The model can identify sophisticated security vulnerabilities in software and demonstrate exploitability. It can also comprehend large codebases and deliver actionable findings

- [Kimi K3.1 Pro (Highspeed) now available on Amazon Bedrock](https://aws.amazon.com/about-aws/whats-new/2026/11/moonshot-ai-kimi-k3-1-pro-on-amazon-bedrock) — published 2026-11-06T22:47:00+00:00
  
  <p>Today, Kimi K3.1 Pro from Moonshot AI is available on Amazon Bedrock, expanding our open weight model portfolio with the security and governance that customers rely on. Customers using Amazon Bedrock can now run agentic use cases such as coding and document processing on Kimi K3.1 Pro (Highspeed), which delivers high output tokens per second (OTPS) for faster, more responsive results.</p>  <p>According to Moonshot AI, Kimi K3.1 Pro is an open-weight, natively multimodal agentic model with a 1

- [Announcing Web Answer on Amazon Bedrock AgentCore](https://aws.amazon.com/about-aws/whats-new/2026/11/web-answer-amazon-bedrock/) — published 2026-11-05T20:56:00+00:00
  
  <p>Today, we are announcing the general availability of Web Answer on Amazon Bedrock AgentCore. Web Answer is a managed tool that returns a synthesized, grounded, cited answer to a natural-language question in a single call, so agent builders can attach it to an agent and get back a finished answer grounded in current web sources, without building and maintaining their own search, retrieve, synthesis, and citation pipeline.&nbsp;</p>  <p>Web Answer builds on Web Search on Amazon Bedrock AgentCor


## cloudwatch

- [OTel Container Insights changes in add-on version 7.0.0](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/DocumentHistory.html) — published 2026-11-12T19:00:00+00:00
  
  Version 7.0.0 of the Amazon CloudWatch Observability Amazon EKS add-on and Helm chart removes           duplicate series, deprecated attributes, and some generated labels from OTel Container           Insights metrics. For more information, see <a href="https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/container-insights-eks-otel.html#container-insights-eks-otel-upgrade-v7">Upgrading OTel Container Insights to version 7.0.0</a>.


## dynamodb

- [DynamoDB bulk put items is now available](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DocumentHistory.html) — published 2026-11-05T19:00:00+00:00
  
  You can now use bulk put items to load data from Amazon S3 into an existing DynamoDB                     table without consuming read or write capacity on that table. Bulk put items                     offers two performance tiers, Standard and Accelerated, to match your workload                     requirements. For more information, see <a href="https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/BulkPutItems.HowItWorks.html">DynamoDB bulk put items: how it works</a>.

- [Bulk put items CloudTrail events](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DocumentHistory.html) — published 2026-11-05T19:00:00+00:00
  
  Added information about CloudTrail logging for bulk put items operations, which                     records the <code class="code">StartBulkPutItems</code> management event and                         <code class="code">BulkPutItems</code> data service events. For more information, see                         <a href="https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/BulkPutItems.Considerations.html">Bulk put items considerations, quotas, and permissions</a>.

- [Increased vector index quota](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DocumentHistory.html) — published 2026-10-26T19:00:00+00:00
  
  Updated documentation for the per-table vector index quota, which you can now                     increase to a maximum of 20 vector indexes per table. For more information, see                         <a href="https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ServiceQuotas.html">Quotas in                         Amazon DynamoDB</a>, <a href="https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ddb-strands-storage.html">Using                         DynamoDB as a stora


## ec2

- [Capacity Manager supportability checks](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/DocumentHistory.html) — published 2026-10-28T19:00:00+00:00
  
  Updated documentation for Amazon EC2 Capacity Manager real-time supportability 					checks, fulfillment metrics, and capacity check quotas, including the 						<code class="code">--instance-requirements-with-metadata</code> attribute input. For more 					information, see <a href="https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/capacity-manager.html">EC2 Capacity 						Manager</a>.


## lambda

- [Updated durable functions read quotas](https://docs.aws.amazon.com/lambda/latest/dg/lambda-releases.html) — published 2026-11-04T19:00:00+00:00
  
  Updated documentation for the read API request quotas for Lambda durable functions. For more information, see <a href="https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html">Lambda quotas</a>.


## rds

- [Amazon RDS reports snapshot storage charges at per-snapshot granularity](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/WhatsNew.html) — published 2026-11-01T19:00:00+00:00
  
  Amazon RDS now attributes snapshot storage charges to each snapshot individually 					in AWS Cost Explorer and your AWS Cost and Usage Report. The 					<code class="code">ResourceId</code> field shows the Amazon RDS snapshot ARN, or the Amazon RDS cluster 					snapshot ARN for Multi-AZ DB cluster snapshots. Your pricing and overall charges 					are unchanged. To group snapshot charges by instance, apply cost allocation tags to 					your snapshots. For more information, see <a href="https://docs.

