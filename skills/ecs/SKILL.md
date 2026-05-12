---
name: ecs
description: AWS ECS container orchestration for running Docker containers. Use when deploying containerized applications, configuring task definitions, setting up services, managing clusters, or troubleshooting container issues.
last_updated: "2026-01-07"
doc_source: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/
---

# AWS ECS

Amazon Elastic Container Service (ECS) is a fully managed container orchestration service. Run containers on AWS Fargate (serverless) or EC2 instances.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Common Patterns](#common-patterns)
- [CLI Reference](#cli-reference)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [References](#references)

## Core Concepts

### Cluster

Logical grouping of tasks or services. Can contain Fargate tasks, EC2 instances, or both.

### Task Definition

Blueprint for your application. Defines containers, resources, networking, and IAM roles.

### Task

Running instance of a task definition. Can run standalone or as part of a service.

### Service

Maintains desired count of tasks. Handles deployments, load balancing, and auto scaling.

### Launch Types

| Type | Description | Use Case |
|------|-------------|----------|
| **Fargate** | Serverless, pay per task | Most workloads |
| **EC2** | Self-managed instances | GPU, Windows, specific requirements |

## Common Patterns

### Create a Fargate Cluster

**AWS CLI:**

```bash
# Create cluster
aws ecs create-cluster --cluster-name my-cluster

# With capacity providers
aws ecs create-cluster \
  --cluster-name my-cluster \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy \
    capacityProvider=FARGATE,weight=1 \
    capacityProvider=FARGATE_SPOT,weight=1
```

### Register Task Definition

```bash
cat > task-definition.json << 'EOF'
{
  "family": "web-app",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::123456789012:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "web",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "NODE_ENV", "value": "production"}
      ],
      "secrets": [
        {
          "name": "DB_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:db-password"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/web-app",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs",
          "mode": "non-blocking",
          "max-buffer-size": "25m"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
EOF

aws ecs register-task-definition --cli-input-json file://task-definition.json
```

### Create Service with Load Balancer

```bash
aws ecs create-service \
  --cluster my-cluster \
  --service-name web-service \
  --task-definition web-app:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={
    subnets=[subnet-12345678,subnet-87654321],
    securityGroups=[sg-12345678],
    assignPublicIp=DISABLED
  }" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/web-tg/1234567890123456,containerName=web,containerPort=8080" \
  --health-check-grace-period-seconds 60 \
  --deployment-configuration "deploymentCircuitBreaker={enable=true,rollback=true}"
```

### Run Standalone Task

```bash
aws ecs run-task \
  --cluster my-cluster \
  --task-definition my-batch-job:1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={
    subnets=[subnet-12345678],
    securityGroups=[sg-12345678],
    assignPublicIp=ENABLED
  }"
```

### Update Service (Deploy New Image)

```bash
# Register new task definition with updated image
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Update service to use new version
aws ecs update-service \
  --cluster my-cluster \
  --service web-service \
  --task-definition web-app:2 \
  --force-new-deployment
```

### Fargate Spot with SQS-Based Scaling

Use `FARGATE_SPOT` for batch/queue workloads to cut costs ~70%. Always include a fallback to regular `FARGATE`.

```bash
# Create service with Spot + fallback
aws ecs create-service \
  --cluster batch-cluster \
  --service-name queue-processor \
  --task-definition my-processor:1 \
  --desired-count 0 \
  --capacity-provider-strategy \
    capacityProvider=FARGATE_SPOT,weight=4,base=0 \
    capacityProvider=FARGATE,weight=1,base=1 \
  --network-configuration "awsvpcConfiguration={
    subnets=[subnet-12345678],
    securityGroups=[sg-12345678],
    assignPublicIp=DISABLED
  }"

# Register scalable target (scale to zero when queue empty)
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/batch-cluster/queue-processor \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 0 \
  --max-capacity 20

# Scale-out alarm: messages > 100
aws cloudwatch put-metric-alarm \
  --alarm-name queue-scale-out \
  --metric-name ApproximateNumberOfMessagesVisible \
  --namespace AWS/SQS \
  --dimensions Name=QueueName,Value=my-queue \
  --statistic Average \
  --period 60 \
  --evaluation-periods 1 \
  --threshold 100 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions <scale-out-policy-arn>

# Scale-in alarm: queue empty for 3 periods (conservative to avoid flapping)
aws cloudwatch put-metric-alarm \
  --alarm-name queue-scale-in \
  --metric-name ApproximateNumberOfMessagesVisible \
  --namespace AWS/SQS \
  --dimensions Name=QueueName,Value=my-queue \
  --statistic Average \
  --period 60 \
  --evaluation-periods 3 \
  --threshold 0 \
  --comparison-operator LessThanOrEqualToThreshold \
  --alarm-actions <scale-in-policy-arn>
```

**Fargate Spot interruption handling:** Spot tasks receive a SIGTERM 2 minutes before termination. Catch it in your application for graceful shutdown. For SQS consumers, call `ChangeMessageVisibility` on in-flight messages so they return to the queue rather than timing out.

### Auto Scaling

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/my-cluster/web-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# Target tracking policy
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/my-cluster/web-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-target-tracking \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleOutCooldown": 60,
    "ScaleInCooldown": 120
  }'
```

## CLI Reference

### Cluster Management

| Command | Description |
|---------|-------------|
| `aws ecs create-cluster` | Create cluster |
| `aws ecs describe-clusters` | Get cluster details |
| `aws ecs list-clusters` | List clusters |
| `aws ecs delete-cluster` | Delete cluster |

### Task Definitions

| Command | Description |
|---------|-------------|
| `aws ecs register-task-definition` | Create task definition |
| `aws ecs describe-task-definition` | Get task definition |
| `aws ecs list-task-definitions` | List task definitions |
| `aws ecs deregister-task-definition` | Deregister version |

### Services

| Command | Description |
|---------|-------------|
| `aws ecs create-service` | Create service |
| `aws ecs update-service` | Update service |
| `aws ecs describe-services` | Get service details |
| `aws ecs delete-service` | Delete service |

### Tasks

| Command | Description |
|---------|-------------|
| `aws ecs run-task` | Run standalone task |
| `aws ecs stop-task` | Stop running task |
| `aws ecs describe-tasks` | Get task details |
| `aws ecs list-tasks` | List tasks |

## Best Practices

### Security

- **Use task roles** for AWS API access (not access keys)
- **Use execution roles** for ECR/Secrets access
- **Store secrets in Secrets Manager** or Parameter Store
- **Use private subnets** with NAT gateway
- **Enable CloudTrail** for API auditing

### Performance

- **Right-size CPU/memory** — monitor and adjust
- **Use Fargate Spot** for fault-tolerant workloads (70% savings)
- **Enable container insights** for monitoring
- **Use service discovery** for internal communication

### Reliability

- **Deploy across multiple AZs**
- **Configure health checks** properly
- **Set appropriate deregistration delay**
- **Use circuit breaker** for deployments

```bash
aws ecs update-service \
  --cluster my-cluster \
  --service web-service \
  --deployment-configuration '{
    "deploymentCircuitBreaker": {
      "enable": true,
      "rollback": true
    }
  }'
