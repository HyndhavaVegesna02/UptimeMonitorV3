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
from src.core.domain import ComponentStatus, Health, Provenance, SignalObservation

# The `engine` fixture is provided by conftest.py (STORY-039: includes
# clean_runtime_tables for per-test isolation on a reused DB).


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
    response_status_code: int | None = None,
) -> SignalObservation:
    return SignalObservation(
        signal_key=signal_key,
        observed_at=observed_at or datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc),
        health=health,
        source_event_id=event_id,
        source=Provenance(system="dynatrace", native_id="X-1", native_kind="http"),
        location=location,
        response_status_code=response_status_code,
    )


# --- ObservationRepository --------------------------------------------------


def test_observations_response_status_code_column_exists_and_is_nullable(migrated_db):
    """STORY-064 AC2: the migration adds a nullable Integer
    `observations.response_status_code` column."""
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT data_type, is_nullable FROM information_schema.columns "
                "WHERE table_name = 'observations' "
                "AND column_name = 'response_status_code'"
            )
            row = cur.fetchone()

    assert row is not None, "observations.response_status_code column is missing"
    data_type, is_nullable = row
    assert data_type == "integer"
    assert is_nullable == "YES"


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


def test_save_new_reinserting_existing_event_ids_inserts_zero_new_rows(
    migrated_db, engine
):
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


def test_in_window_returns_only_observations_inside_the_half_open_range(
    migrated_db, engine
):
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


def test_postgres_proposal_repository_enforces_one_open_proposal_per_component(
    migrated_db, engine
):
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


def test_postgres_proposal_repository_get_open(migrated_db, engine):
    from src.adapters.persistence.proposal_repository import PostgresProposalRepository
    from src.core.domain.proposal import ProposalState, StatusProposal

    seed_component(migrated_db.database_url, "get-open-comp")
    repo = PostgresProposalRepository(engine)

    # get_open returns None when no open proposal exists
    assert repo.get_open("get-open-comp") is None

    prop = StatusProposal(
        component_id="get-open-comp",
        from_status=ComponentStatus.OPERATIONAL,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
    )
    saved = repo.create_open(prop)
    assert saved is not None

    # get_open returns the open proposal
    fetched = repo.get_open("get-open-comp")
    assert fetched is not None
    assert fetched.id == saved.id
    assert fetched.component_id == "get-open-comp"
    assert fetched.from_status == ComponentStatus.OPERATIONAL
    assert fetched.to_status == ComponentStatus.DEGRADED
    assert fetched.state == ProposalState.OPEN
    assert fetched.proposed_at == datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc)
    assert fetched.resolved_at is None


def test_postgres_proposal_repository_resolve(migrated_db, engine):
    from src.adapters.persistence.proposal_repository import PostgresProposalRepository
    from src.core.domain.proposal import ProposalState, StatusProposal

    seed_component(migrated_db.database_url, "resolve-comp")
    repo = PostgresProposalRepository(engine)

    prop = StatusProposal(
        component_id="resolve-comp",
        from_status=None,
        to_status=ComponentStatus.MAJOR_OUTAGE,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
    )
    saved = repo.create_open(prop)
    assert saved is not None

    resolved_time = datetime(2026, 6, 26, 12, 10, 0, tzinfo=timezone.utc)
    repo.resolve(
        saved.id,
        to_state=ProposalState.APPROVED,
        reason="Incident verified",
        resolved_at=resolved_time,
    )

    # get_open returns None because it is now terminal
    assert repo.get_open("resolve-comp") is None

    # We can create a new open proposal for the component now
    new_prop = StatusProposal(
        component_id="resolve-comp",
        from_status=ComponentStatus.MAJOR_OUTAGE,
        to_status=ComponentStatus.OPERATIONAL,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 26, 12, 15, 0, tzinfo=timezone.utc),
    )
    new_saved = repo.create_open(new_prop)
    assert new_saved is not None
    assert new_saved.id != saved.id


