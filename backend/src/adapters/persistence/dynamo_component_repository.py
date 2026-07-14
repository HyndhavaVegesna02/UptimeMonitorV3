"""DynamoDB implementation of ComponentRepository."""

from __future__ import annotations

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from src.core.domain.component import Component, ComponentNotFoundError
from src.core.domain.status import ComponentStatus
from src.core.ports.component_repository import ComponentRepository


class DynamoComponentRepository(ComponentRepository):
    """DynamoDB repository for managing system components."""

    def __init__(self, db_resource, table_name: str) -> None:
        self._db = db_resource
        self._table = self._db.Table(table_name)

    def _map_item(self, item: dict) -> Component:
        return Component(
            id=item["id"],
            name=item["name"],
            status=ComponentStatus(item["status"]),
            app_id=item["app_id"],
        )

    def list_components(self) -> list[Component]:
        response = self._table.query(
            KeyConditionExpression=Key("pk").eq("TOPOLOGY")
            & Key("sk").begins_with("COMPONENT#")
        )
        items = response.get("Items", [])
        return [self._map_item(item) for item in items]

    def get(self, component_id: str) -> Component | None:
        response = self._table.get_item(
            Key={
                "pk": "TOPOLOGY",
                "sk": f"COMPONENT#{component_id}",
            },
            ConsistentRead=True,
        )
        item = response.get("Item")
        if not item:
            return None
        return self._map_item(item)

    def set_status(self, component_id: str, status: ComponentStatus) -> None:
        try:
            self._table.update_item(
                Key={
                    "pk": "TOPOLOGY",
                    "sk": f"COMPONENT#{component_id}",
                },
                UpdateExpression="SET #status = :status",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={":status": status.value},
                ConditionExpression="attribute_exists(pk)",
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise ComponentNotFoundError(component_id)
            raise
