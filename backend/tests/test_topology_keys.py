"""Unit tests for the shared DynamoDB topology key schema (STORY-205, ZR-8 Finding 1).

Cites: docs/scrum/wiki/zone-rules.md ZR-8. The two key SHAPES the finding names --
the item-key dict and the boto3 query condition -- are pinned separately so a fix
that only moves the dict shape cannot pass silently.
"""

from __future__ import annotations

from boto3.dynamodb.conditions import Key
from src.adapters.persistence.topology_keys import (
    _TOPOLOGY_PK,
    app_item_key,
    component_item_key,
    component_query_condition,
    signal_item_key,
    signal_query_condition,
)


def test_topology_pk_constant() -> None:
    assert _TOPOLOGY_PK == "TOPOLOGY"


def test_app_item_key_shape() -> None:
    assert app_item_key("app-1") == {"pk": "TOPOLOGY", "sk": "APP#app-1"}


def test_component_item_key_shape() -> None:
    assert component_item_key("comp-1") == {"pk": "TOPOLOGY", "sk": "COMPONENT#comp-1"}


def test_signal_item_key_shape() -> None:
    assert signal_item_key("sig-1") == {"pk": "TOPOLOGY", "sk": "SIGNAL#sig-1"}


def test_component_query_condition_matches_hand_built_condition() -> None:
    expected = Key("pk").eq("TOPOLOGY") & Key("sk").begins_with("COMPONENT#")
    assert component_query_condition() == expected


def test_signal_query_condition_matches_hand_built_condition() -> None:
    expected = Key("pk").eq("TOPOLOGY") & Key("sk").begins_with("SIGNAL#")
    assert signal_query_condition() == expected