def test_postgres_proposal_repository_record_approval_event(migrated_db, engine):
    from src.adapters.persistence.proposal_repository import PostgresProposalRepository
    from src.core.domain.proposal import ProposalState, StatusProposal

    seed_component(migrated_db.database_url, "event-comp")
    repo = PostgresProposalRepository(engine)

    prop = StatusProposal(
        component_id="event-comp",
        from_status=None,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
    )
    saved = repo.create_open(prop)
    assert saved is not None

    occurred_time = datetime(2026, 6, 26, 12, 5, 0, tzinfo=timezone.utc)
    repo.record_approval_event(
        saved.id,
        actor="ops-admin",
        action="approved",
        notes="Checked dashboard, confirmed",
        occurred_at=occurred_time,
    )

    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT proposal_id, actor, action, notes, occurred_at FROM approval_events "
                "WHERE proposal_id = %s",
                (saved.id,),
            )
            rows = cur.fetchall()

    assert len(rows) == 1
    proposal_id, actor, action, notes, occurred_at = rows[0]
    assert proposal_id == saved.id
    assert actor == "ops-admin"
    assert action == "approved"
    assert notes == "Checked dashboard, confirmed"
    assert occurred_at == occurred_time


def test_approval_service_approve_and_reject_persist_action_via_real_postgres(
    migrated_db, engine
):
    """STORY-071 regression (AC1/AC2): drives a REAL approve AND a REAL reject
    through the REAL `ApprovalService` + `PostgresProposalRepository` against the
    real Postgres `ck_approval_events_action` constraint (`action IN ('approved',
    'rejected')`). Before the fix, `ApprovalService._decide` recorded the present
    -tense verb ("approve"/"reject") and this test failed with
    `psycopg.errors.CheckViolation` on `ck_approval_events_action`. After the fix
    (`action=to_state.value`), both persist cleanly with the past-tense value that
    matches the resolved `state` — closing the fake/adapter-parity gap (no DB-gated
    test previously drove approve/reject through the real constraint).
    """
    from src.adapters.persistence.proposal_repository import PostgresProposalRepository
    from src.core.domain.proposal import ProposalState, StatusProposal
    from src.core.services.approval import ApprovalService
    from tests.fakes import FakeClock, RecordingStatusPublisher

    seed_component(migrated_db.database_url, "approve-real-comp")
    seed_component(migrated_db.database_url, "reject-real-comp")
    repo = PostgresProposalRepository(engine)
    clock = FakeClock(datetime(2026, 7, 8, 9, 0, 0, tzinfo=timezone.utc))
    publisher = RecordingStatusPublisher()
    service = ApprovalService(proposal_repo=repo, clock=clock, publisher=publisher)

    approve_prop = StatusProposal(
        component_id="approve-real-comp",
        from_status=ComponentStatus.OPERATIONAL,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 7, 8, 8, 0, 0, tzinfo=timezone.utc),
    )
    saved_approve = repo.create_open(approve_prop)
    assert saved_approve is not None

    reject_prop = StatusProposal(
        component_id="reject-real-comp",
        from_status=ComponentStatus.OPERATIONAL,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 7, 8, 8, 0, 0, tzinfo=timezone.utc),
    )
    saved_reject = repo.create_open(reject_prop)
    assert saved_reject is not None

    # No CheckViolation on either path.
    approved = service.approve(saved_approve.id, actor="ops-1", notes="Approve it")
    rejected = service.reject(saved_reject.id, actor="ops-1", notes="Reject it")

    assert approved.state == ProposalState.APPROVED
    assert rejected.state == ProposalState.REJECTED

    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT proposal_id, action FROM approval_events "
                "WHERE proposal_id IN (%s, %s) ORDER BY proposal_id",
                (saved_approve.id, saved_reject.id),
            )
            rows = cur.fetchall()

    assert rows == [
        (saved_approve.id, "approved"),
        (saved_reject.id, "rejected"),
    ]


