"""Postgres-backed `ComponentRepository` (dossier §9, §17)."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.engine import Engine

from src.core.domain.component import Component
from src.core.domain.status import ComponentStatus
from src.core.ports.component_repository import ComponentRepository

_COMPONENTS = sa.table(
    "components",
    sa.column("id"),
    sa.column("name"),
    sa.column("status"),
    sa.column("app_id"),
)


class PostgresComponentRepository(ComponentRepository):
    """Concrete Postgres adapter for components (dossier §9, §17)."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_components(self) -> list[Component]:
        """Retrieve all components from the components table.

        Returns:
            list[Component]: All components, or [] if none exist.
        """
        stmt = sa.select(
            _COMPONENTS.c.id,
            _COMPONENTS.c.name,
            _COMPONENTS.c.status,
            _COMPONENTS.c.app_id,
        )

        with self._engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()

        return [
            Component(
                id=row.id,
                name=row.name,
                status=ComponentStatus(row.status),
                app_id=row.app_id,
            )
            for row in rows
        ]
