# IAM Security Best Practices

Comprehensive security best practices for AWS IAM.

## Foundational Security

### Root Account Protection

1. **Never use root for daily operations**
2. **Enable MFA** on root account (hardware key preferred)
3. **Delete root access keys** if they exist
4. **Set up CloudWatch alarms** for root account usage:

```bash
# Create metric filter for root login
aws logs put-metric-filter \
  --log-group-name CloudTrail/DefaultLogGroup \
  --filter-name RootAccountUsage \
  --filter-pattern '{ $.userIdentity.type = "Root" }' \
  --metric-transformations \
    metricName=RootAccountUsageCount,metricNamespace=CloudTrailMetrics,metricValue=1

# Create alarm
aws cloudwatch put-metric-alarm \
  --alarm-name RootAccountUsage \
  --metric-name RootAccountUsageCount \
  --namespace CloudTrailMetrics \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:security-alerts
```

### User Management

1. **Use IAM Identity Center (SSO)** for human access
2. **Enforce MFA** for all console users
3. **Set password policies**:

```bash
aws iam update-account-password-policy \
  --minimum-password-length 14 \
  --require-symbols \
  --require-numbers \
  --require-uppercase-characters \
  --require-lowercase-characters \
  --max-password-age 90 \
  --password-reuse-prevention 24
```

4. **Review and remove unused credentials**:

```bash
# Generate credential report
aws iam generate-credential-report

# Get the report
aws iam get-credential-report --query Content --output text | base64 -d
```

## Least Privilege Implementation

### Principles

1. **Start with zero permissions**, add as needed
2. **Use AWS managed policies** as starting points
3. **Scope resources explicitly** — avoid `*` where possible
4. **Use conditions** to further restrict access
5. **Separate duties** — different roles for different functions

### Implementing Least Privilege

**Step 1: Analyze required permissions**

Use CloudTrail to see what actions are actually used:

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=Username,AttributeValue=developer-user \
  --start-time 2024-01-01 \
  --end-time 2024-01-31
```

**Step 2: Use IAM Access Analyzer**

```bash
# Create analyzer
aws accessanalyzer create-analyzer \
  --analyzer-name MyAnalyzer \
  --type ACCOUNT

# Generate policy from CloudTrail activity
aws accessanalyzer start-policy-generation \
  --policy-generation-details '{
    "principalArn": "arn:aws:iam::123456789012:role/MyRole",
    "cloudTrailDetails": {
      "trailArn": "arn:aws:cloudtrail:us-east-1:123456789012:trail/MyTrail",
      "startTime": "2024-01-01T00:00:00Z",
      "endTime": "2024-01-31T23:59:59Z"
    }
  }'
```

**Step 3: Validate policies**

```bash
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:role/MyRole \
  --action-names s3:GetObject s3:PutObject \
  --resource-arns arn:aws:s3:::my-bucket/*
```

## Attribute-Based Access Control (ABAC)

Use tags for dynamic, scalable access control.

### Tag-Based Policy Example

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:StartInstances",
        "ec2:StopInstances"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:ResourceTag/Project": "${aws:PrincipalTag/Project}",
          "aws:ResourceTag/Environment": "${aws:PrincipalTag/Environment}"
        }
      }
    }
  ]
}
```

### Benefits of ABAC

- **Scales automatically** — new resources inherit tags
- **Reduces policy management** — fewer policies needed
- **Enables self-service** — users manage tagged resources
- **Audit-friendly** — clear relationship between principal and resource

## Role-Based Best Practices

### Service Roles

1. **One role per function** — Lambda function A gets RoleA
2. **Use service-linked roles** when available
3. **Scope trust policies tightly**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "123456789012"
        },
        "ArnLike": {
          "aws:SourceArn": "arn:aws:lambda:us-east-1:123456789012:function:my-*"
        }
      }
    }
  ]
}
```

### Cross-Account Roles

1. **Always use External ID** for third-party access
2. **Limit session duration** appropriately
3. **Restrict source accounts explicitly**
4. **Monitor assumeRole events** via CloudTrail

## Monitoring and Auditing

### Enable CloudTrail

```bash
aws cloudtrail create-trail \
  --name ManagementEventsTrail \
  --s3-bucket-name my-cloudtrail-bucket \
  --is-multi-region-trail \
  --enable-log-file-validation
```

### Key Events to Monitor

| Event | Description |
|-------|-------------|
| `CreateUser` | New IAM user created |
| `CreateAccessKey` | New access key generated |
| `AttachUserPolicy` | Policy attached to user |
| `CreateRole` | New role created |
| `UpdateAssumeRolePolicy` | Trust policy modified |
| `ConsoleLogin` | Console access |
| `AssumeRole` | Role assumption |

### IAM Access Analyzer

Continuously analyzes policies to identify unintended access:

```bash
# List findings
aws accessanalyzer list-findings \
  --analyzer-arn arn:aws:access-analyzer:us-east-1:123456789012:analyzer/MyAnalyzer

# Archive resolved findings
aws accessanalyzer update-findings \
  --analyzer-arn arn:aws:access-analyzer:us-east-1:123456789012:analyzer/MyAnalyzer \
  --status ARCHIVED \
  --ids finding-id-1 finding-id-2
```

## Credential Rotation

### Access Key Rotation

```python
import boto3
from datetime import datetime, timedelta

iam = boto3.client('iam')

# List access keys
response = iam.list_access_keys(UserName='my-user')

for key in response['AccessKeyMetadata']:
    age = datetime.now(key['CreateDate'].tzinfo) - key['CreateDate']
    if age > timedelta(days=90):
        print(f"Key {key['AccessKeyId']} is {age.days} days old - rotate it!")

        # Create new key
        new_key = iam.create_access_key(UserName='my-user')

        # Deactivate old key (after updating applications)
        iam.update_access_key(
            UserName='my-user',
            AccessKeyId=key['AccessKeyId'],
            Status='Inactive'
        )
```

### Automation with AWS Config

```yaml
# Config rule for access key rotation
Type: AWS::Config::ConfigRule
Properties:
  ConfigRuleName: access-keys-rotated
  Source:
    Owner: AWS
    SourceIdentifier: ACCESS_KEYS_ROTATED
  InputParameters:
    maxAccessKeyAge: 90
```

## Security Checklist

- [ ] Root account MFA enabled
- [ ] Root access keys deleted
- [ ] IAM users have MFA
- [ ] Password policy enforced
- [ ] Unused credentials removed
- [ ] Access keys rotated < 90 days
- [ ] CloudTrail enabled
- [ ] IAM Access Analyzer active
- [ ] Permission boundaries in use
- [ ] Service control policies defined (Organizations)
- [ ] Roles used instead of users for applications
- [ ] Cross-account access uses External ID
- [ ] Policies follow least privilege
- [ ] Credential report reviewed monthly
