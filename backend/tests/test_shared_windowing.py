"""Unit tests for the centralized windowing policy.

Cites: Proposal (2026-07-10) §3.4 G3, §10 Phase 3.
"""

from datetime import datetime, timezone

from src.api.v1._shared.windowing import resolve_window


def test_resolve_window_both_defaults() -> None:
    """Verify that when both parameters are None, a 24h window ending at now is resolved.

    Cites: Proposal (2026-07-10) §3.4 G3.
    """
    now = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)
    since, until = resolve_window(None, None, now)
    assert until == now
    assert since == datetime(2026, 7, 9, 12, 0, 0, tzinfo=timezone.utc)


def test_resolve_window_until_defaulted() -> None:
    """Verify that when only since is provided, until defaults to now.

    Cites: Proposal (2026-07-10) §3.4 G3.
    """
    now = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)
    since, until = resolve_window("2026-07-10T10:00:00Z", None, now)
    assert until == now
    assert since == datetime(2026, 7, 10, 10, 0, 0, tzinfo=timezone.utc)


def test_resolve_window_since_defaulted() -> None:
    """Verify that when only until is provided, since defaults to until - 24h.

    Cites: Proposal (2026-07-10) §3.4 G3.
    """
    now = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)
    since, until = resolve_window(None, "2026-07-10T10:00:00Z", now)
    assert until == datetime(2026, 7, 10, 10, 0, 0, tzinfo=timezone.utc)
    assert since == datetime(2026, 7, 9, 10, 0, 0, tzinfo=timezone.utc)


def test_resolve_window_explicit_passthrough() -> None:
    """Verify that when both are provided, they are parsed and returned directly.

    Cites: Proposal (2026-07-10) §3.4 G3.
    """
    now = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)
    since, until = resolve_window("2026-07-10T08:00:00Z", "2026-07-10T10:00:00Z", now)
    assert since == datetime(2026, 7, 10, 8, 0, 0, tzinfo=timezone.utc)
    assert until == datetime(2026, 7, 10, 10, 0, 0, tzinfo=timezone.utc)
