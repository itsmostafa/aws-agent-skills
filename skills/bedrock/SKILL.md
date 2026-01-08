---
name: bedrock
description: AWS Bedrock foundation models for generative AI. Use when invoking foundation models, building AI applications, creating embeddings, configuring model access, or implementing RAG patterns.
last_updated: "2026-01-07"
doc_source: https://docs.aws.amazon.com/bedrock/latest/userguide/
---

# AWS Bedrock

Amazon Bedrock provides access to foundation models (FMs) from AI companies through a unified API. Build generative AI applications with text generation, embeddings, and image generation capabilities.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Common Patterns](#common-patterns)
- [CLI Reference](#cli-reference)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [References](#references)

## Core Concepts

### Foundation Models

Pre-trained models available through Bedrock:
- **Claude** (Anthropic): Text generation, analysis, coding
- **Titan** (Amazon): Text, embeddings, image generation
- **Llama** (Meta): Open-weight text generation
- **Mistral**: Efficient text generation
- **Stable Diffusion** (Stability AI): Image generation

### Model Access

Models must be enabled in your account before use:
- Request access in Bedrock console
- Some models require acceptance of EULAs
- Access is region-specific

### Inference Types

| Type | Use Case | Pricing |
|------|----------|---------|
| **On-Demand** | Variable workloads | Per token |
| **Provisioned Throughput** | Consistent high-volume | Hourly commitment |
| **Batch Inference** | Async large-scale | Discounted per token |

## Common Patterns

### Invoke Model (Text Generation)

**AWS CLI:**

```bash
# Invoke Claude
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-sonnet-20240229-v1:0 \
  --content-type application/json \
  --accept application/json \
  --body '{
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 1024,
    "messages": [
      {"role": "user", "content": "Explain AWS Lambda in 3 sentences."}
    ]
  }' \
  response.json

cat response.json | jq -r '.content[0].text'
```

**boto3:**

```python
import boto3
import json

bedrock = boto3.client('bedrock-runtime')

def invoke_claude(prompt, max_tokens=1024):
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        contentType='application/json',
        accept='application/json',
        body=json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': max_tokens,
            'messages': [
                {'role': 'user', 'content': prompt}
            ]
        })
    )

    result = json.loads(response['body'].read())
    return result['content'][0]['text']

# Usage
response = invoke_claude('What is Amazon S3?')
print(response)
```

### Streaming Response

```python
import boto3
import json

bedrock = boto3.client('bedrock-runtime')

def stream_claude(prompt):
    response = bedrock.invoke_model_with_response_stream(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        contentType='application/json',
        accept='application/json',
        body=json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 1024,
            'messages': [
                {'role': 'user', 'content': prompt}
            ]
        })
    )

    for event in response['body']:
        chunk = json.loads(event['chunk']['bytes'])
        if chunk['type'] == 'content_block_delta':
            yield chunk['delta'].get('text', '')

# Usage
for text in stream_claude('Write a haiku about cloud computing.'):
    print(text, end='', flush=True)
```

### Generate Embeddings

```python
import boto3
import json

bedrock = boto3.client('bedrock-runtime')

def get_embedding(text):
    response = bedrock.invoke_model(
        modelId='amazon.titan-embed-text-v2:0',
        contentType='application/json',
        accept='application/json',
        body=json.dumps({
            'inputText': text,
            'dimensions': 1024,
            'normalize': True
        })
    )

    result = json.loads(response['body'].read())
    return result['embedding']

# Usage
embedding = get_embedding('AWS Lambda is a serverless compute service.')
print(f'Embedding dimension: {len(embedding)}')
```

### Conversation with History

```python
import boto3
import json

bedrock = boto3.client('bedrock-runtime')

class Conversation:
    def __init__(self, system_prompt=None):
        self.messages = []
        self.system = system_prompt

    def chat(self, user_message):
        self.messages.append({
            'role': 'user',
            'content': user_message
        })

        body = {
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 1024,
            'messages': self.messages
        }

        if self.system:
            body['system'] = self.system

        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps(body)
        )

        result = json.loads(response['body'].read())
        assistant_message = result['content'][0]['text']

        self.messages.append({
            'role': 'assistant',
            'content': assistant_message
        })

        return assistant_message

# Usage
conv = Conversation(system_prompt='You are an AWS solutions architect.')
print(conv.chat('What database should I use for a chat application?'))
print(conv.chat('What about for time-series data?'))
```

### List Available Models

```bash
# List all foundation models
aws bedrock list-foundation-models \
  --query 'modelSummaries[*].[modelId,modelName,providerName]' \
  --output table

# Filter by provider
aws bedrock list-foundation-models \
  --by-provider anthropic \
  --query 'modelSummaries[*].modelId'

# Get model details
aws bedrock get-foundation-model \
  --model-identifier anthropic.claude-3-sonnet-20240229-v1:0
```

### Request Model Access

```bash
# List model access status
aws bedrock list-foundation-model-agreement-offers \
  --model-id anthropic.claude-3-sonnet-20240229-v1:0
```

## CLI Reference

### Bedrock (Control Plane)

| Command | Description |
|---------|-------------|
| `aws bedrock list-foundation-models` | List available models |
| `aws bedrock get-foundation-model` | Get model details |
| `aws bedrock list-custom-models` | List fine-tuned models |
| `aws bedrock create-model-customization-job` | Start fine-tuning |
| `aws bedrock list-provisioned-model-throughputs` | List provisioned capacity |

### Bedrock Runtime (Data Plane)

| Command | Description |
|---------|-------------|
| `aws bedrock-runtime invoke-model` | Invoke model synchronously |
| `aws bedrock-runtime invoke-model-with-response-stream` | Invoke with streaming |
| `aws bedrock-runtime converse` | Multi-turn conversation API |
| `aws bedrock-runtime converse-stream` | Streaming conversation |

### Bedrock Agent Runtime

| Command | Description |
|---------|-------------|
| `aws bedrock-agent-runtime invoke-agent` | Invoke a Bedrock agent |
| `aws bedrock-agent-runtime retrieve` | Query knowledge base |
| `aws bedrock-agent-runtime retrieve-and-generate` | RAG query |

## Best Practices

### Cost Optimization

- **Use appropriate models**: Smaller models for simple tasks
- **Set max_tokens**: Limit output length when possible
- **Cache responses**: For repeated identical queries
- **Batch when possible**: Use batch inference for bulk processing
- **Monitor usage**: Set up CloudWatch alarms for cost

### Performance

- **Use streaming**: For better user experience with long outputs
- **Connection pooling**: Reuse boto3 clients
- **Regional deployment**: Use closest region to reduce latency
- **Provisioned throughput**: For consistent high-volume workloads

### Security

- **Least privilege IAM**: Only grant needed model access
- **VPC endpoints**: Keep traffic private
- **Guardrails**: Implement content filtering
- **Audit with CloudTrail**: Track model invocations

### IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0",
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
      ]
    }
  ]
}
```

## Troubleshooting

### AccessDeniedException

**Causes:**
- Model access not enabled in console
- IAM policy missing `bedrock:InvokeModel`
- Wrong model ID or region

**Debug:**

```bash
# Check model access status
aws bedrock list-foundation-models \
  --query 'modelSummaries[?modelId==`anthropic.claude-3-sonnet-20240229-v1:0`]'

