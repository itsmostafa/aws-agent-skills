# DynamoDB Query Patterns

Advanced query patterns and single-table design strategies.

## Single-Table Design

### Entity Modeling

Store multiple entity types in one table using composite keys:

```
PK                  SK                  Data
USER#123            PROFILE             {name, email, ...}
USER#123            ORDER#2024-001      {total, status, ...}
USER#123            ORDER#2024-002      {total, status, ...}
ORDER#2024-001      ITEM#1              {product, qty, ...}
ORDER#2024-001      ITEM#2              {product, qty, ...}
PRODUCT#ABC         METADATA            {name, price, ...}
PRODUCT#ABC         REVIEW#user-456     {rating, comment, ...}
```

### Access Patterns

| Pattern | Query |
|---------|-------|
| Get user profile | `PK = USER#123, SK = PROFILE` |
| Get user's orders | `PK = USER#123, SK begins_with ORDER#` |
| Get order items | `PK = ORDER#2024-001, SK begins_with ITEM#` |
| Get product reviews | `PK = PRODUCT#ABC, SK begins_with REVIEW#` |

## Query Examples

### Range Queries with Sort Key

```python
from boto3.dynamodb.conditions import Key

# Orders in date range
response = table.query(
    KeyConditionExpression=Key('PK').eq('USER#123') &
        Key('SK').between('ORDER#2024-01', 'ORDER#2024-12')
)

# Latest 10 orders (descending)
response = table.query(
    KeyConditionExpression=Key('PK').eq('USER#123') &
        Key('SK').begins_with('ORDER#'),
    ScanIndexForward=False,
    Limit=10
)
```

### Querying GSI

```python
# GSI: email-index (email as PK)
response = table.query(
    IndexName='email-index',
    KeyConditionExpression=Key('email').eq('john@example.com')
)

# GSI: status-created-index (status as PK, created_at as SK)
response = table.query(
    IndexName='status-created-index',
    KeyConditionExpression=Key('status').eq('pending') &
        Key('created_at').gt('2024-01-01')
)
```

### Filter Expressions

Filters apply AFTER read, so they don't reduce consumed capacity:

```python
response = table.query(
    KeyConditionExpression=Key('PK').eq('USER#123'),
    FilterExpression=Attr('status').eq('active') &
        Attr('amount').gt(100)
)
```

### Projection Expressions

Reduce data transfer by selecting specific attributes:

```python
response = table.query(
    KeyConditionExpression=Key('PK').eq('USER#123'),
    ProjectionExpression='PK, SK, #name, email',
    ExpressionAttributeNames={'#name': 'name'}  # 'name' is reserved word
)
```

## Advanced Patterns

### Hierarchical Data

Model parent-child relationships:

```
PK                  SK                          Data
ORG#acme            METADATA                    {name, ...}
ORG#acme            DEPT#engineering            {name, head, ...}
ORG#acme            DEPT#engineering#TEAM#api   {name, lead, ...}
ORG#acme            DEPT#sales                  {name, head, ...}
```

Query patterns:
```python
# All departments
table.query(
    KeyConditionExpression=Key('PK').eq('ORG#acme') &
        Key('SK').begins_with('DEPT#')
)

# Teams in engineering
table.query(
    KeyConditionExpression=Key('PK').eq('ORG#acme') &
        Key('SK').begins_with('DEPT#engineering#TEAM#')
)
```

### Inverted Index (GSI)

Enable reverse lookups:

```
Table:
PK          SK              GSI1PK      GSI1SK
USER#123    FOLLOWS#456     USER#456    FOLLOWER#123
USER#123    FOLLOWS#789     USER#789    FOLLOWER#123
```

```python
# Who does user 123 follow?
table.query(
    KeyConditionExpression=Key('PK').eq('USER#123') &
        Key('SK').begins_with('FOLLOWS#')
)

# Who follows user 456?
table.query(
    IndexName='GSI1',
    KeyConditionExpression=Key('GSI1PK').eq('USER#456') &
        Key('GSI1SK').begins_with('FOLLOWER#')
)
```

### Sparse Indexes

Only items with the GSI key are indexed:

```python
# Table: all items
# GSI: only items with 'featured' attribute

# Add item to GSI by setting the attribute
table.put_item(
    Item={
        'PK': 'PRODUCT#123',
        'SK': 'METADATA',
        'name': 'Widget',
        'featured': 'FEATURED'  # This enables GSI inclusion
    }
)

# Query featured products only
table.query(
    IndexName='featured-index',
    KeyConditionExpression=Key('featured').eq('FEATURED')
)
```

### Time-Based Data

Use sort key for time-series:

```python
# Store with ISO timestamp
table.put_item(
    Item={
        'PK': 'SENSOR#temp-001',
        'SK': '2024-01-15T10:30:00Z',
        'value': 23.5
    }
)

# Query time range
response = table.query(
    KeyConditionExpression=Key('PK').eq('SENSOR#temp-001') &
        Key('SK').between('2024-01-15T00:00:00Z', '2024-01-15T23:59:59Z')
)

# Latest reading
response = table.query(
    KeyConditionExpression=Key('PK').eq('SENSOR#temp-001'),
    ScanIndexForward=False,
    Limit=1
)
```

