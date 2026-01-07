# EC2 Instance Management

Advanced instance lifecycle and management patterns.

## Instance Lifecycle

### States

```
pending → running → stopping → stopped
                ↓
           shutting-down → terminated
```

### Start/Stop Automation

```python
import boto3

ec2 = boto3.client('ec2')

def stop_instances_by_tag(tag_key, tag_value):
    """Stop all instances with specific tag."""
    response = ec2.describe_instances(
        Filters=[
            {'Name': f'tag:{tag_key}', 'Values': [tag_value]},
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )

    instance_ids = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_ids.append(instance['InstanceId'])

    if instance_ids:
        ec2.stop_instances(InstanceIds=instance_ids)
        print(f"Stopped: {instance_ids}")

# Stop all dev instances
stop_instances_by_tag('Environment', 'dev')
```

### Scheduled Start/Stop with EventBridge

```bash
# Create Lambda function for start/stop
# Then create EventBridge rules

# Stop at 7 PM
aws events put-rule \
  --name "stop-dev-instances" \
  --schedule-expression "cron(0 19 ? * MON-FRI *)"

aws events put-targets \
  --rule "stop-dev-instances" \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:123456789012:function:StopInstances"

# Start at 7 AM
aws events put-rule \
  --name "start-dev-instances" \
  --schedule-expression "cron(0 7 ? * MON-FRI *)"

aws events put-targets \
  --rule "start-dev-instances" \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:123456789012:function:StartInstances"
```

## Auto Scaling

### Create Launch Template

```bash
aws ec2 create-launch-template \
  --launch-template-name web-server-template \
  --version-description "v1" \
  --launch-template-data '{
    "ImageId": "ami-0123456789abcdef0",
    "InstanceType": "t3.micro",
    "KeyName": "my-key",
    "SecurityGroupIds": ["sg-12345678"],
    "IamInstanceProfile": {"Name": "web-server-profile"},
    "UserData": "IyEvYmluL2Jhc2gKeXVtIHVwZGF0ZSAteQo=",
    "TagSpecifications": [{
      "ResourceType": "instance",
      "Tags": [{"Key": "Name", "Value": "web-server"}]
    }],
    "MetadataOptions": {
      "HttpTokens": "required",
      "HttpEndpoint": "enabled"
    }
  }'
```

### Create Auto Scaling Group

```bash
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name web-asg \
  --launch-template LaunchTemplateName=web-server-template,Version='$Latest' \
  --min-size 2 \
  --max-size 10 \
  --desired-capacity 2 \
  --vpc-zone-identifier "subnet-12345678,subnet-87654321" \
  --target-group-arns arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/web-tg/1234567890123456 \
  --health-check-type ELB \
  --health-check-grace-period 300 \
  --tags "Key=Environment,Value=production,PropagateAtLaunch=true"
```

### Scaling Policies

```bash
# Target tracking (CPU)
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name web-asg \
  --policy-name cpu-target-tracking \
  --policy-type TargetTrackingScaling \
  --target-tracking-configuration '{
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ASGAverageCPUUtilization"
    },
    "TargetValue": 70.0,
    "ScaleOutCooldown": 300,
    "ScaleInCooldown": 300
  }'

# Step scaling
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name web-asg \
  --policy-name scale-out-policy \
  --policy-type StepScaling \
  --adjustment-type ChangeInCapacity \
  --step-adjustments '[
    {"MetricIntervalLowerBound": 0, "MetricIntervalUpperBound": 20, "ScalingAdjustment": 1},
    {"MetricIntervalLowerBound": 20, "ScalingAdjustment": 2}
  ]'
```

### Scheduled Scaling

```bash
# Scale up for peak hours
aws autoscaling put-scheduled-update-group-action \
  --auto-scaling-group-name web-asg \
  --scheduled-action-name scale-up-morning \
  --recurrence "0 8 * * MON-FRI" \
  --min-size 5 \
  --max-size 20 \
  --desired-capacity 10

# Scale down at night
aws autoscaling put-scheduled-update-group-action \
  --auto-scaling-group-name web-asg \
  --scheduled-action-name scale-down-night \
  --recurrence "0 20 * * *" \
  --min-size 2 \
  --max-size 5 \
  --desired-capacity 2
```

## Instance Connect and Session Manager

### EC2 Instance Connect

```bash
# Push SSH key temporarily
aws ec2-instance-connect send-ssh-public-key \
  --instance-id i-1234567890abcdef0 \
  --instance-os-user ec2-user \
  --ssh-public-key file://~/.ssh/id_rsa.pub

# Connect via browser or CLI
aws ec2-instance-connect ssh --instance-id i-1234567890abcdef0
```

