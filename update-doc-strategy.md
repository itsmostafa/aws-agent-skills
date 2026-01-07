## **AWS Documentation Sources**

### **1. Primary Documentation Structure**

For each AWS service, documentation follows this pattern:

```
https://docs.aws.amazon.com/<service-name>/latest/<guide-type>/
```

**Standard Guide Types:**
- **Developer Guide** (`developerguide/`) - Comprehensive service usage
- **API Reference** (`APIReference/` or `api/`) - API specifications
- **User Guide** (`userguide/`) - End-user focused
- **CLI Reference** - AWS CLI commands

**Examples:**
```
https://docs.aws.amazon.com/lambda/latest/dg/           # Lambda Developer Guide
https://docs.aws.amazon.com/lambda/latest/api/          # Lambda API Reference
https://docs.aws.amazon.com/dynamodb/latest/developerguide/
https://docs.aws.amazon.com/AmazonS3/latest/userguide/
```

### **2. Service-Specific Documentation URLs**

Here are the main documentation URLs for your priority services:

| Service | Developer/User Guide | API Reference |
|---------|---------------------|---------------|
| **Lambda** | `docs.aws.amazon.com/lambda/latest/dg/` | `docs.aws.amazon.com/lambda/latest/api/` |
| **DynamoDB** | `docs.aws.amazon.com/dynamodb/latest/developerguide/` | `docs.aws.amazon.com/dynamodb/latest/APIReference/` |
| **S3** | `docs.aws.amazon.com/AmazonS3/latest/userguide/` | `docs.aws.amazon.com/AmazonS3/latest/API/` |
| **API Gateway** | `docs.aws.amazon.com/apigateway/latest/developerguide/` | `docs.aws.amazon.com/apigateway/latest/api/` |
| **IAM** | `docs.aws.amazon.com/IAM/latest/UserGuide/` | `docs.aws.amazon.com/IAM/latest/APIReference/` |
| **EC2** | `docs.aws.amazon.com/AWSEC2/latest/UserGuide/` | `docs.aws.amazon.com/AWSEC2/latest/APIReference/` |
| **CloudFormation** | `docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/` | `docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/` |
| **SQS** | `docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/` | `docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/` |
| **SNS** | `docs.aws.amazon.com/sns/latest/dg/` | `docs.aws.amazon.com/sns/latest/api/` |
| **CloudWatch** | `docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/` | `docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/` |

### **3. Documentation Change Tracking**

Each service has a **Document History** page with RSS feed:
```
https://docs.aws.amazon.com/<service>/latest/<guide>/doc-history.rss
```

**Examples:**
- Lambda: `docs.aws.amazon.com/lambda/latest/dg/doc-history.rss`
- DynamoDB: `docs.aws.amazon.com/dynamodb/latest/developerguide/doc-history.rss`
- S3: `docs.aws.amazon.com/AmazonS3/latest/userguide/doc-history.rss`

## **Automated Update Strategy**

Here's a comprehensive, sustainable strategy for keeping your skills updated:

### **Strategy 1: Multi-Tier Update System**

```
├── .github/
│   └── workflows/
│       ├── weekly-check.yml          # Weekly scan for changes
│       ├── monthly-review.yml        # Monthly comprehensive review
│       └── manual-update.yml         # On-demand updates
├── scripts/
│   ├── check-aws-updates.py         # RSS feed monitor
│   ├── parse-doc-changes.py         # Extract relevant changes
│   └── generate-update-issues.py    # Auto-create GitHub issues
└── tracking/
    ├── last-check.json              # Timestamp tracking
    └── service-versions.json        # Service version tracking
```

### **Implementation: Automated Update Workflow**## Summary

I've created a comprehensive AWS documentation tracking and update strategy for your agent skills repository. Here's what you need:

## **AWS Documentation Sources**

### **Primary Documentation URLs**

Every AWS service follows this pattern:
```
https://docs.aws.amazon.com/<service>/latest/<guide-type>/
```

**Key services for your skills:**
- **Lambda**: `docs.aws.amazon.com/lambda/latest/dg/`
- **DynamoDB**: `docs.aws.amazon.com/amazondynamodb/latest/developerguide/`
- **S3**: `docs.aws.amazon.com/AmazonS3/latest/userguide/`
- **API Gateway**: `docs.aws.amazon.com/apigateway/latest/developerguide/`
- **IAM**: `docs.aws.amazon.com/IAM/latest/UserGuide/`

