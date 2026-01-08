#!/usr/bin/env python3
"""
AWS Documentation Update Checker

Monitors AWS RSS feeds for documentation changes and detects significant updates
using keyword matching. Outputs results for GitHub Actions consumption.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import feedparser

# Service RSS feed mappings (verified working feeds)
SERVICE_FEEDS = {
    "lambda": {
        "rss_url": "https://docs.aws.amazon.com/lambda/latest/dg/lambda-updates.rss",
        "doc_url": "https://docs.aws.amazon.com/lambda/latest/dg/",
    },
    "dynamodb": {
        "rss_url": "https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/dynamodbupdates.rss",
        "doc_url": "https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/",
    },
    "s3": {
        "rss_url": "https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-userguide-rss-updates.rss",
        "doc_url": "https://docs.aws.amazon.com/AmazonS3/latest/userguide/",
    },
    "iam": {
        "rss_url": "https://docs.aws.amazon.com/IAM/latest/UserGuide/aws-iam-release-notes.rss",
        "doc_url": "https://docs.aws.amazon.com/IAM/latest/UserGuide/",
    },
    "api-gateway": {
        "rss_url": "https://docs.aws.amazon.com/apigateway/latest/developerguide/amazon-apigateway-release-notes.rss",
        "doc_url": "https://docs.aws.amazon.com/apigateway/latest/developerguide/",
    },
    "ec2": {
        "rss_url": "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-release-notes.rss",
        "doc_url": "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/",
    },
    "ecs": {
        "rss_url": "https://docs.aws.amazon.com/AmazonECS/latest/developerguide/amazon-ecs-release-notes.rss",
        "doc_url": "https://docs.aws.amazon.com/AmazonECS/latest/developerguide/",
    },
    "eks": {
        "rss_url": "https://docs.aws.amazon.com/eks/latest/userguide/doc-history.rss",
        "doc_url": "https://docs.aws.amazon.com/eks/latest/userguide/",
    },
    "cloudwatch": {
        "rss_url": "https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/amazon-cloudwatch-document-history.rss",
        "doc_url": "https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/",
    },
    "rds": {
        "rss_url": "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rdsupdates.rss",
        "doc_url": "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/",
    },
    "sqs": {
        "rss_url": "https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/recent-updates.rss",
        "doc_url": "https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/",
    },
    "sns": {
        "rss_url": "https://docs.aws.amazon.com/sns/latest/dg/recent-updates.rss",
        "doc_url": "https://docs.aws.amazon.com/sns/latest/dg/",
    },
    "step-functions": {
        "rss_url": "https://docs.aws.amazon.com/step-functions/latest/dg/recent-updates.rss",
        "doc_url": "https://docs.aws.amazon.com/step-functions/latest/dg/",
    },
    "secrets-manager": {
        "rss_url": "https://docs.aws.amazon.com/secretsmanager/latest/userguide/aws-secretsmanager-documentation-updates.rss",
        "doc_url": "https://docs.aws.amazon.com/secretsmanager/latest/userguide/",
    },
}

# Services without dedicated RSS feeds - use AWS What's New feed
FALLBACK_SERVICES = ["cloudformation", "cognito", "eventbridge", "bedrock"]
WHATS_NEW_FEED = "https://aws.amazon.com/new/feed/"

# Keywords that indicate significant changes
SIGNIFICANT_KEYWORDS = [
    "new feature",
    "deprecated",
    "breaking change",
    "security",
    "best practice",
    "performance",
    "limit",
    "quota",
    "pricing",
    "behavior change",
    "api change",
    "syntax change",
    "removed",
    "end of support",
    "migration",
    "update required",
]


def load_last_check(tracking_dir: Path) -> dict:
    """Load the last check timestamp from tracking file."""
    last_check_file = tracking_dir / "last-check.json"
    if last_check_file.exists():
        with open(last_check_file) as f:
            return json.load(f)
    return {"last_check": "1970-01-01T00:00:00", "services_checked": []}


def save_last_check(tracking_dir: Path, data: dict) -> None:
    """Save the current check timestamp to tracking file."""
    last_check_file = tracking_dir / "last-check.json"
    with open(last_check_file, "w") as f:
        json.dump(data, f, indent=2)


def parse_rss_date(date_str: str) -> datetime:
    """Parse RSS date string to datetime object."""
    try:
        # feedparser provides parsed time tuple
        return datetime(*date_str[:6], tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return datetime.min.replace(tzinfo=timezone.utc)


def is_significant(title: str, description: str) -> bool:
    """Check if an update is significant based on keywords."""
    text = f"{title} {description}".lower()
    return any(keyword in text for keyword in SIGNIFICANT_KEYWORDS)


def check_service_feed(service: str, config: dict, since: datetime) -> list:
    """Check a service's RSS feed for updates since the given date."""
    updates = []
    try:
        feed = feedparser.parse(config["rss_url"])
        if feed.bozo:
            print(f"Warning: Error parsing feed for {service}: {feed.bozo_exception}")
            return updates

        for entry in feed.entries:
            pub_date = parse_rss_date(entry.get("published_parsed"))
            if pub_date > since:
                title = entry.get("title", "No title")
                description = entry.get("description", entry.get("summary", ""))
                link = entry.get("link", config["doc_url"])

                if is_significant(title, description):
                    updates.append(
                        {
                            "service": service,
                            "title": title,
                            "description": description[:500],
                            "link": link,
                            "published": pub_date.isoformat(),
                            "significant": True,
                        }
                    )
    except Exception as e:
        print(f"Error checking {service}: {e}")

    return updates


