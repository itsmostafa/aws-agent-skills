---
name: rds
description: AWS RDS relational database service for managed databases. Use when provisioning databases, configuring backups, managing replicas, troubleshooting connectivity, or optimizing performance.
last_updated: "2026-01-07"
doc_source: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/
---

# AWS RDS

Amazon Relational Database Service (RDS) provides managed relational databases including MySQL, PostgreSQL, MariaDB, Oracle, SQL Server, and Aurora. RDS handles provisioning, patching, backups, and failover.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Common Patterns](#common-patterns)
- [CLI Reference](#cli-reference)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [References](#references)

## Core Concepts

### DB Instance Classes

| Category | Example | Use Case |
|----------|---------|----------|
| Standard | db.m6g.large | General purpose |
| Memory Optimized | db.r6g.large | High memory workloads |
| Burstable | db.t3.medium | Variable workloads, dev/test |

### Storage Types

| Type | IOPS | Use Case |
|------|------|----------|
| gp3 | 3,000-16,000 | Most workloads |
| io1/io2 | Up to 256,000 | High-performance OLTP |
| magnetic | N/A | Legacy, avoid |

### Multi-AZ Deployments

- **Multi-AZ Instance**: Synchronous standby in different AZ
- **Multi-AZ Cluster**: One writer, two reader instances (Aurora-like)

### Read Replicas

Asynchronous copies for read scaling. Can be cross-region.

## Common Patterns

### Create a PostgreSQL Instance

**AWS CLI:**

```bash
# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name my-db-subnet-group \
  --db-subnet-group-description "Private subnets for RDS" \
  --subnet-ids subnet-12345678 subnet-87654321

# Create security group (allow PostgreSQL from app)
aws ec2 create-security-group \
  --group-name rds-postgres-sg \
  --description "RDS PostgreSQL access" \
  --vpc-id vpc-12345678

aws ec2 authorize-security-group-ingress \
  --group-id sg-rds12345 \
  --protocol tcp \
  --port 5432 \
  --source-group sg-app12345

# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier my-postgres \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 16.1 \
  --master-username admin \
  --master-user-password 'SecurePassword123!' \
  --allocated-storage 100 \
  --storage-type gp3 \
  --db-subnet-group-name my-db-subnet-group \
  --vpc-security-group-ids sg-rds12345 \
  --multi-az \
  --backup-retention-period 7 \
  --storage-encrypted \
  --no-publicly-accessible
```

**boto3:**

```python
import boto3

rds = boto3.client('rds')

response = rds.create_db_instance(
    DBInstanceIdentifier='my-postgres',
    DBInstanceClass='db.t3.medium',
    Engine='postgres',
    EngineVersion='16.1',
    MasterUsername='admin',
    MasterUserPassword='SecurePassword123!',
    AllocatedStorage=100,
    StorageType='gp3',
    DBSubnetGroupName='my-db-subnet-group',
    VpcSecurityGroupIds=['sg-rds12345'],
    MultiAZ=True,
    BackupRetentionPeriod=7,
    StorageEncrypted=True,
    PubliclyAccessible=False
)
```

### Create Read Replica

```bash
aws rds create-db-instance-read-replica \
  --db-instance-identifier my-postgres-replica \
  --source-db-instance-identifier my-postgres \
  --db-instance-class db.t3.medium \
  --availability-zone us-east-1b
```

### Take a Snapshot

```bash
aws rds create-db-snapshot \
  --db-snapshot-identifier my-postgres-snapshot-2024-01-15 \
  --db-instance-identifier my-postgres
```

### Restore from Snapshot

```bash
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier my-postgres-restored \
  --db-snapshot-identifier my-postgres-snapshot-2024-01-15 \
  --db-instance-class db.t3.medium \
  --db-subnet-group-name my-db-subnet-group \
  --vpc-security-group-ids sg-rds12345
```

### Point-in-Time Recovery

```bash
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier my-postgres \
  --target-db-instance-identifier my-postgres-pitr \
  --restore-time 2024-01-15T10:30:00Z \
  --db-instance-class db.t3.medium
```

### Modify Instance

```bash
# Change instance class (with downtime)
aws rds modify-db-instance \
  --db-instance-identifier my-postgres \
  --db-instance-class db.m6g.large \
  --apply-immediately

# Scale storage (no downtime)
aws rds modify-db-instance \
  --db-instance-identifier my-postgres \
  --allocated-storage 200 \
  --apply-immediately
```

### Connect with IAM Authentication

```python
import boto3
import psycopg2

rds = boto3.client('rds')

# Generate auth token
token = rds.generate_db_auth_token(
    DBHostname='my-postgres.abc123.us-east-1.rds.amazonaws.com',
    Port=5432,
    DBUsername='iam_user',
    Region='us-east-1'
)

# Connect
conn = psycopg2.connect(
    host='my-postgres.abc123.us-east-1.rds.amazonaws.com',
    port=5432,
    database='mydb',
    user='iam_user',
    password=token,
    sslmode='require'
)
```

## CLI Reference

### Instance Management

| Command | Description |
|---------|-------------|
| `aws rds create-db-instance` | Create instance |
| `aws rds describe-db-instances` | List instances |
| `aws rds modify-db-instance` | Modify settings |
| `aws rds delete-db-instance` | Delete instance |
| `aws rds reboot-db-instance` | Reboot instance |
| `aws rds start-db-instance` | Start stopped instance |
| `aws rds stop-db-instance` | Stop instance |

### Backups

| Command | Description |
|---------|-------------|
| `aws rds create-db-snapshot` | Manual snapshot |
| `aws rds describe-db-snapshots` | List snapshots |
| `aws rds restore-db-instance-from-db-snapshot` | Restore from snapshot |
| `aws rds restore-db-instance-to-point-in-time` | Point-in-time restore |
| `aws rds copy-db-snapshot` | Copy snapshot |

### Replicas

| Command | Description |
|---------|-------------|
| `aws rds create-db-instance-read-replica` | Create read replica |
| `aws rds promote-read-replica` | Promote to standalone |

## Best Practices

### Security

- **Never make publicly accessible** — use VPC and security groups
- **Enable encryption** at rest (KMS) and in transit (SSL)
- **Use IAM authentication** for application access
- **Store credentials in Secrets Manager** with rotation
- **Use parameter groups** to enforce SSL

```bash
# Enforce SSL in PostgreSQL
aws rds modify-db-parameter-group \
  --db-parameter-group-name my-pg-params \
  --parameters "ParameterName=rds.force_ssl,ParameterValue=1,ApplyMethod=pending-reboot"
```

### Performance

- **Right-size instances** — monitor CPU, memory, IOPS
- **Use gp3** for cost-effective performance
- **Enable Performance Insights** for query analysis
- **Use read replicas** for read scaling
- **Optimize queries** — check slow query log

### High Availability

- **Enable Multi-AZ** for production
- **Use Aurora** for mission-critical workloads
- **Configure appropriate backup retention**
- **Test failover** periodically
- **Monitor replication lag** for replicas

### Cost Optimization

- **Use Reserved Instances** for steady-state workloads
- **Stop dev/test instances** when not in use
- **Delete old snapshots** regularly
- **Right-size instance classes**

## Troubleshooting

### Cannot Connect

**Causes:**
1. Security group not allowing access
2. Instance not in VPC subnet
3. SSL required but not used
4. Wrong endpoint/port

**Debug:**

```bash
# Check security group
aws ec2 describe-security-groups --group-ids sg-rds12345

# Check instance status
aws rds describe-db-instances \
  --db-instance-identifier my-postgres \
  --query "DBInstances[0].{Status:DBInstanceStatus,Endpoint:Endpoint}"

# Test connectivity from EC2
nc -zv my-postgres.abc123.us-east-1.rds.amazonaws.com 5432
```

### High CPU/Memory

**Debug:**

```bash
# Enable Enhanced Monitoring
aws rds modify-db-instance \
  --db-instance-identifier my-postgres \
  --monitoring-interval 60 \
  --monitoring-role-arn arn:aws:iam::123456789012:role/rds-monitoring-role

# Enable Performance Insights
aws rds modify-db-instance \
  --db-instance-identifier my-postgres \
  --enable-performance-insights \
  --performance-insights-retention-period 7
```

**Solutions:**
- Scale up instance class
- Optimize slow queries
- Add read replicas
- Check for locking/blocking

### Storage Full

**Symptom:** Instance becomes unavailable

**Prevention:**

```bash
# Enable storage autoscaling
aws rds modify-db-instance \
  --db-instance-identifier my-postgres \
  --max-allocated-storage 500

# Set CloudWatch alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "RDS-Storage-Low" \
  --metric-name FreeStorageSpace \
  --namespace AWS/RDS \
  --dimensions Name=DBInstanceIdentifier,Value=my-postgres \
  --statistic Average \
  --period 300 \
  --threshold 10000000000 \
  --comparison-operator LessThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:alerts
```

### Replication Lag

**Monitor:**

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name ReplicaLag \
  --dimensions Name=DBInstanceIdentifier,Value=my-postgres-replica \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 60 \
  --statistics Average
```

**Causes:**
- Replica instance too small
- Heavy write load
- Network issues
- Long-running queries on replica

## References

- [RDS User Guide](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/)
- [RDS API Reference](https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/)
- [RDS CLI Reference](https://docs.aws.amazon.com/cli/latest/reference/rds/)
- [boto3 RDS](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rds.html)