def test_fake_and_real_proposal_repository_agree_on_recorded_action(
    migrated_db, engine
):
    """STORY-071 AC3 (fake/adapter parity): the fake and the real repository
    must record the SAME `action` string for approve/reject when driven through
    `ApprovalService`, so a future drift between them is caught without needing
    Postgres to reject it."""
    from src.adapters.persistence.proposal_repository import PostgresProposalRepository
    from src.core.domain.proposal import ProposalState, StatusProposal
    from src.core.services.approval import ApprovalService
    from tests.fakes import FakeClock, FakeProposalRepository, RecordingStatusPublisher

    clock = FakeClock(datetime(2026, 7, 8, 9, 0, 0, tzinfo=timezone.utc))

    def _prop(component_id: str) -> StatusProposal:
        return StatusProposal(
            component_id=component_id,
            from_status=ComponentStatus.OPERATIONAL,
            to_status=ComponentStatus.DEGRADED,
            state=ProposalState.OPEN,
            proposed_at=datetime(2026, 7, 8, 8, 0, 0, tzinfo=timezone.utc),
        )

    # Real repository.
    seed_component(migrated_db.database_url, "parity-approve-comp")
    seed_component(migrated_db.database_url, "parity-reject-comp")
    real_repo = PostgresProposalRepository(engine)
    real_service = ApprovalService(
        proposal_repo=real_repo, clock=clock, publisher=RecordingStatusPublisher()
    )
    real_approved = real_repo.create_open(_prop("parity-approve-comp"))
    real_rejected = real_repo.create_open(_prop("parity-reject-comp"))
    assert real_approved is not None and real_rejected is not None
    real_service.approve(real_approved.id, actor="ops-1")
    real_service.reject(real_rejected.id, actor="ops-1")

    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT action FROM approval_events WHERE proposal_id = %s",
                (real_approved.id,),
            )
            real_approve_action = cur.fetchone()[0]
            cur.execute(
                "SELECT action FROM approval_events WHERE proposal_id = %s",
                (real_rejected.id,),
            )
            real_reject_action = cur.fetchone()[0]

    # Fake repository.
    fake_repo = FakeProposalRepository()
    fake_service = ApprovalService(
        proposal_repo=fake_repo, clock=clock, publisher=RecordingStatusPublisher()
    )
    fake_approved = fake_repo.create_open(_prop("parity-approve-comp"))
    fake_rejected = fake_repo.create_open(_prop("parity-reject-comp"))
    assert fake_approved is not None and fake_rejected is not None
    fake_service.approve(fake_approved.id, actor="ops-1")
    fake_service.reject(fake_rejected.id, actor="ops-1")

    fake_approve_action = fake_repo.approval_events[0]["action"]
    fake_reject_action = fake_repo.approval_events[1]["action"]

    assert real_approve_action == fake_approve_action == "approved"
    assert real_reject_action == fake_reject_action == "rejected"


def test_postgres_proposal_repository_resolve_unknown_raises(migrated_db, engine):
    from src.adapters.persistence.proposal_repository import PostgresProposalRepository
    from src.core.domain.proposal import ProposalState

    repo = PostgresProposalRepository(engine)
    resolved_time = datetime(2026, 6, 26, 12, 10, 0, tzinfo=timezone.utc)

    # Resolving unknown proposal ID raises
    with pytest.raises(ValueError):
        repo.resolve(
            9999,
            to_state=ProposalState.APPROVED,
            reason="Will fail",
            resolved_at=resolved_time,
        )


