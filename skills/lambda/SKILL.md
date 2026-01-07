---
name: lambda
description: AWS Lambda serverless functions for event-driven compute. Use when creating functions, configuring triggers, debugging invocations, optimizing cold starts, setting up event source mappings, or managing layers.
---

# AWS Lambda

AWS Lambda runs code without provisioning servers. You pay only for compute time consumed. Lambda automatically scales from a few requests per day to thousands per second.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Common Patterns](#common-patterns)
- [CLI Reference](#cli-reference)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [References](#references)

## Core Concepts

### Function

Your code packaged with configuration. Includes runtime, handler, memory, timeout, and IAM role.

### Invocation Types

| Type | Description | Use Case |
|------|-------------|----------|
| **Synchronous** | Caller waits for response | API Gateway, direct invoke |
| **Asynchronous** | Fire and forget | S3, SNS, EventBridge |
| **Poll-based** | Lambda polls source | SQS, Kinesis, DynamoDB Streams |

### Execution Environment

Lambda creates execution environments to run your function. Components:
- **Cold start**: New environment initialization
- **Warm start**: Reusing existing environment
- **Handler**: Entry point function
- **Context**: Runtime information

### Layers

Reusable packages of libraries, dependencies, or custom runtimes (up to 5 per function).

## Common Patterns

### Create a Python Function

**AWS CLI:**

```bash
# Create deployment package
zip function.zip lambda_function.py

# Create function
aws lambda create-function \
  --function-name MyFunction \
  --runtime python3.12 \
  --role arn:aws:iam::123456789012:role/lambda-role \
  --handler lambda_function.handler \
  --zip-file fileb://function.zip \
  --timeout 30 \
  --memory-size 256

# Update function code
aws lambda update-function-code \
  --function-name MyFunction \
  --zip-file fileb://function.zip
```

**boto3:**

```python
import boto3
import zipfile
import io

lambda_client = boto3.client('lambda')

# Create zip in memory
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w') as zf:
    zf.writestr('lambda_function.py', '''
def handler(event, context):
    return {"statusCode": 200, "body": "Hello"}
''')
zip_buffer.seek(0)

# Create function
lambda_client.create_function(
    FunctionName='MyFunction',
    Runtime='python3.12',
    Role='arn:aws:iam::123456789012:role/lambda-role',
    Handler='lambda_function.handler',
    Code={'ZipFile': zip_buffer.read()},
    Timeout=30,
    MemorySize=256
)
```

### Add S3 Trigger

```bash
# Add permission for S3 to invoke Lambda
aws lambda add-permission \
  --function-name MyFunction \
  --statement-id s3-trigger \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::my-bucket \
  --source-account 123456789012

# Configure S3 notification (see S3 skill)
```

### Add SQS Event Source

```bash
aws lambda create-event-source-mapping \
  --function-name MyFunction \
  --event-source-arn arn:aws:sqs:us-east-1:123456789012:my-queue \
  --batch-size 10 \
  --maximum-batching-window-in-seconds 5
```

### Environment Variables

```bash
aws lambda update-function-configuration \
  --function-name MyFunction \
  --environment "Variables={DB_HOST=mydb.cluster-xyz.us-east-1.rds.amazonaws.com,LOG_LEVEL=INFO}"
```

### Create and Attach Layer

```bash
# Create layer
zip -r layer.zip python/

aws lambda publish-layer-version \
  --layer-name my-dependencies \
  --compatible-runtimes python3.12 \
  --zip-file fileb://layer.zip

# Attach to function
aws lambda update-function-configuration \
  --function-name MyFunction \
  --layers arn:aws:lambda:us-east-1:123456789012:layer:my-dependencies:1
```

### Invoke Function

```bash
# Synchronous invoke
aws lambda invoke \
  --function-name MyFunction \
  --payload '{"key": "value"}' \
  response.json

# Asynchronous invoke
aws lambda invoke \
  --function-name MyFunction \
  --invocation-type Event \
  --payload '{"key": "value"}' \
  response.json
```

## CLI Reference

### Function Management

| Command | Description |
|---------|-------------|
| `aws lambda create-function` | Create new function |
| `aws lambda update-function-code` | Update function code |
| `aws lambda update-function-configuration` | Update settings |
| `aws lambda delete-function` | Delete function |
| `aws lambda list-functions` | List all functions |
| `aws lambda get-function` | Get function details |

### Invocation

| Command | Description |
|---------|-------------|
| `aws lambda invoke` | Invoke function |
| `aws lambda invoke-async` | Async invoke (deprecated) |

### Event Sources

| Command | Description |
|---------|-------------|
| `aws lambda create-event-source-mapping` | Add event source |
| `aws lambda list-event-source-mappings` | List mappings |
| `aws lambda update-event-source-mapping` | Update mapping |
| `aws lambda delete-event-source-mapping` | Remove mapping |

### Permissions

| Command | Description |
|---------|-------------|
| `aws lambda add-permission` | Add resource-based policy |
| `aws lambda remove-permission` | Remove permission |
| `aws lambda get-policy` | View resource policy |

## Best Practices

### Performance

- **Right-size memory**: More memory = more CPU = faster execution
- **Minimize cold starts**: Keep functions warm, use Provisioned Concurrency
- **Optimize package size**: Smaller packages deploy faster
- **Use layers** for shared dependencies
- **Initialize outside handler**: Reuse connections across invocations

```python
# GOOD: Initialize outside handler
import boto3
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('MyTable')

def handler(event, context):
    # Reuses existing connection
    return table.get_item(Key={'id': event['id']})
```

### Security

- **Least privilege IAM roles** — only grant needed permissions
- **Use Secrets Manager** for sensitive data
- **Enable VPC** only if needed (adds latency)
- **Encrypt environment variables** with KMS

### Cost Optimization

- **Set appropriate timeout** — don't use max 15 minutes unnecessarily
- **Use ARM architecture** (Graviton2) for 34% better price/performance
- **Batch process** where possible
- **Use Reserved Concurrency** to limit costs

### Reliability

- **Configure DLQ** for async invocations
- **Handle retries** — async events retry twice
- **Make handlers idempotent**
- **Use structured logging**

## Troubleshooting

### Timeout Errors

**Symptom:** `Task timed out after X seconds`

**Causes:**
- Function takes longer than timeout
- Network call to unreachable resource
- VPC configuration issues

**Debug:**

```bash
# Check function configuration
aws lambda get-function-configuration \
  --function-name MyFunction \
  --query "Timeout"

# Increase timeout
aws lambda update-function-configuration \
  --function-name MyFunction \
  --timeout 60
```

### Out of Memory

**Symptom:** Function crashes with memory error

**Fix:**

```bash
aws lambda update-function-configuration \
  --function-name MyFunction \
  --memory-size 512
```

### Cold Start Latency

**Causes:**
- Large deployment package
- VPC configuration
- Many dependencies to load

**Solutions:**
- Use Provisioned Concurrency
- Reduce package size
- Use layers for dependencies
- Consider Graviton2 (ARM)

```bash
# Enable Provisioned Concurrency
aws lambda put-provisioned-concurrency-config \
  --function-name MyFunction \
  --qualifier LIVE \
  --provisioned-concurrent-executions 5
```

### Permission Denied

**Symptom:** `AccessDeniedException`

**Debug:**

```bash
# Check execution role
aws lambda get-function-configuration \
  --function-name MyFunction \
  --query "Role"

# Check role policies
aws iam list-attached-role-policies \
  --role-name lambda-role
```

### VPC Connectivity Issues

**Symptom:** Cannot reach internet or AWS services

**Causes:**
- No NAT Gateway for internet access
- Missing VPC endpoint for AWS services
- Security group blocking outbound

**Solutions:**
- Add NAT Gateway for internet
- Add VPC endpoints for AWS services
- Check security group rules

## References

- [Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/)
- [Lambda API Reference](https://docs.aws.amazon.com/lambda/latest/api/)
- [Lambda CLI Reference](https://docs.aws.amazon.com/cli/latest/reference/lambda/)
- [boto3 Lambda](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html)
