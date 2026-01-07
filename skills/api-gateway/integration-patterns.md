# API Gateway Integration Patterns

Advanced integration patterns and configurations.

## Lambda Integrations

### Proxy Integration (Recommended)

Pass entire request to Lambda:

```yaml
# SAM
Resources:
  GetItemsFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: app.handler
      Events:
        GetItems:
          Type: Api
          Properties:
            Path: /items
            Method: GET
```

Lambda receives:

```json
{
  "resource": "/items",
  "path": "/items",
  "httpMethod": "GET",
  "headers": {...},
  "queryStringParameters": {...},
  "pathParameters": {...},
  "body": "...",
  "isBase64Encoded": false
}
```

### Custom Integration

Transform request/response:

```bash
# Request template
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method POST \
  --type AWS \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-1:lambda:path/... \
  --request-templates '{
    "application/json": "{\"action\": \"$input.params(\"action\")\", \"data\": $input.json(\"$.body\")}"
  }'

# Response template
aws apigateway put-integration-response \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method POST \
  --status-code 200 \
  --response-templates '{
    "application/json": "{\"result\": $input.json(\"$.Payload\")}"
  }'
```

## AWS Service Integrations

### Direct DynamoDB Integration

```json
{
  "type": "AWS",
  "uri": "arn:aws:apigateway:us-east-1:dynamodb:action/GetItem",
  "credentials": "arn:aws:iam::123456789012:role/apigw-dynamodb-role",
  "requestTemplates": {
    "application/json": "{\"TableName\": \"Users\", \"Key\": {\"id\": {\"S\": \"$input.params('id')\"}}}"
  },
  "responses": {
    "default": {
      "statusCode": "200",
      "responseTemplates": {
        "application/json": "#set($item = $input.path('$.Item'))\n{\"id\": \"$item.id.S\", \"name\": \"$item.name.S\"}"
      }
    }
  }
}
```

### Direct SQS Integration

```json
{
  "type": "AWS",
  "uri": "arn:aws:apigateway:us-east-1:sqs:path/123456789012/my-queue",
  "credentials": "arn:aws:iam::123456789012:role/apigw-sqs-role",
  "requestParameters": {
    "integration.request.header.Content-Type": "'application/x-www-form-urlencoded'"
  },
  "requestTemplates": {
    "application/json": "Action=SendMessage&MessageBody=$util.urlEncode($input.body)"
  },
  "responses": {
    "default": {
      "statusCode": "200",
      "responseTemplates": {
        "application/json": "{\"messageId\": \"$input.path('$.SendMessageResponse.SendMessageResult.MessageId')\"}"
      }
    }
  }
}
```

### Direct Step Functions Integration

```json
{
  "type": "AWS",
  "uri": "arn:aws:apigateway:us-east-1:states:action/StartExecution",
  "credentials": "arn:aws:iam::123456789012:role/apigw-stepfunctions-role",
  "requestTemplates": {
    "application/json": "{\"input\": \"$util.escapeJavaScript($input.json('$'))\", \"stateMachineArn\": \"arn:aws:states:us-east-1:123456789012:stateMachine:MyWorkflow\"}"
  }
}
```

## HTTP Integrations

### HTTP Proxy

```bash
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method GET \
  --type HTTP_PROXY \
  --integration-http-method GET \
  --uri https://api.example.com/items
```

### HTTP with VPC Link

```bash
# Create VPC Link
aws apigateway create-vpc-link \
  --name my-vpc-link \
  --target-arns arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/net/my-nlb/abc123

# Use VPC Link in integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method GET \
  --type HTTP_PROXY \
  --connection-type VPC_LINK \
  --connection-id vpc-link-id \
  --uri http://my-nlb.internal:8080/items
```

## Request Validation

### Enable Request Validation

```bash
# Create validator
aws apigateway create-request-validator \
  --rest-api-id $API_ID \
  --name body-validator \
  --validate-request-body \
  --validate-request-parameters

# Create model
aws apigateway create-model \
  --rest-api-id $API_ID \
  --name CreateUserModel \
  --content-type application/json \
  --schema '{
    "type": "object",
    "required": ["name", "email"],
    "properties": {
      "name": {"type": "string", "minLength": 1},
      "email": {"type": "string", "format": "email"}
    }
  }'

# Apply to method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method POST \
  --authorization-type NONE \
  --request-validator-id validator-id \
  --request-models '{"application/json": "CreateUserModel"}'
```

## Authorization

### Cognito Authorizer (REST API)

