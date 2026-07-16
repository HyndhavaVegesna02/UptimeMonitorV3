#!/usr/bin/env python
"""Create DynamoDB Local tables for Uptime Monitor V3."""

from __future__ import annotations

import sys
from pathlib import Path

# Add backend to path so we can import src.composition.settings
REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND = REPO_ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import boto3  # noqa: E402
from botocore.exceptions import ClientError  # noqa: E402
from src.composition.settings import load_settings  # noqa: E402


def create_tables() -> None:
    settings = load_settings()

    # Build resource client
    client_kwargs: dict = {
        "region_name": settings.aws_region,
    }
    if settings.dynamo_endpoint_url:
        client_kwargs["endpoint_url"] = settings.dynamo_endpoint_url
        client_kwargs["aws_access_key_id"] = "test"
        client_kwargs["aws_secret_access_key"] = "test"

    dynamodb = boto3.client("dynamodb", **client_kwargs)

    # 1. Create Observations Table
    obs_name = settings.dynamo_observations_table
    try:
        print(f"Creating observations table {obs_name!r}...")
        dynamodb.create_table(
            TableName=obs_name,
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        # Wait for table to exist
        waiter = dynamodb.get_waiter("table_exists")
        waiter.wait(TableName=obs_name)
        print(f"Observations table {obs_name!r} is ACTIVE.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"Observations table {obs_name!r} already exists.")
        else:
            raise

    # 2. Create Control Table
    ctrl_name = settings.dynamo_control_table
    try:
        print(f"Creating control table {ctrl_name!r}...")
        dynamodb.create_table(
            TableName=ctrl_name,
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
                {"AttributeName": "gsi1pk", "AttributeType": "S"},
                {"AttributeName": "gsi1sk", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "gsi1",
                    "KeySchema": [
                        {"AttributeName": "gsi1pk", "KeyType": "HASH"},
                        {"AttributeName": "gsi1sk", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
        )
        # Wait for table to exist
        waiter = dynamodb.get_waiter("table_exists")
        waiter.wait(TableName=ctrl_name)
        print(f"Control table {ctrl_name!r} is ACTIVE.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"Control table {ctrl_name!r} already exists.")
        else:
            raise


def main(argv: list[str] | None = None) -> int:
    create_tables()
    return 0


if __name__ == "__main__":
    sys.exit(main())
