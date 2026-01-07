# Step Functions Workflow Patterns

Advanced workflow patterns and SDK integrations.

## SDK Integrations

### Lambda (Optimized)

```json
{
  "Type": "Task",
  "Resource": "arn:aws:states:::lambda:invoke",
  "Parameters": {
    "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:MyFunction",
    "Payload.$": "$"
  },
  "OutputPath": "$.Payload",
  "End": true
}
```

### DynamoDB GetItem

```json
{
  "Type": "Task",
  "Resource": "arn:aws:states:::dynamodb:getItem",
  "Parameters": {
    "TableName": "Orders",
    "Key": {
      "order_id": {"S.$": "$.order_id"}
    }
  },
  "ResultPath": "$.order",
  "Next": "ProcessOrder"
}
```

### DynamoDB PutItem

```json
{
  "Type": "Task",
  "Resource": "arn:aws:states:::dynamodb:putItem",
  "Parameters": {
    "TableName": "Orders",
    "Item": {
      "order_id": {"S.$": "$.order_id"},
      "status": {"S": "processed"},
      "processed_at": {"S.$": "$$.State.EnteredTime"}
    }
  },
  "End": true
}
```

### SQS SendMessage

```json
{
  "Type": "Task",
  "Resource": "arn:aws:states:::sqs:sendMessage",
  "Parameters": {
    "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789012/my-queue",
    "MessageBody.$": "States.JsonToString($)"
  },
  "End": true
}
```

### SNS Publish

```json
{
  "Type": "Task",
  "Resource": "arn:aws:states:::sns:publish",
  "Parameters": {
    "TopicArn": "arn:aws:sns:us-east-1:123456789012:my-topic",
    "Message.$": "$.message",
    "Subject": "Order Notification"
  },
  "End": true
}
```

### Step Functions (Nested)

```json
{
  "Type": "Task",
  "Resource": "arn:aws:states:::states:startExecution.sync:2",
  "Parameters": {
    "StateMachineArn": "arn:aws:states:us-east-1:123456789012:stateMachine:ChildWorkflow",
    "Input.$": "$"
  },
  "End": true
}
```

### ECS RunTask

```json
{
  "Type": "Task",
  "Resource": "arn:aws:states:::ecs:runTask.sync",
  "Parameters": {
    "LaunchType": "FARGATE",
    "Cluster": "arn:aws:ecs:us-east-1:123456789012:cluster/my-cluster",
    "TaskDefinition": "my-task:1",
    "NetworkConfiguration": {
      "AwsvpcConfiguration": {
        "Subnets": ["subnet-12345678"],
        "SecurityGroups": ["sg-12345678"],
        "AssignPublicIp": "ENABLED"
      }
    },
    "Overrides": {
      "ContainerOverrides": [{
        "Name": "my-container",
        "Environment": [
          {"Name": "INPUT", "Value.$": "States.JsonToString($)"}
        ]
      }]
    }
  },
  "End": true
}
```

### EventBridge PutEvents

```json
{
  "Type": "Task",
  "Resource": "arn:aws:states:::events:putEvents",
  "Parameters": {
    "Entries": [
      {
        "Source": "my-app.orders",
        "DetailType": "Order Completed",
        "Detail.$": "States.JsonToString($)",
        "EventBusName": "my-event-bus"
      }
    ]
  },
  "End": true
}
```

## Callback Pattern

### Wait for External Process

```json
{
  "Type": "Task",
  "Resource": "arn:aws:states:::sqs:sendMessage.waitForTaskToken",
  "Parameters": {
    "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789012/approval-queue",
    "MessageBody": {
      "token.$": "$$.Task.Token",
      "order_id.$": "$.order_id",
      "action": "approve_order"
    }
  },
  "TimeoutSeconds": 86400,
  "Next": "ProcessApproval"
}
```

### Complete Callback (from external process)

```python
import boto3

sfn = boto3.client('stepfunctions')

# On success
sfn.send_task_success(
    taskToken=task_token,
    output='{"approved": true, "approver": "user@example.com"}'
)

# On failure
sfn.send_task_failure(
    taskToken=task_token,
    error='RejectedError',
    cause='Order rejected by approver'
)

# Heartbeat (for long-running tasks)
sfn.send_task_heartbeat(taskToken=task_token)
```

## Distributed Map

### Process Large Dataset

