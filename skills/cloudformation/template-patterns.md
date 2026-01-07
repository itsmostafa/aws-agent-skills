# CloudFormation Template Patterns

Advanced template patterns and techniques.

## Intrinsic Functions

### Reference Functions

```yaml
# Reference a resource or parameter
!Ref MyResource

# Get attribute from resource
!GetAtt MyLambda.Arn
!GetAtt MyBucket.DomainName
!GetAtt MyBucket.RegionalDomainName

# Import from another stack
!ImportValue other-stack-BucketName
```

### String Functions

```yaml
# Substitution
!Sub 'arn:aws:s3:::${BucketName}/*'
!Sub
  - 'arn:aws:s3:::${Bucket}/*'
  - Bucket: !Ref MyBucket

# Join
!Join
  - ','
  - - !Ref Subnet1
    - !Ref Subnet2

# Split
!Split [',', !Ref SubnetList]

# Select
!Select [0, !GetAZs '']
!Select [1, !Split [',', !Ref SubnetList]]
```

### Conditional Functions

```yaml
Conditions:
  IsProd: !Equals [!Ref Environment, prod]
  HasBucket: !Not [!Equals [!Ref BucketName, '']]
  IsProdAndHasBucket: !And [!Condition IsProd, !Condition HasBucket]
  IsDevOrStaging: !Or
    - !Equals [!Ref Environment, dev]
    - !Equals [!Ref Environment, staging]

Resources:
  MyResource:
    Type: AWS::S3::Bucket
    Condition: IsProd
    Properties:
      BucketName: !If
        - IsProd
        - !Sub 'prod-${AWS::StackName}'
        - !Sub 'dev-${AWS::StackName}'
```

### Transform Functions

```yaml
# Include from S3
!Transform
  Name: AWS::Include
  Parameters:
    Location: s3://my-bucket/snippet.yaml

# Use macros
Transform: AWS::Serverless-2016-10-31
```

## Parameters

### Comprehensive Parameter Types

```yaml
Parameters:
  # String with validation
  ProjectName:
    Type: String
    MinLength: 3
    MaxLength: 20
    AllowedPattern: ^[a-z][a-z0-9-]*$
    ConstraintDescription: Must start with letter, lowercase alphanumeric and hyphens

  # Constrained values
  Environment:
    Type: String
    AllowedValues: [dev, staging, prod]
    Default: dev

  # Number with range
  InstanceCount:
    Type: Number
    MinValue: 1
    MaxValue: 10
    Default: 2

  # AWS-specific types
  VpcId:
    Type: AWS::EC2::VPC::Id
  SubnetIds:
    Type: List<AWS::EC2::Subnet::Id>
  KeyPair:
    Type: AWS::EC2::KeyPair::KeyName
  AMI:
    Type: AWS::SSM::Parameter::Value<AWS::EC2::Image::Id>
    Default: /aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2

  # Secrets (NoEcho)
  DatabasePassword:
    Type: String
    NoEcho: true
    MinLength: 8
```

## Mappings

```yaml
Mappings:
  RegionAMI:
    us-east-1:
      HVM64: ami-0123456789abcdef0
      HVM32: ami-0987654321fedcba0
    us-west-2:
      HVM64: ami-abcdef01234567890
      HVM32: ami-fedcba0987654321

  EnvironmentConfig:
    dev:
      InstanceType: t3.micro
      MinSize: 1
      MaxSize: 2
    prod:
      InstanceType: t3.large
      MinSize: 2
      MaxSize: 10

Resources:
  Instance:
    Type: AWS::EC2::Instance
    Properties:
      ImageId: !FindInMap [RegionAMI, !Ref 'AWS::Region', HVM64]
      InstanceType: !FindInMap [EnvironmentConfig, !Ref Environment, InstanceType]
```

## Cross-Stack References

### Stack A (Exporter)

```yaml
Resources:
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16

Outputs:
  VpcId:
    Value: !Ref VPC
    Export:
      Name: !Sub '${AWS::StackName}-VpcId'

  VpcCidr:
    Value: !GetAtt VPC.CidrBlock
    Export:
      Name: !Sub '${AWS::StackName}-VpcCidr'
```

### Stack B (Importer)

```yaml
Parameters:
  NetworkStackName:
    Type: String
    Default: network-stack

Resources:
  SecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      VpcId: !ImportValue
        Fn::Sub: '${NetworkStackName}-VpcId'
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: !ImportValue
            Fn::Sub: '${NetworkStackName}-VpcCidr'
```

## Nested Stacks

### Parent Stack

