# SQS Messaging Patterns

Advanced messaging patterns and configurations.

## Queue Policies

### Allow SNS to Send Messages

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "sns.amazonaws.com"
      },
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

### Allow S3 to Send Messages

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "s3.amazonaws.com"
      },
      "Action": "sqs:SendMessage",
      "Resource": "arn:aws:sqs:us-east-1:123456789012:my-queue",
      "Condition": {
        "ArnLike": {
          "aws:SourceArn": "arn:aws:s3:::my-bucket"
        }
      }
    }
  ]
}
```

### Cross-Account Access

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::111111111111:root"
      },
      "Action": [
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage"
      ],
      "Resource": "arn:aws:sqs:us-east-1:123456789012:my-queue"
    }
  ]
}
```

## Encryption

### Server-Side Encryption (SSE-SQS)

```bash
aws sqs create-queue \
  --queue-name my-queue \
  --attributes '{
    "SqsManagedSseEnabled": "true"
  }'
```

### SSE with KMS

```bash
aws sqs create-queue \
  --queue-name my-queue \
  --attributes '{
    "KmsMasterKeyId": "alias/my-key",
    "KmsDataKeyReusePeriodSeconds": "300"
  }'
```

## FIFO Queue Patterns

### Message Groups for Parallel Processing

```python
import boto3
import json

sqs = boto3.client('sqs')
queue_url = 'https://sqs.us-east-1.amazonaws.com/123456789012/orders.fifo'

# Different customers can be processed in parallel
# Same customer maintains order
orders = [
    {'customer_id': 'A', 'order_id': '1'},
    {'customer_id': 'B', 'order_id': '2'},
    {'customer_id': 'A', 'order_id': '3'},  # After order 1
]

for order in orders:
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(order),
        MessageGroupId=order['customer_id'],  # Group by customer
        MessageDeduplicationId=f"{order['customer_id']}-{order['order_id']}"
    )
```

### High Throughput FIFO

```bash
aws sqs create-queue \
  --queue-name my-queue.fifo \
  --attributes '{
    "FifoQueue": "true",
    "ContentBasedDeduplication": "true",
    "DeduplicationScope": "messageGroup",
    "FifoThroughputLimit": "perMessageGroupId"
  }'
```

## Batch Processing with Lambda

### Partial Batch Failure

```python
def handler(event, context):
    batch_item_failures = []

    for record in event['Records']:
        try:
            body = json.loads(record['body'])
            process_message(body)
        except Exception as e:
            # Report this specific message as failed
            batch_item_failures.append({
                'itemIdentifier': record['messageId']
            })

    return {'batchItemFailures': batch_item_failures}
```

### Configure Lambda for Partial Failures

```bash
aws lambda update-event-source-mapping \
  --uuid <mapping-uuid> \
  --function-response-types ReportBatchItemFailures
```

## Visibility Timeout Management

### Extend Visibility During Processing

```python
import boto3
import time
import threading

sqs = boto3.client('sqs')

def extend_visibility(queue_url, receipt_handle, stop_event):
    """Background thread to extend visibility."""
    while not stop_event.wait(timeout=30):
        try:
            sqs.change_message_visibility(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle,
                VisibilityTimeout=60
            )
        except Exception:
            break

def process_long_running_message(queue_url, message):
    stop_event = threading.Event()

    # Start background visibility extender
    extender = threading.Thread(
        target=extend_visibility,
        args=(queue_url, message['ReceiptHandle'], stop_event)
    )
    extender.start()

    try:
        # Long processing...
        do_long_processing(message['Body'])

        # Delete on success
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=message['ReceiptHandle']
        )
    finally:
        stop_event.set()
        extender.join()
```

## Message Delay Patterns

### Per-Message Delay

```python
# Delay individual message up to 15 minutes
sqs.send_message(
    QueueUrl=queue_url,
    MessageBody=json.dumps({'action': 'reminder'}),
    DelaySeconds=900  # 15 minutes
)
```

### Scheduled Processing

```python
import time

def schedule_message(queue_url, body, execute_at):
    """Schedule message for future processing."""
    delay = int(execute_at - time.time())

    if delay <= 0:
        delay = 0
    elif delay > 900:
        # For delays > 15 min, use message attribute
        # and filter on receive
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps({
                **body,
                '_execute_at': execute_at
            }),
            DelaySeconds=900  # Maximum delay
        )
        return

    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(body),
        DelaySeconds=delay
    )
```

## Monitoring

