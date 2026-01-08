---
name: api-gateway
description: AWS API Gateway for REST and HTTP API management. Use when creating APIs, configuring integrations, setting up authorization, managing stages, implementing rate limiting, or troubleshooting API issues.
last_updated: "2026-01-07"
doc_source: https://docs.aws.amazon.com/apigateway/latest/developerguide/
---

# AWS API Gateway

Amazon API Gateway is a fully managed service for creating, publishing, and securing APIs at any scale. Supports REST APIs, HTTP APIs, and WebSocket APIs.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Common Patterns](#common-patterns)
- [CLI Reference](#cli-reference)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [References](#references)

## Core Concepts

### API Types

| Type | Description | Use Case |
|------|-------------|----------|
| **HTTP API** | Low-latency, cost-effective | Simple APIs, Lambda proxy |
| **REST API** | Full-featured, more control | Complex APIs, transformation |
| **WebSocket API** | Bidirectional communication | Real-time apps, chat |

### Key Components

- **Resources**: URL paths (/users, /orders/{id})
- **Methods**: HTTP verbs (GET, POST, PUT, DELETE)
- **Integrations**: Backend connections (Lambda, HTTP, AWS services)
- **Stages**: Deployment environments (dev, prod)

### Integration Types

| Type | Description |
|------|-------------|
| **Lambda Proxy** | Pass-through to Lambda (recommended) |
| **Lambda Custom** | Transform request/response |
| **HTTP Proxy** | Pass-through to HTTP endpoint |
| **AWS Service** | Direct integration with AWS services |
| **Mock** | Return static response |

## Common Patterns

### Create HTTP API with Lambda

**AWS CLI:**

```bash
# Create HTTP API
aws apigatewayv2 create-api \
  --name my-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:us-east-1:123456789012:function:MyFunction

# Get API endpoint
aws apigatewayv2 get-api --api-id abc123 --query 'ApiEndpoint'
```

**SAM Template:**

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  MyApi:
    Type: AWS::Serverless::HttpApi
    Properties:
      StageName: prod

  MyFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: app.handler
      Runtime: python3.12
      Events:
        ApiEvent:
          Type: HttpApi
          Properties:
            ApiId: !Ref MyApi
            Path: /items
            Method: GET
```

### Create REST API with Lambda Proxy

```bash
# Create REST API
aws apigateway create-rest-api \
  --name my-rest-api \
  --endpoint-configuration types=REGIONAL

API_ID=abc123

# Get root resource ID
ROOT_ID=$(aws apigateway get-resources --rest-api-id $API_ID --query 'items[0].id' --output text)

# Create resource
aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part items

RESOURCE_ID=xyz789

# Create method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method GET \
  --authorization-type NONE

# Create Lambda integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:123456789012:function:MyFunction/invocations

# Deploy to stage
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod
```

### Lambda Handler for API Gateway

```python
import json

def handler(event, context):
    # HTTP API event
    http_method = event.get('requestContext', {}).get('http', {}).get('method')
    path = event.get('rawPath', '')
    query_params = event.get('queryStringParameters', {})
    body = event.get('body', '')

    if body and event.get('isBase64Encoded'):
        import base64
        body = base64.b64decode(body).decode('utf-8')

    # Process request
    response_body = {'message': 'Success', 'path': path}

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(response_body)
    }
```

### Configure CORS

**HTTP API:**

```bash
aws apigatewayv2 update-api \
  --api-id abc123 \
  --cors-configuration '{
    "AllowOrigins": ["https://example.com"],
    "AllowMethods": ["GET", "POST", "PUT", "DELETE"],
    "AllowHeaders": ["Content-Type", "Authorization"],
    "MaxAge": 86400
  }'
```

**REST API:**

```bash
# Enable CORS on resource
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method OPTIONS \
  --authorization-type NONE

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method OPTIONS \
  --type MOCK \
  --request-templates '{"application/json": "{\"statusCode\": 200}"}'

