# RDS Administration

Database administration tasks for RDS.

## Parameter Groups

### Create Parameter Group

```bash
aws rds create-db-parameter-group \
  --db-parameter-group-name my-postgres-params \
  --db-parameter-group-family postgres16 \
  --description "Custom PostgreSQL parameters"
```

### Common PostgreSQL Parameters

```bash
# Set parameters
aws rds modify-db-parameter-group \
  --db-parameter-group-name my-postgres-params \
  --parameters \
    "ParameterName=max_connections,ParameterValue=200,ApplyMethod=pending-reboot" \
    "ParameterName=shared_buffers,ParameterValue={DBInstanceClassMemory/4},ApplyMethod=pending-reboot" \
    "ParameterName=work_mem,ParameterValue=65536,ApplyMethod=immediate" \
    "ParameterName=maintenance_work_mem,ParameterValue=524288,ApplyMethod=immediate" \
    "ParameterName=log_statement,ParameterValue=ddl,ApplyMethod=immediate" \
    "ParameterName=log_min_duration_statement,ParameterValue=1000,ApplyMethod=immediate"
```

### Common MySQL Parameters

```bash
aws rds modify-db-parameter-group \
  --db-parameter-group-name my-mysql-params \
  --parameters \
    "ParameterName=max_connections,ParameterValue=200,ApplyMethod=pending-reboot" \
    "ParameterName=innodb_buffer_pool_size,ParameterValue={DBInstanceClassMemory*3/4},ApplyMethod=pending-reboot" \
    "ParameterName=slow_query_log,ParameterValue=1,ApplyMethod=immediate" \
    "ParameterName=long_query_time,ParameterValue=1,ApplyMethod=immediate" \
    "ParameterName=log_queries_not_using_indexes,ParameterValue=1,ApplyMethod=immediate"
```

### Apply Parameter Group

```bash
aws rds modify-db-instance \
  --db-instance-identifier my-postgres \
  --db-parameter-group-name my-postgres-params \
  --apply-immediately
```

## Option Groups

### Create Option Group (SQL Server, Oracle, MySQL)

```bash
aws rds create-option-group \
  --option-group-name my-mysql-options \
  --engine-name mysql \
  --major-engine-version 8.0 \
  --option-group-description "MySQL options"
```

### Add Options

```bash
# Add MySQL memcached
aws rds add-option-to-option-group \
  --option-group-name my-mysql-options \
  --options OptionName=MEMCACHED

# Add SQL Server TDE
aws rds add-option-to-option-group \
  --option-group-name my-sqlserver-options \
  --options OptionName=TDE
```

## Backup Management

### Automated Backups

```bash
# Configure backup window
aws rds modify-db-instance \
  --db-instance-identifier my-postgres \
  --backup-retention-period 14 \
  --preferred-backup-window "03:00-04:00"
```

### Manual Snapshots

```bash
# Create snapshot
aws rds create-db-snapshot \
  --db-snapshot-identifier my-postgres-$(date +%Y%m%d) \
  --db-instance-identifier my-postgres

# Wait for completion
aws rds wait db-snapshot-available \
  --db-snapshot-identifier my-postgres-20240115
```

### Copy Snapshot Cross-Region

```bash
aws rds copy-db-snapshot \
  --source-db-snapshot-identifier arn:aws:rds:us-east-1:123456789012:snapshot:my-postgres-20240115 \
  --target-db-snapshot-identifier my-postgres-20240115 \
  --source-region us-east-1 \
  --region us-west-2 \
  --kms-key-id alias/aws/rds
```

### Share Snapshot

```bash
aws rds modify-db-snapshot-attribute \
  --db-snapshot-identifier my-postgres-20240115 \
  --attribute-name restore \
  --values-to-add 111111111111
```

### Export to S3

```bash
aws rds start-export-task \
  --export-task-identifier my-export-2024 \
  --source-arn arn:aws:rds:us-east-1:123456789012:snapshot:my-postgres-20240115 \
  --s3-bucket-name my-rds-exports \
  --iam-role-arn arn:aws:iam::123456789012:role/rds-s3-export-role \
  --kms-key-id alias/aws/rds
```

## Maintenance

### Maintenance Window

```bash
aws rds modify-db-instance \
  --db-instance-identifier my-postgres \
  --preferred-maintenance-window "sun:04:00-sun:05:00"
```

### Pending Maintenance

