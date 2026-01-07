# ECS Task Definitions

Detailed patterns for ECS task definitions.

## Task Definition Structure

```json
{
  "family": "my-app",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::123456789012:role/ecsTaskRole",
  "containerDefinitions": [...],
  "volumes": [...],
  "runtimePlatform": {
    "cpuArchitecture": "ARM64",
    "operatingSystemFamily": "LINUX"
  }
}
```

## CPU and Memory Combinations (Fargate)

| CPU | Memory Options |
|-----|----------------|
| 256 (.25 vCPU) | 512 MB, 1 GB, 2 GB |
| 512 (.5 vCPU) | 1-4 GB (1 GB increments) |
| 1024 (1 vCPU) | 2-8 GB (1 GB increments) |
| 2048 (2 vCPU) | 4-16 GB (1 GB increments) |
| 4096 (4 vCPU) | 8-30 GB (1 GB increments) |
| 8192 (8 vCPU) | 16-60 GB (4 GB increments) |
| 16384 (16 vCPU) | 32-120 GB (8 GB increments) |

## Container Definition Examples

### Web Application

```json
{
  "name": "web",
  "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:latest",
  "essential": true,
  "portMappings": [
    {
      "containerPort": 8080,
      "protocol": "tcp",
      "appProtocol": "http"
    }
  ],
  "environment": [
    {"name": "NODE_ENV", "value": "production"},
    {"name": "PORT", "value": "8080"}
  ],
  "secrets": [
    {
      "name": "DB_PASSWORD",
      "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:db-password:password::"
    },
    {
      "name": "API_KEY",
      "valueFrom": "arn:aws:ssm:us-east-1:123456789012:parameter/my-app/api-key"
    }
  ],
  "logConfiguration": {
    "logDriver": "awslogs",
    "options": {
      "awslogs-group": "/ecs/my-app",
      "awslogs-region": "us-east-1",
      "awslogs-stream-prefix": "web"
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
```

### Sidecar Pattern

```json
{
  "containerDefinitions": [
    {
      "name": "app",
      "image": "my-app:latest",
      "essential": true,
      "portMappings": [{"containerPort": 8080}],
      "dependsOn": [
        {"containerName": "envoy", "condition": "HEALTHY"}
      ]
    },
    {
      "name": "envoy",
      "image": "envoyproxy/envoy:v1.28.0",
      "essential": true,
      "portMappings": [{"containerPort": 9901}],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:9901/ready || exit 1"],
        "interval": 5,
        "timeout": 2,
        "retries": 3,
        "startPeriod": 10
      }
    },
    {
      "name": "xray-daemon",
      "image": "amazon/aws-xray-daemon",
      "essential": false,
      "portMappings": [{"containerPort": 2000, "protocol": "udp"}],
      "memory": 256
    }
  ]
}
```

### Init Container Pattern

```json
{
  "containerDefinitions": [
    {
      "name": "init-db",
      "image": "my-migrations:latest",
      "essential": false,
      "command": ["./run-migrations.sh"],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/my-app",
          "awslogs-stream-prefix": "init"
        }
      }
    },
    {
      "name": "app",
      "image": "my-app:latest",
      "essential": true,
      "dependsOn": [
        {"containerName": "init-db", "condition": "SUCCESS"}
      ]
    }
  ]
}
```

## Secrets Management

### From Secrets Manager

```json
{
  "secrets": [
    {
      "name": "FULL_SECRET",
      "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:my-secret"
    },
    {
      "name": "SPECIFIC_KEY",
      "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:my-secret:username::"
    },
    {
      "name": "SPECIFIC_VERSION",
      "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:my-secret:password::abc123"
    }
  ]
}
```

### From Parameter Store

```json
{
  "secrets": [
    {
      "name": "API_KEY",
      "valueFrom": "arn:aws:ssm:us-east-1:123456789012:parameter/my-app/api-key"
    },
    {
      "name": "DB_HOST",
      "valueFrom": "arn:aws:ssm:us-east-1:123456789012:parameter/my-app/db-host"
    }
  ]
}
```

