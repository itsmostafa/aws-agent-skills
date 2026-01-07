# SNS Notification Patterns

Advanced notification patterns and configurations.

## Topic Policies

### Allow Cross-Account Publishing

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::111111111111:root"
      },
      "Action": "sns:Publish",
      "Resource": "arn:aws:sns:us-east-1:123456789012:my-topic"
    }
  ]
}
```

### Allow S3 Events

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "s3.amazonaws.com"
      },
      "Action": "sns:Publish",
      "Resource": "arn:aws:sns:us-east-1:123456789012:my-topic",
      "Condition": {
        "ArnLike": {
          "aws:SourceArn": "arn:aws:s3:::my-bucket"
        }
      }
    }
  ]
}
```

### Allow CloudWatch Alarms

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudwatch.amazonaws.com"
      },
      "Action": "sns:Publish",
      "Resource": "arn:aws:sns:us-east-1:123456789012:alerts-topic"
    }
  ]
}
```

## Delivery Policies

### HTTP/HTTPS Retry Policy

```json
{
  "http": {
    "defaultHealthyRetryPolicy": {
      "minDelayTarget": 1,
      "maxDelayTarget": 60,
      "numRetries": 50,
      "numMaxDelayRetries": 0,
      "numNoDelayRetries": 3,
      "numMinDelayRetries": 2,
      "backoffFunction": "exponential"
    },
    "disableSubscriptionOverrides": false,
    "defaultThrottlePolicy": {
      "maxReceivesPerSecond": 10
    }
  }
}
```

### Configure Delivery Policy

```bash
aws sns set-topic-attributes \
  --topic-arn arn:aws:sns:us-east-1:123456789012:my-topic \
  --attribute-name DeliveryPolicy \
  --attribute-value file://delivery-policy.json
```

## Dead-Letter Queues

### Configure DLQ for Subscription

```bash
# Create DLQ
aws sqs create-queue --queue-name sns-dlq

# Get DLQ ARN
DLQ_ARN=$(aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/sns-dlq \
  --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)

# Set DLQ on subscription
aws sns set-subscription-attributes \
  --subscription-arn arn:aws:sns:us-east-1:123456789012:my-topic:abc123 \
  --attribute-name RedrivePolicy \
  --attribute-value "{\"deadLetterTargetArn\":\"${DLQ_ARN}\"}"
```

## SMS Notifications

### Send SMS

```python
import boto3

sns = boto3.client('sns')

# Direct publish to phone number
sns.publish(
    PhoneNumber='+12025551234',
    Message='Your verification code is 123456',
    MessageAttributes={
        'AWS.SNS.SMS.SMSType': {
            'DataType': 'String',
            'StringValue': 'Transactional'  # or 'Promotional'
        },
        'AWS.SNS.SMS.SenderID': {
            'DataType': 'String',
            'StringValue': 'MyApp'
        }
    }
)
```

### SMS Preferences

```bash
aws sns set-sms-attributes \
  --attributes '{
    "DefaultSMSType": "Transactional",
    "DefaultSenderID": "MyApp",
    "MonthlySpendLimit": "100"
  }'
```

### Check SMS Status

```bash
# Check spending
aws sns get-sms-attributes \
  --attributes MonthlySpendLimit
```

## Mobile Push Notifications

### Create Platform Application

```bash
# For iOS (APNS)
aws sns create-platform-application \
  --name MyApp-iOS \
  --platform APNS \
  --attributes '{
    "PlatformCredential": "<private-key>",
    "PlatformPrincipal": "<certificate>"
  }'

# For Android (FCM)
aws sns create-platform-application \
  --name MyApp-Android \
  --platform GCM \
  --attributes '{
    "PlatformCredential": "<server-key>"
  }'
```

### Register Device Endpoint

```python
import boto3

sns = boto3.client('sns')

# Register device
response = sns.create_platform_endpoint(
    PlatformApplicationArn='arn:aws:sns:us-east-1:123456789012:app/GCM/MyApp-Android',
    Token='device-token-from-fcm'
)
endpoint_arn = response['EndpointArn']
```

### Send Push Notification

```python
import boto3
import json

