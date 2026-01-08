---
name: s3
description: AWS S3 object storage for bucket management, object operations, and access control. Use when creating buckets, uploading files, configuring lifecycle policies, setting up static websites, managing permissions, or implementing cross-region replication.
last_updated: "2026-01-07"
doc_source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/
---

# AWS S3

Amazon Simple Storage Service (S3) provides scalable object storage with industry-leading durability (99.999999999%). S3 is fundamental to AWS—used for data lakes, backups, static websites, and as storage for many other AWS services.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Common Patterns](#common-patterns)
- [CLI Reference](#cli-reference)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [References](#references)

## Core Concepts

### Buckets

Containers for objects. Bucket names are globally unique across all AWS accounts.

### Objects

Files stored in S3, consisting of data, metadata, and a unique key (path). Maximum size: 5 TB.

### Storage Classes

| Class | Use Case | Durability | Availability |
|-------|----------|------------|--------------|
| Standard | Frequently accessed | 99.999999999% | 99.99% |
| Intelligent-Tiering | Unknown access patterns | 99.999999999% | 99.9% |
| Standard-IA | Infrequent access | 99.999999999% | 99.9% |
| Glacier Instant | Archive with instant retrieval | 99.999999999% | 99.9% |
| Glacier Flexible | Archive (minutes to hours) | 99.999999999% | 99.99% |
| Glacier Deep Archive | Long-term archive | 99.999999999% | 99.99% |

### Versioning

Keeps multiple versions of an object. Essential for data protection and recovery.

## Common Patterns

### Create a Bucket with Best Practices

**AWS CLI:**

```bash
# Create bucket (us-east-1 doesn't need LocationConstraint)
aws s3api create-bucket \
  --bucket my-secure-bucket-12345 \
  --region us-west-2 \
  --create-bucket-configuration LocationConstraint=us-west-2

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket my-secure-bucket-12345 \
  --versioning-configuration Status=Enabled

# Block public access
aws s3api put-public-access-block \
  --bucket my-secure-bucket-12345 \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket my-secure-bucket-12345 \
  --server-side-encryption-configuration '{
    "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
  }'
```

**boto3:**

```python
import boto3

s3 = boto3.client('s3', region_name='us-west-2')

# Create bucket
s3.create_bucket(
    Bucket='my-secure-bucket-12345',
    CreateBucketConfiguration={'LocationConstraint': 'us-west-2'}
)

# Enable versioning
s3.put_bucket_versioning(
    Bucket='my-secure-bucket-12345',
    VersioningConfiguration={'Status': 'Enabled'}
)

# Block public access
s3.put_public_access_block(
    Bucket='my-secure-bucket-12345',
    PublicAccessBlockConfiguration={
        'BlockPublicAcls': True,
        'IgnorePublicAcls': True,
        'BlockPublicPolicy': True,
        'RestrictPublicBuckets': True
    }
)
```

### Upload and Download Objects

```bash
# Upload a single file
aws s3 cp myfile.txt s3://my-bucket/path/myfile.txt

# Upload with metadata
aws s3 cp myfile.txt s3://my-bucket/path/myfile.txt \
  --metadata "environment=production,version=1.0"

# Download a file
aws s3 cp s3://my-bucket/path/myfile.txt ./myfile.txt

# Sync a directory
aws s3 sync ./local-folder s3://my-bucket/prefix/ --delete

# Copy between buckets
aws s3 cp s3://source-bucket/file.txt s3://dest-bucket/file.txt
```

### Generate Presigned URL

```python
import boto3
from botocore.config import Config

s3 = boto3.client('s3', config=Config(signature_version='s3v4'))

# Generate presigned URL for download (GET)
url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': 'my-bucket', 'Key': 'path/to/file.txt'},
    ExpiresIn=3600  # URL valid for 1 hour
)

# Generate presigned URL for upload (PUT)
upload_url = s3.generate_presigned_url(
    'put_object',
    Params={
        'Bucket': 'my-bucket',
        'Key': 'uploads/newfile.txt',
        'ContentType': 'text/plain'
    },
    ExpiresIn=3600
)
```

### Configure Lifecycle Policy

```bash
cat > lifecycle.json << 'EOF'
{
  "Rules": [
    {
      "ID": "MoveToGlacierAfter90Days",
      "Status": "Enabled",
      "Filter": {"Prefix": "logs/"},
      "Transitions": [
        {"Days": 90, "StorageClass": "GLACIER"}
      ],
      "Expiration": {"Days": 365}
    },
    {
      "ID": "DeleteOldVersions",
      "Status": "Enabled",
      "Filter": {},
      "NoncurrentVersionExpiration": {"NoncurrentDays": 30}
    }
  ]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
  --bucket my-bucket \
  --lifecycle-configuration file://lifecycle.json
```

### Event Notifications to Lambda

```bash
aws s3api put-bucket-notification-configuration \
  --bucket my-bucket \
  --notification-configuration '{
    "LambdaFunctionConfigurations": [
      {
        "LambdaFunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:ProcessS3Upload",
        "Events": ["s3:ObjectCreated:*"],
        "Filter": {
          "Key": {
            "FilterRules": [
              {"Name": "prefix", "Value": "uploads/"},
              {"Name": "suffix", "Value": ".jpg"}
            ]
          }
        }
      }
    ]
  }'
```

## CLI Reference

### High-Level Commands (aws s3)

| Command | Description |
|---------|-------------|
| `aws s3 ls` | List buckets or objects |
| `aws s3 cp` | Copy files |
| `aws s3 mv` | Move files |
| `aws s3 rm` | Delete files |
| `aws s3 sync` | Sync directories |
| `aws s3 mb` | Make bucket |
| `aws s3 rb` | Remove bucket |

### Low-Level Commands (aws s3api)

| Command | Description |
|---------|-------------|
| `aws s3api create-bucket` | Create bucket with options |
| `aws s3api put-object` | Upload with full control |
| `aws s3api get-object` | Download with options |
| `aws s3api delete-object` | Delete single object |
| `aws s3api put-bucket-policy` | Set bucket policy |
| `aws s3api put-bucket-versioning` | Enable versioning |
| `aws s3api list-object-versions` | List all versions |

### Useful Flags

- `--recursive`: Process all objects in prefix
- `--exclude/--include`: Filter objects
- `--dryrun`: Preview changes
- `--storage-class`: Set storage class
- `--acl`: Set access control (prefer policies instead)

## Best Practices

### Security

- **Block public access** at account and bucket level
- **Enable versioning** for data protection
- **Use bucket policies** over ACLs
- **Enable encryption** (SSE-S3 or SSE-KMS)
- **Enable access logging** for audit
- **Use VPC endpoints** for private access
- **Enable MFA Delete** for critical buckets

### Performance

- **Use Transfer Acceleration** for distant uploads
- **Use multipart upload** for files > 100 MB
- **Randomize key prefixes** for high-throughput (less relevant with 2024 improvements)
- **Use byte-range fetches** for large file downloads

### Cost Optimization

- **Use lifecycle policies** to transition to cheaper storage
- **Enable Intelligent-Tiering** for unpredictable access
- **Delete incomplete multipart uploads**:
  ```json
  {
    "Rules": [{
      "ID": "AbortIncompleteMultipartUpload",
      "Status": "Enabled",
      "Filter": {},
      "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7}
    }]
  }
  ```
- **Use S3 Storage Lens** to analyze storage patterns

## Troubleshooting

### Access Denied Errors

**Causes:**
1. Bucket policy denies access
2. IAM policy missing permissions
3. Public access block preventing access
4. Object owned by different account
5. VPC endpoint policy blocking

**Debug steps:**

```bash
# Check your identity
aws sts get-caller-identity

# Check bucket policy
aws s3api get-bucket-policy --bucket my-bucket

# Check public access block
aws s3api get-public-access-block --bucket my-bucket

# Check object ownership
aws s3api get-object-attributes \
  --bucket my-bucket \
  --key myfile.txt \
  --object-attributes ObjectOwner
```

### CORS Errors

**Symptom:** Browser blocks cross-origin request

**Fix:**

```bash
aws s3api put-bucket-cors --bucket my-bucket --cors-configuration '{
  "CORSRules": [{
    "AllowedOrigins": ["https://myapp.com"],
    "AllowedMethods": ["GET", "PUT", "POST"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }]
}'
```

### Slow Uploads

**Solutions:**
- Use multipart upload for large files
- Enable Transfer Acceleration
- Use `aws s3 cp` with `--expected-size` for large files
- Check network throughput to the region

### 403 on Presigned URL

**Causes:**
- URL expired
- Signer lacks permissions
- Bucket policy blocks access
- Region mismatch (v4 signatures are region-specific)

**Fix:** Ensure signer has permissions and use correct region.

## References

- [S3 User Guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/)
- [S3 API Reference](https://docs.aws.amazon.com/AmazonS3/latest/API/)
- [S3 CLI Reference](https://docs.aws.amazon.com/cli/latest/reference/s3/)
- [boto3 S3](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
