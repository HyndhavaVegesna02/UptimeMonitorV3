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

from src.core.domain import ComponentStatus, Health, Provenance, SignalObservation


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


def test_save_new_reinserting_existing_event_ids_inserts_zero_new_rows(migrated_db, engine):
    """AC3: re-inserting a batch whose `source_event_id`s already exist must
    insert 0 new rows (`ON CONFLICT (source_event_id) DO NOTHING`), and the
    returned count must reflect only newly-inserted rows — proven by mixing
    one duplicate with one genuinely new event id.

    Uses a signal_key/event-id namespace unique to this test (the session-
    scoped `migrated_db` fixture is shared across tests in this module, so
    rows from other tests' batches persist for the life of the session).
    """
    from src.adapters.persistence.observation_repository import (
        PostgresObservationRepository,
    )

    seed_signal(migrated_db.database_url, "dedup-http")
    repo = PostgresObservationRepository(engine)

    first_batch = [
        _observation(signal_key="dedup-http", event_id="dedup-evt-1"),
        _observation(signal_key="dedup-http", event_id="dedup-evt-2"),
    ]
    assert repo.save_new(first_batch) == 2

    # Re-insert the exact same batch: every source_event_id already exists.
    duplicate_inserted = repo.save_new(first_batch)
    assert duplicate_inserted == 0

    # Mixed batch: one duplicate + one genuinely new id -> only the new one counts.
    mixed_batch = [
        _observation(signal_key="dedup-http", event_id="dedup-evt-2"),
        _observation(signal_key="dedup-http", event_id="dedup-evt-3"),
    ]
    mixed_inserted = repo.save_new(mixed_batch)
    assert mixed_inserted == 1

    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM observations WHERE signal_key = %s",
                ("dedup-http",),
            )
            (total,) = cur.fetchone()

    assert total == 3


def test_in_window_returns_only_observations_inside_the_half_open_range(migrated_db, engine):
    """STORY-011 AC5: the read side of the persistence boundary the
    availability engine derives from. Half-open `[since, until)` — a row
    exactly AT `until` must be excluded, proving adjacent windows can never
    double-count the boundary instant.
    """
    from src.adapters.persistence.observation_repository import (
        PostgresObservationRepository,
    )

    seed_signal(migrated_db.database_url, "in-window-http")
    repo = PostgresObservationRepository(engine)
    since = datetime(2026, 6, 25, 9, 0, 0, tzinfo=timezone.utc)
    until = datetime(2026, 6, 25, 9, 10, 0, tzinfo=timezone.utc)

    repo.save_new(
        [
            _observation(
                signal_key="in-window-http",
                event_id="before-window",
                observed_at=since - timedelta(minutes=1),
            ),
            _observation(
                signal_key="in-window-http",
                event_id="at-since-boundary",
                observed_at=since,
            ),
            _observation(
                signal_key="in-window-http",
                event_id="inside-window",
                observed_at=since + timedelta(minutes=5),
                health=Health.DOWN,
                location="eu-west",
            ),
            _observation(
                signal_key="in-window-http",
                event_id="at-until-boundary",
                observed_at=until,
            ),
            _observation(
                signal_key="in-window-http",
                event_id="after-window",
                observed_at=until + timedelta(minutes=1),
            ),
        ]
    )

    result = repo.in_window("in-window-http", since, until)

    by_event_id = {o.source_event_id: o for o in result}
    assert set(by_event_id) == {"at-since-boundary", "inside-window"}
    assert by_event_id["inside-window"].health == Health.DOWN
    assert by_event_id["inside-window"].location == "eu-west"
    assert by_event_id["inside-window"].observed_at == since + timedelta(minutes=5)
    assert by_event_id["inside-window"].observed_at.tzinfo is not None


def test_in_window_filters_by_signal_key_and_returns_empty_for_unknown_signal(
    migrated_db, engine
):
    """A signal with zero rows (or a signal nothing has ever reported for) is
    a legitimate empty result, not an error — this is exactly the AC6
    degenerate input the availability engine must handle without crashing.
    """
    from src.adapters.persistence.observation_repository import (
        PostgresObservationRepository,
    )

    seed_signal(migrated_db.database_url, "in-window-other-signal")
    repo = PostgresObservationRepository(engine)
    since = datetime(2026, 6, 25, 9, 0, 0, tzinfo=timezone.utc)
    until = datetime(2026, 6, 25, 9, 10, 0, tzinfo=timezone.utc)

    repo.save_new(
        [
            _observation(
                signal_key="in-window-other-signal",
                event_id="belongs-to-other-signal",
                observed_at=since + timedelta(minutes=1),
            ),
        ]
    )

    result = repo.in_window("signal-with-no-rows-at-all", since, until)

    assert result == []


# --- WatermarkRepository ----------------------------------------------------


def test_watermark_get_returns_none_before_any_advance(migrated_db, engine):
    from src.adapters.persistence.watermark_repository import (
        PostgresWatermarkRepository,
    )

    seed_signal(migrated_db.database_url, "watermark-get-none")
    repo = PostgresWatermarkRepository(engine)

    assert repo.get("watermark-get-none") is None


