"""DynamoDB implementation of WatermarkRepository."""

from __future__ import annotations

from datetime import datetime

from src.adapters.persistence.dynamo_serde import from_canonical_iso, to_canonical_iso
from src.core.ports.watermark import WatermarkRepository


class DynamoWatermarkRepository(WatermarkRepository):
    """DynamoDB repository for managing ingestion watermarks."""

    def __init__(self, db_resource, table_name: str) -> None:
        self._db = db_resource
        self._table = self._db.Table(table_name)

    def get(self, signal_key: str) -> datetime | None:
        response = self._table.get_item(
            Key={
                "pk": f"WATERMARK#{signal_key}",
                "sk": "META",
            },
            ConsistentRead=True,
        )
        item = response.get("Item")
        if not item:
            return None
        return from_canonical_iso(item["watermark"])

    def advance(self, signal_key: str, to: datetime) -> None:
        self._table.put_item(
            Item={
                "pk": f"WATERMARK#{signal_key}",
                "sk": "META",
                "watermark": to_canonical_iso(to),
            }
        )
