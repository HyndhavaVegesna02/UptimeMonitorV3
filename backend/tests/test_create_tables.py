from __future__ import annotations

import os
import sys
from pathlib import Path
import boto3
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

# Import create_tables (fails initially since scripts/create_tables.py doesn't exist)
try:
    import create_tables
except ImportError:
    create_tables = None  # type: ignore


def test_import_create_tables():
    assert create_tables is not None


def test_create_tables_idempotency_and_schema(dynamo_local, monkeypatch):
    assert create_tables is not None

    endpoint_url = dynamo_local.endpoint_url
    # Use monkeypatch to ensure settings resolve to our test local DynamoDB
    monkeypatch.setenv("DYNAMO_ENDPOINT_URL", endpoint_url)
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    # Clean env tables names to defaults
    monkeypatch.delenv("DYNAMO_OBSERVATIONS_TABLE", raising=False)
    monkeypatch.delenv("DYNAMO_CONTROL_TABLE", raising=False)

    # First run: create tables
    create_tables.main([])

    # Verify tables exist and have correct schemas
    dynamo = boto3.resource(
        "dynamodb",
        endpoint_url=endpoint_url,
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )

    obs_table = dynamo.Table("uptime-observations")
    ctrl_table = dynamo.Table("uptime-control")

    # Assert observations schema
    obs_desc = obs_table.meta.client.describe_table(TableName="uptime-observations")["Table"]
    assert obs_desc["TableStatus"] == "ACTIVE"
    assert obs_desc["BillingModeSummary"]["BillingMode"] == "PAY_PER_REQUEST"
    
    key_schema = {k["AttributeName"]: k["KeyType"] for k in obs_desc["KeySchema"]}
    assert key_schema == {"pk": "HASH", "sk": "RANGE"}

    attr_types = {a["AttributeName"]: a["AttributeType"] for a in obs_desc["AttributeDefinitions"]}
    assert attr_types["pk"] == "S"
    assert attr_types["sk"] == "S"

    # Assert control schema
    ctrl_desc = ctrl_table.meta.client.describe_table(TableName="uptime-control")["Table"]
    assert ctrl_desc["TableStatus"] == "ACTIVE"
    assert ctrl_desc["BillingModeSummary"]["BillingMode"] == "PAY_PER_REQUEST"

    ctrl_keys = {k["AttributeName"]: k["KeyType"] for k in ctrl_desc["KeySchema"]}
    assert ctrl_keys == {"pk": "HASH", "sk": "RANGE"}

    # Check GSI
    gsi = ctrl_desc["GlobalSecondaryIndexes"][0]
    assert gsi["IndexName"] == "gsi1"
    assert gsi["Projection"]["ProjectionType"] == "ALL"
    
    gsi_keys = {k["AttributeName"]: k["KeyType"] for k in gsi["KeySchema"]}
    assert gsi_keys == {"gsi1pk": "HASH", "gsi1sk": "RANGE"}

    ctrl_attrs = {a["AttributeName"]: a["AttributeType"] for a in ctrl_desc["AttributeDefinitions"]}
    assert ctrl_attrs["pk"] == "S"
    assert ctrl_attrs["sk"] == "S"
    assert ctrl_attrs["gsi1pk"] == "S"
    assert ctrl_attrs["gsi1sk"] == "S"

    # Second run: should run cleanly and not raise errors (idempotence)
    create_tables.main([])


def test_create_tables_custom_names_via_env(dynamo_local, monkeypatch):
    assert create_tables is not None

    endpoint_url = dynamo_local.endpoint_url
    monkeypatch.setenv("DYNAMO_ENDPOINT_URL", endpoint_url)
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("DYNAMO_OBSERVATIONS_TABLE", "custom-observations-table")
    monkeypatch.setenv("DYNAMO_CONTROL_TABLE", "custom-control-table")

    create_tables.main([])

    dynamo = boto3.resource(
        "dynamodb",
        endpoint_url=endpoint_url,
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )

    obs_table = dynamo.Table("custom-observations-table")
    ctrl_table = dynamo.Table("custom-control-table")

    assert obs_table.table_status == "ACTIVE"
    assert ctrl_table.table_status == "ACTIVE"
