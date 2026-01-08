---
name: cloudformation
description: AWS CloudFormation infrastructure as code for stack management. Use when writing templates, deploying stacks, managing drift, troubleshooting deployments, or organizing infrastructure with nested stacks.
last_updated: "2026-01-07"
doc_source: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/
---

# AWS CloudFormation

AWS CloudFormation provisions and manages AWS resources using templates. Define infrastructure as code, version control it, and deploy consistently across environments.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Common Patterns](#common-patterns)
- [CLI Reference](#cli-reference)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [References](#references)

## Core Concepts

### Templates

JSON or YAML files defining AWS resources. Key sections:
- **Parameters**: Input values
- **Mappings**: Static lookup tables
- **Conditions**: Conditional resource creation
- **Resources**: AWS resources (required)
- **Outputs**: Return values

### Stacks

Collection of resources managed as a single unit. Created from templates.

### Change Sets

Preview changes before executing updates.

### Stack Sets

Deploy stacks across multiple accounts and regions.

## Common Patterns

### Basic Template Structure

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: My infrastructure template

Parameters:
  Environment:
    Type: String
    AllowedValues: [dev, staging, prod]
    Default: dev

Mappings:
  EnvironmentConfig:
    dev:
      InstanceType: t3.micro
    prod:
      InstanceType: t3.large

Conditions:
  IsProd: !Equals [!Ref Environment, prod]

Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub 'my-app-${Environment}-${AWS::AccountId}'
      VersioningConfiguration:
        Status: !If [IsProd, Enabled, Suspended]

Outputs:
  BucketName:
    Description: S3 bucket name
    Value: !Ref MyBucket
    Export:
      Name: !Sub '${AWS::StackName}-BucketName'
```

### Deploy a Stack

**AWS CLI:**

```bash
# Create stack
aws cloudformation create-stack \
  --stack-name my-stack \
  --template-body file://template.yaml \
  --parameters ParameterKey=Environment,ParameterValue=prod \
  --capabilities CAPABILITY_IAM

# Wait for completion
aws cloudformation wait stack-create-complete --stack-name my-stack

# Update stack
aws cloudformation update-stack \
  --stack-name my-stack \
  --template-body file://template.yaml \
  --parameters ParameterKey=Environment,ParameterValue=prod

# Delete stack
aws cloudformation delete-stack --stack-name my-stack
```

### Use Change Sets

```bash
# Create change set
aws cloudformation create-change-set \
  --stack-name my-stack \
  --change-set-name my-changes \
  --template-body file://template.yaml \
  --parameters ParameterKey=Environment,ParameterValue=prod

# Describe changes
aws cloudformation describe-change-set \
  --stack-name my-stack \
  --change-set-name my-changes

# Execute change set
aws cloudformation execute-change-set \
  --stack-name my-stack \
  --change-set-name my-changes
```

### Lambda Function

```yaml
Resources:
  LambdaFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: !Sub '${AWS::StackName}-function'
      Runtime: python3.12
      Handler: index.handler
      Role: !GetAtt LambdaRole.Arn
      Code:
        ZipFile: |
          def handler(event, context):
              return {'statusCode': 200, 'body': 'Hello'}
      Environment:
        Variables:
          ENVIRONMENT: !Ref Environment

  LambdaRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### VPC with Subnets

```yaml
Resources:
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      Tags:
        - Key: Name
          Value: !Sub '${AWS::StackName}-vpc'

  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: 10.0.1.0/24
      MapPublicIpOnLaunch: true

  PrivateSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: 10.0.10.0/24

  InternetGateway:
    Type: AWS::EC2::InternetGateway

  AttachGateway:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId: !Ref InternetGateway

  PublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC

  PublicRoute:
    Type: AWS::EC2::Route
    DependsOn: AttachGateway
    Properties:
      RouteTableId: !Ref PublicRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway

  PublicSubnet1RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PublicSubnet1
      RouteTableId: !Ref PublicRouteTable
```

### DynamoDB Table

```yaml
Resources:
  OrdersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub '${AWS::StackName}-orders'
      AttributeDefinitions:
        - AttributeName: PK
          AttributeType: S
        - AttributeName: SK
          AttributeType: S
        - AttributeName: GSI1PK
          AttributeType: S
        - AttributeName: GSI1SK
          AttributeType: S
      KeySchema:
        - AttributeName: PK
          KeyType: HASH
        - AttributeName: SK
          KeyType: RANGE
      GlobalSecondaryIndexes:
        - IndexName: GSI1
          KeySchema:
            - AttributeName: GSI1PK
              KeyType: HASH
            - AttributeName: GSI1SK
              KeyType: RANGE
          Projection:
            ProjectionType: ALL
      BillingMode: PAY_PER_REQUEST
      PointInTimeRecoverySpecification:
        PointInTimeRecoveryEnabled: true
```

## CLI Reference

### Stack Operations

| Command | Description |
|---------|-------------|
| `aws cloudformation create-stack` | Create stack |
| `aws cloudformation update-stack` | Update stack |
| `aws cloudformation delete-stack` | Delete stack |
| `aws cloudformation describe-stacks` | Get stack info |
| `aws cloudformation list-stacks` | List stacks |
| `aws cloudformation describe-stack-events` | Get events |
| `aws cloudformation describe-stack-resources` | Get resources |

### Change Sets

| Command | Description |
|---------|-------------|
| `aws cloudformation create-change-set` | Create change set |
| `aws cloudformation describe-change-set` | View changes |
| `aws cloudformation execute-change-set` | Apply changes |
| `aws cloudformation delete-change-set` | Delete change set |

### Template

| Command | Description |
|---------|-------------|
| `aws cloudformation validate-template` | Validate template |
| `aws cloudformation get-template` | Get stack template |
| `aws cloudformation get-template-summary` | Get template info |

## Best Practices

### Template Design

- **Use parameters** for environment-specific values
- **Use mappings** for static lookup tables
- **Use conditions** for optional resources
- **Export outputs** for cross-stack references
- **Add descriptions** to parameters and outputs

### Security

- **Use IAM roles** instead of access keys
- **Enable termination protection** for production
- **Use stack policies** to protect resources
- **Never hardcode secrets** — use Secrets Manager

```bash
# Enable termination protection
aws cloudformation update-termination-protection \
  --stack-name my-stack \
  --enable-termination-protection
```

### Organization

- **Use nested stacks** for complex infrastructure
- **Create reusable modules**
- **Version control templates**
- **Use consistent naming conventions**

### Reliability

- **Use DependsOn** for explicit dependencies
- **Configure creation policies** for instances
- **Use update policies** for Auto Scaling groups
- **Implement rollback triggers**

## Troubleshooting

### Stack Creation Failed

```bash
# Get failure reason
aws cloudformation describe-stack-events \
  --stack-name my-stack \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'

# Common causes:
# - IAM permissions
# - Resource limits
# - Invalid property values
# - Dependency failures
```

### Stack Stuck in DELETE_FAILED

```bash
# Identify resources that couldn't be deleted
aws cloudformation describe-stack-resources \
  --stack-name my-stack \
  --query 'StackResources[?ResourceStatus==`DELETE_FAILED`]'

# Retry with resources to skip
aws cloudformation delete-stack \
  --stack-name my-stack \
  --retain-resources ResourceLogicalId1 ResourceLogicalId2
```

### Drift Detection

```bash
# Detect drift
aws cloudformation detect-stack-drift --stack-name my-stack

# Check drift status
aws cloudformation describe-stack-drift-detection-status \
  --stack-drift-detection-id abc123

# View drifted resources
aws cloudformation describe-stack-resource-drifts \
  --stack-name my-stack
```

### Rollback Failed

```bash
# Continue update rollback
aws cloudformation continue-update-rollback \
  --stack-name my-stack \
  --resources-to-skip ResourceLogicalId1
```

## References

- [CloudFormation User Guide](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/)
- [CloudFormation API Reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/)
- [CloudFormation CLI Reference](https://docs.aws.amazon.com/cli/latest/reference/cloudformation/)
- [Resource and Property Reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-type-ref.html)
