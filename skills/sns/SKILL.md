---
name: sns
description: AWS SNS notification service for pub/sub messaging. Use when creating topics, managing subscriptions, configuring message filtering, sending notifications, or setting up mobile push.
last_updated: "2026-01-07"
doc_source: https://docs.aws.amazon.com/sns/latest/dg/
---

# AWS SNS

Amazon Simple Notification Service (SNS) is a fully managed pub/sub messaging service for application-to-application (A2A) and application-to-person (A2P) communication.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Common Patterns](#common-patterns)
- [CLI Reference](#cli-reference)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [References](#references)

## Core Concepts

### Topics

Named channels for publishing messages. Publishers send to topics, subscribers receive from topics.

### Topic Types

| Type | Description | Use Case |
|------|-------------|----------|
| **Standard** | Best-effort ordering, at-least-once | Most use cases |
| **FIFO** | Strict ordering, exactly-once | Order-sensitive |

### Subscription Protocols

| Protocol | Description |
|----------|-------------|
| **Lambda** | Invoke Lambda function |
| **SQS** | Send to SQS queue |
| **HTTP/HTTPS** | POST to endpoint |
| **Email** | Send email |
| **SMS** | Send text message |
| **Application** | Mobile push notification |

### Message Filtering

Route messages to specific subscribers based on message attributes.

## Common Patterns

### Create Topic and Subscribe

**AWS CLI:**

```bash
# Create standard topic
aws sns create-topic --name my-topic

# Create FIFO topic
aws sns create-topic \
  --name my-topic.fifo \
  --attributes FifoTopic=true

# Subscribe Lambda
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:my-topic \
  --protocol lambda \
  --notification-endpoint arn:aws:lambda:us-east-1:123456789012:function:my-function

# Subscribe SQS
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:my-topic \
  --protocol sqs \
  --notification-endpoint arn:aws:sqs:us-east-1:123456789012:my-queue

# Subscribe email
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:my-topic \
  --protocol email \
  --notification-endpoint user@example.com
```

**boto3:**

```python
import boto3

sns = boto3.client('sns')

# Create topic
response = sns.create_topic(Name='my-topic')
topic_arn = response['TopicArn']

# Subscribe Lambda
sns.subscribe(
    TopicArn=topic_arn,
    Protocol='lambda',
    Endpoint='arn:aws:lambda:us-east-1:123456789012:function:my-function'
)

# Subscribe SQS with filter
sns.subscribe(
    TopicArn=topic_arn,
    Protocol='sqs',
    Endpoint='arn:aws:sqs:us-east-1:123456789012:order-queue',
    Attributes={
        'FilterPolicy': '{"event_type": ["order_created", "order_updated"]}'
    }
)
```

### Publish Messages

```python
import boto3
import json

sns = boto3.client('sns')
topic_arn = 'arn:aws:sns:us-east-1:123456789012:my-topic'

# Simple publish
sns.publish(
    TopicArn=topic_arn,
    Message='Hello, World!',
    Subject='Notification'
)

# Publish with attributes (for filtering)
sns.publish(
    TopicArn=topic_arn,
    Message=json.dumps({'order_id': '12345', 'status': 'created'}),
    MessageAttributes={
        'event_type': {
            'DataType': 'String',
            'StringValue': 'order_created'
        },
        'priority': {
            'DataType': 'Number',
            'StringValue': '1'
        }
    }
)

# Publish to FIFO topic
sns.publish(
    TopicArn='arn:aws:sns:us-east-1:123456789012:my-topic.fifo',
    Message=json.dumps({'order_id': '12345'}),
    MessageGroupId='order-12345',
    MessageDeduplicationId='unique-id'
)
```

### Message Filtering

```bash
# Add filter policy to subscription
aws sns set-subscription-attributes \
  --subscription-arn arn:aws:sns:us-east-1:123456789012:my-topic:abc123 \
  --attribute-name FilterPolicy \
  --attribute-value '{
    "event_type": ["order_created"],
    "priority": [{"numeric": [">=", 1]}]
  }'
```

Filter policy examples:

```json
// Exact match
{"event_type": ["order_created", "order_updated"]}

// Prefix match
{"customer_id": [{"prefix": "PREMIUM-"}]}

// Numeric comparison
{"price": [{"numeric": [">=", 100, "<=", 500]}]}

// Exists check
{"customer_id": [{"exists": true}]}

// Anything but
{"event_type": [{"anything-but": ["deleted"]}]}

// Combined
{
  "event_type": ["order_created"],
  "region": ["us-east", "us-west"],
  "priority": [{"numeric": [">=", 1]}]
}
```

### Fan-Out Pattern (SNS to Multiple SQS)

```python
import boto3
import json

sns = boto3.client('sns')
sqs = boto3.client('sqs')

# Create topic
topic = sns.create_topic(Name='orders-topic')
topic_arn = topic['TopicArn']

# Create queues for different processors
queues = {
    'analytics': sqs.create_queue(QueueName='order-analytics')['QueueUrl'],
    'fulfillment': sqs.create_queue(QueueName='order-fulfillment')['QueueUrl'],
    'notification': sqs.create_queue(QueueName='order-notification')['QueueUrl']
}

# Subscribe each queue
for name, queue_url in queues.items():
    queue_arn = sqs.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=['QueueArn']
    )['Attributes']['QueueArn']

    sns.subscribe(
        TopicArn=topic_arn,
        Protocol='sqs',
        Endpoint=queue_arn
    )

# One publish reaches all queues
sns.publish(
    TopicArn=topic_arn,
    Message=json.dumps({'order_id': '12345', 'total': 99.99})
)
```

### Lambda Permission for SNS

```bash
aws lambda add-permission \
  --function-name my-function \
  --statement-id sns-trigger \
  --action lambda:InvokeFunction \
  --principal sns.amazonaws.com \
  --source-arn arn:aws:sns:us-east-1:123456789012:my-topic
```

## CLI Reference

### Topic Management

| Command | Description |
|---------|-------------|
| `aws sns create-topic` | Create topic |
| `aws sns delete-topic` | Delete topic |
| `aws sns list-topics` | List topics |
| `aws sns get-topic-attributes` | Get topic settings |
| `aws sns set-topic-attributes` | Update topic settings |

### Subscriptions

| Command | Description |
|---------|-------------|
| `aws sns subscribe` | Create subscription |
| `aws sns unsubscribe` | Remove subscription |
| `aws sns list-subscriptions` | List all subscriptions |
| `aws sns list-subscriptions-by-topic` | List topic subscriptions |
| `aws sns confirm-subscription` | Confirm pending subscription |

### Publishing

| Command | Description |
|---------|-------------|
| `aws sns publish` | Publish message |

## Best Practices

### Reliability

- **Use SQS for durability** — SNS is push-based, SQS queues messages
- **Implement retries** for HTTP/HTTPS endpoints
- **Configure DLQ** for failed deliveries
- **Use FIFO topics** for ordering requirements

### Security

- **Use topic policies** to control access
- **Enable encryption** with SSE
- **Use VPC endpoints** for private access

```bash
# Enable SSE
aws sns set-topic-attributes \
  --topic-arn arn:aws:sns:us-east-1:123456789012:my-topic \
  --attribute-name KmsMasterKeyId \
  --attribute-value alias/my-key
```

### Cost Optimization

- **Use message filtering** to reduce unnecessary deliveries
- **Batch operations** where possible
- **Monitor and clean up** unused topics/subscriptions

### Message Design

- **Keep messages small** (256 KB limit)
- **Use message attributes** for routing
- **Include correlation IDs** for tracing

## Troubleshooting

### Subscription Not Receiving Messages

**Check:**
1. Subscription is confirmed (not pending)
2. Filter policy matches message attributes
3. Target permissions (Lambda, SQS)

```bash
# Check subscription status
aws sns list-subscriptions-by-topic \
  --topic-arn arn:aws:sns:us-east-1:123456789012:my-topic

# Check subscription attributes
aws sns get-subscription-attributes \
  --subscription-arn arn:aws:sns:us-east-1:123456789012:my-topic:abc123
```

### HTTP Endpoint Not Working

**Debug:**

```bash
# Check delivery status logging
aws sns set-topic-attributes \
  --topic-arn arn:aws:sns:us-east-1:123456789012:my-topic \
  --attribute-name DeliveryPolicy \
  --attribute-value '{
    "http": {
      "defaultHealthyRetryPolicy": {
        "minDelayTarget": 20,
        "maxDelayTarget": 20,
        "numRetries": 3,
        "numMaxDelayRetries": 0,
        "numNoDelayRetries": 0,
        "numMinDelayRetries": 0,
        "backoffFunction": "linear"
      }
    }
  }'
```

### Messages Not Matching Filter

**Verify:**
- Message attributes are set (not in body)
- Attribute types match (String vs Number)
- Filter policy syntax is correct

```python
# Correct: attributes must be message attributes
sns.publish(
    TopicArn=topic_arn,
    Message='body content',
    MessageAttributes={
        'event_type': {
            'DataType': 'String',
            'StringValue': 'order_created'  # This is filtered
        }
    }
)

# Wrong: this won't be filtered
sns.publish(
    TopicArn=topic_arn,
    Message=json.dumps({'event_type': 'order_created'})  # Not filtered
)
```

### SQS Not Receiving from SNS

**Check SQS queue policy:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Service": "sns.amazonaws.com"},
      "Action": "sqs:SendMessage",
      "Resource": "arn:aws:sqs:us-east-1:123456789012:my-queue",
      "Condition": {
        "ArnEquals": {
          "aws:SourceArn": "arn:aws:sns:us-east-1:123456789012:my-topic"
        }
      }
    }
  ]
}
```

## References

- [SNS Developer Guide](https://docs.aws.amazon.com/sns/latest/dg/)
- [SNS API Reference](https://docs.aws.amazon.com/sns/latest/api/)
- [SNS CLI Reference](https://docs.aws.amazon.com/cli/latest/reference/sns/)
- [boto3 SNS](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sns.html)