def check_whats_new_for_services(services: list, since: datetime) -> list:
    """Check AWS What's New feed for updates to specific services."""
    updates = []
    try:
        feed = feedparser.parse(WHATS_NEW_FEED)
        if feed.bozo:
            print(f"Warning: Error parsing What's New feed: {feed.bozo_exception}")
            return updates

        for entry in feed.entries:
            pub_date = parse_rss_date(entry.get("published_parsed"))
            if pub_date > since:
                title = entry.get("title", "No title")
                description = entry.get("description", entry.get("summary", ""))
                link = entry.get("link", "")
                text = f"{title} {description}".lower()

                # Check if any of our fallback services are mentioned
                for service in services:
                    service_keywords = {
                        "cloudformation": ["cloudformation", "cfn"],
                        "cognito": ["cognito"],
                        "eventbridge": ["eventbridge", "event bridge"],
                        "bedrock": ["bedrock"],
                    }
                    if any(
                        kw in text for kw in service_keywords.get(service, [service])
                    ):
                        if is_significant(title, description):
                            updates.append(
                                {
                                    "service": service,
                                    "title": title,
                                    "description": description[:500],
                                    "link": link,
                                    "published": pub_date.isoformat(),
                                    "significant": True,
                                    "source": "whats-new",
                                }
                            )
    except Exception as e:
        print(f"Error checking What's New feed: {e}")

    return updates


def main():
    # Determine paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    tracking_dir = repo_root / "tracking"

    # Load last check timestamp
    last_check_data = load_last_check(tracking_dir)
    last_check_str = last_check_data.get("last_check", "1970-01-01T00:00:00")
    since = datetime.fromisoformat(last_check_str.replace("Z", "+00:00"))

    print(f"Checking for updates since: {since.isoformat()}")

    all_updates = []

    # Check services with dedicated RSS feeds
    for service, config in SERVICE_FEEDS.items():
        print(f"Checking {service}...")
        updates = check_service_feed(service, config, since)
        all_updates.extend(updates)
        print(f"  Found {len(updates)} significant updates")

    # Check fallback services via What's New feed
    print("Checking What's New feed for fallback services...")
    fallback_updates = check_whats_new_for_services(FALLBACK_SERVICES, since)
    all_updates.extend(fallback_updates)
    print(f"  Found {len(fallback_updates)} significant updates")

    # Save results
    now = datetime.now(timezone.utc)
    save_last_check(
        tracking_dir,
        {
            "last_check": now.isoformat(),
            "services_checked": list(SERVICE_FEEDS.keys()) + FALLBACK_SERVICES,
        },
    )

    # Output for GitHub Actions
    updates_file = tracking_dir / "pending-updates.json"
    with open(updates_file, "w") as f:
        json.dump(all_updates, f, indent=2)

    # Set GitHub Actions outputs
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"updates_found={len(all_updates) > 0}\n")
            f.write(f"update_count={len(all_updates)}\n")

    print(f"\nTotal significant updates found: {len(all_updates)}")

    if all_updates:
        print("\nUpdates summary:")
        for update in all_updates:
            print(f"  - [{update['service']}] {update['title']}")

    return 0 if not all_updates else 1


if __name__ == "__main__":
    sys.exit(main())