def test_postgres_proposal_repository_resolve_already_terminal_raises(
    migrated_db, engine
):
    from src.adapters.persistence.proposal_repository import PostgresProposalRepository
    from src.core.domain.proposal import ProposalState, StatusProposal

    seed_component(migrated_db.database_url, "resolve-terminal-comp")
    repo = PostgresProposalRepository(engine)

    prop = StatusProposal(
        component_id="resolve-terminal-comp",
        from_status=None,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
    )
    saved = repo.create_open(prop)
    assert saved is not None

    resolved_time = datetime(2026, 6, 26, 12, 5, 0, tzinfo=timezone.utc)
    # First resolve succeeds
    repo.resolve(
        saved.id,
        to_state=ProposalState.APPROVED,
        reason="first",
        resolved_at=resolved_time,
    )

    # Resolving again raises ValueError and doesn't change stored row
    with pytest.raises(ValueError):
        repo.resolve(
            saved.id,
            to_state=ProposalState.SUPERSEDED,
            reason="second",
            resolved_at=resolved_time + timedelta(minutes=5),
        )

    # Verify that it remains APPROVED in the DB, not SUPERSEDED
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT state, reason FROM status_proposals WHERE id = %s", (saved.id,)
            )
            state, reason = cur.fetchone()
    assert state == "approved"
    assert reason == "first"


def test_postgres_proposal_repository_get(migrated_db, engine):
    from src.adapters.persistence.proposal_repository import PostgresProposalRepository
    from src.core.domain.proposal import ProposalState, StatusProposal

    seed_component(migrated_db.database_url, "get-comp")
    repo = PostgresProposalRepository(engine)

    # get returns None for unknown id
    assert repo.get(99999) is None

    prop = StatusProposal(
        component_id="get-comp",
        from_status=ComponentStatus.OPERATIONAL,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
    )
    saved = repo.create_open(prop)
    assert saved is not None
    assert saved.id is not None

    # get returns the saved proposal
    fetched = repo.get(saved.id)
    assert fetched is not None
    assert fetched.id == saved.id
    assert fetched.component_id == "get-comp"
    assert fetched.from_status == ComponentStatus.OPERATIONAL
    assert fetched.to_status == ComponentStatus.DEGRADED
    assert fetched.state == ProposalState.OPEN
    assert fetched.proposed_at == datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc)
    assert fetched.resolved_at is None


def test_postgres_component_repository_list_components(migrated_db, engine):
    from src.adapters.persistence.component_repository import (
        PostgresComponentRepository,
    )
    from src.core.domain.status import ComponentStatus

    # Clear components table for isolation in this test
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE components CASCADE;")
        conn.commit()

    repo = PostgresComponentRepository(engine)
    # Empty case
    assert repo.list_components() == []

    # Seed some components
    seed_component(migrated_db.database_url, "comp-a", "app-a")
    seed_component(migrated_db.database_url, "comp-b", "app-a")

    # Update status of one component to degraded to verify status mapping
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE components SET status = 'degraded' WHERE id = 'comp-b';"
            )
        conn.commit()

    components = repo.list_components()
    assert len(components) == 2

    # Sort by ID to assert safely
    components_sorted = sorted(components, key=lambda c: c.id)

    assert components_sorted[0].id == "comp-a"
    assert components_sorted[0].name == "comp-a"
    assert components_sorted[0].status == ComponentStatus.OPERATIONAL
    assert components_sorted[0].app_id == "app-a"

    assert components_sorted[1].id == "comp-b"
    assert components_sorted[1].name == "comp-b"
    assert components_sorted[1].status == ComponentStatus.DEGRADED
    assert components_sorted[1].app_id == "app-a"


def test_postgres_component_repository_get(migrated_db, engine):
    """DB-gated: PostgresComponentRepository.get() returns Component or None.

    Fake/adapter parity (working-agreements.md 2026-06-26): same None-on-not-found
    behaviour as FakeComponentRepository.get. STORY-016a A3.
    """
    from src.adapters.persistence.component_repository import (
        PostgresComponentRepository,
    )
    from src.core.domain.status import ComponentStatus

    # Clear components for isolation
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE components CASCADE;")
        conn.commit()

    repo = PostgresComponentRepository(engine)

    # not-found → None (before seeding)
    assert repo.get("get-by-id-comp") is None

    # seed a component
    seed_component(migrated_db.database_url, "get-by-id-comp", "app-1")

    # found → Component
    result = repo.get("get-by-id-comp")
    assert result is not None
    assert result.id == "get-by-id-comp"
    assert result.name == "get-by-id-comp"
    assert result.status == ComponentStatus.OPERATIONAL
    assert result.app_id == "app-1"

    # absent component_id → None even when other components exist
    assert repo.get("other-comp-does-not-exist") is None


