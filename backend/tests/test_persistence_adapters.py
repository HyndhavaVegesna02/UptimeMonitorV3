"""Integration tests for the persistence adapters (STORY-007, dossier §6/§9).

These exercise the real `ObservationRepository`/`WatermarkRepository`
implementations (`src/adapters/persistence/`) against a live, migrated
Postgres obtained via the shared `migrated_db` session fixture (STORY-019).
No mock of the database — per the working agreement, real adapters get a
real (throwaway) DB.

The spine FKs `observations.signal_key` / `watermarks.signal_key` into
`signals.signal_key` (`ON DELETE RESTRICT`), and `signals.app_id` into
`apps.id`. Topology seeding from config is a later story, so each test seeds
a minimal parent `apps` row + `signals` row itself via raw SQL — that's test
arrangement, not production code, and stays out of `src/`.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import psycopg
import pytest
import sqlalchemy as sa

from src.core.domain import Health, Provenance, SignalObservation


def _engine_url(database_url: str) -> str:
    """Convert the plain libpq URL (`migrated_db.database_url`) into the
    `postgresql+psycopg://` form SQLAlchemy 2 needs for the psycopg3 driver.
    """
    assert database_url.startswith("postgresql://"), database_url
    return "postgresql+psycopg://" + database_url[len("postgresql://") :]


@pytest.fixture
def engine(migrated_db):
    eng = sa.create_engine(_engine_url(migrated_db.database_url), future=True)
    try:
        yield eng
    finally:
        eng.dispose()


def seed_signal(database_url: str, signal_key: str, app_id: str = "app-1") -> None:
    """Insert a minimal `apps` row + `signals` row so FK-constrained inserts
    against `observations`/`watermarks` for `signal_key` succeed. Raw SQL is
    fine here: this is test arrangement, not the repository layer under test.
    """
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO apps (id, name, config)
                VALUES (%s, %s, '{}'::jsonb)
                ON CONFLICT (id) DO NOTHING
                """,
                (app_id, app_id),
            )
            cur.execute(
                """
                INSERT INTO signals (signal_key, app_id, name)
                VALUES (%s, %s, %s)
                ON CONFLICT (signal_key) DO NOTHING
                """,
                (signal_key, app_id, signal_key),
            )
        conn.commit()


def _observation(
    signal_key: str = "checkout-http",
    event_id: str = "evt-1",
    observed_at: datetime | None = None,
    health: Health = Health.UP,
    location: str = "us-east",
) -> SignalObservation:
    return SignalObservation(
        signal_key=signal_key,
        observed_at=observed_at or datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc),
        health=health,
        source_event_id=event_id,
        source=Provenance(system="dynatrace", native_id="X-1", native_kind="http"),
        location=location,
    )


# --- ObservationRepository --------------------------------------------------


def test_save_new_inserts_a_fresh_batch_and_reports_count(migrated_db, engine):
    from src.adapters.persistence.observation_repository import (
        PostgresObservationRepository,
    )

    seed_signal(migrated_db.database_url, "checkout-http")
    repo = PostgresObservationRepository(engine)
    batch = [
        _observation(event_id="evt-1"),
        _observation(event_id="evt-2"),
    ]

    inserted = repo.save_new(batch)

    assert inserted == 2

    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT source_event_id, health, location FROM observations "
                "WHERE signal_key = %s ORDER BY source_event_id",
                ("checkout-http",),
            )
            rows = cur.fetchall()

    assert rows == [("evt-1", "up", "us-east"), ("evt-2", "up", "us-east")]
