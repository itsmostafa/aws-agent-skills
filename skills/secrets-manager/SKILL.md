---
name: secrets-manager
description: AWS Secrets Manager for secure secret storage and rotation. Use when storing credentials, configuring automatic rotation, managing secret versions, retrieving secrets in applications, or integrating with RDS.
last_updated: "2026-01-07"
doc_source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/
---

# AWS Secrets Manager

AWS Secrets Manager helps protect access to applications, services, and IT resources. Store, retrieve, and automatically rotate credentials, API keys, and other secrets.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Common Patterns](#common-patterns)
- [CLI Reference](#cli-reference)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [References](#references)

## Core Concepts

### Secrets

Encrypted data stored in Secrets Manager. Can contain:
- Database credentials
- API keys
- OAuth tokens
- Any key-value pairs (up to 64 KB)

### Versions

Each secret can have multiple versions:
- **AWSCURRENT**: Current active version
- **AWSPENDING**: Version being rotated to
- **AWSPREVIOUS**: Previous version

### Rotation

Automatic credential rotation using Lambda functions. Built-in support for:
- Amazon RDS
- Amazon Redshift
- Amazon DocumentDB
- Custom secrets

## Common Patterns

### Create a Secret

**AWS CLI:**

```bash
# Create secret with JSON
aws secretsmanager create-secret \
  --name prod/myapp/database \
  --description "Production database credentials" \
  --secret-string '{"username":"admin","password":"MySecurePassword123!","host":"mydb.cluster-xyz.us-east-1.rds.amazonaws.com","port":5432,"database":"myapp"}'

# Create secret with binary data
aws secretsmanager create-secret \
  --name prod/myapp/certificate \
  --secret-binary fileb://certificate.pem
```

**boto3:**

```python
import boto3
import json

secrets = boto3.client('secretsmanager')

response = secrets.create_secret(
    Name='prod/myapp/database',
    Description='Production database credentials',
    SecretString=json.dumps({
        'username': 'admin',
        'password': 'MySecurePassword123!',
        'host': 'mydb.cluster-xyz.us-east-1.rds.amazonaws.com',
        'port': 5432,
        'database': 'myapp'
    }),
    Tags=[
        {'Key': 'Environment', 'Value': 'production'},
        {'Key': 'Application', 'Value': 'myapp'}
    ]
)
```

### Retrieve a Secret

```python
import boto3
import json

secrets = boto3.client('secretsmanager')

def get_secret(secret_name):
    response = secrets.get_secret_value(SecretId=secret_name)

    if 'SecretString' in response:
        return json.loads(response['SecretString'])
    else:
        import base64
        return base64.b64decode(response['SecretBinary'])

# Usage
credentials = get_secret('prod/myapp/database')
db_password = credentials['password']
```

### Caching Secrets

```python
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig

# Configure cache
cache_config = SecretCacheConfig(
    max_cache_size=100,
    secret_refresh_interval=3600,
    secret_version_stage_refresh_interval=3600
)

cache = SecretCache(config=cache_config)

def get_cached_secret(secret_name):
    secret = cache.get_secret_string(secret_name)
    return json.loads(secret)
```

### Update a Secret

```bash
# Update secret value
aws secretsmanager update-secret \
  --secret-id prod/myapp/database \
  --secret-string '{"username":"admin","password":"NewPassword456!"}'

# Put new version with staging labels
aws secretsmanager put-secret-value \
  --secret-id prod/myapp/database \
  --secret-string '{"username":"admin","password":"NewPassword456!"}' \
  --version-stages AWSCURRENT
```

### Enable Rotation for RDS

```bash
aws secretsmanager rotate-secret \
  --secret-id prod/myapp/database \
  --rotation-lambda-arn arn:aws:lambda:us-east-1:123456789012:function:SecretsManagerRDSPostgreSQLRotation \
  --rotation-rules AutomaticallyAfterDays=30
```

### Create Secret with Rotation

```bash
# Use CloudFormation for RDS secret with rotation
aws cloudformation deploy \
  --template-file rds-secret.yaml \
  --stack-name rds-secret
```

```yaml
# rds-secret.yaml
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  DBSecret:
    Type: AWS::SecretsManager::Secret
    Properties:
      Name: prod/myapp/database
      GenerateSecretString:
        SecretStringTemplate: '{"username": "admin"}'
        GenerateStringKey: password
        PasswordLength: 32
        ExcludeCharacters: '"@/\'

  DBSecretRotation:
    Type: AWS::SecretsManager::RotationSchedule
    Properties:
      SecretId: !Ref DBSecret
      RotationLambdaARN: !GetAtt RotationLambda.Arn
      RotationRules:
        AutomaticallyAfterDays: 30
```

### Use in Lambda with Extension

```python
import json
import urllib.request

def handler(event, context):
    # Use AWS Parameters and Secrets Lambda Extension
    secrets_port = 2773
    secret_name = 'prod/myapp/database'

    url = f'http://localhost:{secrets_port}/secretsmanager/get?secretId={secret_name}'
    headers = {'X-Aws-Parameters-Secrets-Token': os.environ['AWS_SESSION_TOKEN']}

    request = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(request)
    secret = json.loads(response.read())['SecretString']

    credentials = json.loads(secret)
    return credentials
```

## CLI Reference

### Secret Management

| Command | Description |
|---------|-------------|
| `aws secretsmanager create-secret` | Create secret |
| `aws secretsmanager describe-secret` | Get secret metadata |
| `aws secretsmanager get-secret-value` | Retrieve secret value |
| `aws secretsmanager update-secret` | Update secret |
| `aws secretsmanager delete-secret` | Delete secret |
| `aws secretsmanager restore-secret` | Restore deleted secret |
| `aws secretsmanager list-secrets` | List secrets |

### Versions

| Command | Description |
|---------|-------------|
| `aws secretsmanager put-secret-value` | Add new version |
| `aws secretsmanager list-secret-version-ids` | List versions |
| `aws secretsmanager update-secret-version-stage` | Move staging labels |

### Rotation

| Command | Description |
|---------|-------------|
| `aws secretsmanager rotate-secret` | Configure/trigger rotation |
| `aws secretsmanager cancel-rotate-secret` | Cancel rotation |

## Best Practices

### Secret Organization

- **Use hierarchical names**: `environment/application/secret-type`
- **Tag secrets** for organization and cost allocation
- **Separate by environment** (dev, staging, prod)

### Security

- **Use resource policies** to control access
- **Enable encryption** with customer-managed KMS keys
- **Rotate secrets** regularly (30-90 days)
- **Audit access** with CloudTrail
- **Use VPC endpoints** for private access

### Access Control

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/*",
      "Condition": {
        "StringEquals": {
          "secretsmanager:ResourceTag/Environment": "production"
        }
      }
    }
  ]
}
```

### Application Integration

- **Cache secrets** to reduce API calls
- **Handle rotation** gracefully (retry with new credentials)
- **Use Lambda extension** for faster access
- **Never log secrets**

## Troubleshooting

### AccessDeniedException

**Causes:**
- IAM policy missing `secretsmanager:GetSecretValue`
- Resource policy denying access
- KMS key policy missing permissions

**Debug:**

```bash
# Check secret resource policy
aws secretsmanager get-resource-policy --secret-id my-secret

# Check IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:role/my-role \
  --action-names secretsmanager:GetSecretValue \
  --resource-arns arn:aws:secretsmanager:us-east-1:123456789012:secret:my-secret
```

### Rotation Failed

**Debug:**

```bash
# Check rotation status
aws secretsmanager describe-secret --secret-id my-secret

# Check Lambda logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/SecretsManagerRotation \
  --filter-pattern "ERROR"
```

**Common causes:**
- Lambda timeout (increase to 30+ seconds)
- Network connectivity (VPC configuration)
- Database connection issues
- Wrong secret format

### Secret Not Found

```bash
# List secrets to find correct name
aws secretsmanager list-secrets \
  --filters Key=name,Values=myapp

# Check if deleted (within recovery window)
aws secretsmanager list-secrets \
  --include-planned-deletion
```

## References

- [Secrets Manager User Guide](https://docs.aws.amazon.com/secretsmanager/latest/userguide/)
- [Secrets Manager API Reference](https://docs.aws.amazon.com/secretsmanager/latest/apireference/)
- [Secrets Manager CLI Reference](https://docs.aws.amazon.com/cli/latest/reference/secretsmanager/)
- [boto3 Secrets Manager](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager.html)