aws apigateway put-method-response \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters '{
    "method.response.header.Access-Control-Allow-Headers": true,
    "method.response.header.Access-Control-Allow-Methods": true,
    "method.response.header.Access-Control-Allow-Origin": true
  }'

aws apigateway put-integration-response \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters '{
    "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,Authorization'\''",
    "method.response.header.Access-Control-Allow-Methods": "'\''GET,POST,PUT,DELETE,OPTIONS'\''",
    "method.response.header.Access-Control-Allow-Origin": "'\''*'\''"
  }'
```

### JWT Authorization (HTTP API)

```bash
aws apigatewayv2 create-authorizer \
  --api-id abc123 \
  --name jwt-authorizer \
  --authorizer-type JWT \
  --identity-source '$request.header.Authorization' \
  --jwt-configuration '{
    "Issuer": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_abc123",
    "Audience": ["client-id"]
  }'
```

## CLI Reference

### HTTP API (apigatewayv2)

| Command | Description |
|---------|-------------|
| `aws apigatewayv2 create-api` | Create API |
| `aws apigatewayv2 get-apis` | List APIs |
| `aws apigatewayv2 create-route` | Create route |
| `aws apigatewayv2 create-integration` | Create integration |
| `aws apigatewayv2 create-stage` | Create stage |
| `aws apigatewayv2 create-authorizer` | Create authorizer |

### REST API (apigateway)

| Command | Description |
|---------|-------------|
| `aws apigateway create-rest-api` | Create API |
| `aws apigateway get-rest-apis` | List APIs |
| `aws apigateway create-resource` | Create resource |
| `aws apigateway put-method` | Create method |
| `aws apigateway put-integration` | Create integration |
| `aws apigateway create-deployment` | Deploy API |

## Best Practices

### Performance

- **Use HTTP APIs** for simple use cases (70% cheaper, lower latency)
- **Enable caching** for REST APIs
- **Use regional endpoints** unless global distribution needed
- **Implement pagination** for list endpoints

### Security

- **Use authorization** on all endpoints
- **Enable WAF** for REST APIs
- **Use API keys** for rate limiting (not authentication)
- **Enable access logging**
- **Use HTTPS only**

### Reliability

- **Set up throttling** to protect backends
- **Configure timeout** appropriately
- **Use canary deployments** for updates
- **Monitor with CloudWatch**

## Troubleshooting

### 403 Forbidden

**Causes:**
- Missing authorization
- Invalid API key
- WAF blocking
- Resource policy denying

**Debug:**

```bash
# Check API key
aws apigateway get-api-key --api-key abc123 --include-value

# Check authorizer
aws apigatewayv2 get-authorizer --api-id abc123 --authorizer-id xyz789
```

### 502 Bad Gateway

**Causes:**
- Lambda error
- Integration timeout
- Invalid response format

**Lambda response format:**

```python
# Correct format
return {
    'statusCode': 200,
    'headers': {'Content-Type': 'application/json'},
    'body': json.dumps({'message': 'success'})
}

# Wrong - missing statusCode
return {'message': 'success'}
```

### 504 Gateway Timeout

**Causes:**
- Backend timeout (Lambda max 29 seconds for REST API)
- Integration timeout too short

**Solutions:**
- Increase Lambda timeout
- Use async processing for long operations
- Increase integration timeout (max 29s for REST, 30s for HTTP)

### CORS Errors

**Debug:**
- Check OPTIONS method exists
- Verify headers in response
- Check origin matches allowed origins

## References

- [API Gateway Developer Guide](https://docs.aws.amazon.com/apigateway/latest/developerguide/)
- [API Gateway REST API Reference](https://docs.aws.amazon.com/apigateway/latest/api/)
- [API Gateway CLI Reference](https://docs.aws.amazon.com/cli/latest/reference/apigateway/)
- [boto3 API Gateway](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigateway.html)
