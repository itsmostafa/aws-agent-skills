---
name: dynamodb
description: AWS DynamoDB NoSQL database for scalable data storage. Use when designing table schemas, writing queries, configuring indexes, managing capacity, implementing single-table design, or troubleshooting performance issues.
last_updated: "2026-01-07"
doc_source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/
---

# AWS DynamoDB

Amazon DynamoDB is a fully managed NoSQL database service providing fast, predictable performance at any scale. It supports key-value and document data structures.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Common Patterns](#common-patterns)
- [CLI Reference](#cli-reference)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [References](#references)

## Core Concepts

### Keys

| Key Type | Description |
|----------|-------------|
| **Partition Key (PK)** | Required. Determines data distribution |
| **Sort Key (SK)** | Optional. Enables range queries within partition |
| **Composite Key** | PK + SK combination |

### Secondary Indexes

| Index Type | Description |
|------------|-------------|
| **GSI (Global Secondary Index)** | Different PK/SK, separate throughput, eventually consistent |
| **LSI (Local Secondary Index)** | Same PK, different SK, shares table throughput, strongly consistent option |

### Capacity Modes

| Mode | Use Case |
|------|----------|
| **On-Demand** | Unpredictable traffic, pay-per-request |
| **Provisioned** | Predictable traffic, lower cost, can use auto-scaling |

## Common Patterns

### Create a Table

**AWS CLI:**

```bash
aws dynamodb create-table \
  --table-name Users \
  --attribute-definitions \
    AttributeName=PK,AttributeType=S \
    AttributeName=SK,AttributeType=S \
  --key-schema \
    AttributeName=PK,KeyType=HASH \
    AttributeName=SK,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
```

**boto3:**

```python
import boto3

dynamodb = boto3.resource('dynamodb')

table = dynamodb.create_table(
    TableName='Users',
    KeySchema=[
        {'AttributeName': 'PK', 'KeyType': 'HASH'},
        {'AttributeName': 'SK', 'KeyType': 'RANGE'}
    ],
    AttributeDefinitions=[
        {'AttributeName': 'PK', 'AttributeType': 'S'},
        {'AttributeName': 'SK', 'AttributeType': 'S'}
    ],
    BillingMode='PAY_PER_REQUEST'
)

table.wait_until_exists()
```

### Basic CRUD Operations

```python
import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Users')

# Put item
table.put_item(
    Item={
        'PK': 'USER#123',
        'SK': 'PROFILE',
        'name': 'John Doe',
        'email': 'john@example.com',
        'created_at': '2024-01-15T10:30:00Z'
    }
)

# Get item
response = table.get_item(
    Key={'PK': 'USER#123', 'SK': 'PROFILE'}
)
item = response.get('Item')

# Update item
table.update_item(
    Key={'PK': 'USER#123', 'SK': 'PROFILE'},
    UpdateExpression='SET #name = :name, updated_at = :updated',
    ExpressionAttributeNames={'#name': 'name'},
    ExpressionAttributeValues={
        ':name': 'John Smith',
        ':updated': '2024-01-16T10:30:00Z'
    }
)

# Delete item
table.delete_item(
    Key={'PK': 'USER#123', 'SK': 'PROFILE'}
)
```

### Query Operations

```python
# Query by partition key
response = table.query(
    KeyConditionExpression=Key('PK').eq('USER#123')
)

# Query with sort key condition
response = table.query(
    KeyConditionExpression=Key('PK').eq('USER#123') & Key('SK').begins_with('ORDER#')
)

# Query with filter
response = table.query(
    KeyConditionExpression=Key('PK').eq('USER#123'),
    FilterExpression=Attr('status').eq('active')
)

# Query with projection
response = table.query(
    KeyConditionExpression=Key('PK').eq('USER#123'),
    ProjectionExpression='PK, SK, #name, email',
    ExpressionAttributeNames={'#name': 'name'}
)

# Paginated query
paginator = dynamodb.meta.client.get_paginator('query')
for page in paginator.paginate(
    TableName='Users',
    KeyConditionExpression='PK = :pk',
    ExpressionAttributeValues={':pk': {'S': 'USER#123'}}
):
    for item in page['Items']:
        print(item)
```

### Batch Operations

```python
# Batch write (up to 25 items)
with table.batch_writer() as batch:
    for i in range(100):
        batch.put_item(Item={
            'PK': f'USER#{i}',
            'SK': 'PROFILE',
            'name': f'User {i}'
        })

# Batch get (up to 100 items)
dynamodb = boto3.resource('dynamodb')
response = dynamodb.batch_get_item(
    RequestItems={
        'Users': {
            'Keys': [
                {'PK': 'USER#1', 'SK': 'PROFILE'},
                {'PK': 'USER#2', 'SK': 'PROFILE'}
            ]
        }
    }
)
```

### Create GSI

```bash
aws dynamodb update-table \
  --table-name Users \
  --attribute-definitions AttributeName=email,AttributeType=S \
  --global-secondary-index-updates '[
    {
      "Create": {
        "IndexName": "email-index",
        "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
        "Projection": {"ProjectionType": "ALL"}
      }
    }
  ]'
```

### Conditional Writes

```python
from botocore.exceptions import ClientError

# Only put if item doesn't exist
try:
    table.put_item(
        Item={'PK': 'USER#123', 'SK': 'PROFILE', 'name': 'John'},
        ConditionExpression='attribute_not_exists(PK)'
    )
except ClientError as e:
    if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
        print("Item already exists")

# Optimistic locking with version
table.update_item(
    Key={'PK': 'USER#123', 'SK': 'PROFILE'},
    UpdateExpression='SET #name = :name, version = version + :inc',
    ConditionExpression='version = :current_version',
    ExpressionAttributeNames={'#name': 'name'},
    ExpressionAttributeValues={
        ':name': 'New Name',
        ':inc': 1,
        ':current_version': 5
    }
)
```

## CLI Reference

### Table Operations

| Command | Description |
|---------|-------------|
| `aws dynamodb create-table` | Create table |
| `aws dynamodb describe-table` | Get table info |
| `aws dynamodb update-table` | Modify table/indexes |
| `aws dynamodb delete-table` | Delete table |
| `aws dynamodb list-tables` | List all tables |

### Item Operations

| Command | Description |
|---------|-------------|
| `aws dynamodb put-item` | Create/replace item |
| `aws dynamodb get-item` | Read single item |
| `aws dynamodb update-item` | Update item attributes |
| `aws dynamodb delete-item` | Delete item |
| `aws dynamodb query` | Query by key |
| `aws dynamodb scan` | Full table scan |

### Batch Operations

| Command | Description |
|---------|-------------|
| `aws dynamodb batch-write-item` | Batch write (25 max) |
| `aws dynamodb batch-get-item` | Batch read (100 max) |
| `aws dynamodb transact-write-items` | Transaction write |
| `aws dynamodb transact-get-items` | Transaction read |

## Best Practices

### Data Modeling

- **Design for access patterns** — know your queries before designing
- **Use composite keys** — PK for grouping, SK for sorting/filtering
- **Prefer query over scan** — scans are expensive
- **Use sparse indexes** — only items with index attributes are indexed
- **Consider single-table design** for related entities

### Performance

- **Distribute partition keys evenly** — avoid hot partitions
- **Use batch operations** to reduce API calls
- **Enable DAX** for read-heavy workloads
- **Use projections** to reduce data transfer

### Cost Optimization

- **Use on-demand** for variable workloads
- **Use provisioned + auto-scaling** for predictable workloads
- **Set TTL** for expiring data
- **Archive to S3** for cold data

## Troubleshooting

### Throttling

**Symptom:** `ProvisionedThroughputExceededException`

**Causes:**
- Hot partition (uneven key distribution)
- Burst traffic exceeding capacity
- GSI throttling affecting base table

**Solutions:**

```python
# Use exponential backoff
import time
from botocore.config import Config

config = Config(
    retries={
        'max_attempts': 10,
        'mode': 'adaptive'
    }
)
dynamodb = boto3.resource('dynamodb', config=config)
```

### Hot Partitions

**Debug:**

```bash
# Check consumed capacity by partition
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=Users \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 60 \
  --statistics Sum
```

**Solutions:**
- Add randomness to partition keys
- Use write sharding
- Distribute access across partitions

### Query Returns No Items

**Debug checklist:**
1. Verify key values exactly match (case-sensitive)
2. Check key types (S, N, B)
3. Confirm table/index name
4. Review filter expressions (they apply AFTER read)

### Scan Performance

**Issue:** Scans are slow and expensive

**Solutions:**
- Use parallel scan for large tables
- Create GSI for the access pattern
- Use filter expressions to reduce returned data

```python
# Parallel scan
import concurrent.futures

def scan_segment(segment, total_segments):
    return table.scan(
        Segment=segment,
        TotalSegments=total_segments
    )

with concurrent.futures.ThreadPoolExecutor() as executor:
    results = list(executor.map(
        lambda s: scan_segment(s, 4),
        range(4)
    ))
```

## References

- [DynamoDB Developer Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/)
- [DynamoDB API Reference](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/)
- [DynamoDB CLI Reference](https://docs.aws.amazon.com/cli/latest/reference/dynamodb/)
- [boto3 DynamoDB](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
