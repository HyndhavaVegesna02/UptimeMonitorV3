from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from src.adapters.persistence.dynamo_rejected_observation_repository import (
    DynamoRejectedObservationRepository,
)
from src.composition.settings import load_settings


def test_dynamo_rejected_observation_repository_save(dynamo_resource):
    settings = load_settings()
    repo = DynamoRejectedObservationRepository(
        dynamo_resource, settings.dynamo_control_table
    )

    rejected_at = datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
    payload = {"metric": "cpu", "value": 99.9, "tags": {"env": "prod", "weight": 1.5}}

    # 1. Normal save with signal_key
    repo.save(
        signal_key="signal-1",
        reason="Value out of range",
        payload=payload,
        rejected_at=rejected_at,
    )

    # Scan/Query the table directly to retrieve the item, since the repository has no read method
    response = repo._table.query(
        KeyConditionExpression="pk = :pk",
        ExpressionAttributeValues={":pk": "REJECTED#signal-1"},
    )
    items = response.get("Items", [])
    assert len(items) == 1
    item = items[0]
    assert item["reason"] == "Value out of range"
    assert item["signal_key"] == "signal-1"
    assert item["rejected_at"] == "2026-07-15T12:00:00.000000+00:00"

    # Assert floats were converted to Decimal
    assert item["payload"]["value"] == Decimal("99.9")
    assert item["payload"]["tags"]["weight"] == Decimal("1.5")
    assert item["payload"]["tags"]["env"] == "prod"


def test_dynamo_rejected_observation_repository_save_no_signal_key(dynamo_resource):
    settings = load_settings()
    repo = DynamoRejectedObservationRepository(
        dynamo_resource, settings.dynamo_control_table
    )

    rejected_at = datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
    payload = {"raw": "data"}

    # 2. Save with signal_key=None
    repo.save(
        signal_key=None,
        reason="Malformed JSON",
        payload=payload,
        rejected_at=rejected_at,
    )

    response = repo._table.query(
        KeyConditionExpression="pk = :pk",
        ExpressionAttributeValues={":pk": "REJECTED#UNKNOWN"},
    )
    items = response.get("Items", [])
    assert len(items) == 1
    assert items[0]["reason"] == "Malformed JSON"
    assert "signal_key" not in items[0]


def test_dynamo_rejected_observation_repository_multiple_saves_same_instant(
    dynamo_resource,
):
    settings = load_settings()
    repo = DynamoRejectedObservationRepository(
        dynamo_resource, settings.dynamo_control_table
    )

    rejected_at = datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)

    # Two saves at the same instant should both persist due to distinct uuids in sk
    repo.save(
        signal_key="signal-dup",
        reason="Error 1",
        payload={"x": 1},
        rejected_at=rejected_at,
    )
    repo.save(
        signal_key="signal-dup",
        reason="Error 2",
        payload={"x": 2},
        rejected_at=rejected_at,
    )

    response = repo._table.query(
        KeyConditionExpression="pk = :pk",
        ExpressionAttributeValues={":pk": "REJECTED#signal-dup"},
    )
    items = response.get("Items", [])
    assert len(items) == 2
    reasons = {item["reason"] for item in items}
    assert reasons == {"Error 1", "Error 2"}
