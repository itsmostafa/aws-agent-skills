# EventBridge Event Patterns

Comprehensive guide to event pattern matching.

## Pattern Syntax

### Exact Match

```json
{
  "source": ["my-app.orders"]
}
```

### Multiple Values (OR)

```json
{
  "source": ["my-app.orders", "my-app.inventory"]
}
```

### Nested Fields

```json
{
  "detail": {
    "order": {
      "status": ["completed", "cancelled"]
    }
  }
}
```

### Prefix Match

```json
{
  "source": [{"prefix": "my-app."}]
}
```

### Suffix Match

```json
{
  "detail": {
    "filename": [{"suffix": ".pdf"}]
  }
}
```

### Anything-But

```json
{
  "detail": {
    "status": [{"anything-but": ["test", "draft"]}]
  }
}
```

### Numeric Matching

```json
{
  "detail": {
    "price": [{"numeric": [">=", 100]}],
    "quantity": [{"numeric": [">", 0, "<=", 100]}]
  }
}
```

### Exists

```json
{
  "detail": {
    "customer_id": [{"exists": true}],
    "discount_code": [{"exists": false}]
  }
}
```

### IP Address Matching

```json
{
  "detail": {
    "source_ip": [{"cidr": "10.0.0.0/8"}]
  }
}
```

### Empty Array/String

```json
{
  "detail": {
    "tags": [{"equals-ignore-case": ""}]
  }
}
```

### Case-Insensitive

```json
{
  "detail": {
    "action": [{"equals-ignore-case": "CREATE"}]
  }
}
```

### Wildcard

```json
{
  "detail": {
    "key": [{"wildcard": "prod-*-us-east-1"}]
  }
}
```

## AWS Service Event Patterns

### EC2 State Changes

```json
{
  "source": ["aws.ec2"],
  "detail-type": ["EC2 Instance State-change Notification"],
  "detail": {
    "state": ["running", "stopped", "terminated"]
  }
}
```

### S3 Object Events

```json
{
  "source": ["aws.s3"],
  "detail-type": ["Object Created"],
  "detail": {
    "bucket": {
      "name": ["my-bucket"]
    },
    "object": {
      "key": [{"prefix": "uploads/"}]
    }
  }
}
```

### CodePipeline State Changes

```json
{
  "source": ["aws.codepipeline"],
  "detail-type": ["CodePipeline Pipeline Execution State Change"],
  "detail": {
    "state": ["FAILED", "SUCCEEDED"],
    "pipeline": ["my-pipeline"]
  }
}
```

### ECS Task State Changes

```json
{
  "source": ["aws.ecs"],
  "detail-type": ["ECS Task State Change"],
  "detail": {
    "clusterArn": [{"suffix": "/my-cluster"}],
    "lastStatus": ["RUNNING", "STOPPED"]
  }
}
```

### CloudWatch Alarm State Changes

```json
{
  "source": ["aws.cloudwatch"],
  "detail-type": ["CloudWatch Alarm State Change"],
  "detail": {
    "state": {
      "value": ["ALARM"]
    }
  }
}
```

### RDS Events

```json
{
  "source": ["aws.rds"],
  "detail-type": ["RDS DB Instance Event"],
  "detail": {
    "EventCategories": ["failover", "failure"]
  }
}
```

### Lambda Function Events

```json
{
  "source": ["aws.lambda"],
  "detail-type": ["Lambda Function Invocation Result - Failure"]
}
```

### Secrets Manager Rotation

```json
{
  "source": ["aws.secretsmanager"],
  "detail-type": ["AWS API Call via CloudTrail"],
  "detail": {
    "eventSource": ["secretsmanager.amazonaws.com"],
    "eventName": ["RotateSecret"]
  }
}
```

## Complex Patterns

### Combined Conditions

```json
{
  "source": ["my-app.orders"],
  "detail-type": ["Order Created"],
  "detail": {
    "order": {
      "total": [{"numeric": [">=", 100]}],
      "region": ["us-east-1", "us-west-2"],
      "priority": [{"anything-but": ["low"]}],
      "expedited": [{"exists": true}]
    }
  }
}
```

### Content-Based Routing

```json
// Route high-value orders
{
  "source": ["ecommerce.orders"],
  "detail-type": ["Order Placed"],
  "detail": {
    "total": [{"numeric": [">=", 1000]}],
    "customer_tier": ["premium", "enterprise"]
  }
}

// Route standard orders
{
  "source": ["ecommerce.orders"],
  "detail-type": ["Order Placed"],
  "detail": {
    "total": [{"numeric": ["<", 1000]}]
  }
}
```

