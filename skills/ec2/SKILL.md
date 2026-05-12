---
name: ec2
description: >
  AWS EC2 virtual machine management — instances, security groups, key pairs, AMIs, EBS volumes,
  Auto Scaling Groups, Spot Instances, Session Manager, placement groups, and instance lifecycle automation.

  Trigger on ANY of these, even when EC2 isn't named explicitly:
  - Launching or provisioning: "spin up a server", "create a VM", "new instance", "run-instances", mention of instance types (t3, m5, c5, r6, g5, p4d, t4g, c7g, etc.)
  - SSH / connectivity problems: "connection refused", "connection timed out", "permission denied publickey", "can't connect to my instance", "SSH not working"
  - Instance management: resize, stop, start, terminate, reboot, change instance type
  - Cost optimization: stop dev instances overnight, save money on EC2, spot vs on-demand, reserved instances
  - Auto Scaling: ASG, launch template, mixed instances policy, scale to zero, scheduled scaling
  - Spot Instances: spot fleet, spot interruption, capacity-optimized, price-capacity-optimized
  - AMIs and backups: create image, custom AMI, EBS snapshot, DLM lifecycle policy, copy AMI
  - Monitoring: EC2 CPU utilization, CloudWatch metrics for instance, instance status checks, console output
  - Access methods: Session Manager, EC2 Instance Connect, bastion host, port forwarding
  - Security: IMDSv2, instance metadata, IAM role on instance, security group rules
  - User data and bootstrap scripts, cloud-init
last_updated: "2026-05-12"
doc_source: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/
---

# AWS EC2

Amazon Elastic Compute Cloud (EC2) provides resizable compute capacity in the cloud.

**Advanced patterns** (Auto Scaling, Spot Fleets, Session Manager, Instance Connect, IMDS, Placement Groups, scheduled scaling): see [instance-management.md](instance-management.md).

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
| General Purpose | t3, m6i, t4g (Graviton) | Web servers, dev environments |
| Compute Optimized | c6i, c7g (Graviton) | Batch processing, gaming |
| Memory Optimized | r6i, r7g (Graviton) | Databases, caching |
| Storage Optimized | i3, d3 | Data warehousing |
| Accelerated | p4d, g5 | ML, graphics |

Graviton (ARM) instances (t4g, m7g, c7g, r7g) are ~20% cheaper than x86 equivalents for the same performance — worth considering for new workloads.

### Purchasing Options

| Option | Description |
|--------|-------------|
| On-Demand | Pay by the hour/second |
| Reserved | 1-3 year commitment, up to 72% discount |
| Spot | Unused capacity, up to 90% discount — can be interrupted with 2-minute notice |
| Savings Plans | Flexible commitment-based discount |

### AMI (Amazon Machine Image)

Template containing OS, software, and configuration for launching instances. Use SSM Parameter Store to look up the latest official AMIs rather than hardcoding IDs:

```bash
# Latest Amazon Linux 2 AMI
aws ssm get-parameter \
  --name /aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2 \
  --query 'Parameter.Value' --output text

# Latest Amazon Linux 2023
aws ssm get-parameter \
  --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
  --query 'Parameter.Value' --output text

# Latest Ubuntu 22.04
aws ssm get-parameter \
  --name /aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id \
  --query 'Parameter.Value' --output text
```

### Security Groups

Virtual firewalls controlling inbound and outbound traffic. Changes take effect immediately — no restart required.

## Common Patterns

### Launch an Instance

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
  --associate-public-ip-address \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=web-server}]'

# Wait until running, then get IP
aws ec2 wait instance-running --instance-ids i-1234567890abcdef0
aws ec2 describe-instances \
  --instance-ids i-1234567890abcdef0 \
  --query 'Reservations[].Instances[].PublicIpAddress' --output text
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

> **OS package manager note:**
> - **Amazon Linux 2**: use `amazon-linux-extras install nginx1 -y` — `yum install nginx` fails because nginx is not in the default AL2 repos
> - **Amazon Linux 2023**: use `dnf install -y nginx`
> - **Ubuntu**: use `apt-get install -y nginx`
> - **Amazon Linux 2 / RHEL**: `httpd` (Apache) is always available via `yum install -y httpd`

```bash
# Amazon Linux 2 — nginx via amazon-linux-extras
aws ec2 run-instances \
  --image-id ami-0123456789abcdef0 \
  --instance-type t3.micro \
  --key-name my-key \
  --security-group-ids sg-12345678 \
  --subnet-id subnet-12345678 \
  --user-data '#!/bin/bash
amazon-linux-extras install nginx1 -y
systemctl start nginx
systemctl enable nginx
'

# Amazon Linux 2 — httpd (Apache, simpler alternative)
# --user-data '#!/bin/bash
# yum install -y httpd
# systemctl start httpd
# systemctl enable httpd
# echo "<h1>Hello from $(hostname -f)</h1>" > /var/www/html/index.html
# '
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

### Auto Scaling Group with Spot (Modern Approach)

The recommended way to use Spot Instances at scale is via Auto Scaling Groups with a mixed-instances policy — not the legacy `request-spot-instances` API. This supports instance diversification to minimize interruptions.

See [instance-management.md](instance-management.md) for the full setup. Quick example:

```bash
# 1. Create launch template with IMDSv2
aws ec2 create-launch-template \
  --launch-template-name my-lt \
  --launch-template-data '{
    "ImageId": "ami-0123456789abcdef0",
    "SecurityGroupIds": ["sg-12345678"],
    "IamInstanceProfile": {"Name": "my-profile"},
    "MetadataOptions": {"HttpTokens": "required", "HttpEndpoint": "enabled"}
  }'

