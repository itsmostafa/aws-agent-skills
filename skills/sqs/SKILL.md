---
name: sqs
description: AWS SQS message queue service for decoupled architectures. Use when creating queues, configuring dead-letter queues, managing visibility timeouts, implementing FIFO ordering, or integrating with Lambda.
last_updated: "2026-01-07"
doc_source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/
---

# AWS SQS

Amazon Simple Queue Service (SQS) is a fully managed message queuing service for decoupling and scaling microservices, distributed systems, and serverless applications.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Common Patterns](#common-patterns)
- [CLI Reference](#cli-reference)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [References](#references)

## Core Concepts

### Queue Types

| Type | Description | Use Case |
|------|-------------|----------|
| **Standard** | At-least-once, best-effort ordering | High throughput |
| **FIFO** | Exactly-once, strict ordering | Order-sensitive processing |

### Key Settings

| Setting | Description | Default |
|---------|-------------|---------|
| **Visibility Timeout** | Time message is hidden after receive | 30 seconds |
| **Message Retention** | How long messages are kept | 4 days (max 14) |
| **Delay Seconds** | Delay before message is available | 0 |
| **Max Message Size** | Maximum message size | 256 KB |

### Dead-Letter Queue (DLQ)

Queue for messages that failed processing after maxReceiveCount attempts.

## Common Patterns

### Create a Standard Queue

**AWS CLI:**

```bash
aws sqs create-queue \
  --queue-name my-queue \
  --attributes '{
    "VisibilityTimeout": "60",
    "MessageRetentionPeriod": "604800",
    "ReceiveMessageWaitTimeSeconds": "20"
  }'
```

**boto3:**

```python
import boto3

sqs = boto3.client('sqs')

response = sqs.create_queue(
    QueueName='my-queue',
    Attributes={
        'VisibilityTimeout': '60',
        'MessageRetentionPeriod': '604800',
        'ReceiveMessageWaitTimeSeconds': '20'  # Long polling
    }
)
queue_url = response['QueueUrl']
```

### Create FIFO Queue

```bash
aws sqs create-queue \
  --queue-name my-queue.fifo \
  --attributes '{
    "FifoQueue": "true",
    "ContentBasedDeduplication": "true"
  }'
```

### Configure Dead-Letter Queue

```bash
# Create DLQ
aws sqs create-queue --queue-name my-queue-dlq

# Get DLQ ARN
DLQ_ARN=$(aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/my-queue-dlq \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' --output text)

# Set redrive policy on main queue
aws sqs set-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/my-queue \
  --attributes "{
    \"RedrivePolicy\": \"{\\\"deadLetterTargetArn\\\":\\\"${DLQ_ARN}\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"
  }"
```

### Send Messages

```python
import boto3
import json

sqs = boto3.client('sqs')
queue_url = 'https://sqs.us-east-1.amazonaws.com/123456789012/my-queue'

# Send single message
sqs.send_message(
    QueueUrl=queue_url,
    MessageBody=json.dumps({'order_id': '12345', 'action': 'process'}),
    MessageAttributes={
        'MessageType': {
            'DataType': 'String',
            'StringValue': 'Order'
        }
    }
)

# Send to FIFO queue
sqs.send_message(
    QueueUrl='https://sqs.us-east-1.amazonaws.com/123456789012/my-queue.fifo',
    MessageBody=json.dumps({'order_id': '12345'}),
    MessageGroupId='order-12345',
    MessageDeduplicationId='unique-id-12345'
)

# Batch send (up to 10 messages)
sqs.send_message_batch(
    QueueUrl=queue_url,
    Entries=[
        {'Id': '1', 'MessageBody': json.dumps({'id': 1})},
        {'Id': '2', 'MessageBody': json.dumps({'id': 2})},
        {'Id': '3', 'MessageBody': json.dumps({'id': 3})}
    ]
)
```

### Receive and Process Messages

```python
import boto3
import json

sqs = boto3.client('sqs')
queue_url = 'https://sqs.us-east-1.amazonaws.com/123456789012/my-queue'

while True:
    # Long polling (wait up to 20 seconds)
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=20,
        MessageAttributeNames=['All'],
        AttributeNames=['All']
    )

    messages = response.get('Messages', [])

    for message in messages:
        try:
            body = json.loads(message['Body'])
            print(f"Processing: {body}")

            # Process message...

            # Delete on success
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=message['ReceiptHandle']
            )
        except Exception as e:
            print(f"Error processing message: {e}")
            # Message will become visible again after visibility timeout
```

### Lambda Integration

```bash
# Create event source mapping
aws lambda create-event-source-mapping \
  --function-name my-function \
  --event-source-arn arn:aws:sqs:us-east-1:123456789012:my-queue \
  --batch-size 10 \
  --maximum-batching-window-in-seconds 5
```

Lambda handler:

```python
def handler(event, context):
    for record in event['Records']:
        body = json.loads(record['body'])
        message_id = record['messageId']

        try:
            process_message(body)
        except Exception as e:
            # Raise to put message back in queue
            raise

    return {'batchItemFailures': []}
```

## CLI Reference

### Queue Management

| Command | Description |
|---------|-------------|
| `aws sqs create-queue` | Create queue |
| `aws sqs delete-queue` | Delete queue |
| `aws sqs list-queues` | List queues |
| `aws sqs get-queue-url` | Get queue URL by name |
| `aws sqs get-queue-attributes` | Get queue settings |
| `aws sqs set-queue-attributes` | Update queue settings |

### Messaging

| Command | Description |
|---------|-------------|
| `aws sqs send-message` | Send single message |
| `aws sqs send-message-batch` | Send up to 10 messages |
| `aws sqs receive-message` | Receive messages |
| `aws sqs delete-message` | Delete message |
| `aws sqs delete-message-batch` | Delete up to 10 messages |
| `aws sqs purge-queue` | Delete all messages |

### Visibility

| Command | Description |
|---------|-------------|
| `aws sqs change-message-visibility` | Change timeout |
| `aws sqs change-message-visibility-batch` | Batch change |

## Best Practices

### Message Processing

- **Use long polling** (WaitTimeSeconds=20) to reduce API calls
- **Delete messages promptly** after successful processing
- **Configure appropriate visibility timeout** (> processing time)
- **Implement idempotent consumers** for at-least-once delivery

### Dead-Letter Queues

- **Always configure DLQ** for production queues
- **Set appropriate maxReceiveCount** (usually 3-5)
- **Monitor DLQ depth** with CloudWatch alarms
- **Process DLQ messages** manually or with automation

### FIFO Queues

- **Use message group IDs** to partition ordering
- **Enable content-based deduplication** or provide dedup IDs
- **Throughput**: 300 msgs/sec without batching, 3000 with

### Security

- **Use queue policies** to control access
- **Enable encryption** with SSE-SQS or SSE-KMS
- **Use VPC endpoints** for private access

## Troubleshooting

### Messages Not Being Received

**Causes:**
- Short polling returning empty
- All messages in flight (visibility timeout)
- Messages delayed (DelaySeconds)

**Debug:**

```bash
# Check queue attributes
aws sqs get-queue-attributes \
  --queue-url $QUEUE_URL \
  --attribute-names All

# Check approximate message counts
aws sqs get-queue-attributes \
  --queue-url $QUEUE_URL \
  --attribute-names \
    ApproximateNumberOfMessages,\
    ApproximateNumberOfMessagesNotVisible,\
    ApproximateNumberOfMessagesDelayed
```

### Messages Going to DLQ

**Causes:**
- Processing errors
- Visibility timeout too short
- Consumer not deleting messages

**Redrive from DLQ:**

```bash
# Enable redrive allow policy on source queue
aws sqs set-queue-attributes \
  --queue-url $MAIN_QUEUE_URL \
  --attributes '{"RedriveAllowPolicy": "{\"redrivePermission\":\"allowAll\"}"}'

# Start redrive
aws sqs start-message-move-task \
  --source-arn arn:aws:sqs:us-east-1:123456789012:my-queue-dlq \
  --destination-arn arn:aws:sqs:us-east-1:123456789012:my-queue
```

### Duplicate Processing

**Solutions:**
- Use FIFO queues for exactly-once
- Implement idempotency in consumer
- Track processed message IDs in database

### Lambda Not Processing

```bash
# Check event source mapping
aws lambda list-event-source-mappings \
  --function-name my-function

# Check for errors
aws lambda get-event-source-mapping \
  --uuid <mapping-uuid>
```

## References

- [SQS Developer Guide](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/)
- [SQS API Reference](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/)
- [SQS CLI Reference](https://docs.aws.amazon.com/cli/latest/reference/sqs/)
- [boto3 SQS](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html)