def test_postgres_proposal_repository_list_open(migrated_db, engine):
    from src.adapters.persistence.proposal_repository import PostgresProposalRepository
    from src.core.domain.proposal import ProposalState, StatusProposal
    from src.core.domain.status import ComponentStatus

    # Clear status_proposals and components for isolation
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE components CASCADE;")
        conn.commit()

    repo = PostgresProposalRepository(engine)
    # Empty case
    assert repo.list_open() == []

    # Seed component so we can insert proposals
    seed_component(migrated_db.database_url, "comp-a", "app-a")

    # Create an open proposal
    prop1 = StatusProposal(
        component_id="comp-a",
        from_status=ComponentStatus.OPERATIONAL,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
    )
    saved1 = repo.create_open(prop1)
    assert saved1 is not None

    # Retrieve when one open proposal exists
    open_proposals = repo.list_open()
    assert len(open_proposals) == 1
    assert open_proposals[0].id == saved1.id
    assert open_proposals[0].component_id == "comp-a"
    assert open_proposals[0].state == ProposalState.OPEN

    # Resolve proposal (move to terminal APPROVED state)
    repo.resolve(
        saved1.id,
        to_state=ProposalState.APPROVED,
        reason="Approved",
        resolved_at=datetime(2026, 6, 26, 12, 5, 0, tzinfo=timezone.utc),
    )

    # Empty case again because the proposal is terminal
    assert repo.list_open() == []


def test_postgres_maintenance_repository(migrated_db, engine):
    from src.adapters.persistence.maintenance_repository import (
        PostgresMaintenanceRepository,
    )
    from src.core.domain.maintenance import MaintenanceWindow

    # Clear tables for isolation
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE components CASCADE;")
        conn.commit()

    repo = PostgresMaintenanceRepository(engine)

    # Empty case parity
    assert repo.list_windows() == []
    at_time = datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)
    assert repo.is_under_maintenance("checkout", at_time) is False

    # Seed component
    seed_component(migrated_db.database_url, "checkout", "app-1")

    # Create window
    w1 = MaintenanceWindow(
        component_id="checkout",
        starts_at=datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 6, 28, 14, 0, 0, tzinfo=timezone.utc),
        reason="Update 1",
    )
    saved1 = repo.create(w1)
    assert saved1.id is not None
    assert saved1.component_id == "checkout"
    assert saved1.reason == "Update 1"

    # Create another window, starts earlier so we test ordering
    w2 = MaintenanceWindow(
        component_id="checkout",
        starts_at=datetime(2026, 6, 28, 10, 0, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 6, 28, 11, 0, 0, tzinfo=timezone.utc),
        reason="Update 2",
    )
    saved2 = repo.create(w2)
    assert saved2.id is not None

    # list_windows returns all ordered by starts_at
    windows = repo.list_windows()
    assert len(windows) == 2
    assert windows[0].id == saved2.id
    assert windows[1].id == saved1.id

    # Test is_under_maintenance boundaries (inclusive start / exclusive end)
    # 1. Exact start of w1 (inclusive)
    assert (
        repo.is_under_maintenance(
            "checkout", datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)
        )
        is True
    )
    # 2. Inside w1
    assert (
        repo.is_under_maintenance(
            "checkout", datetime(2026, 6, 28, 13, 0, 0, tzinfo=timezone.utc)
        )
        is True
    )
    # 3. Exact end of w1 (exclusive)
    assert (
        repo.is_under_maintenance(
            "checkout", datetime(2026, 6, 28, 14, 0, 0, tzinfo=timezone.utc)
        )
        is False
    )
    # 4. Outside w1 (before)
    assert (
        repo.is_under_maintenance(
            "checkout", datetime(2026, 6, 28, 11, 30, 0, tzinfo=timezone.utc)
        )
        is False
    )
    # 5. Outside w1 (after)
    assert (
        repo.is_under_maintenance(
            "checkout", datetime(2026, 6, 28, 15, 0, 0, tzinfo=timezone.utc)
        )
        is False
    )

    # Test different component_id
    assert (
        repo.is_under_maintenance(
            "other-component",
            datetime(2026, 6, 28, 12, 30, 0, tzinfo=timezone.utc),
        )
        is False
    )


