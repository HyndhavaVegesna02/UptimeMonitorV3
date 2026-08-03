"""DynamoDB implementation of SignalRepository."""

from __future__ import annotations

from src.adapters.persistence.topology_keys import (
    signal_item_key,
    signal_query_condition,
)
from src.core.domain.topology import Signal
from src.core.ports.signal_repository import SignalRepository


class DynamoSignalRepository(SignalRepository):
    """DynamoDB repository for reading topology signals."""

    def __init__(self, db_resource, table_name: str) -> None:
        self._db = db_resource
        self._table = self._db.Table(table_name)
        self._limit: int | None = None  # Hook for testing pagination

    def _map_item(self, item: dict) -> Signal:
        interval = item.get("interval_seconds")
        if interval is not None:
            interval = int(interval)
        return Signal(
            signal_key=item["signal_key"],
            name=item["name"],
            component_id=item.get("component_id"),
            interval_seconds=interval,
        )

    def list_signals(self) -> list[Signal]:
        items = []
        exclusive_start_key = None

        while True:
            kwargs = {"KeyConditionExpression": signal_query_condition()}
            if exclusive_start_key:
                kwargs["ExclusiveStartKey"] = exclusive_start_key
            if self._limit is not None:
                kwargs["Limit"] = self._limit

            response = self._table.query(**kwargs)
            items.extend(response.get("Items", []))

            exclusive_start_key = response.get("LastEvaluatedKey")
            if not exclusive_start_key:
                break

        signals = [self._map_item(item) for item in items]
        return sorted(signals, key=lambda s: s.signal_key)

    def get(self, signal_key: str) -> Signal | None:
        response = self._table.get_item(Key=signal_item_key(signal_key))
        item = response.get("Item")
        if not item:
            return None
        return self._map_item(item)
