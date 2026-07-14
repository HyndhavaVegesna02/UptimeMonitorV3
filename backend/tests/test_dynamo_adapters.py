from __future__ import annotations

from src.composition.settings import load_settings
from src.core.domain.topology import Signal
from tests.test_signal_repository_contract import (
    _assert_signal_repository_contract,
    _sample_signals,
)


def _seed_signals_dynamo(dynamo_resource, settings, signals: list[Signal]) -> None:
    table = dynamo_resource.Table(settings.dynamo_control_table)
    for signal in signals:
        item = {
            "pk": "TOPOLOGY",
            "sk": f"SIGNAL#{signal.signal_key}",
            "signal_key": signal.signal_key,
            "name": signal.name,
        }
        if signal.component_id is not None:
            item["component_id"] = signal.component_id
        if signal.interval_seconds is not None:
            item["interval_seconds"] = signal.interval_seconds
        table.put_item(Item=item)


def test_dynamo_signal_repository_empty(dynamo_resource):
    from src.adapters.persistence.dynamo_signal_repository import DynamoSignalRepository

    settings = load_settings()
    repo = DynamoSignalRepository(dynamo_resource, settings)
    assert repo.list_signals() == []
    assert repo.get("anything") is None


def test_dynamo_signal_repository_contract(dynamo_resource):
    from src.adapters.persistence.dynamo_signal_repository import DynamoSignalRepository

    settings = load_settings()
    _seed_signals_dynamo(dynamo_resource, settings, _sample_signals())
    repo = DynamoSignalRepository(dynamo_resource, settings)
    _assert_signal_repository_contract(repo)