```bash
aws apigateway create-authorizer \
  --rest-api-id $API_ID \
  --name cognito-authorizer \
  --type COGNITO_USER_POOLS \
  --identity-source 'method.request.header.Authorization' \
  --provider-arns arn:aws:cognito-idp:us-east-1:123456789012:userpool/us-east-1_abc123
```

### Lambda Authorizer

```bash
aws apigateway create-authorizer \
  --rest-api-id $API_ID \
  --name custom-authorizer \
  --type TOKEN \
  --authorizer-uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:123456789012:function:Authorizer/invocations \
  --identity-source 'method.request.header.Authorization' \
  --authorizer-result-ttl-in-seconds 300
```

Lambda authorizer code:

```python
def handler(event, context):
    token = event['authorizationToken']
    method_arn = event['methodArn']

    # Validate token
    if is_valid_token(token):
        principal_id = get_user_id(token)
        return generate_policy(principal_id, 'Allow', method_arn)
    else:
        raise Exception('Unauthorized')

def generate_policy(principal_id, effect, resource):
    return {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': effect,
                'Resource': resource
            }]
        },
        'context': {
            'userId': principal_id
        }
    }
```

## Rate Limiting

### Usage Plans and API Keys

```bash
# Create API key
aws apigateway create-api-key \
  --name client-api-key \
  --enabled

# Create usage plan
aws apigateway create-usage-plan \
  --name basic-plan \
  --throttle burstLimit=100,rateLimit=50 \
  --quota limit=10000,period=MONTH \
  --api-stages apiId=$API_ID,stage=prod

# Associate key with plan
aws apigateway create-usage-plan-key \
  --usage-plan-id plan-id \
  --key-id key-id \
  --key-type API_KEY
```

### Method-Level Throttling

```bash
aws apigateway update-stage \
  --rest-api-id $API_ID \
  --stage-name prod \
  --patch-operations '[{
    "op": "replace",
    "path": "/~1items/GET/throttling/burstLimit",
    "value": "50"
  }, {
    "op": "replace",
    "path": "/~1items/GET/throttling/rateLimit",
    "value": "100"
  }]'
```

## Caching (REST API)

### Enable Caching

```bash
aws apigateway update-stage \
  --rest-api-id $API_ID \
  --stage-name prod \
  --patch-operations '[{
    "op": "replace",
    "path": "/cacheClusterEnabled",
    "value": "true"
  }, {
    "op": "replace",
    "path": "/cacheClusterSize",
    "value": "0.5"
  }]'
```

### Cache Key Parameters

```bash
aws apigateway update-method \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method GET \
  --patch-operations '[{
    "op": "replace",
    "path": "/requestParameters/method.request.querystring.category",
    "value": "true"
  }]'
```

### Cache Invalidation

```bash
# From client with API key
curl -X GET "https://api.example.com/prod/items" \
  -H "Cache-Control: max-age=0"
```

## Logging and Monitoring

### Access Logging

```bash
# Create log group
aws logs create-log-group --log-group-name API-Gateway-Access-Logs

# Enable access logging
aws apigateway update-stage \
  --rest-api-id $API_ID \
  --stage-name prod \
  --patch-operations '[{
    "op": "replace",
    "path": "/accessLogSettings/destinationArn",
    "value": "arn:aws:logs:us-east-1:123456789012:log-group:API-Gateway-Access-Logs"
  }, {
    "op": "replace",
    "path": "/accessLogSettings/format",
    "value": "{\"requestId\":\"$context.requestId\",\"ip\":\"$context.identity.sourceIp\",\"method\":\"$context.httpMethod\",\"path\":\"$context.path\",\"status\":\"$context.status\",\"latency\":\"$context.responseLatency\"}"
  }]'
```

### Execution Logging

```bash
aws apigateway update-stage \
  --rest-api-id $API_ID \
  --stage-name prod \
  --patch-operations '[{
    "op": "replace",
    "path": "/*/*/logging/loglevel",
    "value": "INFO"
  }, {
    "op": "replace",
    "path": "/*/*/logging/dataTrace",
    "value": "true"
  }]'
```

## Canary Deployments

```bash
# Create canary
aws apigateway update-stage \
  --rest-api-id $API_ID \
  --stage-name prod \
  --patch-operations '[{
    "op": "replace",
    "path": "/canarySettings/percentTraffic",
    "value": "10"
  }, {
    "op": "replace",
    "path": "/canarySettings/deploymentId",
    "value": "new-deployment-id"
  }]'

# Promote canary
aws apigateway update-stage \
  --rest-api-id $API_ID \
  --stage-name prod \
  --patch-operations '[{
    "op": "remove",
    "path": "/canarySettings"
  }]'
```
