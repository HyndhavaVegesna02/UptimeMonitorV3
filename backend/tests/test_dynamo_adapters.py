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
    repo = DynamoSignalRepository(dynamo_resource, settings.dynamo_control_table)
    assert repo.list_signals() == []
    assert repo.get("anything") is None


def test_dynamo_signal_repository_contract(dynamo_resource):
    from src.adapters.persistence.dynamo_signal_repository import DynamoSignalRepository

    settings = load_settings()
    _seed_signals_dynamo(dynamo_resource, settings, _sample_signals())
    repo = DynamoSignalRepository(dynamo_resource, settings.dynamo_control_table)
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
    repo = DynamoComponentRepository(dynamo_resource, settings.dynamo_control_table)
    assert repo.list_components() == []
    assert repo.get("anything") is None


def test_dynamo_component_repository_get_consistent_read(dynamo_resource):
    from src.adapters.persistence.dynamo_component_repository import (
        DynamoComponentRepository,
    )

    settings = load_settings()
    _seed_component_dynamo(dynamo_resource, settings, "comp-1")
    repo = DynamoComponentRepository(dynamo_resource, settings.dynamo_control_table)

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
    repo = DynamoComponentRepository(dynamo_resource, settings.dynamo_control_table)
    _assert_set_status_contract(repo, known_id="set-status-comp")


def test_dynamo_component_repository_list_components_paginates(dynamo_resource):
    """STORY-199 AC2: forcing a small page size must not truncate list_components
    against component_repository.py's 'retrieve all components' contract."""
    from src.adapters.persistence.dynamo_component_repository import (
        DynamoComponentRepository,
    )

    settings = load_settings()
    repo = DynamoComponentRepository(dynamo_resource, settings.dynamo_control_table)

    for i in range(10):
        _seed_component_dynamo(dynamo_resource, settings, f"comp-page-{i}", "app-a")

    repo._limit = 2

    components = repo.list_components()
    assert {c.id for c in components} == {f"comp-page-{i}" for i in range(10)}


def test_dynamo_watermark_repository_lifecycle(dynamo_resource):
    from datetime import datetime, timezone

    from src.adapters.persistence.dynamo_watermark_repository import (
        DynamoWatermarkRepository,
    )

    settings = load_settings()
    repo = DynamoWatermarkRepository(dynamo_resource, settings.dynamo_control_table)

    assert repo.get("signal-1") is None

    dt1 = datetime(2026, 7, 14, 12, 0, 0, 0, tzinfo=timezone.utc)
    repo.advance("signal-1", dt1)

    got1 = repo.get("signal-1")
    assert got1 == dt1
    assert got1.tzinfo == timezone.utc

    # advance twice
    dt2 = datetime(2026, 7, 14, 12, 30, 0, 0, tzinfo=timezone.utc)
    repo.advance("signal-1", dt2)
    assert repo.get("signal-1") == dt2

    # Spy on get to check ConsistentRead
    table = repo._table
    original_get_item = table.get_item
    spy_kwargs = []

    def spied_get_item(*args, **kwargs):
        spy_kwargs.append(kwargs)
        return original_get_item(*args, **kwargs)

    table.get_item = spied_get_item

    repo.get("signal-1")
    assert len(spy_kwargs) == 1
    assert spy_kwargs[0].get("ConsistentRead") is True


def test_dynamo_sample_mode_repository_lifecycle(dynamo_resource):
    from src.adapters.persistence.dynamo_sample_mode_repository import (
        DynamoSampleModeRepository,
    )

    settings = load_settings()
    repo = DynamoSampleModeRepository(dynamo_resource, settings.dynamo_control_table)

    # absent item -> disabled
    assert repo.is_enabled() is False

    # set_enabled(True)
    repo.set_enabled(True)
    assert repo.is_enabled() is True

    # idempotent re-set
    repo.set_enabled(True)
    assert repo.is_enabled() is True

    # set_enabled(False)
    repo.set_enabled(False)
    assert repo.is_enabled() is False

    # Spy on get_item to check ConsistentRead
    table = repo._table
    original_get_item = table.get_item
    spy_kwargs = []

    def spied_get_item(*args, **kwargs):
        spy_kwargs.append(kwargs)
        return original_get_item(*args, **kwargs)

    table.get_item = spied_get_item

    repo.is_enabled()
    assert len(spy_kwargs) == 1
    assert spy_kwargs[0].get("ConsistentRead") is True


def test_dynamo_component_repository_list_components(dynamo_resource):
    from src.adapters.persistence.dynamo_component_repository import (
        DynamoComponentRepository,
    )

    settings = load_settings()
    repo = DynamoComponentRepository(dynamo_resource, settings.dynamo_control_table)

    # Empty case
    assert repo.list_components() == []

    # Seed components
    _seed_component_dynamo(dynamo_resource, settings, "comp-a", "app-a")
    _seed_component_dynamo(dynamo_resource, settings, "comp-b", "app-a")

    # Update status of comp-b to degraded
    repo.set_status("comp-b", ComponentStatus.DEGRADED)

    components = repo.list_components()
    assert len(components) == 2

    components_sorted = sorted(components, key=lambda c: c.id)

    assert components_sorted[0].id == "comp-a"
    assert components_sorted[0].name == "comp-a"
    assert components_sorted[0].status == ComponentStatus.OPERATIONAL
    assert components_sorted[0].app_id == "app-a"

    assert components_sorted[1].id == "comp-b"
    assert components_sorted[1].name == "comp-b"
    assert components_sorted[1].status == ComponentStatus.DEGRADED
    assert components_sorted[1].app_id == "app-a"
