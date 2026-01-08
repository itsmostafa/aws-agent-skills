---
name: ec2
description: AWS EC2 virtual machine management for instances, AMIs, and networking. Use when launching instances, configuring security groups, managing key pairs, troubleshooting connectivity, or automating instance lifecycle.
last_updated: "2026-01-07"
doc_source: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/
---

# AWS EC2

Amazon Elastic Compute Cloud (EC2) provides resizable compute capacity in the cloud. Launch virtual servers, configure networking and security, and manage storage.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Common Patterns](#common-patterns)
- [CLI Reference](#cli-reference)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [References](#references)

## Core Concepts

### Instance Types

| Category | Example | Use Case |
|----------|---------|----------|
| General Purpose | t3, m6i | Web servers, dev environments |
| Compute Optimized | c6i | Batch processing, gaming |
| Memory Optimized | r6i | Databases, caching |
| Storage Optimized | i3, d3 | Data warehousing |
| Accelerated | p4d, g5 | ML, graphics |

### Purchasing Options

| Option | Description |
|--------|-------------|
| On-Demand | Pay by the hour/second |
| Reserved | 1-3 year commitment, up to 72% discount |
| Spot | Unused capacity, up to 90% discount |
| Savings Plans | Flexible commitment-based discount |

### AMI (Amazon Machine Image)

Template containing OS, software, and configuration for launching instances.

### Security Groups

Virtual firewalls controlling inbound and outbound traffic.

## Common Patterns

### Launch an Instance

**AWS CLI:**

```bash
# Create key pair
aws ec2 create-key-pair \
  --key-name my-key \
  --query 'KeyMaterial' \
  --output text > my-key.pem
chmod 400 my-key.pem

# Create security group
aws ec2 create-security-group \
  --group-name web-server-sg \
  --description "Web server security group" \
  --vpc-id vpc-12345678

# Allow SSH and HTTP
aws ec2 authorize-security-group-ingress \
  --group-id sg-12345678 \
  --protocol tcp \
  --port 22 \
  --cidr 10.0.0.0/8

aws ec2 authorize-security-group-ingress \
  --group-id sg-12345678 \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Launch instance
aws ec2 run-instances \
  --image-id ami-0123456789abcdef0 \
  --instance-type t3.micro \
  --key-name my-key \
  --security-group-ids sg-12345678 \
  --subnet-id subnet-12345678 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=web-server}]'
```

**boto3:**

```python
import boto3

ec2 = boto3.resource('ec2')

instances = ec2.create_instances(
    ImageId='ami-0123456789abcdef0',
    InstanceType='t3.micro',
    KeyName='my-key',
    SecurityGroupIds=['sg-12345678'],
    SubnetId='subnet-12345678',
    MinCount=1,
    MaxCount=1,
    TagSpecifications=[{
        'ResourceType': 'instance',
        'Tags': [{'Key': 'Name', 'Value': 'web-server'}]
    }]
)

instance = instances[0]
instance.wait_until_running()
instance.reload()
print(f"Instance ID: {instance.id}")
print(f"Public IP: {instance.public_ip_address}")
```

### User Data Script

```bash
aws ec2 run-instances \
  --image-id ami-0123456789abcdef0 \
  --instance-type t3.micro \
  --key-name my-key \
  --security-group-ids sg-12345678 \
  --subnet-id subnet-12345678 \
  --user-data '#!/bin/bash
    yum update -y
    yum install -y httpd
    systemctl start httpd
    systemctl enable httpd
    echo "<h1>Hello from $(hostname)</h1>" > /var/www/html/index.html
  '
```

### Attach IAM Role

```bash
# Create instance profile
aws iam create-instance-profile \
  --instance-profile-name web-server-profile

aws iam add-role-to-instance-profile \
  --instance-profile-name web-server-profile \
  --role-name web-server-role

# Launch with profile
aws ec2 run-instances \
  --image-id ami-0123456789abcdef0 \
  --instance-type t3.micro \
  --iam-instance-profile Name=web-server-profile \
  ...
```

### Create AMI from Instance

```bash
aws ec2 create-image \
  --instance-id i-1234567890abcdef0 \
  --name "my-custom-ami-$(date +%Y%m%d)" \
  --description "Custom AMI with web server" \
  --no-reboot
```

### Spot Instance Request

```bash
aws ec2 request-spot-instances \
  --instance-count 1 \
  --type "one-time" \
  --launch-specification '{
    "ImageId": "ami-0123456789abcdef0",
    "InstanceType": "c5.large",
    "KeyName": "my-key",
    "SecurityGroupIds": ["sg-12345678"],
    "SubnetId": "subnet-12345678"
  }' \
  --spot-price "0.05"
```

### EBS Volume Management

```bash
# Create volume
aws ec2 create-volume \
  --availability-zone us-east-1a \
  --size 100 \
  --volume-type gp3 \
  --iops 3000 \
  --throughput 125 \
  --encrypted

# Attach to instance
aws ec2 attach-volume \
  --volume-id vol-12345678 \
  --instance-id i-1234567890abcdef0 \
  --device /dev/sdf

# Create snapshot
aws ec2 create-snapshot \
  --volume-id vol-12345678 \
  --description "Daily backup"
```

## CLI Reference

### Instance Management

| Command | Description |
|---------|-------------|
| `aws ec2 run-instances` | Launch instances |
| `aws ec2 describe-instances` | List instances |
| `aws ec2 start-instances` | Start stopped instances |
| `aws ec2 stop-instances` | Stop running instances |
| `aws ec2 reboot-instances` | Reboot instances |
| `aws ec2 terminate-instances` | Terminate instances |
| `aws ec2 modify-instance-attribute` | Modify instance settings |

### Security Groups

| Command | Description |
|---------|-------------|
| `aws ec2 create-security-group` | Create security group |
| `aws ec2 describe-security-groups` | List security groups |
| `aws ec2 authorize-security-group-ingress` | Add inbound rule |
| `aws ec2 revoke-security-group-ingress` | Remove inbound rule |
| `aws ec2 authorize-security-group-egress` | Add outbound rule |

### AMIs

| Command | Description |
|---------|-------------|
| `aws ec2 describe-images` | List AMIs |
| `aws ec2 create-image` | Create AMI from instance |
| `aws ec2 copy-image` | Copy AMI to another region |
| `aws ec2 deregister-image` | Delete AMI |

### EBS Volumes

| Command | Description |
|---------|-------------|
| `aws ec2 create-volume` | Create EBS volume |
| `aws ec2 attach-volume` | Attach to instance |
| `aws ec2 detach-volume` | Detach from instance |
| `aws ec2 create-snapshot` | Create snapshot |
| `aws ec2 modify-volume` | Resize/modify volume |

## Best Practices

### Security

- **Use IAM roles** instead of access keys on instances
- **Restrict security groups** — principle of least privilege
- **Use private subnets** for backend instances
- **Enable IMDSv2** to prevent SSRF attacks
- **Encrypt EBS volumes** at rest

```bash
# Require IMDSv2
aws ec2 modify-instance-metadata-options \
  --instance-id i-1234567890abcdef0 \
  --http-tokens required \
  --http-endpoint enabled
```

### Performance

- **Right-size instances** — monitor and adjust
- **Use EBS-optimized instances**
- **Choose appropriate EBS volume type**
- **Use placement groups** for low-latency networking

### Cost Optimization

- **Use Spot Instances** for fault-tolerant workloads
- **Stop/terminate unused instances**
- **Use Reserved Instances** for steady-state workloads
- **Delete unused EBS volumes and snapshots**

### Reliability

- **Use Auto Scaling Groups** for high availability
- **Deploy across multiple AZs**
- **Use Elastic Load Balancer** for traffic distribution
- **Implement health checks**

## Troubleshooting

### Cannot SSH to Instance

**Checklist:**

1. Security group allows SSH (port 22) from your IP
2. Instance has public IP or use bastion/SSM
3. Key pair matches instance
4. Instance is running
5. Network ACL allows traffic

```bash
# Check security group
aws ec2 describe-security-groups --group-ids sg-12345678

# Check instance state
aws ec2 describe-instances \
  --instance-ids i-1234567890abcdef0 \
  --query "Reservations[].Instances[].{State:State.Name,PublicIP:PublicIpAddress}"
```

**Use Session Manager instead:**

```bash
aws ssm start-session --target i-1234567890abcdef0
```

### Instance Won't Start

**Causes:**
- Reached instance limits
- Insufficient capacity in AZ
- EBS volume issue
- Invalid AMI

```bash
# Check instance state reason
aws ec2 describe-instances \
  --instance-ids i-1234567890abcdef0 \
  --query "Reservations[].Instances[].StateReason"
```

### Instance Unreachable

**Debug:**

```bash
# Check instance status
aws ec2 describe-instance-status \
  --instance-ids i-1234567890abcdef0

# Get console output
aws ec2 get-console-output \
  --instance-id i-1234567890abcdef0

# Get screenshot (for Windows/GUI issues)
aws ec2 get-console-screenshot \
  --instance-id i-1234567890abcdef0
```

### High CPU/Memory

```bash
# Enable detailed monitoring
aws ec2 monitor-instances \
  --instance-ids i-1234567890abcdef0

# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-1234567890abcdef0 \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Average
```

## References

- [EC2 User Guide](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/)
- [EC2 API Reference](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/)
- [EC2 CLI Reference](https://docs.aws.amazon.com/cli/latest/reference/ec2/)
- [boto3 EC2](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html)
