# Secrets Manager Rotation Strategies

Secret rotation patterns and Lambda rotation functions.

## Rotation Strategies

### Single User Rotation

One user, password changes in place. Brief connection interruption during rotation.

```
1. AWSCURRENT has current password
2. Lambda creates new password → AWSPENDING
3. Lambda updates database with new password
4. Lambda tests AWSPENDING credentials
5. Lambda moves AWSPENDING → AWSCURRENT
```

### Alternating Users Rotation

Two users alternate, zero downtime.

```
User A (AWSCURRENT) → User B (AWSPENDING)
1. Lambda creates new password for User B
2. Lambda updates User B in database
3. Lambda tests User B credentials
4. Lambda moves User B → AWSCURRENT
5. Next rotation: User A becomes AWSPENDING
```

## Built-in Rotation Functions

### RDS PostgreSQL

```bash
# Use AWS-provided rotation Lambda
aws secretsmanager rotate-secret \
  --secret-id prod/myapp/database \
  --rotation-lambda-arn arn:aws:lambda:us-east-1:123456789012:function:SecretsManagerRDSPostgreSQLRotationSingleUser \
  --rotation-rules AutomaticallyAfterDays=30
```

### RDS MySQL

```bash
aws secretsmanager rotate-secret \
  --secret-id prod/myapp/database \
  --rotation-lambda-arn arn:aws:lambda:us-east-1:123456789012:function:SecretsManagerRDSMySQLRotationSingleUser \
  --rotation-rules AutomaticallyAfterDays=30
```

### Deploy Rotation Lambda

```bash
# Use SAR to deploy rotation function
aws serverlessrepo create-cloud-formation-change-set \
  --application-id arn:aws:serverlessrepo:us-east-1:297356227824:applications/SecretsManagerRDSPostgreSQLRotationSingleUser \
  --stack-name rds-rotation-lambda \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    Name=endpoint,Value=mydb.cluster-xyz.us-east-1.rds.amazonaws.com \
    Name=functionName,Value=SecretsManagerRDSPostgreSQLRotation
```

## Custom Rotation Lambda

### Lambda Structure

```python
import boto3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

secrets = boto3.client('secretsmanager')

def handler(event, context):
    secret_id = event['SecretId']
    token = event['ClientRequestToken']
    step = event['Step']

    if step == 'createSecret':
        create_secret(secret_id, token)
    elif step == 'setSecret':
        set_secret(secret_id, token)
    elif step == 'testSecret':
        test_secret(secret_id, token)
    elif step == 'finishSecret':
        finish_secret(secret_id, token)
    else:
        raise ValueError(f'Unknown step: {step}')

def create_secret(secret_id, token):
    """Create new secret version with AWSPENDING label."""
    # Check if already exists
    try:
        secrets.get_secret_value(
            SecretId=secret_id,
            VersionId=token,
            VersionStage='AWSPENDING'
        )
        logger.info('AWSPENDING already exists')
        return
    except secrets.exceptions.ResourceNotFoundException:
        pass

    # Get current secret
    current = secrets.get_secret_value(
        SecretId=secret_id,
        VersionStage='AWSCURRENT'
    )
    current_secret = json.loads(current['SecretString'])

    # Generate new password
    new_password = secrets.get_random_password(
        PasswordLength=32,
        ExcludeCharacters='"@/\\'
    )['RandomPassword']

    # Create new version
    new_secret = current_secret.copy()
    new_secret['password'] = new_password

    secrets.put_secret_value(
        SecretId=secret_id,
        ClientRequestToken=token,
        SecretString=json.dumps(new_secret),
        VersionStages=['AWSPENDING']
    )

def set_secret(secret_id, token):
    """Update the resource with the new credentials."""
    pending = secrets.get_secret_value(
        SecretId=secret_id,
        VersionId=token,
        VersionStage='AWSPENDING'
    )
    pending_secret = json.loads(pending['SecretString'])

    # Update the actual resource (e.g., API key in external service)
    # This is where you'd call your service's API to update the credential
    update_resource_credential(pending_secret)

def test_secret(secret_id, token):
    """Test that the new credentials work."""
    pending = secrets.get_secret_value(
        SecretId=secret_id,
        VersionId=token,
        VersionStage='AWSPENDING'
    )
    pending_secret = json.loads(pending['SecretString'])

    # Test the credentials
    if not verify_credentials_work(pending_secret):
        raise ValueError('New credentials failed validation')

def finish_secret(secret_id, token):
    """Finalize rotation by moving labels."""
    # Get current version
    metadata = secrets.describe_secret(SecretId=secret_id)

    current_version = None
    for version_id, stages in metadata['VersionIdsToStages'].items():
        if 'AWSCURRENT' in stages:
            current_version = version_id
            break

    # Move AWSCURRENT to new version
    secrets.update_secret_version_stage(
        SecretId=secret_id,
        VersionStage='AWSCURRENT',
        MoveToVersionId=token,
        RemoveFromVersionId=current_version
    )
```

### API Key Rotation Example