### Session Manager

No SSH keys or open ports required:

```bash
# Install Session Manager plugin first
# https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html

# Start session
aws ssm start-session --target i-1234567890abcdef0

# Port forwarding
aws ssm start-session \
  --target i-1234567890abcdef0 \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["3306"],"localPortNumber":["3306"]}'
```

### Enable Session Manager

```bash
# Instance needs SSM agent (pre-installed on Amazon Linux 2, Windows)
# Instance needs IAM role with AmazonSSMManagedInstanceCore policy

# Verify SSM agent is running
aws ssm describe-instance-information \
  --filters "Key=InstanceIds,Values=i-1234567890abcdef0"
```

## Instance Metadata Service (IMDS)

### IMDSv2 (Recommended)

```bash
# Get token
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

# Use token to get metadata
curl -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/instance-id

curl -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/security-credentials/my-role
```

### Enforce IMDSv2

```bash
# New instances
aws ec2 run-instances \
  --metadata-options "HttpTokens=required,HttpEndpoint=enabled" \
  ...

# Existing instances
aws ec2 modify-instance-metadata-options \
  --instance-id i-1234567890abcdef0 \
  --http-tokens required \
  --http-endpoint enabled
```

## Placement Groups

### Cluster (Low Latency)

```bash
aws ec2 create-placement-group \
  --group-name hpc-cluster \
  --strategy cluster

aws ec2 run-instances \
  --placement "GroupName=hpc-cluster" \
  ...
```

### Spread (High Availability)

```bash
aws ec2 create-placement-group \
  --group-name ha-spread \
  --strategy spread

# Max 7 instances per AZ
aws ec2 run-instances \
  --placement "GroupName=ha-spread" \
  ...
```

### Partition (Large Distributed)

```bash
aws ec2 create-placement-group \
  --group-name hadoop-cluster \
  --strategy partition \
  --partition-count 7

aws ec2 run-instances \
  --placement "GroupName=hadoop-cluster,PartitionNumber=1" \
  ...
```

## Spot Instances

### Spot Fleet

```bash
aws ec2 request-spot-fleet \
  --spot-fleet-request-config '{
    "IamFleetRole": "arn:aws:iam::123456789012:role/spot-fleet-role",
    "TargetCapacity": 10,
    "SpotPrice": "0.10",
    "AllocationStrategy": "diversified",
    "LaunchSpecifications": [
      {
        "ImageId": "ami-0123456789abcdef0",
        "InstanceType": "c5.large",
        "SubnetId": "subnet-12345678",
        "SecurityGroups": [{"GroupId": "sg-12345678"}]
      },
      {
        "ImageId": "ami-0123456789abcdef0",
        "InstanceType": "c5.xlarge",
        "SubnetId": "subnet-12345678",
        "SecurityGroups": [{"GroupId": "sg-12345678"}]
      }
    ]
  }'
```

### Handle Spot Interruption

```python
import requests
import time

def check_spot_interruption():
    """Check for spot interruption notice (2-minute warning)."""
    try:
        # IMDSv2
        token = requests.put(
            'http://169.254.169.254/latest/api/token',
            headers={'X-aws-ec2-metadata-token-ttl-seconds': '21600'},
            timeout=1
        ).text

        response = requests.get(
            'http://169.254.169.254/latest/meta-data/spot/termination-time',
            headers={'X-aws-ec2-metadata-token': token},
            timeout=1
        )

        if response.status_code == 200:
            return response.text  # Termination time
        return None
    except:
        return None

# Check periodically
while True:
    termination_time = check_spot_interruption()
    if termination_time:
        print(f"Spot interruption! Terminating at {termination_time}")
        # Graceful shutdown, save state, deregister from LB
        graceful_shutdown()
        break
    time.sleep(5)
```

## Instance Tags

### Bulk Tagging

```bash
# Tag multiple resources
aws ec2 create-tags \
  --resources i-1234567890abcdef0 vol-12345678 \
  --tags Key=Project,Value=WebApp Key=Environment,Value=production

# Tag based on filter
aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running" \
  --query "Reservations[].Instances[].InstanceId" \
  --output text | xargs -n 1 aws ec2 create-tags --tags Key=Status,Value=active --resources
```

### Enforce Tagging

Use Service Control Policies (SCPs) or IAM policies:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Action": "ec2:RunInstances",
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "Null": {
          "aws:RequestTag/Environment": "true"
        }
      }
    }
  ]
}
```
