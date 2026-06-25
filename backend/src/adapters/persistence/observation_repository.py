"""Postgres-backed `ObservationRepository` (dossier §6, §8, §9). Zone 2.

`PostgresObservationRepository` is the concrete adapter for the
`ObservationRepository` port owned by the core. It is constructed with an
injected SQLAlchemy `Engine` (never a global) and persists batches of
canonical `SignalObservation`s into the `observations` spine table using
`INSERT ... ON CONFLICT (source_event_id) DO NOTHING` — concurrency-safe
idempotency enforced by the database's own UNIQUE constraint, not a racy
read-then-write in application code.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine

from src.core.domain import SignalObservation
from src.core.ports import ObservationRepository

_OBSERVATIONS = sa.table(
    "observations",
    sa.column("signal_key"),
    sa.column("observed_at"),
    sa.column("health"),
    sa.column("source_event_id"),
    sa.column("source", JSONB),
    sa.column("location"),
    sa.column("latency_ms"),
    sa.column("raw_ref"),
)


class PostgresObservationRepository(ObservationRepository):
    """Persists canonical observations idempotently against Postgres (dossier §6, §9)."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save_new(self, batch: Sequence[SignalObservation]) -> int:
        """Insert `batch` via `ON CONFLICT (source_event_id) DO NOTHING`.

        Returns the count of rows actually inserted (i.e. excluding any whose
        `source_event_id` already existed) by counting the rows the
        `RETURNING` clause produces — a row that was skipped by the conflict
        target never reaches `RETURNING`.
        """
        if not batch:
            return 0

        values = [
            {
                "signal_key": observation.signal_key,
                "observed_at": observation.observed_at,
                "health": observation.health.value,
                "source_event_id": observation.source_event_id,
                "source": observation.source.model_dump(),
                "location": observation.location,
                "latency_ms": observation.latency_ms,
                "raw_ref": observation.raw_ref,
            }
            for observation in batch
        ]

        stmt = (
            pg_insert(_OBSERVATIONS)
            .values(values)
            .on_conflict_do_nothing(index_elements=["source_event_id"])
            .returning(_OBSERVATIONS.c.source_event_id)
        )

        with self._engine.begin() as conn:
            result = conn.execute(stmt)
            return len(result.fetchall())
