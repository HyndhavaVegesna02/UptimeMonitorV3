"""Tests for the MaintenanceWindow domain type (dossier §9, §10, §17)."""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError
from src.core.domain.maintenance import MaintenanceWindow


def test_valid_maintenance_window():
    starts = datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)
    ends = datetime(2026, 6, 28, 14, 0, 0, tzinfo=timezone.utc)
    window = MaintenanceWindow(
        component_id="checkout",
        starts_at=starts,
        ends_at=ends,
        reason="Upgrading database",
        id=42,
    )
    assert window.component_id == "checkout"
    assert window.starts_at == starts
    assert window.ends_at == ends
    assert window.reason == "Upgrading database"
    assert window.id == 42


def test_maintenance_window_ends_at_must_be_greater_than_starts_at():
    starts = datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)
    # equal
    with pytest.raises(ValidationError) as excinfo:
        MaintenanceWindow(
            component_id="checkout",
            starts_at=starts,
            ends_at=starts,
            reason="Equal",
        )
    assert "ends_at must be strictly greater than starts_at" in str(excinfo.value)

    # less than
    ends = datetime(2026, 6, 28, 11, 0, 0, tzinfo=timezone.utc)
    with pytest.raises(ValidationError) as excinfo:
        MaintenanceWindow(
            component_id="checkout",
            starts_at=starts,
            ends_at=ends,
            reason="Ends before starts",
        )
    assert "ends_at must be strictly greater than starts_at" in str(excinfo.value)


def test_maintenance_window_requires_utc_timezone():
    starts_ok = datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)
    ends_ok = datetime(2026, 6, 28, 14, 0, 0, tzinfo=timezone.utc)

    # naive starts_at
    with pytest.raises(ValidationError) as excinfo:
        MaintenanceWindow(
            component_id="checkout",
            starts_at=datetime(2026, 6, 28, 12, 0, 0),
            ends_at=ends_ok,
        )
    assert "starts_at must be a tz-aware UTC datetime" in str(excinfo.value)

    # naive ends_at
    with pytest.raises(ValidationError) as excinfo:
        MaintenanceWindow(
            component_id="checkout",
            starts_at=starts_ok,
            ends_at=datetime(2026, 6, 28, 14, 0, 0),
        )
    assert "ends_at must be a tz-aware UTC datetime" in str(excinfo.value)

    # non-UTC tz starts_at
    est = timezone(timedelta(hours=-5))
    with pytest.raises(ValidationError) as excinfo:
        MaintenanceWindow(
            component_id="checkout",
            starts_at=datetime(2026, 6, 28, 12, 0, 0, tzinfo=est),
            ends_at=ends_ok,
        )
    assert "starts_at must be a tz-aware UTC datetime" in str(excinfo.value)