def test_postgres_publication_repository(migrated_db, engine):
    """DB-gated: PostgresPublicationRepository record + list_recent + fake parity.

    STORY-037 AC1. Publications FK into components (RESTRICT), so we seed a
    component first. The test cleans up publications before running to stay
    order/reused-DB independent (working-agreements.md DB-test reused-DB isolation).
    """
    from src.adapters.persistence.publication_repository import (
        PostgresPublicationRepository,
    )
    from src.core.domain.publication import Publication, PublicationOutcome
    from src.core.domain.status import ComponentStatus

    # Isolation: truncate publications (FKs into components; clean it first)
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE publications;")
        conn.commit()

    # Seed the component FK parent
    seed_component(migrated_db.database_url, "pub-comp", "pub-app")

    repo = PostgresPublicationRepository(engine)

    # Parity: empty → []
    assert repo.list_recent() == []

    # record() inserts + returns persisted row with id
    pub1 = Publication(
        component_id="pub-comp",
        status=ComponentStatus.DEGRADED,
        published_at=datetime(2026, 6, 29, 10, 0, 0, tzinfo=timezone.utc),
    )
    saved1 = repo.record(pub1)
    assert saved1.id is not None
    assert saved1.component_id == "pub-comp"
    assert saved1.status == ComponentStatus.DEGRADED
    assert saved1.published_at == datetime(2026, 6, 29, 10, 0, 0, tzinfo=timezone.utc)
    assert saved1.proposal_id is None
    # STORY-072: outcome defaults to SUCCEEDED and round-trips through Postgres.
    assert saved1.outcome == PublicationOutcome.SUCCEEDED

    # Record a second, more recent publication
    pub2 = Publication(
        component_id="pub-comp",
        status=ComponentStatus.OPERATIONAL,
        published_at=datetime(2026, 6, 29, 12, 0, 0, tzinfo=timezone.utc),
    )
    saved2 = repo.record(pub2)
    assert saved2.id is not None
    assert saved2.id != saved1.id

    # list_recent returns most-recent-first
    results = repo.list_recent()
    assert len(results) == 2
    assert results[0].id == saved2.id  # more recent first
    assert results[1].id == saved1.id

    # limit parameter is honoured
    limited = repo.list_recent(limit=1)
    assert len(limited) == 1
    assert limited[0].id == saved2.id


def test_postgres_publication_repository_records_failed_outcome(migrated_db, engine):
    """STORY-072 AC1/AC2: PostgresPublicationRepository persists an explicit
    outcome=FAILED record and round-trips it correctly."""
    from src.adapters.persistence.publication_repository import (
        PostgresPublicationRepository,
    )
    from src.core.domain.publication import Publication, PublicationOutcome
    from src.core.domain.status import ComponentStatus

    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE publications;")
        conn.commit()

    seed_component(migrated_db.database_url, "pub-failed-comp", "pub-app")

    repo = PostgresPublicationRepository(engine)

    pub = Publication(
        component_id="pub-failed-comp",
        status=ComponentStatus.MAJOR_OUTAGE,
        published_at=datetime(2026, 7, 8, 9, 0, 0, tzinfo=timezone.utc),
        outcome=PublicationOutcome.FAILED,
    )
    saved = repo.record(pub)

    assert saved.outcome == PublicationOutcome.FAILED

    # Re-read via list_recent to confirm the outcome round-trips from storage,
    # not just from the INSERT ... RETURNING row.
    results = repo.list_recent()
    assert len(results) == 1
    assert results[0].outcome == PublicationOutcome.FAILED