def test_watermark_advance_then_get_round_trips_as_tz_aware_utc(migrated_db, engine):
    from src.adapters.persistence.watermark_repository import (
        PostgresWatermarkRepository,
    )

    seed_signal(migrated_db.database_url, "watermark-advance")
    repo = PostgresWatermarkRepository(engine)
    mark = datetime(2026, 6, 24, 10, 5, 0, tzinfo=timezone.utc)

    repo.advance("watermark-advance", mark)
    result = repo.get("watermark-advance")

    assert result == mark
    assert result.tzinfo is not None
    assert result.utcoffset() == timedelta(0)


def test_watermark_re_advance_moves_it_forward(migrated_db, engine):
    from src.adapters.persistence.watermark_repository import (
        PostgresWatermarkRepository,
    )

    seed_signal(migrated_db.database_url, "watermark-readvance")
    repo = PostgresWatermarkRepository(engine)
    first = datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc)
    second = datetime(2026, 6, 24, 11, 30, 0, tzinfo=timezone.utc)

    repo.advance("watermark-readvance", first)
    assert repo.get("watermark-readvance") == first

    repo.advance("watermark-readvance", second)
    assert repo.get("watermark-readvance") == second


# --- RejectedObservationRepository (STORY-009, AC1 persistence) -------------


def test_rejected_observation_save_writes_a_row_with_reason_and_payload(
    migrated_db, engine
):
    """`rejected_observations` has NO FK (dossier §9 — a quarantined row may
    carry a signal_key that does not, or does not yet, exist in seeded
    topology), so unlike the observations/watermarks tests above this needs
    no `seed_signal` call.
    """
    from src.adapters.persistence.rejected_observation_repository import (
        PostgresRejectedObservationRepository,
    )

    repo = PostgresRejectedObservationRepository(engine)
    rejected_at = datetime(2026, 6, 24, 12, 0, 0, tzinfo=timezone.utc)
    payload = {
        "signal_key": "checkout-http",
        "observed_at": "2099-01-01T00:00:00+00:00",
        "source_event_id": "evt-future",
    }

    repo.save(
        signal_key="checkout-http",
        reason="observed_at is implausibly in the future",
        payload=payload,
        rejected_at=rejected_at,
    )

    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT signal_key, reason, payload, rejected_at FROM rejected_observations "
                "WHERE signal_key = %s",
                ("checkout-http",),
            )
            rows = cur.fetchall()

    assert len(rows) == 1
    signal_key, reason, stored_payload, stored_rejected_at = rows[0]
    assert signal_key == "checkout-http"
    assert reason == "observed_at is implausibly in the future"
    assert stored_payload == payload
    assert stored_rejected_at == rejected_at


def test_rejected_observation_save_allows_null_signal_key(migrated_db, engine):
    """An unknown/absent signal_key is exactly the kind of row this table must
    accept — that's often *why* the observation was rejected in the first
    place (no FK, deliberately, per the migration's column comment).
    """
    from src.adapters.persistence.rejected_observation_repository import (
        PostgresRejectedObservationRepository,
    )

    repo = PostgresRejectedObservationRepository(engine)
    rejected_at = datetime(2026, 6, 24, 12, 30, 0, tzinfo=timezone.utc)

    repo.save(
        signal_key=None,
        reason="missing required field",
        payload={"raw": "malformed"},
        rejected_at=rejected_at,
    )

    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT signal_key, reason, payload FROM rejected_observations "
                "WHERE reason = %s",
                ("missing required field",),
            )
            rows = cur.fetchall()

    assert len(rows) == 1
    signal_key, reason, stored_payload = rows[0]
    assert signal_key is None
    assert reason == "missing required field"
    assert stored_payload == {"raw": "malformed"}


# --- ProposalRepository (STORY-012, Postgres adapter) -------------------------


def seed_component(database_url: str, component_id: str, app_id: str = "app-1") -> None:
    """Insert a minimal `apps` row + `components` row so FK-constrained inserts
    against `status_proposals` succeed.
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
                INSERT INTO components (id, app_id, name, status)
                VALUES (%s, %s, %s, 'operational')
                ON CONFLICT (id) DO NOTHING
                """,
                (component_id, app_id, component_id),
            )
        conn.commit()


def test_postgres_proposal_repository_enforces_one_open_proposal_per_component(migrated_db, engine):
    from src.adapters.persistence.proposal_repository import PostgresProposalRepository
    from src.core.domain.proposal import ProposalState, StatusProposal

    seed_component(migrated_db.database_url, "checkout-comp")
    repo = PostgresProposalRepository(engine)

    prop1 = StatusProposal(
        component_id="checkout-comp",
        from_status=None,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
    )

    # First succeeds and returns StatusProposal with id populated
    saved1 = repo.create_open(prop1)
    assert saved1 is not None
    assert saved1.id is not None
    assert saved1.state == ProposalState.OPEN

    # Second open proposal for same component returns None (ON CONFLICT DO NOTHING)
    prop2 = StatusProposal(
        component_id="checkout-comp",
        from_status=ComponentStatus.DEGRADED,
        to_status=ComponentStatus.MAJOR_OUTAGE,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 26, 12, 1, 0, tzinfo=timezone.utc),
    )
    saved2 = repo.create_open(prop2)
    assert saved2 is None