sns = boto3.client('sns')

# Direct to device
sns.publish(
    TargetArn=endpoint_arn,
    Message=json.dumps({
        'default': 'Default message',
        'GCM': json.dumps({
            'notification': {
                'title': 'New Message',
                'body': 'You have a new message'
            },
            'data': {
                'message_id': '12345'
            }
        })
    }),
    MessageStructure='json'
)
```

## Multi-Protocol Messages

### Protocol-Specific Messages

```python
import boto3
import json

sns = boto3.client('sns')

sns.publish(
    TopicArn='arn:aws:sns:us-east-1:123456789012:my-topic',
    Message=json.dumps({
        'default': 'Default message for all protocols',
        'email': 'Detailed email message with formatting',
        'sms': 'Short SMS msg',
        'lambda': json.dumps({'action': 'process', 'data': {...}}),
        'sqs': json.dumps({'queue_message': {...}}),
        'http': json.dumps({'webhook_payload': {...}})
    }),
    MessageStructure='json',
    Subject='Email Subject Line'
)
```

## Raw Message Delivery

### Enable Raw Delivery for SQS

By default, SNS wraps messages. Raw delivery sends just the message body.

```bash
aws sns set-subscription-attributes \
  --subscription-arn arn:aws:sns:us-east-1:123456789012:my-topic:abc123 \
  --attribute-name RawMessageDelivery \
  --attribute-value true
```

### Message Format Comparison

**Without raw delivery (wrapped):**
```json
{
  "Type": "Notification",
  "MessageId": "...",
  "TopicArn": "arn:aws:sns:...",
  "Subject": "...",
  "Message": "{\"actual\":\"content\"}",
  "Timestamp": "...",
  "SignatureVersion": "1",
  "Signature": "...",
  "SigningCertURL": "...",
  "UnsubscribeURL": "..."
}
```

**With raw delivery:**
```json
{"actual": "content"}
```

## FIFO Topics

### Create FIFO Topic

```bash
aws sns create-topic \
  --name orders.fifo \
  --attributes FifoTopic=true,ContentBasedDeduplication=true
```

### Subscribe FIFO Queue to FIFO Topic

```bash
# Create FIFO queue
aws sqs create-queue \
  --queue-name order-processing.fifo \
  --attributes FifoQueue=true

# Subscribe
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:orders.fifo \
  --protocol sqs \
  --notification-endpoint arn:aws:sqs:us-east-1:123456789012:order-processing.fifo
```

### Publish to FIFO Topic

```python
sns.publish(
    TopicArn='arn:aws:sns:us-east-1:123456789012:orders.fifo',
    Message=json.dumps({'order_id': '12345'}),
    MessageGroupId='customer-abc',
    MessageDeduplicationId='order-12345-v1'
)
```

## Monitoring

### CloudWatch Metrics

Key metrics:
- `NumberOfMessagesPublished`
- `NumberOfNotificationsDelivered`
- `NumberOfNotificationsFailed`
- `PublishSize`

### Enable Delivery Status Logging

```bash
# Create IAM role for logging
aws sns set-topic-attributes \
  --topic-arn arn:aws:sns:us-east-1:123456789012:my-topic \
  --attribute-name LambdaSuccessFeedbackRoleArn \
  --attribute-value arn:aws:iam::123456789012:role/sns-delivery-status-role

aws sns set-topic-attributes \
  --topic-arn arn:aws:sns:us-east-1:123456789012:my-topic \
  --attribute-name LambdaFailureFeedbackRoleArn \
  --attribute-value arn:aws:iam::123456789012:role/sns-delivery-status-role

# Sample percentage (0-100)
aws sns set-topic-attributes \
  --topic-arn arn:aws:sns:us-east-1:123456789012:my-topic \
  --attribute-name LambdaSuccessFeedbackSampleRate \
  --attribute-value 100
```

### Alarm for Failed Deliveries

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "SNS-DeliveryFailures" \
  --metric-name NumberOfNotificationsFailed \
  --namespace AWS/SNS \
  --dimensions Name=TopicName,Value=my-topic \
  --statistic Sum \
  --period 60 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:alerts-topic
```
