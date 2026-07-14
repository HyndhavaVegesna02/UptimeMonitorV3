from __future__ import annotations

import pytest
from src.composition.settings import load_settings

# Import make_dynamo_resource (will fail initially since composition/dynamo.py doesn't exist)
try:
    from src.composition.dynamo import make_dynamo_resource
except ImportError:
    make_dynamo_resource = None  # type: ignore


def test_import_make_dynamo_resource():
    assert make_dynamo_resource is not None


def test_make_dynamo_resource_roundtrip(dynamo_local, clean_dynamo_tables):
    assert make_dynamo_resource is not None
    settings = load_settings()
    
    # We should have a valid local endpoint URL set by the fixture
    assert settings.dynamo_endpoint_url == dynamo_local.endpoint_url
    
    resource = make_dynamo_resource(settings)
    
    # Assert round-trip on a bootstrapped table (clean_dynamo_tables ensures they exist)
    table = resource.Table(settings.dynamo_control_table)
    table.put_item(Item={"pk": "TEST#COMP", "sk": "META", "val": "composition-works"})
    
    res = table.get_item(Key={"pk": "TEST#COMP", "sk": "META"})
    assert "Item" in res
    assert res["Item"]["val"] == "composition-works"
