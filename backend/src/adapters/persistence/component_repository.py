"""Postgres-backed `ComponentRepository` (dossier §9, §17).

STORY-016a (Sprint 17): adds `get(component_id) -> Component | None` — SELECT
by id, `None` when absent, for the pipeline orchestrator (dossier §8 step 5).
STORY-045: adds `set_status` — a conditional `UPDATE` that raises
`ComponentNotFoundError` on zero rows affected (never a bare `ValueError`).
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.engine import Engine

from src.core.domain.component import Component, ComponentNotFoundError
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

    def get(self, component_id: str) -> Component | None:
        """Retrieve a single component by id (dossier §9, §17).

        Returns `None` when no component with `component_id` exists — never
        raises, never returns a sentinel value (fake/adapter parity agreement
        2026-06-26). Used by the pipeline orchestrator (dossier §8 step 5) to
        read `current_status` before calling `DecideService.decide` (§12).
        """
        stmt = sa.select(
            _COMPONENTS.c.id,
            _COMPONENTS.c.name,
            _COMPONENTS.c.status,
            _COMPONENTS.c.app_id,
        ).where(_COMPONENTS.c.id == component_id)

        with self._engine.connect() as conn:
            row = conn.execute(stmt).fetchone()

        if row is None:
            return None
        return Component(
            id=row.id,
            name=row.name,
            status=ComponentStatus(row.status),
            app_id=row.app_id,
        )

    def set_status(self, component_id: str, status: ComponentStatus) -> None:
        """Write back a component's published status (dossier §9, §12, §17, STORY-045).

        A single conditional `UPDATE … WHERE id = :id`; `rowcount == 0` means
        no component with `component_id` exists, so raises
        `ComponentNotFoundError` rather than silently no-op'ing (2026-06-28
        check-then-act agreement) — mirrors
        `PostgresProposalRepository.resolve`'s conditional-write-then-guard shape.
        """
        stmt = (
            sa.update(_COMPONENTS)
            .where(_COMPONENTS.c.id == component_id)
            .values(status=status.value)
        )
        with self._engine.begin() as conn:
            result = conn.execute(stmt)
            if result.rowcount == 0:
                raise ComponentNotFoundError(f"Component {component_id!r} not found.")
