"""Postgres-backed `SignalRepository` (dossier §7, §9, STORY-044).

Read-only: SELECTs only against the `signals` table, mirroring
`PostgresComponentRepository`'s style (injected `Engine`, lightweight
`sa.table` construct, no ORM model). The seed (`composition/seed.py`) is the
only writer of `signals`.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.engine import Engine

from src.core.domain.topology import Signal
from src.core.ports.signal_repository import SignalRepository

_SIGNALS = sa.table(
    "signals",
    sa.column("signal_key"),
    sa.column("name"),
    sa.column("component_id"),
    sa.column("interval_seconds"),
)


class PostgresSignalRepository(SignalRepository):
    """Concrete Postgres adapter for seeded-topology signals (dossier §7, §9)."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_signals(self) -> list[Signal]:
        """Retrieve every seeded signal, ordered by `signal_key`.

        Returns:
            list[Signal]: All signals, or `[]` if none exist.
        """
        stmt = sa.select(
            _SIGNALS.c.signal_key,
            _SIGNALS.c.name,
            _SIGNALS.c.component_id,
            _SIGNALS.c.interval_seconds,
        ).order_by(_SIGNALS.c.signal_key)

        with self._engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()

        return [
            Signal(
                signal_key=row.signal_key,
                name=row.name,
                component_id=row.component_id,
                interval_seconds=row.interval_seconds,
            )
            for row in rows
        ]

    def get(self, signal_key: str) -> Signal | None:
        """Retrieve a single signal by key.

        Returns `None` when no signal with `signal_key` exists — never
        raises, never a sentinel value (fake/adapter parity agreement
        2026-06-26).
        """
        stmt = sa.select(
            _SIGNALS.c.signal_key,
            _SIGNALS.c.name,
            _SIGNALS.c.component_id,
            _SIGNALS.c.interval_seconds,
        ).where(_SIGNALS.c.signal_key == signal_key)

        with self._engine.connect() as conn:
            row = conn.execute(stmt).fetchone()

        if row is None:
            return None
        return Signal(
            signal_key=row.signal_key,
            name=row.name,
            component_id=row.component_id,
            interval_seconds=row.interval_seconds,
        )