## Event Structure

### Standard Event Format

```json
{
  "version": "0",
  "id": "12345678-1234-1234-1234-123456789012",
  "detail-type": "Order Created",
  "source": "my-app.orders",
  "account": "123456789012",
  "time": "2024-01-15T10:30:00Z",
  "region": "us-east-1",
  "resources": [
    "arn:aws:dynamodb:us-east-1:123456789012:table/Orders"
  ],
  "detail": {
    "order_id": "12345",
    "customer_id": "cust-789",
    "items": [...],
    "total": 99.99
  }
}
```

### Custom Event with Metadata

```python
import boto3
import json
from datetime import datetime

events = boto3.client('events')

events.put_events(
    Entries=[{
        'Source': 'mycompany.orders.api',
        'DetailType': 'Order Created',
        'Time': datetime.utcnow(),
        'Resources': [
            f'arn:aws:dynamodb:us-east-1:123456789012:table/Orders/item/{order_id}'
        ],
        'Detail': json.dumps({
            'version': '1.0',
            'metadata': {
                'correlation_id': correlation_id,
                'trace_id': trace_id,
                'user_agent': user_agent
            },
            'data': {
                'order_id': order_id,
                'customer_id': customer_id,
                'items': items,
                'total': total
            }
        }),
        'EventBusName': 'orders-bus'
    }]
)
```

## Input Transformation

### Transform Event for Target

```bash
aws events put-targets \
  --rule my-rule \
  --targets '[{
    "Id": "1",
    "Arn": "arn:aws:lambda:us-east-1:123456789012:function:ProcessOrder",
    "InputTransformer": {
      "InputPathsMap": {
        "orderId": "$.detail.order_id",
        "customerId": "$.detail.customer_id",
        "total": "$.detail.total"
      },
      "InputTemplate": "{\"order\": {\"id\": <orderId>, \"customer\": <customerId>, \"amount\": <total>}}"
    }
  }]'
```

### Pass Static Input

```json
{
  "Id": "1",
  "Arn": "arn:aws:lambda:...",
  "Input": "{\"action\": \"process\", \"source\": \"eventbridge\"}"
}
```

### Pass Matched Event

```json
{
  "Id": "1",
  "Arn": "arn:aws:lambda:...",
  "InputPath": "$.detail"
}
```

## Cross-Account Events

### Send Events to Another Account

```bash
# In source account: create rule to forward
aws events put-rule \
  --name forward-to-central \
  --event-pattern '{"source": ["my-app"]}' \
  --event-bus-name default

aws events put-targets \
  --rule forward-to-central \
  --targets '[{
    "Id": "central-bus",
    "Arn": "arn:aws:events:us-east-1:222222222222:event-bus/central-events",
    "RoleArn": "arn:aws:iam::111111111111:role/EventBridgeCrossAccountRole"
  }]'

# In target account: allow source account
aws events put-permission \
  --event-bus-name central-events \
  --action events:PutEvents \
  --principal 111111111111 \
  --statement-id allow-source-account
```

## Archive and Replay

### Create Archive

```bash
aws events create-archive \
  --archive-name order-events-archive \
  --event-source-arn arn:aws:events:us-east-1:123456789012:event-bus/orders-bus \
  --event-pattern '{"source": ["my-app.orders"]}' \
  --retention-days 30
```

### Replay Events

```bash
aws events start-replay \
  --replay-name replay-jan-15 \
  --event-source-arn arn:aws:events:us-east-1:123456789012:event-bus/orders-bus \
  --destination '{
    "Arn": "arn:aws:events:us-east-1:123456789012:event-bus/orders-bus"
  }' \
  --event-start-time 2024-01-15T00:00:00Z \
  --event-end-time 2024-01-15T23:59:59Z
```

## Testing Patterns

### Test Event Pattern Match

```bash
aws events test-event-pattern \
  --event-pattern '{
    "source": ["my-app.orders"],
    "detail": {
      "total": [{"numeric": [">=", 100]}]
    }
  }' \
  --event '{
    "source": "my-app.orders",
    "detail-type": "Order Created",
    "detail": {"order_id": "123", "total": 150}
  }'
```

Returns `true` if pattern matches.