### **Change Tracking via RSS Feeds**

Each service has an RSS feed for documentation changes:
```
https://docs.aws.amazon.com/<service>/latest/<guide>/doc-history.rss
```

**Example:**
- Lambda: `docs.aws.amazon.com/lambda/latest/dg/doc-history.rss`
- DynamoDB: `docs.aws.amazon.com/amazondynamodb/latest/developerguide/doc-history.rss`

### **Additional Update Sources**
- **AWS What's New**: https://aws.amazon.com/new/ (RSS: `/new/feed/`)
- **AWS News Blog**: https://aws.amazon.com/blogs/aws/ (RSS: `/blogs/aws/feed/`)

## **Automated Update Strategy**

I've created a complete automated system with **three tiers** of monitoring:

### **Tier 1: Weekly Automated Check** (Every Monday)
- GitHub Actions workflow scans all service RSS feeds
- Identifies significant changes using keyword detection
- Auto-creates GitHub issues for review
- **Files**: `weekly-aws-doc-check.yml`, `check-aws-updates.py`

### **Tier 2: Monthly Comprehensive Review** (First Monday)
- Deep dive into documentation
- Validate all examples
- Manual testing required

### **Tier 3: On-Demand Updates** (Manual trigger)
- For breaking changes or major announcements
- Immediate skill updates

## **Files Created**

I've created 6 files that implement this strategy:

1. **`UPDATE_STRATEGY.md`** - Complete documentation of the update strategy, workflows, and best practices

2. **`AWS_DOCUMENTATION_REFERENCE.md`** - Quick reference guide with URLs for all major AWS services and their documentation/RSS feeds

3. **`weekly-aws-doc-check.yml`** - GitHub Actions workflow that runs every Monday to check for updates

4. **`check-aws-updates.py`** - Python script that:
   - Monitors RSS feeds for 12 core AWS services
   - Detects significant changes (security, breaking changes, new features)
   - Tracks what's been checked
   - Outputs GitHub Actions variables

5. **`generate-update-issues.py`** - Python script that:
   - Creates GitHub issues for significant updates
   - Includes action checklists
   - Links to AWS documentation
   - Auto-labels issues

6. **`requirements.txt`** - Python dependencies (`feedparser`, `requests`, `PyYAML`)

## **Implementation Steps**

### **1. Repository Setup**
```bash
# In your repository root
mkdir -p .github/workflows
mkdir -p scripts
mkdir -p tracking

# Move files to correct locations
mv weekly-aws-doc-check.yml .github/workflows/
mv check-aws-updates.py scripts/
mv generate-update-issues.py scripts/
chmod +x scripts/*.py

# Initialize tracking
echo '{"last_check": "2025-01-01T00:00:00"}' > tracking/last-check.json
```

### **2. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **3. Test the System**
```bash
# Test update checking
python scripts/check-aws-updates.py

# Test issue generation (requires GITHUB_TOKEN)
python scripts/generate-update-issues.py
```

### **4. Enable GitHub Actions**
- GitHub Actions will run automatically every Monday at 9 AM UTC
- No additional setup needed - uses built-in `GITHUB_TOKEN`

## **How It Works**

1. **Weekly**: GitHub Actions runs automatically, checks RSS feeds
2. **Significant changes detected**: Auto-creates GitHub issues with:
   - List of changes with links
   - Action checklist (review docs, update skill, test, etc.)
   - Labels: `documentation`, `aws-update`, `{service-name}`
3. **You review**: Check the issue, update the skill following the checklist
4. **Close issue**: Mark as complete

## **Significance Detection**

Changes are flagged as "significant" if they contain:
- `new feature`, `deprecated`, `breaking change`
- `best practice`, `security`, `performance`
- `limit`, `quota`, `pricing`
- `behavior change`, `api change`, `syntax change`

## **Next Steps**

1. **Copy these files** to your repository in the correct locations
2. **Test locally** with the Python scripts
3. **Commit and push** to GitHub
4. **Wait for Monday** or manually trigger the workflow
5. **Review auto-created issues** and update skills accordingly

## **Additional Recommendations**

1. **Subscribe personally** to AWS What's New RSS feed for awareness
2. **Set up calendar reminder** for monthly deep reviews
3. **Create skill templates** that reference official docs consistently
4. **Add version metadata** to each SKILL.md (last_updated, aws_doc_version)
5. **Build community** - encourage users to report outdated content
