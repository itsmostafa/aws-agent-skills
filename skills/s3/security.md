# S3 Security Configuration

Comprehensive security configurations for S3 buckets.

## Access Control Hierarchy

S3 access is evaluated in this order:

1. **Account-level public access block** (strongest)
2. **Bucket-level public access block**
3. **Bucket policy**
4. **IAM policies**
5. **ACLs** (legacy, avoid using)

## Block Public Access

### Account-Level Block

```bash
aws s3control put-public-access-block \
  --account-id 123456789012 \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

### Bucket-Level Block

```bash
aws s3api put-public-access-block \
  --bucket my-bucket \
  --public-access-block-configuration '{
    "BlockPublicAcls": true,
    "IgnorePublicAcls": true,
    "BlockPublicPolicy": true,
    "RestrictPublicBuckets": true
  }'
```

### Setting Explanations

| Setting | Effect |
|---------|--------|
| `BlockPublicAcls` | Rejects PUT requests with public ACLs |
| `IgnorePublicAcls` | Ignores existing public ACLs |
| `BlockPublicPolicy` | Rejects bucket policies that grant public access |
| `RestrictPublicBuckets` | Restricts access to AWS principals only |

## Bucket Policies

### Deny Unencrypted Uploads

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyUnencryptedUploads",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::my-bucket/*",
      "Condition": {
        "Null": {
          "s3:x-amz-server-side-encryption": "true"
        }
      }
    }
  ]
}
```

### Enforce HTTPS Only

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyHTTP",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::my-bucket",
        "arn:aws:s3:::my-bucket/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

### Restrict to VPC Endpoint

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "RestrictToVPCEndpoint",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::my-bucket",
        "arn:aws:s3:::my-bucket/*"
      ],
      "Condition": {
        "StringNotEquals": {
          "aws:SourceVpce": "vpce-1234567890abcdef0"
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
      "Sid": "CrossAccountAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::111111111111:role/CrossAccountRole"
      },
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-bucket",
        "arn:aws:s3:::my-bucket/*"
      ]
    }
  ]
}
```

### Restrict to Specific IP Ranges

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "RestrictToOfficeIPs",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::my-bucket",
        "arn:aws:s3:::my-bucket/*"
      ],
      "Condition": {
        "NotIpAddress": {
          "aws:SourceIp": ["192.0.2.0/24", "203.0.113.0/24"]
        },
        "Null": {
          "aws:SourceVpc": "true"
        }
      }
    }
  ]
}
```

## Encryption

### Server-Side Encryption (SSE-S3)

```bash
# Set default encryption
aws s3api put-bucket-encryption \
  --bucket my-bucket \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      },
      "BucketKeyEnabled": true
    }]
  }'
```

### SSE-KMS (Customer Managed Key)

```bash
aws s3api put-bucket-encryption \
  --bucket my-bucket \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "aws:kms",
        "KMSMasterKeyID": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"
      },
      "BucketKeyEnabled": true
    }]
  }'
```

### Bucket Key

Enable Bucket Key to reduce KMS API calls and costs:

```bash
aws s3api put-bucket-encryption \
  --bucket my-bucket \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "aws:kms",
        "KMSMasterKeyID": "alias/my-key"
      },
      "BucketKeyEnabled": true
    }]
  }'
```

## Versioning and MFA Delete

### Enable Versioning

```bash
aws s3api put-bucket-versioning \
  --bucket my-bucket \
  --versioning-configuration Status=Enabled
```

### Enable MFA Delete

Requires using root credentials:

```bash
aws s3api put-bucket-versioning \
  --bucket my-bucket \
  --versioning-configuration Status=Enabled,MFADelete=Enabled \
  --mfa "arn:aws:iam::123456789012:mfa/root-account-mfa-device 123456"
```

## Access Logging

```bash
# Create logging bucket
aws s3api create-bucket --bucket my-bucket-logs --region us-east-1

# Set ACL for S3 log delivery
aws s3api put-bucket-acl \
  --bucket my-bucket-logs \
  --grant-write URI=http://acs.amazonaws.com/groups/s3/LogDelivery \
  --grant-read-acp URI=http://acs.amazonaws.com/groups/s3/LogDelivery

# Enable logging on source bucket
aws s3api put-bucket-logging \
  --bucket my-bucket \
  --bucket-logging-status '{
    "LoggingEnabled": {
      "TargetBucket": "my-bucket-logs",
      "TargetPrefix": "access-logs/"
    }
  }'
```

## Object Lock (WORM)

### Enable Object Lock on New Bucket

```bash
aws s3api create-bucket \
  --bucket my-worm-bucket \
  --object-lock-enabled-for-bucket \
  --region us-east-1
```

### Set Default Retention

```bash
aws s3api put-object-lock-configuration \
  --bucket my-worm-bucket \
  --object-lock-configuration '{
    "ObjectLockEnabled": "Enabled",
    "Rule": {
      "DefaultRetention": {
        "Mode": "GOVERNANCE",
        "Days": 365
      }
    }
  }'
```

### Retention Modes

| Mode | Description |
|------|-------------|
| **Governance** | Users with special permissions can delete |
| **Compliance** | No one can delete until retention expires |

## VPC Endpoint Access

### Create Gateway Endpoint

```bash
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-12345678 \
  --service-name com.amazonaws.us-east-1.s3 \
  --route-table-ids rtb-12345678
```

### Endpoint Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::my-bucket/*"
    }
  ]
}
```

## Security Monitoring

### S3 Access Analyzer

```bash
# Check for public or shared buckets
aws accessanalyzer list-analyzed-resources \
  --analyzer-arn arn:aws:access-analyzer:us-east-1:123456789012:analyzer/MyAnalyzer \
  --resource-type AWS::S3::Bucket
```

### CloudTrail Data Events

```bash
aws cloudtrail put-event-selectors \
  --trail-name MyTrail \
  --event-selectors '[{
    "ReadWriteType": "All",
    "IncludeManagementEvents": true,
    "DataResources": [{
      "Type": "AWS::S3::Object",
      "Values": ["arn:aws:s3:::my-bucket/"]
    }]
  }]'
```

## Security Checklist

- [ ] Public access blocked at account level
- [ ] Public access blocked at bucket level
- [ ] Bucket policy enforces HTTPS
- [ ] Server-side encryption enabled
- [ ] Versioning enabled
- [ ] MFA Delete enabled (critical buckets)
- [ ] Access logging enabled
- [ ] CloudTrail data events enabled
- [ ] VPC endpoint for private access
- [ ] Object Lock for compliance (if needed)
- [ ] Regular access reviews with Access Analyzer