```

### Cost Optimization

- **Use Fargate Spot** for batch workloads
- **Right-size task resources**
- **Scale to zero** when not needed
- **Use capacity providers** for mixed Fargate/Spot

## Troubleshooting

### Task Fails to Start

**Check:**

```bash
# View stopped tasks
aws ecs describe-tasks \
  --cluster my-cluster \
  --tasks $(aws ecs list-tasks --cluster my-cluster --desired-status STOPPED --query 'taskArns[0]' --output text)
```

**Common causes:**
- Image not found (ECR permissions)
- Secrets access denied
- Network configuration (subnets, security groups)
- Resource limits exceeded

### Container Keeps Restarting

**Debug:**

```bash
# Check CloudWatch logs
aws logs get-log-events \
  --log-group-name /ecs/web-app \
  --log-stream-name "ecs/web/abc123"

# Check task details
aws ecs describe-tasks \
  --cluster my-cluster \
  --tasks task-arn \
  --query 'tasks[0].containers[0].{reason:reason,exitCode:exitCode}'
```

**Causes:**
- Health check failing
- Application crashing
- Out of memory

### Live Debugging with ECS Exec

Connect directly to a running container without SSH. Requires `enableExecuteCommand: true` on the service and the SSM agent in your container image (included in most base images).

```bash
# Enable on existing service
aws ecs update-service \
  --cluster my-cluster \
  --service web-service \
  --enable-execute-command

# Get a shell in a running task
TASK_ARN=$(aws ecs list-tasks --cluster my-cluster --service-name web-service \
  --query 'taskArns[0]' --output text)

aws ecs execute-command \
  --cluster my-cluster \
  --task $TASK_ARN \
  --container web \
  --interactive \
  --command "/bin/sh"
```

**Requirements:** Task role must have `ssmmessages:CreateControlChannel`, `ssmmessages:CreateDataChannel`, `ssmmessages:OpenControlChannel`, `ssmmessages:OpenDataChannel` permissions.

### Service Stuck Deploying

```bash
# Check deployment status
aws ecs describe-services \
  --cluster my-cluster \
  --services web-service \
  --query 'services[0].deployments'

# Check events
aws ecs describe-services \
  --cluster my-cluster \
  --services web-service \
  --query 'services[0].events[:5]'
```

**Causes:**
- Health check failing on new tasks
- Not enough capacity
- Target group health checks failing

### Cannot Pull Image from ECR

**Check execution role has:**

```json
{
  "Effect": "Allow",
  "Action": [
    "ecr:GetAuthorizationToken",
    "ecr:BatchCheckLayerAvailability",
    "ecr:GetDownloadUrlForLayer",
    "ecr:BatchGetImage"
  ],
  "Resource": "*"
}
```

**Also check:**
- VPC endpoint for ECR (if private subnet)
- NAT gateway (if private subnet)
- Security group allows HTTPS outbound

## References

- [ECS Developer Guide](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/)
- [ECS API Reference](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/)
- [ECS CLI Reference](https://docs.aws.amazon.com/cli/latest/reference/ecs/)
- [boto3 ECS](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html)
