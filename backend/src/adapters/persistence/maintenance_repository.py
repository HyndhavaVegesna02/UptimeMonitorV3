"""Postgres-backed `MaintenanceRepository` (dossier §9, §10, §17)."""

from __future__ import annotations

from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.engine import Engine

from src.core.domain.maintenance import MaintenanceWindow
from src.core.ports.maintenance_repository import MaintenanceRepository

_MAINTENANCE_WINDOWS = sa.table(
    "maintenance_windows",
    sa.column("id"),
    sa.column("component_id"),
    sa.column("starts_at"),
    sa.column("ends_at"),
    sa.column("reason"),
    sa.column("title"),
)


class PostgresMaintenanceRepository(MaintenanceRepository):
    """Concrete Postgres adapter for managing maintenance windows (dossier §9, §10, §17)."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_windows(self) -> list[MaintenanceWindow]:
        """Retrieve all scheduled maintenance windows ordered by starts_at."""
        stmt = sa.select(
            _MAINTENANCE_WINDOWS.c.id,
            _MAINTENANCE_WINDOWS.c.component_id,
            _MAINTENANCE_WINDOWS.c.starts_at,
            _MAINTENANCE_WINDOWS.c.ends_at,
            _MAINTENANCE_WINDOWS.c.reason,
            _MAINTENANCE_WINDOWS.c.title,
        ).order_by(_MAINTENANCE_WINDOWS.c.starts_at)

        with self._engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()

        return [
            MaintenanceWindow(
                id=row.id,
                component_id=row.component_id,
                starts_at=row.starts_at.astimezone(timezone.utc),
                ends_at=row.ends_at.astimezone(timezone.utc),
                reason=row.reason,
                title=row.title,
            )
            for row in rows
        ]

    def create(self, window: MaintenanceWindow) -> MaintenanceWindow:
        """Persist a new maintenance window."""
        stmt = (
            sa.insert(_MAINTENANCE_WINDOWS)
            .values(
                {
                    "component_id": window.component_id,
                    "starts_at": window.starts_at,
                    "ends_at": window.ends_at,
                    "reason": window.reason,
                    "title": window.title,
                }
            )
            .returning(
                _MAINTENANCE_WINDOWS.c.id,
                _MAINTENANCE_WINDOWS.c.component_id,
                _MAINTENANCE_WINDOWS.c.starts_at,
                _MAINTENANCE_WINDOWS.c.ends_at,
                _MAINTENANCE_WINDOWS.c.reason,
                _MAINTENANCE_WINDOWS.c.title,
            )
        )

        with self._engine.begin() as conn:
            row = conn.execute(stmt).fetchone()

        assert row is not None
        return MaintenanceWindow(
            id=row.id,
            component_id=row.component_id,
            starts_at=row.starts_at.astimezone(timezone.utc),
            ends_at=row.ends_at.astimezone(timezone.utc),
            reason=row.reason,
            title=row.title,
        )

    def is_under_maintenance(self, component_id: str, at: datetime) -> bool:
        """Check if a component is under active maintenance at a given timestamp."""
        stmt = sa.select(sa.literal(1)).where(
            _MAINTENANCE_WINDOWS.c.component_id == component_id,
            _MAINTENANCE_WINDOWS.c.starts_at <= at,
            _MAINTENANCE_WINDOWS.c.ends_at > at,
        )

        with self._engine.connect() as conn:
            result = conn.execute(stmt).first()

        return result is not None
