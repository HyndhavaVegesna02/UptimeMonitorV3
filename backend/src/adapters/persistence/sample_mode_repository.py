"""Postgres-backed `SampleModeRepository` (dossier §6/§9/§17, STORY-048 D2).

TEMPORARY feature (PO directive, 2026-07-03) — see
`docs/scrum/wiki/sample-mode.md` for the REMOVAL inventory. Mirrors the
injected-`Engine` / lightweight `sa.table` style every other persistence
adapter in this package uses (no ORM model; the migration is the schema's
source of truth).

The `sample_mode` table is pinned to at most one row by a `CHECK (id)`
constraint on its boolean primary key (see the migration); `is_enabled`/
`set_enabled` never need to disambiguate multiple rows.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine

from src.core.ports.sample_mode_repository import SampleModeRepository

_SAMPLE_MODE = sa.table(
    "sample_mode",
    sa.column("id"),
    sa.column("enabled"),
    sa.column("updated_at"),
)


class PostgresSampleModeRepository(SampleModeRepository):
    """Concrete Postgres adapter for the sample-mode flag (STORY-048 D2)."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def is_enabled(self) -> bool:
        """Return the current flag state; `False` if the row was never set.

        Read-only, so runs on `sa.Engine.connect` (mirrors
        `PostgresWatermarkRepository.get`'s read-path convention).
        """
        stmt = sa.select(_SAMPLE_MODE.c.enabled)
        with self._engine.connect() as conn:
            row = conn.execute(stmt).fetchone()
        if row is None:
            return False
        return bool(row.enabled)

    def set_enabled(self, enabled: bool) -> None:
        """Idempotent upsert of the single row.

        `INSERT ... ON CONFLICT (id) DO UPDATE` — the `id` column is always
        `TRUE` (the CHECK constraint pins the table to one row), so this is
        a plain upsert with no race to guard beyond what the DB already
        serializes. Setting the current value again succeeds silently.
        """
        stmt = (
            pg_insert(_SAMPLE_MODE)
            .values(id=True, enabled=enabled, updated_at=sa.func.now())
            .on_conflict_do_update(
                index_elements=["id"],
                set_={"enabled": enabled, "updated_at": sa.func.now()},
            )
        )
        with self._engine.begin() as conn:
            conn.execute(stmt)