### Write Sharding

Distribute writes across partitions:

```python
import random

# Write with shard suffix
shard = random.randint(0, 9)
table.put_item(
    Item={
        'PK': f'COUNTER#daily#{shard}',
        'SK': '2024-01-15',
        'count': 1
    }
)

# Read aggregates all shards
total = 0
for shard in range(10):
    response = table.get_item(
        Key={
            'PK': f'COUNTER#daily#{shard}',
            'SK': '2024-01-15'
        }
    )
    if 'Item' in response:
        total += response['Item']['count']
```

## Transactions

### TransactWriteItems

```python
dynamodb = boto3.client('dynamodb')

dynamodb.transact_write_items(
    TransactItems=[
        {
            'Put': {
                'TableName': 'Users',
                'Item': {
                    'PK': {'S': 'ORDER#2024-001'},
                    'SK': {'S': 'METADATA'},
                    'total': {'N': '150.00'}
                }
            }
        },
        {
            'Update': {
                'TableName': 'Users',
                'Key': {
                    'PK': {'S': 'USER#123'},
                    'SK': {'S': 'PROFILE'}
                },
                'UpdateExpression': 'SET order_count = order_count + :inc',
                'ExpressionAttributeValues': {':inc': {'N': '1'}}
            }
        },
        {
            'Update': {
                'TableName': 'Users',
                'Key': {
                    'PK': {'S': 'PRODUCT#ABC'},
                    'SK': {'S': 'INVENTORY'}
                },
                'UpdateExpression': 'SET stock = stock - :qty',
                'ConditionExpression': 'stock >= :qty',
                'ExpressionAttributeValues': {':qty': {'N': '2'}}
            }
        }
    ]
)
```

### TransactGetItems

```python
response = dynamodb.transact_get_items(
    TransactItems=[
        {
            'Get': {
                'TableName': 'Users',
                'Key': {
                    'PK': {'S': 'USER#123'},
                    'SK': {'S': 'PROFILE'}
                }
            }
        },
        {
            'Get': {
                'TableName': 'Users',
                'Key': {
                    'PK': {'S': 'USER#123'},
                    'SK': {'S': 'SETTINGS'}
                }
            }
        }
    ]
)
```

## Pagination

### Manual Pagination

```python
items = []
last_key = None

while True:
    params = {
        'KeyConditionExpression': Key('PK').eq('USER#123'),
        'Limit': 100
    }
    if last_key:
        params['ExclusiveStartKey'] = last_key

    response = table.query(**params)
    items.extend(response['Items'])

    last_key = response.get('LastEvaluatedKey')
    if not last_key:
        break
```

### Paginator

```python
paginator = dynamodb.meta.client.get_paginator('query')

for page in paginator.paginate(
    TableName='Users',
    KeyConditionExpression='PK = :pk',
    ExpressionAttributeValues={':pk': {'S': 'USER#123'}},
    PaginationConfig={'PageSize': 100}
):
    for item in page['Items']:
        process(item)
```

## TTL (Time To Live)

### Enable TTL

```bash
aws dynamodb update-time-to-live \
  --table-name Sessions \
  --time-to-live-specification "Enabled=true, AttributeName=expires_at"
```

### Use TTL

```python
import time

# Set expiration (Unix timestamp)
table.put_item(
    Item={
        'PK': 'SESSION#abc123',
        'SK': 'DATA',
        'user_id': 'user-456',
        'expires_at': int(time.time()) + 3600  # 1 hour from now
    }
)
```

## Expression Reference

### Comparison Operators

| Operator | Usage |
|----------|-------|
| `=` | `attribute = :value` |
| `<>` | `attribute <> :value` |
| `<`, `<=`, `>`, `>=` | `attribute >= :value` |
| `BETWEEN` | `attribute BETWEEN :low AND :high` |
| `IN` | `attribute IN (:v1, :v2, :v3)` |

### Functions

| Function | Usage |
|----------|-------|
| `attribute_exists` | `attribute_exists(attr)` |
| `attribute_not_exists` | `attribute_not_exists(attr)` |
| `attribute_type` | `attribute_type(attr, :type)` |
| `begins_with` | `begins_with(attr, :prefix)` |
| `contains` | `contains(attr, :value)` |
| `size` | `size(attr) > :size` |

### Update Operations

| Operation | Expression |
|-----------|------------|
| SET | `SET attr = :value` |
| REMOVE | `REMOVE attr` |
| ADD | `ADD attr :value` (numbers, sets) |
| DELETE | `DELETE attr :value` (sets only) |
| List append | `SET list = list_append(list, :item)` |
| Increment | `SET counter = counter + :inc` |
| If not exists | `SET attr = if_not_exists(attr, :default)` |