# Test IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:role/my-role \
  --action-names bedrock:InvokeModel \
  --resource-arns "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
```

### ModelNotReadyException

**Cause:** Model is still being provisioned or temporarily unavailable.

**Solution:** Implement retry with exponential backoff:

```python
import time
from botocore.exceptions import ClientError

def invoke_with_retry(bedrock, body, max_retries=3):
    for attempt in range(max_retries):
        try:
            return bedrock.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps(body)
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ModelNotReadyException':
                time.sleep(2 ** attempt)
            else:
                raise
    raise Exception('Max retries exceeded')
```

### ThrottlingException

**Causes:**
- Exceeded on-demand quota
- Too many concurrent requests

**Solutions:**
- Request quota increase
- Implement exponential backoff
- Consider provisioned throughput

### ValidationException

**Common issues:**
- Invalid model ID
- Malformed request body
- max_tokens exceeds model limit

**Debug:**

```python
# Check model-specific requirements
aws bedrock get-foundation-model \
  --model-identifier anthropic.claude-3-sonnet-20240229-v1:0 \
  --query 'modelDetails.inferenceTypesSupported'
```

## References

- [Bedrock User Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/)
- [Bedrock API Reference](https://docs.aws.amazon.com/bedrock/latest/APIReference/)
- [Bedrock Runtime API](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_Operations_Amazon_Bedrock_Runtime.html)
- [Model Parameters](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters.html)
- [Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
