from __future__ import annotations

from src.composition.settings import load_settings
from src.core.domain.status import ComponentStatus
from src.core.domain.topology import Signal
from tests.test_component_repository_contract import _assert_set_status_contract
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


def _seed_component_dynamo(
    dynamo_resource,
    settings,
    component_id: str,
    app_id: str = "app-1",
    name: str = None,
    status: ComponentStatus = ComponentStatus.OPERATIONAL,
) -> None:
    table = dynamo_resource.Table(settings.dynamo_control_table)
    table.put_item(
        Item={
            "pk": "TOPOLOGY",
            "sk": f"COMPONENT#{component_id}",
            "id": component_id,
            "name": name or component_id,
            "status": status.value,
            "app_id": app_id,
        }
    )


def test_dynamo_component_repository_empty(dynamo_resource):
    from src.adapters.persistence.dynamo_component_repository import (
        DynamoComponentRepository,
    )

    settings = load_settings()
    repo = DynamoComponentRepository(dynamo_resource, settings)
    assert repo.list_components() == []
    assert repo.get("anything") is None


def test_dynamo_component_repository_get_consistent_read(dynamo_resource):
    from src.adapters.persistence.dynamo_component_repository import (
        DynamoComponentRepository,
    )

    settings = load_settings()
    _seed_component_dynamo(dynamo_resource, settings, "comp-1")
    repo = DynamoComponentRepository(dynamo_resource, settings)

    # Spy on get_item
    table = repo._table
    original_get_item = table.get_item
    spy_kwargs = []

    def spied_get_item(*args, **kwargs):
        spy_kwargs.append(kwargs)
        return original_get_item(*args, **kwargs)

    table.get_item = spied_get_item

    comp = repo.get("comp-1")
    assert comp is not None
    assert comp.id == "comp-1"
    assert len(spy_kwargs) == 1
    assert spy_kwargs[0].get("ConsistentRead") is True


def test_dynamo_component_repository_set_status_contract(dynamo_resource):
    from src.adapters.persistence.dynamo_component_repository import (
        DynamoComponentRepository,
    )

    settings = load_settings()
    _seed_component_dynamo(dynamo_resource, settings, "set-status-comp")
    repo = DynamoComponentRepository(dynamo_resource, settings)
    _assert_set_status_contract(repo, known_id="set-status-comp")
