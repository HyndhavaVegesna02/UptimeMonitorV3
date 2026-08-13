from __future__ import annotations

from src.composition.settings import load_settings
from src.core.domain.status import ComponentStatus
from src.core.domain.topology import Signal
from tests.pagination_diagnostics import PaginationSpy
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


def test_dynamo_signal_repository_list_signals_paginates(dynamo_resource):
    """STORY-199 AC2: forcing a small page size must not truncate list_signals
    against signal_repository.py's 'retrieve every seeded signal' contract.

    STORY-213 AC4: the assertion is self-diagnosing (PaginationSpy) so a
    failure here reports the observed page count, the signal keys actually
    returned, and whether a LastEvaluatedKey was present when the loop
    exited -- the same treatment as list_components below (AC1)."""
    from src.adapters.persistence.dynamo_signal_repository import DynamoSignalRepository

    settings = load_settings()
    signals = [
        Signal(
            signal_key=f"sig-page-{i}",
            name=f"Signal {i}",
            component_id=None,
            interval_seconds=None,
        )
        for i in range(10)
    ]
    _seed_signals_dynamo(dynamo_resource, settings, signals)

    repo = DynamoSignalRepository(dynamo_resource, settings.dynamo_control_table)
    repo._limit = 2

    with PaginationSpy(repo._table) as spy:
        result = repo.list_signals()

    expected_keys = {f"sig-page-{i}" for i in range(10)}
    actual_keys = {s.signal_key for s in result}
    assert actual_keys == expected_keys, spy.diagnostic(expected_keys, actual_keys)


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
    against component_repository.py's 'retrieve all components' contract.

    STORY-213 AC1: this test failed once in eleven full-suite runs with a bare
    set-equality mismatch -- a message indistinguishable from a REAL
    regression of the pagination loop STORY-199 had just fixed. The assertion
    is self-diagnosing (PaginationSpy, backend/tests/pagination_diagnostics.py):
    on failure it reports the observed page count, the ids actually returned,
    and whether a LastEvaluatedKey was present when the loop exited, so a
    reader can tell a flake from a real regression at a glance instead of
    re-instrumenting the failure by hand -- see PaginationSpy.diagnostic's
    docstring for which LEK value means which; it is not restated here to
    avoid a second, driftable copy. Proven by forced truncation in
    test_dynamo_component_repository_list_components_paginates_diagnostic_message_on_forced_truncation
    below (backend/tests/test_dynamo_adapters.py)."""
    from src.adapters.persistence.dynamo_component_repository import (
        DynamoComponentRepository,
    )

    settings = load_settings()
    repo = DynamoComponentRepository(dynamo_resource, settings.dynamo_control_table)

    for i in range(10):
        _seed_component_dynamo(dynamo_resource, settings, f"comp-page-{i}", "app-a")

    repo._limit = 2

    with PaginationSpy(repo._table) as spy:
        components = repo.list_components()

    expected_ids = {f"comp-page-{i}" for i in range(10)}
    actual_ids = {c.id for c in components}
    assert actual_ids == expected_ids, spy.diagnostic(expected_ids, actual_ids)


def test_dynamo_component_repository_list_components_paginates_diagnostic_message_on_forced_truncation(
    dynamo_resource,
):
    """STORY-213 AC1 proof: force EXACTLY the reviewer's hypothesised shape --
    DynamoDB Local returning an absent LastEvaluatedKey after the first page
    even though 8 more comp-page-* ids remain unread -- and record the
    emitted assertion message, not a description of it.

    `list_components` itself is exercised UNMODIFIED (only the raw response
    it receives is tampered with, one frame below it), so it genuinely stops
    after one page -- exactly the early-stop shape AC1 targets -- rather than
    simulating the message by hand."""
    from src.adapters.persistence.dynamo_component_repository import (
        DynamoComponentRepository,
    )

    settings = load_settings()
    repo = DynamoComponentRepository(dynamo_resource, settings.dynamo_control_table)

    for i in range(10):
        _seed_component_dynamo(dynamo_resource, settings, f"comp-page-{i}", "app-a")

    repo._limit = 2
    table = repo._table
    original_query = table.query
    calls = {"count": 0}

    def _truncating_query(**kwargs):
        response = dict(original_query(**kwargs))
        calls["count"] += 1
        if calls["count"] == 1:
            # Simulate the hypothesised DynamoDB Local flake: the first page
            # answers normally, but LastEvaluatedKey is (wrongly) absent even
            # though 8 more ids remain unread.
            response.pop("LastEvaluatedKey", None)
        return response

    table.query = _truncating_query
    try:
        with PaginationSpy(table) as spy:
            components = repo.list_components()
    finally:
        table.query = original_query

    expected_ids = {f"comp-page-{i}" for i in range(10)}
    actual_ids = {c.id for c in components}

    try:
        assert actual_ids == expected_ids, spy.diagnostic(expected_ids, actual_ids)
        raise AssertionError(
            "the forced truncation did not reproduce a failure -- "
            "list_components read past the tampered first page, so this "
            "proof did not exercise what it claims to"
        )
    except AssertionError as exc:
        message = str(exc)

    # The emitted message -- not a description of it -- must answer AC1's
    # three questions.
    assert "1 page(s) read" in message
    assert "LastEvaluatedKey present when loop exited=False" in message
    for i in range(2, 10):
        assert f"comp-page-{i}" in message  # in "missing"
    assert "comp-page-0" in message and "comp-page-1" in message  # in "ids returned"


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
