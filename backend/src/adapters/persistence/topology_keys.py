"""Shared DynamoDB topology key schema (ZR-8 Finding 1, STORY-205).

The single declaration of the `TOPOLOGY` partition's key shape, in BOTH shapes the
schema is consumed in: the item-key dict (`put_item`/`update_item`/`get_item`'s
`Key=`/`Item=`) and the boto3 query condition (`.query()`'s
`KeyConditionExpression=`). `DynamoComponentRepository`, `DynamoSignalRepository`
and `composition/seed_dynamo.py::seed_topology_dynamo` all obtain the schema from
here rather than each re-declaring it — see `docs/scrum/wiki/zone-rules.md` ZR-8.
"""

from __future__ import annotations

from boto3.dynamodb.conditions import ConditionBase, Key

_TOPOLOGY_PK = "TOPOLOGY"

_APP_SK_PREFIX = "APP#"
_COMPONENT_SK_PREFIX = "COMPONENT#"
_SIGNAL_SK_PREFIX = "SIGNAL#"


def app_item_key(app_id: str) -> dict[str, str]:
    """Item key (`pk`/`sk` dict) for an APP topology row."""
    return {"pk": _TOPOLOGY_PK, "sk": f"{_APP_SK_PREFIX}{app_id}"}


def component_item_key(component_id: str) -> dict[str, str]:
    """Item key (`pk`/`sk` dict) for a COMPONENT topology row."""
    return {"pk": _TOPOLOGY_PK, "sk": f"{_COMPONENT_SK_PREFIX}{component_id}"}


def signal_item_key(signal_key: str) -> dict[str, str]:
    """Item key (`pk`/`sk` dict) for a SIGNAL topology row."""
    return {"pk": _TOPOLOGY_PK, "sk": f"{_SIGNAL_SK_PREFIX}{signal_key}"}


def component_query_condition() -> ConditionBase:
    """Query condition selecting every COMPONENT topology row."""
    return Key("pk").eq(_TOPOLOGY_PK) & Key("sk").begins_with(_COMPONENT_SK_PREFIX)


def signal_query_condition() -> ConditionBase:
    """Query condition selecting every SIGNAL topology row."""
    return Key("pk").eq(_TOPOLOGY_PK) & Key("sk").begins_with(_SIGNAL_SK_PREFIX)
