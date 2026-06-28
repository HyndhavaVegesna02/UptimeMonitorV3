"""System clock adapter (dossier §6)."""

from datetime import datetime, timezone

from src.core.ports import ClockPort


class SystemClock(ClockPort):
    """Production clock reading the system wall clock in UTC (dossier §6)."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)
