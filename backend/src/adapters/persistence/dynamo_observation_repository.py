"""DynamoDB implementation of ObservationRepository."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from src.adapters.persistence.dynamo_serde import from_canonical_iso, to_canonical_iso
from src.core.domain import Health, Provenance, SignalObservation
from src.core.ports.observation_repository import ObservationRepository


class DynamoObservationRepository(ObservationRepository):
    """DynamoDB repository for managing signal observations."""

    def __init__(self, db_resource, table_name: str) -> None:
        self._db = db_resource
        self._table_name = table_name
        self._table = self._db.Table(table_name)
        self._limit: int | None = None  # Hook for testing pagination

    def save_new(self, batch: Sequence[SignalObservation]) -> int:
        """Persist new observations, skipping any whose event ID already exists.

        Uses TransactWriteItems to atomically write both the data item
        and the dedupe marker, returning the number of newly inserted items.
        """
        if not batch:
            return 0

        client = self._db.meta.client
        newly_inserted = 0

        for observation in batch:
            # Format observed_at with canonical timestamp format
            observed_at_str = to_canonical_iso(observation.observed_at)

            # Data item keys: pk = SIG#<key>, sk = <observed_at>#<event_id>
            data_item = {
                "pk": f"SIG#{observation.signal_key}",
                "sk": f"{observed_at_str}#{observation.source_event_id}",
                "signal_key": observation.signal_key,
                "health": observation.health.value,
                "source_event_id": observation.source_event_id,
                "source": observation.source.model_dump(),
                "location": observation.location,
            }
            if observation.latency_ms is not None:
                data_item["latency_ms"] = observation.latency_ms
            if observation.response_status_code is not None:
                data_item["response_status_code"] = observation.response_status_code
            if observation.raw_ref is not None:
                data_item["raw_ref"] = observation.raw_ref

            # Dedupe marker: pk = EVT#<event_id>, sk = DEDUPE
            dedupe_marker = {
                "pk": f"EVT#{observation.source_event_id}",
                "sk": "DEDUPE",
            }

            try:
                client.transact_write_items(
                    TransactItems=[
                        {
                            "Put": {
                                "TableName": self._table_name,
                                "Item": data_item,
                                "ConditionExpression": "attribute_not_exists(pk)",
                            }
                        },
                        {
                            "Put": {
                                "TableName": self._table_name,
                                "Item": dedupe_marker,
                                "ConditionExpression": "attribute_not_exists(pk)",
                            }
                        },
                    ]
                )
                newly_inserted += 1
            except ClientError as e:
                if e.response["Error"]["Code"] == "TransactionCanceledException":
                    # Condition check failed (already exists/duplicate), skip it
                    pass
                else:
                    raise

        return newly_inserted

    def in_window(
        self, signal_key: str, since: datetime, until: datetime
    ) -> Sequence[SignalObservation]:
        """Return signal_key's observations with observed_at in [since, until)."""
        since_str = to_canonical_iso(since)
        until_str = to_canonical_iso(until)

        items = []
        exclusive_start_key = None

        while True:
            kwargs = {
                "KeyConditionExpression": Key("pk").eq(f"SIG#{signal_key}")
                & Key("sk").between(since_str, until_str)
            }
            if exclusive_start_key:
                kwargs["ExclusiveStartKey"] = exclusive_start_key
            if self._limit is not None:
                kwargs["Limit"] = self._limit

            response = self._table.query(**kwargs)
            items.extend(response.get("Items", []))

            exclusive_start_key = response.get("LastEvaluatedKey")
            if not exclusive_start_key:
                break

        observations = []
        for item in items:
            # Map back to domain model
            # Format of sk is <observed_at>#<event_id>
            sk_parts = item["sk"].split("#")
            observed_at_val = from_canonical_iso(sk_parts[0])

            # int() accepts Decimal directly, so no isinstance branching is needed
            # (STORY-084 quality review: collapsed redundant Decimal/else arms).
            latency_ms = None
            if item.get("latency_ms") is not None:
                latency_ms = int(item["latency_ms"])

            response_status_code = None
            if item.get("response_status_code") is not None:
                response_status_code = int(item["response_status_code"])

            observations.append(
                SignalObservation(
                    signal_key=item["signal_key"],
                    observed_at=observed_at_val,
                    health=Health(item["health"]),
                    source_event_id=item["source_event_id"],
                    source=Provenance(**item["source"]),
                    location=item["location"],
                    latency_ms=latency_ms,
                    response_status_code=response_status_code,
                    raw_ref=item.get("raw_ref"),
                )
            )

        return observations
