from __future__ import annotations

from datetime import datetime, timezone

import pytest
from src.adapters.persistence.dynamo_maintenance_repository import (
    DynamoMaintenanceRepository,
)
from src.composition.settings import load_settings
from src.core.domain.maintenance import (
    MaintenanceWindow,
    MaintenanceWindowNotFoundError,
)


def test_dynamo_maintenance_repository_create_list_delete(dynamo_resource):
    settings = load_settings()
    repo = DynamoMaintenanceRepository(dynamo_resource, settings.dynamo_control_table)

    w1 = MaintenanceWindow(
        component_id="comp-1",
        starts_at=datetime(2026, 7, 15, 10, 0, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
        reason="Routine patch",
        title="DB Upgrade",
    )

    w2 = MaintenanceWindow(
        component_id="comp-2",
        starts_at=datetime(2026, 7, 15, 9, 0, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 7, 15, 11, 0, 0, tzinfo=timezone.utc),
        reason="Security update",
        title="Firewall patch",
    )

    # Test create and counter ID assignment
    saved1 = repo.create(w1)
    assert saved1.id is not None

    saved2 = repo.create(w2)
    assert saved2.id is not None
    assert saved2.id > saved1.id

    # Test list_windows (should be ordered by starts_at ascending)
    windows = repo.list_windows()
    assert len(windows) == 2
    # w2 starts at 9:00, w1 starts at 10:00 -> w2 is first
    assert windows[0].id == saved2.id
    assert windows[0].component_id == "comp-2"
    assert windows[1].id == saved1.id
    assert windows[1].component_id == "comp-1"

    # Test delete
    repo.delete(saved1.id)
    windows_after = repo.list_windows()
    assert len(windows_after) == 1
    assert windows_after[0].id == saved2.id

    # Test delete of non-existent ID raises MaintenanceWindowNotFoundError
    with pytest.raises(MaintenanceWindowNotFoundError):
        repo.delete(saved1.id)  # already deleted

    with pytest.raises(MaintenanceWindowNotFoundError):
        repo.delete(99999)


def test_dynamo_maintenance_repository_list_windows_paginates(dynamo_resource):
    """STORY-199 AC2: forcing a small page size must not truncate list_windows
    against maintenance_repository.py's 'retrieve all' contract."""
    settings = load_settings()
    repo = DynamoMaintenanceRepository(dynamo_resource, settings.dynamo_control_table)

    for i in range(10):
        repo.create(
            MaintenanceWindow(
                component_id=f"comp-page-{i}",
                starts_at=datetime(2026, 7, 15, 8, i, 0, tzinfo=timezone.utc),
                ends_at=datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc),
            )
        )

    repo._limit = 2

    windows = repo.list_windows()
    assert {w.component_id for w in windows} == {f"comp-page-{i}" for i in range(10)}


def test_dynamo_maintenance_repository_is_under_maintenance_boundaries(dynamo_resource):
    settings = load_settings()
    repo = DynamoMaintenanceRepository(dynamo_resource, settings.dynamo_control_table)

    t0 = datetime(2026, 7, 15, 10, 0, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
    midpoint = datetime(2026, 7, 15, 11, 0, 0, tzinfo=timezone.utc)
    before = datetime(2026, 7, 15, 9, 59, 59, tzinfo=timezone.utc)
    after = datetime(2026, 7, 15, 12, 0, 1, tzinfo=timezone.utc)

    window = MaintenanceWindow(
        component_id="boundary-comp",
        starts_at=t0,
        ends_at=t1,
        reason="Testing boundaries",
        title="Boundary test",
    )
    repo.create(window)

    # 1. Test before window start -> False
    assert repo.is_under_maintenance("boundary-comp", before) is False

    # 2. Test exactly at starts_at -> True (inclusive start)
    assert repo.is_under_maintenance("boundary-comp", t0) is True

    # 3. Test at midpoint -> True
    assert repo.is_under_maintenance("boundary-comp", midpoint) is True

    # 4. Test exactly at ends_at -> False (exclusive end)
    assert repo.is_under_maintenance("boundary-comp", t1) is False

    # 5. Test after ends_at -> False
    assert repo.is_under_maintenance("boundary-comp", after) is False

    # 6. Test a different component at midpoint -> False
    assert repo.is_under_maintenance("other-comp", midpoint) is False


def test_dynamo_maintenance_repository_empty(dynamo_resource):
    settings = load_settings()
    repo = DynamoMaintenanceRepository(dynamo_resource, settings.dynamo_control_table)
    assert repo.list_windows() == []
    assert (
        repo.is_under_maintenance(
            "any-comp", datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
        )
        is False
    )