### CloudWatch Alarms

```bash
# DLQ depth alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "SQS-DLQ-NotEmpty" \
  --metric-name ApproximateNumberOfMessagesVisible \
  --namespace AWS/SQS \
  --dimensions Name=QueueName,Value=my-queue-dlq \
  --statistic Sum \
  --period 60 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:alerts

# Queue backlog alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "SQS-Queue-Backlog" \
  --metric-name ApproximateNumberOfMessagesVisible \
  --namespace AWS/SQS \
  --dimensions Name=QueueName,Value=my-queue \
  --statistic Sum \
  --period 300 \
  --threshold 1000 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 3 \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:alerts

# Age of oldest message
aws cloudwatch put-metric-alarm \
  --alarm-name "SQS-Old-Messages" \
  --metric-name ApproximateAgeOfOldestMessage \
  --namespace AWS/SQS \
  --dimensions Name=QueueName,Value=my-queue \
  --statistic Maximum \
  --period 300 \
  --threshold 3600 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:alerts
```

### Custom Metrics

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def publish_processing_metrics(queue_name, processing_time, success):
    cloudwatch.put_metric_data(
        Namespace='MyApp/SQS',
        MetricData=[
            {
                'MetricName': 'ProcessingTime',
                'Value': processing_time,
                'Unit': 'Milliseconds',
                'Dimensions': [
                    {'Name': 'QueueName', 'Value': queue_name}
                ]
            },
            {
                'MetricName': 'ProcessingSuccess' if success else 'ProcessingFailure',
                'Value': 1,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'QueueName', 'Value': queue_name}
                ]
            }
        ]
    )
```

## Request-Response Pattern

### Temporary Response Queue

```python
import boto3
import json
import uuid

sqs = boto3.client('sqs')

def send_request_with_response(request_queue_url, payload):
    # Create temporary response queue
    correlation_id = str(uuid.uuid4())
    response_queue = sqs.create_queue(
        QueueName=f'response-{correlation_id}',
        Attributes={'MessageRetentionPeriod': '300'}
    )
    response_queue_url = response_queue['QueueUrl']

    try:
        # Send request with reply-to
        sqs.send_message(
            QueueUrl=request_queue_url,
            MessageBody=json.dumps(payload),
            MessageAttributes={
                'ReplyTo': {
                    'DataType': 'String',
                    'StringValue': response_queue_url
                },
                'CorrelationId': {
                    'DataType': 'String',
                    'StringValue': correlation_id
                }
            }
        )

        # Wait for response
        response = sqs.receive_message(
            QueueUrl=response_queue_url,
            WaitTimeSeconds=20,
            MaxNumberOfMessages=1
        )

        if response.get('Messages'):
            return json.loads(response['Messages'][0]['Body'])

        return None
    finally:
        sqs.delete_queue(QueueUrl=response_queue_url)
```

## Large Message Pattern

### Using S3 for Large Payloads

```python
import boto3
import json
import uuid

s3 = boto3.client('s3')
sqs = boto3.client('sqs')

def send_large_message(queue_url, bucket, payload):
    """Send message > 256KB using S3."""
    payload_str = json.dumps(payload)

    if len(payload_str) > 200000:  # Use S3 for large payloads
        key = f'sqs-payloads/{uuid.uuid4()}.json'
        s3.put_object(Bucket=bucket, Key=key, Body=payload_str)

        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps({
                's3_bucket': bucket,
                's3_key': key
            }),
            MessageAttributes={
                'PayloadLocation': {
                    'DataType': 'String',
                    'StringValue': 's3'
                }
            }
        )
    else:
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=payload_str
        )

def receive_large_message(queue_url, bucket):
    """Receive message, fetch from S3 if needed."""
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MessageAttributeNames=['PayloadLocation'],
        MaxNumberOfMessages=1
    )

    if not response.get('Messages'):
        return None

    message = response['Messages'][0]
    attrs = message.get('MessageAttributes', {})

    if attrs.get('PayloadLocation', {}).get('StringValue') == 's3':
        pointer = json.loads(message['Body'])
        response = s3.get_object(
            Bucket=pointer['s3_bucket'],
            Key=pointer['s3_key']
        )
        body = json.loads(response['Body'].read())

        # Clean up S3 object
        s3.delete_object(Bucket=pointer['s3_bucket'], Key=pointer['s3_key'])
    else:
        body = json.loads(message['Body'])

    return body, message['ReceiptHandle']
```