def test_publications_outcome_check_constraint_allows_values_rejects_others(
    migrated_db,
):
    """STORY-072 AC2 (STORY-071 retro lesson — fakes can't model DB constraints):
    drive the REAL `ck_publications_outcome` CHECK constraint directly. Both
    allowed values ('succeeded', 'failed') insert cleanly; a disallowed value
    ('succeed', a plausible typo/present-tense mistake) is rejected with
    `psycopg.errors.CheckViolation`.
    """
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE publications;")
        conn.commit()

    seed_component(migrated_db.database_url, "pub-ck-comp", "pub-app")

    insert_sql = (
        "INSERT INTO publications (component_id, status, published_at, outcome) "
        "VALUES (%s, 'operational', %s, %s)"
    )
    ts = datetime(2026, 7, 8, 9, 0, 0, tzinfo=timezone.utc)

    # Both allowed values insert cleanly.
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(insert_sql, ("pub-ck-comp", ts, "succeeded"))
            cur.execute(insert_sql, ("pub-ck-comp", ts, "failed"))
        conn.commit()

    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM publications WHERE component_id = %s",
                ("pub-ck-comp",),
            )
            (count,) = cur.fetchone()
    assert count == 2

    # A disallowed value is rejected by the CHECK constraint.
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            with pytest.raises(psycopg.errors.CheckViolation):
                cur.execute(insert_sql, ("pub-ck-comp", ts, "succeed"))
        conn.rollback()


def test_recording_publisher_records_exactly_one_row_via_real_postgres_success_and_failure(
    migrated_db, engine
):
    """STORY-072 AC1 regression: drives the REAL `RecordingPublisher` +
    `PostgresPublicationRepository` (wrapped in `BestEffortPublisher`, mirroring
    the production chain) through BOTH a successful publish and a raising
    delegate against a REAL Postgres. Asserts exactly one row is recorded per
    attempt with the correct outcome, and that `BestEffortPublisher` still
    swallows the raising-delegate's exception for the caller (best-effort
    stays intact even though recording now happens on both paths)."""
    from src.adapters.persistence.publication_repository import (
        PostgresPublicationRepository,
    )
    from src.composition.publish_helper import BestEffortPublisher, RecordingPublisher
    from src.core.domain.publication import PublicationOutcome
    from src.core.domain.status import ComponentStatus, StatusChange
    from tests.fakes import FakeClock, RecordingStatusPublisher

    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE publications;")
        conn.commit()

    seed_component(migrated_db.database_url, "pub-real-success", "pub-app")
    seed_component(migrated_db.database_url, "pub-real-failure", "pub-app")

    repo = PostgresPublicationRepository(engine)
    clock = FakeClock(datetime(2026, 7, 8, 9, 0, 0, tzinfo=timezone.utc))

    class RaisingDelegate:
        def publish(self, change: StatusChange) -> None:
            raise RuntimeError("Statuspage 401")

    # --- Success path -------------------------------------------------
    success_delegate = RecordingStatusPublisher()
    success_recording = RecordingPublisher(success_delegate, repo, clock)
    success_best_effort = BestEffortPublisher(success_recording)

    success_change = StatusChange(
        component_id="pub-real-success", status=ComponentStatus.OPERATIONAL
    )
    success_best_effort.publish(success_change)  # must not raise

    # --- Failure path ---------------------------------------------------
    failure_recording = RecordingPublisher(RaisingDelegate(), repo, clock)
    failure_best_effort = BestEffortPublisher(failure_recording)

    failure_change = StatusChange(
        component_id="pub-real-failure", status=ComponentStatus.MAJOR_OUTAGE
    )
    failure_best_effort.publish(failure_change)  # swallowed — must not raise

    results = repo.list_recent()
    by_component = {r.component_id: r for r in results}
    assert len(results) == 2
    assert by_component["pub-real-success"].outcome == PublicationOutcome.SUCCEEDED
    assert by_component["pub-real-failure"].outcome == PublicationOutcome.FAILED