```json
{
  "Type": "Map",
  "ItemProcessor": {
    "ProcessorConfig": {
      "Mode": "DISTRIBUTED",
      "ExecutionType": "STANDARD"
    },
    "StartAt": "ProcessItem",
    "States": {
      "ProcessItem": {
        "Type": "Task",
        "Resource": "arn:aws:lambda:...:function:ProcessItem",
        "End": true
      }
    }
  },
  "ItemReader": {
    "Resource": "arn:aws:states:::s3:getObject",
    "ReaderConfig": {
      "InputType": "JSON"
    },
    "Parameters": {
      "Bucket": "my-bucket",
      "Key": "input/data.json"
    }
  },
  "ResultWriter": {
    "Resource": "arn:aws:states:::s3:putObject",
    "Parameters": {
      "Bucket": "my-bucket",
      "Prefix": "output"
    }
  },
  "MaxConcurrency": 1000,
  "End": true
}
```

## Intrinsic Functions

### String Operations

```json
{
  "Type": "Pass",
  "Parameters": {
    "concatenated.$": "States.Format('Order {} for customer {}', $.order_id, $.customer_id)",
    "split.$": "States.StringSplit($.tags, ',')",
    "uuid.$": "States.UUID()"
  }
}
```

### Array Operations

```json
{
  "Type": "Pass",
  "Parameters": {
    "arrayLength.$": "States.ArrayLength($.items)",
    "firstItem.$": "States.ArrayGetItem($.items, 0)",
    "range.$": "States.ArrayRange(1, 10, 2)",
    "partition.$": "States.ArrayPartition($.items, 10)",
    "unique.$": "States.ArrayUnique($.items)"
  }
}
```

### JSON Operations

```json
{
  "Type": "Pass",
  "Parameters": {
    "stringified.$": "States.JsonToString($.data)",
    "parsed.$": "States.StringToJson($.jsonString)",
    "merged.$": "States.JsonMerge($.base, $.override, false)"
  }
}
```

### Math Operations

```json
{
  "Type": "Pass",
  "Parameters": {
    "sum.$": "States.MathAdd($.a, $.b)",
    "random.$": "States.MathRandom(1, 100)"
  }
}
```

## Common Patterns

### Saga Pattern (Compensation)

```json
{
  "StartAt": "ReserveInventory",
  "States": {
    "ReserveInventory": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:ReserveInventory",
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "Next": "FailOrder"
      }],
      "Next": "ProcessPayment"
    },
    "ProcessPayment": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:ProcessPayment",
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "ResultPath": "$.error",
        "Next": "ReleaseInventory"
      }],
      "Next": "ShipOrder"
    },
    "ShipOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:ShipOrder",
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "ResultPath": "$.error",
        "Next": "RefundPayment"
      }],
      "End": true
    },
    "ReleaseInventory": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:ReleaseInventory",
      "Next": "FailOrder"
    },
    "RefundPayment": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:RefundPayment",
      "Next": "ReleaseInventory"
    },
    "FailOrder": {
      "Type": "Fail",
      "Error": "OrderFailed",
      "Cause": "Order processing failed"
    }
  }
}
```

### Human Approval

```json
{
  "StartAt": "SubmitRequest",
  "States": {
    "SubmitRequest": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "CreateApprovalRequest",
        "Payload.$": "$"
      },
      "Next": "WaitForApproval"
    },
    "WaitForApproval": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke.waitForTaskToken",
      "Parameters": {
        "FunctionName": "SendApprovalEmail",
        "Payload": {
          "token.$": "$$.Task.Token",
          "request.$": "$"
        }
      },
      "TimeoutSeconds": 604800,
      "Catch": [{
        "ErrorEquals": ["States.Timeout"],
        "Next": "RequestExpired"
      }],
      "Next": "CheckApproval"
    },
    "CheckApproval": {
      "Type": "Choice",
      "Choices": [{
        "Variable": "$.approved",
        "BooleanEquals": true,
        "Next": "ProcessApproved"
      }],
      "Default": "ProcessRejected"
    },
    "ProcessApproved": {
      "Type": "Succeed"
    },
    "ProcessRejected": {
      "Type": "Fail",
      "Error": "Rejected"
    },
    "RequestExpired": {
      "Type": "Fail",
      "Error": "Expired"
    }
  }
}
```

### Polling Pattern

```json
{
  "StartAt": "SubmitJob",
  "States": {
    "SubmitJob": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:SubmitJob",
      "Next": "Wait"
    },
    "Wait": {
      "Type": "Wait",
      "Seconds": 30,
      "Next": "CheckStatus"
    },
    "CheckStatus": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:CheckJobStatus",
      "Next": "IsComplete"
    },
    "IsComplete": {
      "Type": "Choice",
      "Choices": [{
        "Variable": "$.status",
        "StringEquals": "COMPLETED",
        "Next": "GetResults"
      }, {
        "Variable": "$.status",
        "StringEquals": "FAILED",
        "Next": "JobFailed"
      }],
      "Default": "Wait"
    },
    "GetResults": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:GetResults",
      "End": true
    },
    "JobFailed": {
      "Type": "Fail"
    }
  }
}
```