```bash
# View pending maintenance
aws rds describe-pending-maintenance-actions

# Apply immediately
aws rds apply-pending-maintenance-action \
  --resource-identifier arn:aws:rds:us-east-1:123456789012:db:my-postgres \
  --apply-action system-update \
  --opt-in-type immediate
```

### Engine Upgrades

```bash
# Check available versions
aws rds describe-db-engine-versions \
  --engine postgres \
  --engine-version 15.4 \
  --query "DBEngineVersions[].ValidUpgradeTarget"

# Upgrade (causes downtime)
aws rds modify-db-instance \
  --db-instance-identifier my-postgres \
  --engine-version 16.1 \
  --allow-major-version-upgrade \
  --apply-immediately
```

## Monitoring

### CloudWatch Metrics

Key metrics to monitor:

| Metric | Description | Alarm Threshold |
|--------|-------------|-----------------|
| CPUUtilization | CPU usage % | > 80% |
| DatabaseConnections | Active connections | > 80% of max_connections |
| FreeableMemory | Available RAM | < 256 MB |
| FreeStorageSpace | Available storage | < 20% |
| ReadIOPS, WriteIOPS | I/O operations | Near provisioned IOPS |
| ReadLatency, WriteLatency | I/O latency | > 20ms |
| DiskQueueDepth | Pending I/O requests | > 5 |
| ReplicaLag | Replication delay | > 60 seconds |

### Enhanced Monitoring

```bash
# Create IAM role for enhanced monitoring
aws iam create-role \
  --role-name rds-monitoring-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "monitoring.rds.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

aws iam attach-role-policy \
  --role-name rds-monitoring-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole

# Enable on instance
aws rds modify-db-instance \
  --db-instance-identifier my-postgres \
  --monitoring-interval 60 \
  --monitoring-role-arn arn:aws:iam::123456789012:role/rds-monitoring-role
```

### Performance Insights

```bash
aws rds modify-db-instance \
  --db-instance-identifier my-postgres \
  --enable-performance-insights \
  --performance-insights-retention-period 7 \
  --performance-insights-kms-key-id alias/aws/rds
```

### CloudWatch Logs

```bash
# Enable PostgreSQL logs
aws rds modify-db-instance \
  --db-instance-identifier my-postgres \
  --cloudwatch-logs-export-configuration '{
    "EnableLogTypes": ["postgresql", "upgrade"]
  }'

# Enable MySQL logs
aws rds modify-db-instance \
  --db-instance-identifier my-mysql \
  --cloudwatch-logs-export-configuration '{
    "EnableLogTypes": ["audit", "error", "general", "slowquery"]
  }'
```

## Secrets Manager Integration

### Create Secret with Rotation

```bash
# Create secret
aws secretsmanager create-secret \
  --name rds/my-postgres/admin \
  --secret-string '{"username":"admin","password":"InitialPassword123!"}'

# Enable rotation
aws secretsmanager rotate-secret \
  --secret-id rds/my-postgres/admin \
  --rotation-lambda-arn arn:aws:lambda:us-east-1:123456789012:function:SecretsManagerRDSPostgreSQLRotation \
  --rotation-rules AutomaticallyAfterDays=30
```

### Use Secret in Application

```python
import boto3
import json
import psycopg2

secrets = boto3.client('secretsmanager')

def get_connection():
    secret = secrets.get_secret_value(SecretId='rds/my-postgres/admin')
    creds = json.loads(secret['SecretString'])

    return psycopg2.connect(
        host=creds['host'],
        port=creds['port'],
        database=creds['dbname'],
        user=creds['username'],
        password=creds['password']
    )
```

## Failover and Recovery

### Manual Failover (Multi-AZ)

```bash
aws rds reboot-db-instance \
  --db-instance-identifier my-postgres \
  --force-failover
```

### Promote Read Replica

```bash
aws rds promote-read-replica \
  --db-instance-identifier my-postgres-replica \
  --backup-retention-period 7
```

### Blue-Green Deployment

```bash
# Create blue-green deployment
aws rds create-blue-green-deployment \
  --blue-green-deployment-name my-bg-deployment \
  --source arn:aws:rds:us-east-1:123456789012:db:my-postgres \
  --target-engine-version 16.1

# Switchover (after testing green)
aws rds switchover-blue-green-deployment \
  --blue-green-deployment-identifier bgd-abc123
```
