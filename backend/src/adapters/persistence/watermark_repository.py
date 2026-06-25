"""Postgres-backed `WatermarkRepository` (dossier §6, §8, §9). Zone 2.

`PostgresWatermarkRepository` is the concrete adapter for the
`WatermarkRepository` port owned by the core. It is constructed with an
injected SQLAlchemy `Engine` (never a global) and stores the per-signal
ingestion cursor in the `watermarks` spine table, keyed by `signal_key`.
`advance` upserts (`INSERT ... ON CONFLICT (signal_key) DO UPDATE`) since a
signal's watermark row may or may not already exist.
"""

from __future__ import annotations

from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine

from src.core.ports import WatermarkRepository

_WATERMARKS = sa.table(
    "watermarks",
    sa.column("signal_key"),
    sa.column("watermark"),
)


class PostgresWatermarkRepository(WatermarkRepository):
    """Stores and advances the per-signal ingestion watermark in Postgres (dossier §6, §9)."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get(self, signal_key: str) -> datetime | None:
        """Return the watermark for `signal_key` as a tz-aware UTC datetime,
        or None if it has never advanced.

        psycopg returns `timestamptz` values already tz-aware (in the
        connection's session timezone); we normalize to UTC explicitly so
        callers never depend on the session timezone setting.
        """
        stmt = sa.select(_WATERMARKS.c.watermark).where(
            _WATERMARKS.c.signal_key == signal_key
        )
        with self._engine.connect() as conn:
            row = conn.execute(stmt).first()
        if row is None:
            return None
        value = row[0]
        return value.astimezone(timezone.utc)

    def advance(self, signal_key: str, to: datetime) -> None:
        """Move the watermark for `signal_key` forward to instant `to`,
        upserting the row if it does not exist yet.
        """
        stmt = (
            pg_insert(_WATERMARKS)
            .values(signal_key=signal_key, watermark=to)
            .on_conflict_do_update(
                index_elements=["signal_key"],
                set_={"watermark": to},
            )
        )
        with self._engine.begin() as conn:
            conn.execute(stmt)
