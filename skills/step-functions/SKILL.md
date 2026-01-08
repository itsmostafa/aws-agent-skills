---
name: step-functions
description: AWS Step Functions workflow orchestration with state machines. Use when designing workflows, implementing error handling, configuring parallel execution, integrating with AWS services, or debugging executions.
last_updated: "2026-01-07"
doc_source: https://docs.aws.amazon.com/step-functions/latest/dg/
---

# AWS Step Functions

AWS Step Functions is a serverless orchestration service that lets you build and run workflows using state machines. Coordinate multiple AWS services into business-critical applications.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Common Patterns](#common-patterns)
- [CLI Reference](#cli-reference)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [References](#references)

## Core Concepts

### Workflow Types

| Type | Description | Pricing |
|------|-------------|---------|
| **Standard** | Long-running, durable, exactly-once | Per state transition |
| **Express** | High-volume, short-duration | Per execution (time + memory) |

### State Types

| State | Description |
|-------|-------------|
| **Task** | Execute work (Lambda, API call) |
| **Choice** | Conditional branching |
| **Parallel** | Execute branches concurrently |
| **Map** | Iterate over array |
| **Wait** | Delay execution |
| **Pass** | Pass input to output |
| **Succeed** | End successfully |
| **Fail** | End with failure |

### Amazon States Language (ASL)

JSON-based language for defining state machines.

## Common Patterns

### Simple Lambda Workflow

```json
{
  "Comment": "Process order workflow",
  "StartAt": "ValidateOrder",
  "States": {
    "ValidateOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:ValidateOrder",
      "Next": "ProcessPayment"
    },
    "ProcessPayment": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:ProcessPayment",
      "Next": "FulfillOrder"
    },
    "FulfillOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:FulfillOrder",
      "End": true
    }
  }
}
```

### Create State Machine

**AWS CLI:**

```bash
aws stepfunctions create-state-machine \
  --name OrderWorkflow \
  --definition file://workflow.json \
  --role-arn arn:aws:iam::123456789012:role/StepFunctionsRole \
  --type STANDARD
```

**boto3:**

```python
import boto3
import json

sfn = boto3.client('stepfunctions')

definition = {
    "Comment": "Order workflow",
    "StartAt": "ProcessOrder",
    "States": {
        "ProcessOrder": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:...",
            "End": True
        }
    }
}

response = sfn.create_state_machine(
    name='OrderWorkflow',
    definition=json.dumps(definition),
    roleArn='arn:aws:iam::123456789012:role/StepFunctionsRole',
    type='STANDARD'
)
```

### Start Execution

```python
import boto3
import json

sfn = boto3.client('stepfunctions')

response = sfn.start_execution(
    stateMachineArn='arn:aws:states:us-east-1:123456789012:stateMachine:OrderWorkflow',
    name='order-12345',
    input=json.dumps({
        'order_id': '12345',
        'customer_id': 'cust-789',
        'items': [{'product_id': 'prod-1', 'quantity': 2}]
    })
)

execution_arn = response['executionArn']
```

### Choice State (Conditional Logic)

```json
{
  "StartAt": "CheckOrderValue",
  "States": {
    "CheckOrderValue": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.total",
          "NumericGreaterThan": 1000,
          "Next": "HighValueOrder"
        },
        {
          "Variable": "$.priority",
          "StringEquals": "rush",
          "Next": "RushOrder"
        }
      ],
      "Default": "StandardOrder"
    },
    "HighValueOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:ProcessHighValue",
      "End": true
    },
    "RushOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:ProcessRush",
      "End": true
    },
    "StandardOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:ProcessStandard",
      "End": true
    }
  }
}
```

### Parallel Execution

```json
{
  "StartAt": "ProcessInParallel",
  "States": {
    "ProcessInParallel": {
      "Type": "Parallel",
      "Branches": [
        {
          "StartAt": "UpdateInventory",
          "States": {
            "UpdateInventory": {
              "Type": "Task",
              "Resource": "arn:aws:lambda:...:function:UpdateInventory",
              "End": true
            }
          }
        },
        {
          "StartAt": "SendNotification",
          "States": {
            "SendNotification": {
              "Type": "Task",
              "Resource": "arn:aws:lambda:...:function:SendNotification",
              "End": true
            }
          }
        },
        {
          "StartAt": "UpdateAnalytics",
          "States": {
            "UpdateAnalytics": {
              "Type": "Task",
              "Resource": "arn:aws:lambda:...:function:UpdateAnalytics",
              "End": true
            }
          }
        }
      ],
      "Next": "Complete"
    },
    "Complete": {
      "Type": "Succeed"
    }
  }
}
```

### Map State (Iteration)

```json
{
  "StartAt": "ProcessItems",
  "States": {
    "ProcessItems": {
      "Type": "Map",
      "ItemsPath": "$.items",
      "MaxConcurrency": 10,
      "Iterator": {
        "StartAt": "ProcessItem",
        "States": {
          "ProcessItem": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:...:function:ProcessItem",
            "End": true
          }
        }
      },
      "ResultPath": "$.processedItems",
      "End": true
    }
  }
}
```

### Error Handling

```json
{
  "StartAt": "ProcessWithRetry",
  "States": {
    "ProcessWithRetry": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:Process",
      "Retry": [
        {
          "ErrorEquals": ["Lambda.ServiceException", "Lambda.TooManyRequestsException"],
          "IntervalSeconds": 2,
          "MaxAttempts": 6,
          "BackoffRate": 2
        },
        {
          "ErrorEquals": ["States.Timeout"],
          "IntervalSeconds": 5,
          "MaxAttempts": 3,
          "BackoffRate": 1.5
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["CustomError"],
          "ResultPath": "$.error",
          "Next": "HandleCustomError"
        },
        {
          "ErrorEquals": ["States.ALL"],
          "ResultPath": "$.error",
          "Next": "HandleAllErrors"
        }
      ],
      "End": true
    },
    "HandleCustomError": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:function:HandleCustom",
      "End": true
    },
    "HandleAllErrors": {
      "Type": "Fail",
      "Error": "ProcessingFailed",
      "Cause": "An error occurred during processing"
    }
  }
}
```

## CLI Reference

### State Machine Management

| Command | Description |
|---------|-------------|
| `aws stepfunctions create-state-machine` | Create state machine |
| `aws stepfunctions update-state-machine` | Update definition |
| `aws stepfunctions delete-state-machine` | Delete state machine |
| `aws stepfunctions list-state-machines` | List state machines |
| `aws stepfunctions describe-state-machine` | Get details |

### Executions

| Command | Description |
|---------|-------------|
| `aws stepfunctions start-execution` | Start execution |
| `aws stepfunctions stop-execution` | Stop execution |
| `aws stepfunctions describe-execution` | Get execution details |
| `aws stepfunctions list-executions` | List executions |
| `aws stepfunctions get-execution-history` | Get execution history |

## Best Practices

### Design

- **Keep states focused** — one purpose per state
- **Use meaningful state names**
- **Implement comprehensive error handling**
- **Use Parallel for independent tasks**
- **Use Map for batch processing**

### Performance

- **Use Express workflows** for high-volume, short tasks
- **Set appropriate timeouts**
- **Limit Map concurrency** to avoid throttling
- **Use SDK integrations** when possible (avoid Lambda wrapper)

### Reliability

- **Retry transient errors**
- **Catch and handle specific errors**
- **Use idempotent operations**
- **Enable X-Ray tracing**

### Cost Optimization

- **Use Express for short workflows** (< 5 minutes)
- **Combine related operations** to reduce transitions
- **Use Wait states** instead of Lambda delays

## Troubleshooting

### Execution Failed

```bash
# Get execution history
aws stepfunctions get-execution-history \
  --execution-arn arn:aws:states:us-east-1:123456789012:execution:MyWorkflow:exec-123 \
  --query 'events[?type==`TaskFailed` || type==`ExecutionFailed`]'
```

### Lambda Timeout

**Causes:**
- Lambda running too long
- Task timeout too short

**Fix:**

```json
{
  "Type": "Task",
  "Resource": "arn:aws:lambda:...",
  "TimeoutSeconds": 300,
  "HeartbeatSeconds": 60
}
```

### State Stuck

**Check:**
- Task state waiting for callback
- Wait state not yet elapsed
- Activity worker not responding

### Invalid State Machine

```bash
# Validate definition
aws stepfunctions validate-state-machine-definition \
  --definition file://workflow.json
```

## References

- [Step Functions Developer Guide](https://docs.aws.amazon.com/step-functions/latest/dg/)
- [Step Functions API Reference](https://docs.aws.amazon.com/step-functions/latest/apireference/)
- [Step Functions CLI Reference](https://docs.aws.amazon.com/cli/latest/reference/stepfunctions/)
- [Amazon States Language](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-amazon-states-language.html)