```python
import boto3
import json
import requests

secrets = boto3.client('secretsmanager')

def set_secret(secret_id, token):
    """Rotate API key in external service."""
    # Get pending secret
    pending = secrets.get_secret_value(
        SecretId=secret_id,
        VersionId=token,
        VersionStage='AWSPENDING'
    )
    pending_secret = json.loads(pending['SecretString'])

    # Get current secret (for authentication)
    current = secrets.get_secret_value(
        SecretId=secret_id,
        VersionStage='AWSCURRENT'
    )
    current_secret = json.loads(current['SecretString'])

    # Call external API to create new key
    response = requests.post(
        'https://api.example.com/v1/api-keys/rotate',
        headers={'Authorization': f'Bearer {current_secret["api_key"]}'},
        json={'new_key': pending_secret['api_key']}
    )

    if response.status_code != 200:
        raise Exception(f'Failed to rotate API key: {response.text}')

def test_secret(secret_id, token):
    """Test new API key works."""
    pending = secrets.get_secret_value(
        SecretId=secret_id,
        VersionId=token,
        VersionStage='AWSPENDING'
    )
    pending_secret = json.loads(pending['SecretString'])

    response = requests.get(
        'https://api.example.com/v1/me',
        headers={'Authorization': f'Bearer {pending_secret["api_key"]}'}
    )

    if response.status_code != 200:
        raise Exception('New API key validation failed')
```

## VPC Configuration

For RDS rotation, Lambda needs VPC access:

```yaml
Resources:
  RotationLambda:
    Type: AWS::Lambda::Function
    Properties:
      VpcConfig:
        SecurityGroupIds:
          - !Ref LambdaSecurityGroup
        SubnetIds:
          - !Ref PrivateSubnet1
          - !Ref PrivateSubnet2

  LambdaSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      VpcId: !Ref VPC
      SecurityGroupEgress:
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0  # For Secrets Manager API
        - IpProtocol: tcp
          FromPort: 5432
          ToPort: 5432
          DestinationSecurityGroupId: !Ref DBSecurityGroup

  # VPC Endpoint for Secrets Manager
  SecretsManagerEndpoint:
    Type: AWS::EC2::VPCEndpoint
    Properties:
      VpcId: !Ref VPC
      ServiceName: !Sub com.amazonaws.${AWS::Region}.secretsmanager
      VpcEndpointType: Interface
      SubnetIds:
        - !Ref PrivateSubnet1
        - !Ref PrivateSubnet2
      SecurityGroupIds:
        - !Ref EndpointSecurityGroup
```

## Rotation Permissions

### Lambda Execution Role

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
        "secretsmanager:PutSecretValue",
        "secretsmanager:UpdateSecretVersionStage"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/*"
    },
    {
      "Effect": "Allow",
      "Action": "secretsmanager:GetRandomPassword",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:GenerateDataKey"
      ],
      "Resource": "arn:aws:kms:us-east-1:123456789012:key/..."
    }
  ]
}
```

### Secret Resource Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/rotation-lambda-role"
      },
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:PutSecretValue",
        "secretsmanager:UpdateSecretVersionStage"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "secretsmanager:VersionStage": ["AWSCURRENT", "AWSPENDING"]
        }
      }
    }
  ]
}
```

## Handling Rotation in Applications

### Retry with New Credentials

```python
import boto3
import json
import psycopg2
from functools import wraps

secrets = boto3.client('secretsmanager')
_cached_secret = None
_secret_version = None

def get_db_credentials():
    global _cached_secret, _secret_version

    response = secrets.get_secret_value(SecretId='prod/myapp/database')

    if response['VersionId'] != _secret_version:
        _cached_secret = json.loads(response['SecretString'])
        _secret_version = response['VersionId']

    return _cached_secret

def with_credential_refresh(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except psycopg2.OperationalError as e:
            if 'authentication failed' in str(e).lower():
                # Force refresh and retry
                global _cached_secret, _secret_version
                _cached_secret = None
                _secret_version = None
                return func(*args, **kwargs)
            raise
    return wrapper

@with_credential_refresh
def query_database():
    creds = get_db_credentials()
    conn = psycopg2.connect(
        host=creds['host'],
        port=creds['port'],
        database=creds['database'],
        user=creds['username'],
        password=creds['password']
    )
    # Execute query...
```

## Monitoring Rotation

### CloudWatch Alarms

```bash
# Alarm for rotation failures
aws cloudwatch put-metric-alarm \
  --alarm-name SecretsRotationFailed \
  --metric-name RotationFailure \
  --namespace AWS/SecretsManager \
  --statistic Sum \
  --period 86400 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:alerts

# Alarm for secrets not rotated
aws cloudwatch put-metric-alarm \
  --alarm-name SecretsNotRotated \
  --metric-name DaysSinceLastRotation \
  --namespace AWS/SecretsManager \
  --dimensions Name=SecretName,Value=prod/myapp/database \
  --statistic Maximum \
  --period 86400 \
  --threshold 45 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:alerts
```
