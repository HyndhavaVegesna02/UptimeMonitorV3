"""Centralized read-window defaulting policy.

Cites: Proposal (2026-07-10) §3.4 G3, §6.2.
Provides the single home for read-window defaulting (24h window), ensuring
consistent interpretation of time queries across the edge.
"""

from datetime import datetime, timedelta

DEFAULT_WINDOW_HOURS = 24


def resolve_window(
    since_str: str | None, until_str: str | None, now: datetime
) -> tuple[datetime, datetime]:
    """Parse and resolve optional string dates using the default 24h window policy.

    Cites: Proposal (2026-07-10) §3.4 G3.
    """
    if until_str is not None:
        until = datetime.fromisoformat(until_str)
    else:
        until = now

    if since_str is not None:
        since = datetime.fromisoformat(since_str)
    else:
        since = until - timedelta(hours=DEFAULT_WINDOW_HOURS)

    return since, until
