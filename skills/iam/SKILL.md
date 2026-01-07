---
name: iam
description: AWS Identity and Access Management for users, roles, policies, and permissions. Use when creating IAM policies, configuring cross-account access, setting up service roles, troubleshooting permission errors, or managing access control.
---

# AWS IAM

AWS Identity and Access Management (IAM) enables secure access control to AWS services and resources. IAM is foundational to AWS security—every AWS API call is authenticated and authorized through IAM.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Common Patterns](#common-patterns)
- [CLI Reference](#cli-reference)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [References](#references)

## Core Concepts

### Principals

Entities that can make requests to AWS: IAM users, roles, federated users, and applications.

### Policies

JSON documents defining permissions. Types:
- **Identity-based**: Attached to users, groups, or roles
- **Resource-based**: Attached to resources (S3 buckets, SQS queues)
- **Permission boundaries**: Maximum permissions an identity can have
- **Service control policies (SCPs)**: Organization-wide limits

### Roles

Identities with permissions that can be assumed by trusted entities. No permanent credentials—uses temporary security tokens.

### Trust Relationships

Define which principals can assume a role. Configured via the role's trust policy.

## Common Patterns

### Create a Service Role for Lambda

**AWS CLI:**

```bash
# Create the trust policy
cat > trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "lambda.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create the role
aws iam create-role \
  --role-name MyLambdaRole \
  --assume-role-policy-document file://trust-policy.json

# Attach a managed policy
aws iam attach-role-policy \
  --role-name MyLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

**boto3:**

```python
import boto3
import json

iam = boto3.client('iam')

trust_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }
    ]
}

# Create role
iam.create_role(
    RoleName='MyLambdaRole',
    AssumeRolePolicyDocument=json.dumps(trust_policy)
)

# Attach managed policy
iam.attach_role_policy(
    RoleName='MyLambdaRole',
    PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
)
```

### Create Custom Policy with Least Privilege

```bash
cat > policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/MyTable"
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name MyDynamoDBPolicy \
  --policy-document file://policy.json
```

### Cross-Account Role Assumption

```bash
# In Account B (trusted account), create role with trust for Account A
cat > cross-account-trust.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "AWS": "arn:aws:iam::111111111111:root" },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": { "sts:ExternalId": "unique-external-id" }
      }
    }
  ]
}
EOF

# From Account A, assume the role
aws sts assume-role \
  --role-arn arn:aws:iam::222222222222:role/CrossAccountRole \
  --role-session-name MySession \
  --external-id unique-external-id
```

## CLI Reference

### Essential Commands

| Command | Description |
|---------|-------------|
| `aws iam create-role` | Create a new IAM role |
| `aws iam create-policy` | Create a customer managed policy |
| `aws iam attach-role-policy` | Attach a managed policy to a role |
| `aws iam put-role-policy` | Add an inline policy to a role |
| `aws iam get-role` | Get role details |
| `aws iam list-roles` | List all roles |
| `aws iam simulate-principal-policy` | Test policy permissions |
| `aws sts assume-role` | Assume a role and get temporary credentials |
| `aws sts get-caller-identity` | Get current identity |

### Useful Flags

- `--query`: Filter output with JMESPath
- `--output table`: Human-readable output
- `--no-cli-pager`: Disable pager for scripting

## Best Practices

### Security

- **Never use root account** for daily tasks
- **Enable MFA** for all human users
- **Use roles** instead of long-term access keys
- **Apply least privilege** — grant only required permissions
- **Use conditions** to restrict access by IP, time, or MFA
- **Rotate credentials** regularly
- **Use permission boundaries** for delegated administration

### Policy Design

- Start with AWS managed policies, customize as needed
- Use policy variables (`${aws:username}`) for dynamic policies
- Prefer explicit denies for sensitive actions
- Group related permissions logically

### Monitoring

- Enable **CloudTrail** for API auditing
- Use **IAM Access Analyzer** to identify overly permissive policies
- Review **credential reports** regularly
- Set up alerts for root account usage

## Troubleshooting

### Access Denied Errors

**Symptom:** `AccessDeniedException` or `UnauthorizedAccess`

**Debug steps:**
1. Verify identity: `aws sts get-caller-identity`
2. Check attached policies: `aws iam list-attached-role-policies --role-name MyRole`
3. Simulate the action:
   ```bash
   aws iam simulate-principal-policy \
     --policy-source-arn arn:aws:iam::123456789012:role/MyRole \
     --action-names dynamodb:GetItem \
     --resource-arns arn:aws:dynamodb:us-east-1:123456789012:table/MyTable
   ```
4. Check for explicit denies in SCPs or permission boundaries
5. Verify resource-based policies allow the principal

### Role Cannot Be Assumed

**Symptom:** `AccessDenied` when calling `AssumeRole`

**Causes:**
- Trust policy doesn't include the calling principal
- Missing `sts:AssumeRole` permission on the caller
- ExternalId mismatch (for cross-account roles)
- Session duration exceeds maximum

**Fix:** Review and update the role's trust relationship.

### Policy Size Limits

- Managed policy: 6,144 characters
- Inline policy: 2,048 characters (user), 10,240 characters (role/group)
- Trust policy: 2,048 characters

**Solution:** Use multiple policies, reference resources by prefix/wildcard, or use tags-based access control.

## References

- [IAM User Guide](https://docs.aws.amazon.com/IAM/latest/UserGuide/)
- [IAM API Reference](https://docs.aws.amazon.com/IAM/latest/APIReference/)
- [IAM CLI Reference](https://docs.aws.amazon.com/cli/latest/reference/iam/)
- [Policy Reference](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies.html)
- [boto3 IAM](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html)
