Hullo @itsmostafa 👋

I ran your skills through `tessl skill review` at work and found some targeted improvements. Here's the before/after:

| Skill | Before | After | Change |
|-------|--------|-------|--------|
| rds | 74% | 100% | +26% |
| eventbridge | 77% | 100% | +23% |
| bedrock | 74% | 94% | +20% |
| sns | 75% | 94% | +19% |
| ec2 | 83% | 100% | +17% |
| dynamodb | 75% | 90% | +15% |
| step-functions | 77% | 90% | +13% |
| lambda | 83% | 94% | +11% |
| s3 | 83% | 94% | +11% |
| iam | 83% | 94% | +11% |
| cloudwatch | 83% | 94% | +11% |
| ecs | 83% | 94% | +11% |
| eks | 83% | 94% | +11% |
| secrets-manager | 83% | 94% | +11% |
| cognito | 83% | 90% | +7% |
| api-gateway | 90% | 94% | +4% |
| sqs | 89% | 90% | +1% |
| cloudformation | 90% | 90% | +0% |

<details>
<summary>Changes made</summary>

**Across all 18 skills:**
- Removed introductory paragraphs explaining what each service is (Claude already knows)
- Removed Table of Contents sections (unnecessary token overhead for agents)
- Trimmed Core Concepts sections where they explained fundamentals Claude already understands
- Moved `last_updated` and `doc_source` frontmatter keys to `metadata:` block (fixes validation warnings)
- Added validation checkpoints to key workflows (e.g., verify resource created before proceeding)

**Description improvements for 6 skills scoring below 100%:**
- **bedrock**: Added AWS-specific trigger terms (`boto3 bedrock-runtime`, `InvokeModel API`, `Amazon Titan`, `knowledge bases`)
- **rds**: Added RDS-specific terms (`Multi-AZ`, `parameter groups`, `RDS snapshots`, `DB instances`)
- **dynamodb**: Added DynamoDB-specific terms (`partition key`, `sort key`, `GSI`, `LSI`, `read/write capacity units`)
- **sns**: Added user-friendly terms (`push notifications`, `SMS alerts`, `publish-subscribe`, `fan-out patterns`)
- **eventbridge**: Made actions more concrete (`writing event pattern rules`, `creating cron-based or rate-based schedules`)
- **step-functions**: Made actions more concrete (`writing ASL state machine definitions`, `configuring retry and catch policies`)

</details>

Honest disclosure — I work at @tesslio where we build tooling around skills like these. Not a pitch — just saw room for improvement and wanted to contribute.

If you want to run evals yourself, click [here](https://tessl.io/registry/skills/submit).

Thanks in advance 🙏
