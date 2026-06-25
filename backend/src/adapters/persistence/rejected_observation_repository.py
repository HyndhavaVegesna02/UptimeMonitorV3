"""Postgres-backed `RejectedObservationRepository` (dossier §6, §8, §9). Zone 2.

`PostgresRejectedObservationRepository` is the concrete adapter for the
quarantine-sink port owned by the core. It mirrors
`PostgresObservationRepository`: constructed with an injected SQLAlchemy
`Engine` (never a global), persisting into the `rejected_observations` spine
table. Unlike `observations`/`watermarks`, that table has deliberately NO FK
on `signal_key` (it is nullable) — a quarantined row may carry an unknown or
absent signal_key, which is often exactly *why* it was rejected, and
quarantine must never itself be rejectable by a missing-FK error.
"""

from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine

from src.core.ports import RejectedObservationRepository

_REJECTED_OBSERVATIONS = sa.table(
    "rejected_observations",
    sa.column("signal_key"),
    sa.column("reason"),
    sa.column("payload", JSONB),
    sa.column("rejected_at"),
)


class PostgresRejectedObservationRepository(RejectedObservationRepository):
    """Persists quarantined observations against Postgres (dossier §6, §9)."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save(
        self,
        *,
        signal_key: str | None,
        reason: str,
        payload: dict,
        rejected_at: datetime,
    ) -> None:
        """Insert one rejected-observation row.

        No conflict handling is needed here — unlike `observations`, there is
        no idempotency key on this table; every rejection is its own row.
        """
        stmt = _REJECTED_OBSERVATIONS.insert().values(
            signal_key=signal_key,
            reason=reason,
            payload=payload,
            rejected_at=rejected_at,
        )
        with self._engine.begin() as conn:
            conn.execute(stmt)
