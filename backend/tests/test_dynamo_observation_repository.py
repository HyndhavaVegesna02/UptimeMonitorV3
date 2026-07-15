from __future__ import annotations

from datetime import datetime, timedelta, timezone

import psycopg
from src.adapters.persistence.dynamo_observation_repository import (
    DynamoObservationRepository,
)
from src.adapters.persistence.observation_repository import (
    PostgresObservationRepository,
)
from src.composition.settings import load_settings
from src.core.domain import Health, Provenance, SignalObservation
from src.core.queries.availability import AvailabilityCalculator


def seed_signal(database_url: str, signal_key: str, app_id: str = "app-1") -> None:
    """Insert a minimal `apps` row + `signals` row so FK-constrained inserts
    against `observations`/`watermarks` for `signal_key` succeed.
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


def _observation(
    signal_key: str = "checkout-http",
    event_id: str = "evt-1",
    observed_at: datetime | None = None,
    health: Health = Health.UP,
    location: str = "us-east",
    latency_ms: int | None = None,
    response_status_code: int | None = None,
    raw_ref: str | None = None,
) -> SignalObservation:
    return SignalObservation(
        signal_key=signal_key,
        observed_at=observed_at or datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc),
        health=health,
        source_event_id=event_id,
        source=Provenance(system="dynatrace", native_id="X-1", native_kind="http"),
        location=location,
        latency_ms=latency_ms,
        response_status_code=response_status_code,
        raw_ref=raw_ref,
    )


def test_dynamo_observation_repository_save_new_empty(dynamo_resource):
    settings = load_settings()
    repo = DynamoObservationRepository(
        dynamo_resource, settings.dynamo_observations_table
    )

    # Empty batch returns 0
    assert repo.save_new([]) == 0


def test_dynamo_observation_repository_lifecycle(dynamo_resource):
    settings = load_settings()
    repo = DynamoObservationRepository(
        dynamo_resource, settings.dynamo_observations_table
    )

    obs1 = _observation(
        event_id="evt-1", latency_ms=120, response_status_code=200, raw_ref="ref-1"
    )
    obs2 = _observation(
        event_id="evt-2", latency_ms=None, response_status_code=None, raw_ref=None
    )

    # Save new returns 2
    assert repo.save_new([obs1, obs2]) == 2

    # Idempotency: re-saving same events inserts 0
    assert repo.save_new([obs1, obs2]) == 0

    # Idempotency: same event_id but different observed_at (cross-attribute case)
    obs1_dup = _observation(
        event_id="evt-1",
        observed_at=datetime(2026, 6, 24, 11, 0, 0, tzinfo=timezone.utc),
    )
    assert repo.save_new([obs1_dup]) == 0

    # Roundtrip check
    since = datetime(2026, 6, 24, 9, 0, 0, tzinfo=timezone.utc)
    until = datetime(2026, 6, 24, 12, 0, 0, tzinfo=timezone.utc)

    results = repo.in_window("checkout-http", since, until)
    assert len(results) == 2

    # Sort by observed_at to check fields
    sorted_res = sorted(results, key=lambda x: x.source_event_id)

    assert sorted_res[0].source_event_id == "evt-1"
    assert sorted_res[0].latency_ms == 120
    assert sorted_res[0].response_status_code == 200
    assert sorted_res[0].raw_ref == "ref-1"
    assert sorted_res[0].observed_at == obs1.observed_at
    assert sorted_res[0].health == Health.UP
    assert sorted_res[0].location == "us-east"
    assert sorted_res[0].source.system == "dynatrace"

    assert sorted_res[1].source_event_id == "evt-2"
    assert sorted_res[1].latency_ms is None
    assert sorted_res[1].response_status_code is None
    assert sorted_res[1].raw_ref is None


def test_dynamo_observation_repository_half_open_window(dynamo_resource):
    settings = load_settings()
    repo = DynamoObservationRepository(
        dynamo_resource, settings.dynamo_observations_table
    )

    since = datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc)
    until = datetime(2026, 6, 24, 11, 0, 0, tzinfo=timezone.utc)

    obs_before = _observation(
        event_id="evt-before", observed_at=since - timedelta(seconds=1)
    )
    obs_exactly_since = _observation(event_id="evt-since", observed_at=since)
    obs_middle = _observation(
        event_id="evt-middle", observed_at=since + timedelta(minutes=30)
    )
    obs_exactly_until = _observation(event_id="evt-until", observed_at=until)
    obs_after = _observation(
        event_id="evt-after", observed_at=until + timedelta(seconds=1)
    )

    assert (
        repo.save_new(
            [obs_before, obs_exactly_since, obs_middle, obs_exactly_until, obs_after]
        )
        == 5
    )

    results = repo.in_window("checkout-http", since, until)
    event_ids = {r.source_event_id for r in results}

    assert "evt-since" in event_ids
    assert "evt-middle" in event_ids
    assert "evt-before" not in event_ids
    assert "evt-until" not in event_ids
    assert "evt-after" not in event_ids
    assert len(event_ids) == 2


def test_dynamo_observation_repository_pagination(dynamo_resource):
    settings = load_settings()
    repo = DynamoObservationRepository(
        dynamo_resource, settings.dynamo_observations_table
    )

    since = datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc)
    until = datetime(2026, 6, 24, 11, 0, 0, tzinfo=timezone.utc)

    obs = [
        _observation(event_id=f"evt-{i}", observed_at=since + timedelta(minutes=i))
        for i in range(10)
    ]
    assert repo.save_new(obs) == 10

    # Set limit to force pagination
    repo._limit = 2

    results = repo.in_window("checkout-http", since, until)
    assert len(results) == 10
    assert {r.source_event_id for r in results} == {f"evt-{i}" for i in range(10)}


def test_dynamo_observation_repository_availability_parity(
    dynamo_resource, engine, migrated_db
):
    settings = load_settings()
    dynamo_repo = DynamoObservationRepository(
        dynamo_resource, settings.dynamo_observations_table
    )
    postgres_repo = PostgresObservationRepository(engine)

    since = datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc)
    until = datetime(2026, 6, 24, 11, 0, 0, tzinfo=timezone.utc)

    # Seed signal in Postgres to satisfy foreign key constraint
    seed_signal(migrated_db.database_url, "checkout-http")

    # Generate a canonical multi-location fixture set
    obs_list = [
        _observation(
            location="us-east",
            event_id="e-east-1",
            observed_at=since + timedelta(minutes=5),
            health=Health.UP,
        ),
        _observation(
            location="us-east",
            event_id="e-east-2",
            observed_at=since + timedelta(minutes=15),
            health=Health.DEGRADED,
        ),
        _observation(
            location="us-east",
            event_id="e-east-3",
            observed_at=since + timedelta(minutes=25),
            health=Health.UP,
        ),
        _observation(
            location="us-west",
            event_id="e-west-1",
            observed_at=since + timedelta(minutes=5),
            health=Health.UP,
        ),
        _observation(
            location="us-west",
            event_id="e-west-2",
            observed_at=since + timedelta(minutes=15),
            health=Health.DOWN,
        ),
        _observation(
            location="eu-west",
            event_id="e-eu-1",
            observed_at=since + timedelta(minutes=10),
            health=Health.UP,
        ),
    ]

    assert dynamo_repo.save_new(obs_list) == 6
    assert postgres_repo.save_new(obs_list) == 6

    calc_dynamo = AvailabilityCalculator(observation_repo=dynamo_repo)
    calc_postgres = AvailabilityCalculator(observation_repo=postgres_repo)

    res_dynamo = calc_dynamo.compute(
        "checkout-http",
        since=since,
        until=until,
        interval=timedelta(minutes=10),
        window="1h",
        maintenance=lambda cycle_start: False,
        computed_at=since + timedelta(hours=2),
    )

    res_postgres = calc_postgres.compute(
        "checkout-http",
        since=since,
        until=until,
        interval=timedelta(minutes=10),
        window="1h",
        maintenance=lambda cycle_start: False,
        computed_at=since + timedelta(hours=2),
    )

    assert res_dynamo.availability_pct == res_postgres.availability_pct
    assert res_dynamo.completeness_pct == res_postgres.completeness_pct
    assert res_dynamo.total_verdicts == res_postgres.total_verdicts
    assert res_dynamo.passing_verdicts == res_postgres.passing_verdicts
    assert res_dynamo.maintenance_verdicts == res_postgres.maintenance_verdicts
    assert res_dynamo.gap_verdicts == res_postgres.gap_verdicts
    assert res_dynamo.distinct_locations == res_postgres.distinct_locations
