# AWS Agent Skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Claude-Code-blueviolet)](https://claude.ai/code)
![Last Commit](https://img.shields.io/github/last-commit/itsmostafa/aws-agent-skills)
![GitHub Stars](https://img.shields.io/github/stars/itsmostafa/aws-agent-skills)

Supercharge Claude Code with AWS cloud engineering skills across 18 core AWS services.

## 🚀 Why AWS Agent Skills?

Developing AWS solutions is complex spanning IAM, compute, storage, security, serverless, networking, and more.

AWS Agent Skills equips Claude Code (and Codex) with deep expertise across 18 AWS domains, enabling automated cloud engineering support from IaC templates to debugging guidance and security best practices.

Automatically checks AWS documentation for updates on a weekly basis to ensure skills stay current with AWS service changes.

### Why not just use an MCP?

AWS MCP is great for live docs and API calls, but AWS Agent Skills is designed for reasoning first.
It gives AI Agents a curated, LLM-optimized AWS knowledge base with real-world patterns, edge cases, and best practices, without streaming large docs or schemas.
Because the skills are local and pre compressed, it is far more token efficient, keeps the context window small and predictable, and avoids MCP infrastructure, latency, and expanded credential exposure.

## Installation

### Claude Code

#### From Marketplace

```bash
# Add the marketplace
/plugin marketplace add itsmostafa/aws-agent-skills

# Install the plugin
/plugin install aws-agent-skills
```

#### From GitHub

```bash
/plugin install https://github.com/itsmostafa/aws-agent-skills
```

#### Local Development

```bash
/plugin install ./path/to/aws-agent-skills
```

### Codex CLI

```bash
$skill-installer install https://github.com/itsmostafa/aws-agent-skills/<skill-name>
```

For example, to install the `rlhf` skill:

```bash
$skill-installer install https://github.com/itsmostafa/aws-agent-skills/rlhf
```

### sk

Install via [sk](https://github.com/803/skills-supply), the universal package manager for AI agent skills (supports Claude, Codex, OpenCode, etc...).

```bash
sk pkg add claude-plugin aws-agent-skills@itsmostafa/aws-agent-skills
sk sync
```

## Available Skills

| Skill | Description |
|-------|-------------|
| **iam** | Identity and Access Management - users, roles, policies, permissions |
| **lambda** | Serverless functions - deployment, triggers, debugging |
| **dynamodb** | NoSQL database - table design, queries, indexes |
| **s3** | Object storage - buckets, objects, security, lifecycle |
| **api-gateway** | REST and HTTP APIs - integrations, authorization |
| **ec2** | Virtual machines - instances, AMIs, networking |
| **ecs** | Container orchestration - clusters, services, tasks |
| **eks** | Kubernetes - clusters, node groups, IRSA |
| **cloudformation** | Infrastructure as Code - templates, stacks, drift |
| **cloudwatch** | Monitoring - logs, metrics, alarms, dashboards |
| **rds** | Relational databases - instances, backups, replication |
| **sqs** | Message queues - standard, FIFO, dead-letter queues |
| **sns** | Notifications - topics, subscriptions, filtering |
| **cognito** | User authentication - user pools, identity pools, OAuth |
| **step-functions** | Workflow orchestration - state machines, error handling |
| **secrets-manager** | Secret storage - rotation, versioning, RDS integration |
| **eventbridge** | Event bus - rules, patterns, cross-account events |
| **bedrock** | Foundation models - inference, RAG, custom models |

## Usage Examples

### IAM Policy Creation
Ask Claude to help with IAM:
- "Create an IAM policy for Lambda to access DynamoDB"
- "Set up cross-account access for S3"
- "Debug this access denied error"

### Lambda Development
- "Create a Python Lambda function triggered by S3"
- "Debug my Lambda timeout issues"
- "Set up Lambda with VPC access"

### Infrastructure as Code
- "Write a CloudFormation template for a serverless API"
- "Create an ECS Fargate service with load balancer"
- "Set up EventBridge rules for scheduled tasks"

## Skill Structure

Each skill contains:
- `SKILL.md` - Core concepts, patterns, CLI reference, best practices, troubleshooting
- Supplementary files - Deep dives into specific topics

Skills include metadata showing when content was last updated, so you always know how current the information is.

## Contributing

1. Fork this repository
2. Create a feature branch
3. Add or update skills following the SKILL.md template
4. Submit a pull request

### SKILL.md Template

```yaml
---
name: service-name
description: Service description. Use when <trigger phrases>.
---

# AWS Service Name

## Overview
## Core Concepts
## Common Patterns
## CLI Reference
## Best Practices
## Troubleshooting
## References
```

## License

MIT License - see [LICENSE](LICENSE) for details.
