# Lambda Debugging Guide

Techniques for debugging and troubleshooting Lambda functions.

## CloudWatch Logs

### View Logs

```bash
# Get log group
aws logs describe-log-groups \
  --log-group-name-prefix /aws/lambda/MyFunction

# Get recent log streams
aws logs describe-log-streams \
  --log-group-name /aws/lambda/MyFunction \
  --order-by LastEventTime \
  --descending \
  --limit 5

# View log events
aws logs get-log-events \
  --log-group-name /aws/lambda/MyFunction \
  --log-stream-name '2024/01/15/[$LATEST]abc123' \
  --limit 100
```

### Filter Logs

```bash
# Find errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/MyFunction \
  --filter-pattern "ERROR" \
  --start-time $(date -d '1 hour ago' +%s000)

# Find specific request
aws logs filter-log-events \
  --log-group-name /aws/lambda/MyFunction \
  --filter-pattern "request-id-12345"
```

### CloudWatch Logs Insights

```bash
# Query for errors with context
aws logs start-query \
  --log-group-name /aws/lambda/MyFunction \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s) \
  --query-string '
    fields @timestamp, @message, @requestId
    | filter @message like /ERROR/
    | sort @timestamp desc
    | limit 50
  '
```

Common queries:

```sql
-- Cold starts
fields @timestamp, @duration, @billedDuration
| filter @type = "REPORT"
| filter @initDuration > 0
| sort @timestamp desc
| limit 50

-- Slow invocations
fields @timestamp, @requestId, @duration
| filter @type = "REPORT"
| filter @duration > 1000
| sort @duration desc
| limit 20

-- Memory usage
fields @timestamp, @requestId, @maxMemoryUsed, @memorySize
| filter @type = "REPORT"
| stats avg(@maxMemoryUsed), max(@maxMemoryUsed), avg(@memorySize) by bin(1h)

-- Error rate
fields @timestamp
| filter @type = "REPORT"
| stats count(*) as total,
        sum(strcontains(@message, "Error")) as errors,
        sum(strcontains(@message, "Error")) * 100.0 / count(*) as errorRate
  by bin(5m)
```

## X-Ray Tracing

### Enable X-Ray

```bash
aws lambda update-function-configuration \
  --function-name MyFunction \
  --tracing-config Mode=Active
```

### Instrument Code

```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

# Patch AWS SDK calls
patch_all()

def handler(event, context):
    # Create custom subsegment
    with xray_recorder.in_subsegment('process_data') as subsegment:
        subsegment.put_annotation('user_id', event.get('user_id'))
        result = process_data(event)

    return result
```

### Query Traces

```bash
# Get trace summaries
aws xray get-trace-summaries \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --filter-expression 'service(id(name: "MyFunction")) AND responsetime > 1'
```

## Local Testing

### SAM Local

```bash
# Invoke locally
sam local invoke MyFunction --event event.json

# Start local API
sam local start-api

# Debug with IDE
sam local invoke MyFunction --event event.json --debug-port 5678
```

### Docker Lambda Runtime

```bash
# Run function locally
docker run --rm \
  -v $(pwd):/var/task \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  public.ecr.aws/lambda/python:3.12 \
  lambda_function.handler '{"key": "value"}'
```

### Unit Testing

```python
import json
import pytest
from unittest.mock import patch, MagicMock

# Import handler
from lambda_function import handler

class TestHandler:
    def test_successful_request(self):
        event = {"body": json.dumps({"name": "test"})}
        context = MagicMock()

        result = handler(event, context)

        assert result["statusCode"] == 200

    @patch('lambda_function.dynamodb')
    def test_dynamo_error(self, mock_dynamo):
        mock_dynamo.Table.return_value.get_item.side_effect = Exception("DB Error")

        event = {"id": "123"}
        context = MagicMock()

        result = handler(event, context)

        assert result["statusCode"] == 500
```

## Common Issues

### Timeout Debugging

```python
import time
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    start = time.time()

    # Log remaining time periodically
    def check_time(operation):
        elapsed = time.time() - start
        remaining = context.get_remaining_time_in_millis() / 1000
        logger.info(f"{operation}: elapsed={elapsed:.2f}s, remaining={remaining:.2f}s")

    check_time("start")

    result1 = step1()
    check_time("after step1")

    result2 = step2()
    check_time("after step2")

    return {"statusCode": 200}
```

### Memory Issues

```python
import sys
import tracemalloc

def handler(event, context):
    tracemalloc.start()

    # Your code here
    result = process(event)

    current, peak = tracemalloc.get_traced_memory()
    print(f"Current memory: {current / 1024 / 1024:.2f} MB")
    print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")
    tracemalloc.stop()

    return result
```

### Connection Issues

```python
import socket
import urllib.request

def handler(event, context):
    # Test DNS resolution
    try:
        ip = socket.gethostbyname('example.com')
        print(f"DNS resolved: example.com -> {ip}")
    except socket.gaierror as e:
        print(f"DNS failed: {e}")

    # Test HTTP connectivity
    try:
        response = urllib.request.urlopen('https://example.com', timeout=5)
        print(f"HTTP status: {response.status}")
    except Exception as e:
        print(f"HTTP failed: {e}")

    return {"statusCode": 200}
```

## Structured Logging

### AWS Lambda Powertools

```python
from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging import correlation_paths

logger = Logger(service="my-service")

@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
def handler(event, context):
    logger.info("Processing request", extra={
        "user_id": event.get("user_id"),
        "action": "process"
    })

    try:
        result = process(event)
        logger.info("Success", extra={"result": result})
        return {"statusCode": 200, "body": json.dumps(result)}
    except Exception as e:
        logger.exception("Failed to process")
        return {"statusCode": 500}
```

### JSON Logging

```python
import json
import logging

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "function": record.funcName,
        }
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_data)

logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

## Debugging Event Sources

### SQS Events

```python
def handler(event, context):
    for record in event['Records']:
        message_id = record['messageId']
        body = record['body']

        print(f"Processing message {message_id}")
        print(f"Body: {body}")
        print(f"Attributes: {record.get('messageAttributes', {})}")

        try:
            process_message(body)
        except Exception as e:
            print(f"Failed to process {message_id}: {e}")
            raise  # Message goes to DLQ
```

### API Gateway Events

```python
def handler(event, context):
    print(f"HTTP Method: {event['httpMethod']}")
    print(f"Path: {event['path']}")
    print(f"Headers: {json.dumps(event.get('headers', {}))}")
    print(f"Query: {json.dumps(event.get('queryStringParameters', {}))}")
    print(f"Body: {event.get('body', '')}")

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Debug info logged"})
    }
```

## Error Handling

```python
import json
from aws_lambda_powertools import Logger

logger = Logger()

class ProcessingError(Exception):
    """Custom application error"""
    pass

def handler(event, context):
    try:
        result = process(event)
        return {
            "statusCode": 200,
            "body": json.dumps(result)
        }
    except ProcessingError as e:
        logger.warning(f"Processing error: {e}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)})
        }
    except Exception as e:
        logger.exception("Unexpected error")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
```
