"""DynamoDB implementation of SampleModeRepository."""

from __future__ import annotations

from src.core.ports.sample_mode_repository import SampleModeRepository


class DynamoSampleModeRepository(SampleModeRepository):
    """DynamoDB repository for managing the global sample-mode flag."""

    def __init__(self, db_resource, table_name: str) -> None:
        self._db = db_resource
        self._table = self._db.Table(table_name)

    def is_enabled(self) -> bool:
        response = self._table.get_item(
            Key={
                "pk": "CONFIG",
                "sk": "SAMPLE_MODE",
            },
            ConsistentRead=True,
        )
        item = response.get("Item")
        if not item:
            return False
        return bool(item.get("enabled", False))

    def set_enabled(self, enabled: bool) -> None:
        self._table.put_item(
            Item={
                "pk": "CONFIG",
                "sk": "SAMPLE_MODE",
                "enabled": enabled,
            }
        )
