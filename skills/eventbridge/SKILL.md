---
name: eventbridge
description: AWS EventBridge serverless event bus for event-driven architectures. Use when creating rules, configuring event patterns, setting up scheduled events, integrating with SaaS, or building cross-account event routing.
last_updated: "2026-01-07"
doc_source: https://docs.aws.amazon.com/eventbridge/latest/userguide/
---

# AWS EventBridge

Amazon EventBridge is a serverless event bus that connects applications using events. Route events from AWS services, custom applications, and SaaS partners.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Common Patterns](#common-patterns)
- [CLI Reference](#cli-reference)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [References](#references)

## Core Concepts

### Event Bus

Channel that receives events. Types:
- **Default**: Receives AWS service events
- **Custom**: Your application events
- **Partner**: SaaS application events

### Rules

Match incoming events and route to targets. Each rule can have up to 5 targets.

### Event Patterns

JSON patterns that define which events match a rule.

### Targets

AWS services that receive matched events (Lambda, SQS, SNS, Step Functions, etc.).

### Scheduler

Schedule one-time or recurring events to invoke targets.

## Common Patterns

### Create Custom Event Bus and Rule

**AWS CLI:**

```bash
# Create custom event bus
aws events create-event-bus --name my-app-events

# Create rule
aws events put-rule \
  --name order-created-rule \
  --event-bus-name my-app-events \
  --event-pattern '{
    "source": ["my-app.orders"],
    "detail-type": ["Order Created"]
  }'

# Add Lambda target
aws events put-targets \
  --rule order-created-rule \
  --event-bus-name my-app-events \
  --targets '[{
    "Id": "process-order",
    "Arn": "arn:aws:lambda:us-east-1:123456789012:function:ProcessOrder"
  }]'

# Add Lambda permission
aws lambda add-permission \
  --function-name ProcessOrder \
  --statement-id eventbridge-order-created \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-east-1:123456789012:rule/my-app-events/order-created-rule
```

**boto3:**

```python
import boto3

events = boto3.client('events')

# Create event bus
events.create_event_bus(Name='my-app-events')

# Create rule
events.put_rule(
    Name='order-created-rule',
    EventBusName='my-app-events',
    EventPattern=json.dumps({
        'source': ['my-app.orders'],
        'detail-type': ['Order Created']
    }),
    State='ENABLED'
)

# Add target
events.put_targets(
    Rule='order-created-rule',
    EventBusName='my-app-events',
    Targets=[{
        'Id': 'process-order',
        'Arn': 'arn:aws:lambda:us-east-1:123456789012:function:ProcessOrder'
    }]
)
```

### Publish Custom Events

```python
import boto3
import json

events = boto3.client('events')

events.put_events(
    Entries=[
        {
            'Source': 'my-app.orders',
            'DetailType': 'Order Created',
            'Detail': json.dumps({
                'order_id': '12345',
                'customer_id': 'cust-789',
                'total': 99.99,
                'items': [
                    {'product_id': 'prod-1', 'quantity': 2}
                ]
            }),
            'EventBusName': 'my-app-events'
        }
    ]
)
```

### Scheduled Events

```bash
# Run every 5 minutes
aws events put-rule \
  --name every-5-minutes \
  --schedule-expression "rate(5 minutes)"

# Run at specific times (cron)
aws events put-rule \
  --name daily-cleanup \
  --schedule-expression "cron(0 2 * * ? *)"

# Add target
aws events put-targets \
  --rule every-5-minutes \
  --targets '[{
    "Id": "cleanup-function",
    "Arn": "arn:aws:lambda:us-east-1:123456789012:function:Cleanup"
  }]'
```

### EventBridge Scheduler (One-Time and Flexible)

```bash
# One-time schedule
aws scheduler create-schedule \
  --name send-reminder \
  --schedule-expression "at(2024-12-25T09:00:00)" \
  --target '{
    "Arn": "arn:aws:lambda:us-east-1:123456789012:function:SendReminder",
    "RoleArn": "arn:aws:iam::123456789012:role/scheduler-role",
    "Input": "{\"message\": \"Merry Christmas!\"}"
  }' \
  --flexible-time-window '{"Mode": "OFF"}'

# Recurring with flexible window
aws scheduler create-schedule \
  --name hourly-sync \
  --schedule-expression "rate(1 hour)" \
  --target '{
    "Arn": "arn:aws:lambda:us-east-1:123456789012:function:SyncData",
    "RoleArn": "arn:aws:iam::123456789012:role/scheduler-role"
  }' \
  --flexible-time-window '{"Mode": "FLEXIBLE", "MaximumWindowInMinutes": 15}'
```

### AWS Service Events

```bash
# EC2 state changes
aws events put-rule \
  --name ec2-state-change \
  --event-pattern '{
    "source": ["aws.ec2"],
    "detail-type": ["EC2 Instance State-change Notification"],
    "detail": {
      "state": ["stopped", "terminated"]
    }
  }'

# S3 object created
aws events put-rule \
  --name s3-upload \
  --event-pattern '{
    "source": ["aws.s3"],
    "detail-type": ["Object Created"],
    "detail": {
      "bucket": {"name": ["my-bucket"]},
      "object": {"key": [{"prefix": "uploads/"}]}
    }
  }'
```

## CLI Reference

### Event Buses

| Command | Description |
|---------|-------------|
| `aws events create-event-bus` | Create event bus |
| `aws events delete-event-bus` | Delete event bus |
| `aws events list-event-buses` | List event buses |
| `aws events describe-event-bus` | Get event bus details |

### Rules

| Command | Description |
|---------|-------------|
| `aws events put-rule` | Create or update rule |
| `aws events delete-rule` | Delete rule |
| `aws events list-rules` | List rules |
| `aws events describe-rule` | Get rule details |
| `aws events enable-rule` | Enable rule |
| `aws events disable-rule` | Disable rule |

### Targets

| Command | Description |
|---------|-------------|
| `aws events put-targets` | Add targets to rule |
| `aws events remove-targets` | Remove targets |
| `aws events list-targets-by-rule` | List rule targets |

### Events

| Command | Description |
|---------|-------------|
| `aws events put-events` | Publish events |

## Best Practices

### Event Design

- **Use meaningful source names** — `company.service.component`
- **Use descriptive detail-types** — `Order Created`, `User Signed Up`
- **Include correlation IDs** for tracing
- **Keep events small** (< 256 KB)
- **Use versioning** for event schemas

```python
# Good event structure
{
    'Source': 'mycompany.orders.api',
    'DetailType': 'Order Created',
    'Detail': json.dumps({
        'version': '1.0',
        'correlation_id': 'req-abc-123',
        'timestamp': '2024-01-15T10:30:00Z',
        'order_id': '12345',
        'data': {...}
    })
}
```

### Reliability

- **Use DLQs** for failed deliveries
- **Implement idempotency** in consumers
- **Monitor failed invocations**
- **Use archive and replay** for recovery

### Security

- **Use resource policies** to control access
- **Enable encryption** with KMS
- **Use IAM roles** for targets

### Cost Optimization

- **Use specific event patterns** to reduce matches
- **Batch events** when publishing (up to 10 per call)
- **Archive selectively** — not all events

## Troubleshooting

### Rule Not Triggering

**Debug:**

```bash
# Check rule status
aws events describe-rule --name my-rule

# Check targets
aws events list-targets-by-rule --rule my-rule

# Test event pattern
aws events test-event-pattern \
  --event-pattern '{"source": ["my-app"]}' \
  --event '{"source": "my-app", "detail-type": "Test"}'
```

**Common causes:**
- Rule disabled
- Event pattern doesn't match
- Target permissions missing

### Lambda Not Invoked

**Check Lambda permissions:**

```bash
aws lambda get-policy --function-name MyFunction
```

**Required permission:**

```json
{
  "Principal": "events.amazonaws.com",
  "Action": "lambda:InvokeFunction",
  "Resource": "function-arn",
  "Condition": {
    "ArnLike": {
      "AWS:SourceArn": "rule-arn"
    }
  }
}
```

### Events Not Reaching Custom Bus

**Check:**
- Publishing to correct bus name
- Event format is valid JSON
- Put events has proper permissions

```bash
# Test publish
aws events put-events \
  --entries '[{
    "Source": "test",
    "DetailType": "Test Event",
    "Detail": "{}",
    "EventBusName": "my-app-events"
  }]'
```

### Viewing Failed Events

```bash
# Enable CloudWatch metrics
aws events put-rule \
  --name my-rule \
  --event-pattern '...' \
  --state ENABLED

# Check FailedInvocations metric
aws cloudwatch get-metric-statistics \
  --namespace AWS/Events \
  --metric-name FailedInvocations \
  --dimensions Name=RuleName,Value=my-rule \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum
```

## References

- [EventBridge User Guide](https://docs.aws.amazon.com/eventbridge/latest/userguide/)
- [EventBridge API Reference](https://docs.aws.amazon.com/eventbridge/latest/APIReference/)
- [EventBridge CLI Reference](https://docs.aws.amazon.com/cli/latest/reference/events/)
- [boto3 EventBridge](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/events.html)
- [Event Pattern Reference](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-patterns.html)