### Execution Role Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:123456789012:secret:my-app/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameters"
      ],
      "Resource": [
        "arn:aws:ssm:us-east-1:123456789012:parameter/my-app/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt"
      ],
      "Resource": [
        "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"
      ]
    }
  ]
}
```

## Logging Configurations

### CloudWatch Logs

```json
{
  "logConfiguration": {
    "logDriver": "awslogs",
    "options": {
      "awslogs-group": "/ecs/my-app",
      "awslogs-region": "us-east-1",
      "awslogs-stream-prefix": "ecs",
      "awslogs-create-group": "true",
      "mode": "non-blocking",
      "max-buffer-size": "4m"
    }
  }
}
```

### FireLens (Fluent Bit)

```json
{
  "containerDefinitions": [
    {
      "name": "log-router",
      "image": "amazon/aws-for-fluent-bit:latest",
      "essential": true,
      "firelensConfiguration": {
        "type": "fluentbit",
        "options": {
          "enable-ecs-log-metadata": "true"
        }
      }
    },
    {
      "name": "app",
      "image": "my-app:latest",
      "logConfiguration": {
        "logDriver": "awsfirelens",
        "options": {
          "Name": "cloudwatch",
          "region": "us-east-1",
          "log_group_name": "/ecs/my-app",
          "log_stream_prefix": "app-",
          "auto_create_group": "true"
        }
      }
    }
  ]
}
```

## Volume Mounts

### EFS Volume

```json
{
  "volumes": [
    {
      "name": "shared-data",
      "efsVolumeConfiguration": {
        "fileSystemId": "fs-12345678",
        "rootDirectory": "/",
        "transitEncryption": "ENABLED",
        "authorizationConfig": {
          "accessPointId": "fsap-12345678",
          "iam": "ENABLED"
        }
      }
    }
  ],
  "containerDefinitions": [
    {
      "name": "app",
      "mountPoints": [
        {
          "sourceVolume": "shared-data",
          "containerPath": "/data",
          "readOnly": false
        }
      ]
    }
  ]
}
```

### Bind Mount (Fargate)

```json
{
  "volumes": [
    {
      "name": "scratch"
    }
  ],
  "containerDefinitions": [
    {
      "name": "app",
      "mountPoints": [
        {
          "sourceVolume": "scratch",
          "containerPath": "/tmp/scratch"
        }
      ]
    }
  ]
}
```

## Resource Limits

### Per-Container Limits

```json
{
  "containerDefinitions": [
    {
      "name": "app",
      "cpu": 512,
      "memory": 1024,
      "memoryReservation": 512
    },
    {
      "name": "sidecar",
      "cpu": 256,
      "memory": 512
    }
  ]
}
```

### GPU (EC2 Launch Type)

```json
{
  "requiresCompatibilities": ["EC2"],
  "containerDefinitions": [
    {
      "name": "ml-training",
      "image": "my-ml-image:latest",
      "resourceRequirements": [
        {
          "type": "GPU",
          "value": "1"
        }
      ]
    }
  ]
}
```

## Health Checks

### HTTP Health Check

```json
{
  "healthCheck": {
    "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
    "interval": 30,
    "timeout": 5,
    "retries": 3,
    "startPeriod": 60
  }
}
```

### TCP Health Check

```json
{
  "healthCheck": {
    "command": ["CMD-SHELL", "nc -z localhost 8080 || exit 1"],
    "interval": 30,
    "timeout": 5,
    "retries": 3
  }
}
```

### Script-Based Health Check

```json
{
  "healthCheck": {
    "command": ["CMD", "/app/healthcheck.sh"],
    "interval": 30,
    "timeout": 10,
    "retries": 3,
    "startPeriod": 120
  }
}
```

## Container Dependencies

```json
{
  "containerDefinitions": [
    {
      "name": "database",
      "essential": true,
      "healthCheck": {...}
    },
    {
      "name": "cache",
      "essential": false,
      "dependsOn": [
        {"containerName": "database", "condition": "HEALTHY"}
      ]
    },
    {
      "name": "app",
      "essential": true,
      "dependsOn": [
        {"containerName": "database", "condition": "HEALTHY"},
        {"containerName": "cache", "condition": "START"}
      ]
    }
  ]
}
```

Conditions:
- `START`: Container has started
- `COMPLETE`: Container ran and exited with code 0
- `SUCCESS`: Container completed successfully
- `HEALTHY`: Container health check passed
