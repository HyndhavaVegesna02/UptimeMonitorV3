"""DynamoDB implementation of SignalRepository."""

from __future__ import annotations

from boto3.dynamodb.conditions import Key

from src.core.domain.topology import Signal
from src.core.ports.signal_repository import SignalRepository


class DynamoSignalRepository(SignalRepository):
    """DynamoDB repository for reading topology signals."""

    def __init__(self, db_resource, table_name: str) -> None:
        self._db = db_resource
        self._table = self._db.Table(table_name)

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
        response = self._table.query(
            KeyConditionExpression=Key("pk").eq("TOPOLOGY")
            & Key("sk").begins_with("SIGNAL#")
        )
        items = response.get("Items", [])
        signals = [self._map_item(item) for item in items]
        return sorted(signals, key=lambda s: s.signal_key)

    def get(self, signal_key: str) -> Signal | None:
        response = self._table.get_item(
            Key={
                "pk": "TOPOLOGY",
                "sk": f"SIGNAL#{signal_key}",
            }
        )
        item = response.get("Item")
        if not item:
            return None
        return self._map_item(item)