# 2. Create ASG with mixed-instances (Spot + On-Demand diversification)
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name my-asg \
  --min-size 0 --max-size 20 --desired-capacity 2 \
  --vpc-zone-identifier "subnet-111,subnet-222" \
  --mixed-instances-policy '{
    "LaunchTemplate": {
      "LaunchTemplateSpecification": {"LaunchTemplateName": "my-lt", "Version": "$Latest"},
      "Overrides": [
        {"InstanceType": "c5.xlarge"},
        {"InstanceType": "c5.2xlarge"},
        {"InstanceType": "c5a.xlarge"}
      ]
    },
    "InstancesDistribution": {
      "OnDemandBaseCapacity": 0,
      "OnDemandPercentageAboveBaseCapacity": 0,
      "SpotAllocationStrategy": "capacity-optimized"
    }
  }'
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
# Require IMDSv2 on existing instance
aws ec2 modify-instance-metadata-options \
  --instance-id i-1234567890abcdef0 \
  --http-tokens required \
  --http-endpoint enabled
```

### Performance

- **Right-size instances** — monitor and adjust
- **Use EBS-optimized instances**
- **Choose appropriate EBS volume type** (gp3 is the default good choice; io2 for high IOPS)
- **Use placement groups** for low-latency networking (see instance-management.md)

### Cost Optimization

- **Use Spot Instances** for fault-tolerant workloads (batch, ML training, CI)
- **Stop/terminate unused instances**
- **Use Reserved Instances or Savings Plans** for steady-state workloads
- **Delete unused EBS volumes and snapshots**
- **Consider Graviton (t4g, m7g, c7g)** — ~20% cheaper for same performance

### Reliability

- **Use Auto Scaling Groups** for high availability (see instance-management.md)
- **Deploy across multiple AZs**
- **Use Elastic Load Balancer** for traffic distribution
- **Implement health checks**

## Troubleshooting

### Cannot SSH to Instance

**First: identify the error type — it points to different root causes:**

| Error | What it means | Primary suspects |
|-------|--------------|-----------------|
| `Connection refused` | Network is reachable, but SSH daemon is not listening | sshd crashed, sshd not installed, OS firewall (ufw/iptables) blocking, wrong port |
| `Connection timed out` | Packets never arrive | Security group blocks port 22, NACL blocks traffic, no public IP, wrong IP |
| `Permission denied` | Connected, but auth failed | Wrong key file, wrong username, key not authorized |

**Common username by OS:**

| OS | Default SSH user |
|----|-----------------|
| Amazon Linux 2 / 2023 | `ec2-user` |
| Ubuntu | `ubuntu` |
| Debian | `admin` |
| CentOS / RHEL | `ec2-user` or `centos` |
| Windows | `Administrator` |

**Diagnostic commands:**

```bash
# 1. Check instance state and public IP
aws ec2 describe-instances \
  --instance-ids i-1234567890abcdef0 \
  --query "Reservations[].Instances[].{State:State.Name,PublicIP:PublicIpAddress,StatusChecks:State.Name}"

# 2. Check instance status (system + instance checks)
aws ec2 describe-instance-status --instance-ids i-1234567890abcdef0

# 3. Check security group rules for port 22
aws ec2 describe-security-groups \
  --group-ids sg-12345678 \
  --query "SecurityGroups[].IpPermissions[?ToPort==\`22\`]"

# 4. Get console output to see boot logs, sshd errors, OOM events
aws ec2 get-console-output \
  --instance-id i-1234567890abcdef0 \
  --latest \
  --query Output --output text
```

**If connection refused — get inside via Session Manager to fix sshd:**

```bash
# Requires SSM agent on instance + AmazonSSMManagedInstanceCore policy
aws ssm start-session --target i-1234567890abcdef0

# Once inside, diagnose:
systemctl status ssh        # Ubuntu
systemctl status sshd       # Amazon Linux
df -h                       # Check disk full
sudo sshd -t                # Test sshd config for syntax errors
sudo journalctl -u ssh -n 50  # Recent sshd logs
```

**Use Session Manager instead of SSH** (no open ports, no key pair needed):

```bash
aws ssm start-session --target i-1234567890abcdef0

# Port forwarding via SSM
aws ssm start-session \
  --target i-1234567890abcdef0 \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["22"],"localPortNumber":["2222"]}'
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

```bash
# Check instance status
aws ec2 describe-instance-status \
  --instance-ids i-1234567890abcdef0

# Get console output
aws ec2 get-console-output \
  --instance-id i-1234567890abcdef0 \
  --latest

# Get screenshot (for Windows/GUI issues)
aws ec2 get-console-screenshot \
  --instance-id i-1234567890abcdef0
```

### High CPU/Memory

```bash
# Enable detailed monitoring
aws ec2 monitor-instances \
  --instance-ids i-1234567890abcdef0

# Check CloudWatch metrics (cross-platform date command)
START=$(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u --date='1 hour ago' +%Y-%m-%dT%H:%M:%SZ)
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-1234567890abcdef0 \
  --start-time "$START" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --period 300 \
  --statistics Average
```

## References

- [EC2 User Guide](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/)
- [EC2 API Reference](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/)
- [EC2 CLI Reference](https://docs.aws.amazon.com/cli/latest/reference/ec2/)
- [boto3 EC2](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html)
