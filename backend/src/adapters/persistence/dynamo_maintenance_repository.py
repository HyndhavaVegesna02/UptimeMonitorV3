"""DynamoDB implementation of MaintenanceRepository."""

from __future__ import annotations

from datetime import datetime

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from src.adapters.persistence.dynamo_serde import from_canonical_iso, to_canonical_iso
from src.core.domain.maintenance import (
    MaintenanceWindow,
    MaintenanceWindowNotFoundError,
)
from src.core.ports.maintenance_repository import MaintenanceRepository


class DynamoMaintenanceRepository(MaintenanceRepository):
    """DynamoDB repository for scheduling and querying maintenance windows (STORY-086).

    Note: GSI reads are eventually consistent. A window created seconds earlier
    may be missed by is_under_maintenance for one pull cycle. This is an
    accepted design trade-off since maintenance windows are scheduled ahead of time
    (PO-accepted 2026-07-14).
    """

    def __init__(self, db_resource, table_name: str) -> None:
        self._db = db_resource
        self._table_name = table_name
        self._table = self._db.Table(table_name)
        self._limit: int | None = None  # Hook for testing pagination

    def _next_id(self) -> int:
        """Increment sequence counter and return the next Maintenance ID."""
        response = self._table.update_item(
            Key={"pk": "COUNTER", "sk": "maintenance"},
            UpdateExpression="ADD seq :inc",
            ExpressionAttributeValues={":inc": 1},
            ReturnValues="UPDATED_NEW",
        )
        return int(response["Attributes"]["seq"])

    def create(self, window: MaintenanceWindow) -> MaintenanceWindow:
        """Persist a new maintenance window."""
        assigned_id = self._next_id()
        starts_at_str = to_canonical_iso(window.starts_at)
        ends_at_str = to_canonical_iso(window.ends_at)

        item = {
            "pk": f"MAINTWIN#{assigned_id}",
            "sk": "META",
            "id": assigned_id,
            "component_id": window.component_id,
            "starts_at": starts_at_str,
            "ends_at": ends_at_str,
            "gsi1pk": "MAINT",
            "gsi1sk": f"{starts_at_str}#{assigned_id}",
        }
        if window.reason is not None:
            item["reason"] = window.reason
        if window.title is not None:
            item["title"] = window.title

        self._table.put_item(Item=item)
        return window.model_copy(update={"id": assigned_id})

    def list_windows(self) -> list[MaintenanceWindow]:
        """Retrieve all scheduled maintenance windows, ordered by starts_at ascending."""
        items = []
        exclusive_start_key = None

        while True:
            kwargs = {
                "IndexName": "gsi1",
                "KeyConditionExpression": Key("gsi1pk").eq("MAINT"),
                "ScanIndexForward": True,
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

        return [
            MaintenanceWindow(
                id=int(item["id"]),
                component_id=item["component_id"],
                starts_at=from_canonical_iso(item["starts_at"]),
                ends_at=from_canonical_iso(item["ends_at"]),
                reason=item.get("reason"),
                title=item.get("title"),
            )
            for item in items
        ]

    def is_under_maintenance(self, component_id: str, at: datetime) -> bool:
        """Check if a component is under active maintenance at a given timestamp."""
        at_str = to_canonical_iso(at)
        # Query gsi1 for all windows starting at or before `at`
        response = self._table.query(
            IndexName="gsi1",
            KeyConditionExpression=Key("gsi1pk").eq("MAINT")
            & Key("gsi1sk").lte(f"{at_str}#\ufffd"),
            FilterExpression="ends_at > :at_str AND component_id = :cid",
            ExpressionAttributeValues={":at_str": at_str, ":cid": component_id},
        )
        return len(response.get("Items", [])) > 0

    def delete(self, window_id: int) -> None:
        """Delete a maintenance window by its ID."""
        try:
            self._table.delete_item(
                Key={"pk": f"MAINTWIN#{window_id}", "sk": "META"},
                ConditionExpression="attribute_exists(pk)",
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise MaintenanceWindowNotFoundError(
                    f"Maintenance window with ID {window_id} not found."
                )
            raise