```yaml
Resources:
  NetworkStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: https://s3.amazonaws.com/my-bucket/network.yaml
      Parameters:
        Environment: !Ref Environment

  ComputeStack:
    Type: AWS::CloudFormation::Stack
    DependsOn: NetworkStack
    Properties:
      TemplateURL: https://s3.amazonaws.com/my-bucket/compute.yaml
      Parameters:
        VpcId: !GetAtt NetworkStack.Outputs.VpcId
        SubnetIds: !GetAtt NetworkStack.Outputs.SubnetIds
```

## Resource Policies

### Creation Policy

```yaml
Resources:
  AutoScalingGroup:
    Type: AWS::AutoScaling::AutoScalingGroup
    CreationPolicy:
      ResourceSignal:
        Count: !Ref DesiredCapacity
        Timeout: PT15M
    Properties:
      # ...

  LaunchTemplate:
    Type: AWS::EC2::LaunchTemplate
    Properties:
      LaunchTemplateData:
        UserData:
          Fn::Base64: !Sub |
            #!/bin/bash
            # ... setup ...
            /opt/aws/bin/cfn-signal -e $? \
              --stack ${AWS::StackName} \
              --resource AutoScalingGroup \
              --region ${AWS::Region}
```

### Update Policy

```yaml
Resources:
  AutoScalingGroup:
    Type: AWS::AutoScaling::AutoScalingGroup
    UpdatePolicy:
      AutoScalingRollingUpdate:
        MinInstancesInService: 1
        MaxBatchSize: 1
        PauseTime: PT10M
        WaitOnResourceSignals: true
      AutoScalingScheduledAction:
        IgnoreUnmodifiedGroupSizeProperties: true
```

### Deletion Policy

```yaml
Resources:
  Database:
    Type: AWS::RDS::DBInstance
    DeletionPolicy: Snapshot
    UpdateReplacePolicy: Snapshot
    Properties:
      # ...

  LogBucket:
    Type: AWS::S3::Bucket
    DeletionPolicy: Retain
    Properties:
      # ...
```

## Custom Resources

### Lambda-Backed Custom Resource

```yaml
Resources:
  CustomResourceLambda:
    Type: AWS::Lambda::Function
    Properties:
      Runtime: python3.12
      Handler: index.handler
      Role: !GetAtt CustomResourceRole.Arn
      Timeout: 300
      Code:
        ZipFile: |
          import cfnresponse
          import boto3

          def handler(event, context):
              try:
                  if event['RequestType'] == 'Create':
                      # Create logic
                      response_data = {'Result': 'Created'}
                  elif event['RequestType'] == 'Update':
                      # Update logic
                      response_data = {'Result': 'Updated'}
                  elif event['RequestType'] == 'Delete':
                      # Delete logic
                      response_data = {'Result': 'Deleted'}

                  cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)
              except Exception as e:
                  cfnresponse.send(event, context, cfnresponse.FAILED, {'Error': str(e)})

  MyCustomResource:
    Type: Custom::MyResource
    Properties:
      ServiceToken: !GetAtt CustomResourceLambda.Arn
      Parameter1: !Ref SomeParameter
```

## Stack Policies

### Prevent Updates to Critical Resources

```json
{
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "Update:*",
      "Principal": "*",
      "Resource": "*"
    },
    {
      "Effect": "Deny",
      "Action": "Update:Replace",
      "Principal": "*",
      "Resource": "LogicalResourceId/ProductionDatabase"
    },
    {
      "Effect": "Deny",
      "Action": "Update:Delete",
      "Principal": "*",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "ResourceType": ["AWS::RDS::DBInstance"]
        }
      }
    }
  ]
}
```

Apply stack policy:

```bash
aws cloudformation set-stack-policy \
  --stack-name my-stack \
  --stack-policy-body file://stack-policy.json
```

## Rollback Configuration

```bash
aws cloudformation create-stack \
  --stack-name my-stack \
  --template-body file://template.yaml \
  --rollback-configuration '{
    "RollbackTriggers": [
      {
        "Arn": "arn:aws:cloudwatch:us-east-1:123456789012:alarm:HighErrorRate",
        "Type": "AWS::CloudWatch::Alarm"
      }
    ],
    "MonitoringTimeInMinutes": 10
  }'
```

## Transform Macros

### Using AWS::Serverless

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Runtime: python3.12
    Timeout: 30

Resources:
  MyFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: app.handler
      CodeUri: ./src
      Events:
        Api:
          Type: Api
          Properties:
            Path: /items
            Method: GET
```

### Using AWS::LanguageExtensions

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::LanguageExtensions

Resources:
  # Use Fn::ForEach
  Fn::ForEach::Buckets:
    - BucketName
    - [logs, data, backup]
    - '${BucketName}Bucket':
        Type: AWS::S3::Bucket
        Properties:
          BucketName: !Sub 'my-app-${BucketName}-${AWS::AccountId}'
```
