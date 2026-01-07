# Lambda Deployment Patterns

Strategies and patterns for deploying Lambda functions.

## Deployment Methods

### Direct Zip Upload

Best for small functions (< 50 MB):

```bash
# Package and deploy
zip -r function.zip . -x "*.git*"

aws lambda update-function-code \
  --function-name MyFunction \
  --zip-file fileb://function.zip
```

### S3 Deployment

Required for packages > 50 MB (up to 250 MB unzipped):

```bash
# Upload to S3
aws s3 cp function.zip s3://my-deployment-bucket/function.zip

# Deploy from S3
aws lambda update-function-code \
  --function-name MyFunction \
  --s3-bucket my-deployment-bucket \
  --s3-key function.zip
```

### Container Image Deployment

For packages up to 10 GB:

```dockerfile
FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

CMD ["app.handler"]
```

```bash
# Build and push
docker build -t my-lambda .
aws ecr get-login-password | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker tag my-lambda:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-lambda:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-lambda:latest

# Deploy
aws lambda update-function-code \
  --function-name MyFunction \
  --image-uri 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-lambda:latest
```

## AWS SAM Deployment

### Template Example

```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Runtime: python3.12
    Timeout: 30
    MemorySize: 256

Resources:
  MyFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: MyFunction
      Handler: app.handler
      CodeUri: ./src
      Environment:
        Variables:
          TABLE_NAME: !Ref MyTable
      Events:
        Api:
          Type: Api
          Properties:
            Path: /items
            Method: GET
      Policies:
        - DynamoDBReadPolicy:
            TableName: !Ref MyTable

  MyTable:
    Type: AWS::Serverless::SimpleTable
```

### SAM Commands

```bash
# Build
sam build

# Local testing
sam local invoke MyFunction --event event.json
sam local start-api

# Deploy
sam deploy --guided  # First time
sam deploy           # Subsequent deploys

# View logs
sam logs -n MyFunction --tail
```

## Versioning and Aliases

### Publish Version

```bash
# Publish immutable version
aws lambda publish-version \
  --function-name MyFunction \
  --description "v1.0.0 - Initial release"
```

### Create Alias

```bash
# Create PROD alias pointing to version 1
aws lambda create-alias \
  --function-name MyFunction \
  --name PROD \
  --function-version 1

# Create DEV alias pointing to $LATEST
aws lambda create-alias \
  --function-name MyFunction \
  --name DEV \
  --function-version '$LATEST'
```

### Weighted Alias (Canary Deployment)

```bash
# Route 90% to v1, 10% to v2
aws lambda update-alias \
  --function-name MyFunction \
  --name PROD \
  --function-version 2 \
  --routing-config AdditionalVersionWeights={1=0.9}
```

### Blue/Green with Aliases

```bash
# Current state: PROD -> v1

# Deploy new version
aws lambda update-function-code \
  --function-name MyFunction \
  --zip-file fileb://function.zip

aws lambda publish-version \
  --function-name MyFunction \
  --description "v2.0.0"

# Canary: 10% to v2
aws lambda update-alias \
  --function-name MyFunction \
  --name PROD \
  --function-version 2 \
  --routing-config AdditionalVersionWeights={1=0.9}

# Full rollout
aws lambda update-alias \
  --function-name MyFunction \
  --name PROD \
  --function-version 2 \
  --routing-config AdditionalVersionWeights={}

# Rollback if needed
aws lambda update-alias \
  --function-name MyFunction \
  --name PROD \
  --function-version 1
```

## Layers

### Create a Layer

Python dependencies:

```bash
# Structure: python/lib/python3.12/site-packages/
mkdir -p python
pip install -t python/ requests boto3

zip -r layer.zip python/

aws lambda publish-layer-version \
  --layer-name my-python-deps \
  --compatible-runtimes python3.12 \
  --compatible-architectures x86_64 arm64 \
  --zip-file fileb://layer.zip
```

### Use AWS-Provided Layers

```bash
# AWS Parameters and Secrets Layer
aws lambda update-function-configuration \
  --function-name MyFunction \
  --layers arn:aws:lambda:us-east-1:177933569100:layer:AWS-Parameters-and-Secrets-Lambda-Extension:11
```

### Layer Best Practices

- Keep layers under 50 MB
- Version layers properly
- Test compatibility with function runtime
- Use separate layers for different purposes

## CI/CD Integration

### GitHub Actions

```yaml
name: Deploy Lambda

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read

    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-role
          aws-region: us-east-1

      - name: Deploy
        run: |
          zip -r function.zip .
          aws lambda update-function-code \
            --function-name MyFunction \
            --zip-file fileb://function.zip

          aws lambda publish-version \
            --function-name MyFunction \
            --description "${{ github.sha }}"
```

### SAM Pipeline

```bash
# Initialize pipeline
sam pipeline init --bootstrap

# Creates:
# - IAM roles for CI/CD
# - S3 bucket for artifacts
# - CloudFormation for infrastructure
# - Pipeline configuration file
```

## Environment Management

### Environment Variables

```bash
# Set environment variables
aws lambda update-function-configuration \
  --function-name MyFunction \
  --environment "Variables={
    STAGE=production,
    DB_HOST=prod-db.example.com,
    LOG_LEVEL=INFO
  }"
```

### KMS Encryption

```bash
aws lambda update-function-configuration \
  --function-name MyFunction \
  --kms-key-arn arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012 \
  --environment "Variables={
    DB_PASSWORD=encrypted-value
  }"
```

### Using Secrets Manager

```python
import boto3
import json

secrets = boto3.client('secretsmanager')

# Cache secret outside handler for reuse
_secret = None

def get_secret():
    global _secret
    if _secret is None:
        response = secrets.get_secret_value(SecretId='my-secret')
        _secret = json.loads(response['SecretString'])
    return _secret

def handler(event, context):
    secret = get_secret()
    db_password = secret['password']
    # Use secret...
```

## Package Size Optimization

### Reduce Package Size

```bash
# Remove unnecessary files
zip -r function.zip . \
  -x "*.git*" \
  -x "*__pycache__*" \
  -x "*.pyc" \
  -x "tests/*" \
  -x "*.md" \
  -x "*.txt"

# Use zip with compression
zip -9 -r function.zip .
```

### Lambda Powertools (Recommended)

```python
# Use AWS Lambda Powertools for structured logging, tracing, etc.
from aws_lambda_powertools import Logger, Tracer, Metrics

logger = Logger()
tracer = Tracer()
metrics = Metrics()

@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics
def handler(event, context):
    logger.info("Processing request", extra={"event": event})
    return {"statusCode": 200}
```
