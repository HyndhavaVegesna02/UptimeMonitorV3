"""Tests for the history API feature (dossier §13, §17).

Exercises GET /api/v1/history?signal_key=... via TestClient with
FakeObservationRepository (in-memory). Covers:
  - 200 + observation DTOs (most-recent first) when observations exist (AC2)
  - 200 + [] for empty window (AC2)
  - 422 when signal_key is missing (AC2)
  - explicit since/until honored (AC3)
  - Five-file shape assertion (AC4)
  - limit query param (STORY-094 AC1/AC2): fake-repo tests above plus one
    real-DynamoDB-Local test (test_history_limit_against_real_dynamo_repository)
"""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from src.composition.app import create_app
from src.core.domain import Health, Provenance, SignalObservation
from tests.fakes import (
    FakeClock,
    FakeComponentRepository,
    FakeMaintenanceRepository,
    FakeObservationRepository,
    FakeProposalRepository,
)

_NOW = datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)


def _obs(
    signal_key: str = "checkout-http",
    event_id: str = "evt-1",
    observed_at: datetime | None = None,
    health: Health = Health.UP,
    location: str = "us-east",
    response_status_code: int | None = None,
    native_kind: str = "http",
) -> SignalObservation:
    return SignalObservation(
        signal_key=signal_key,
        observed_at=observed_at or (_NOW - timedelta(hours=1)),
        health=health,
        source_event_id=event_id,
        source=Provenance(system="dynatrace", native_id="X-1", native_kind=native_kind),
        location=location,
        response_status_code=response_status_code,
    )


def _app(observation_repo: FakeObservationRepository, clock: FakeClock):
    return create_app(
        proposal_repo=FakeProposalRepository(),
        component_repo=FakeComponentRepository(),
        maintenance_repo=FakeMaintenanceRepository(),
        observation_repo=observation_repo,
        clock=clock,
    )


def test_history_with_observations_returns_200_most_recent_first():
    """AC2: observations in window → 200 + DTOs sorted most-recent first."""
    earlier = _NOW - timedelta(hours=2)
    later = _NOW - timedelta(hours=1)
    obs_repo = FakeObservationRepository()
    obs_repo.save_new(
        [
            _obs(event_id="e-earlier", observed_at=earlier),
            _obs(event_id="e-later", observed_at=later),
        ]
    )
    clock = FakeClock(_NOW)
    client = TestClient(_app(obs_repo, clock))

    response = client.get("/api/v1/history?signal_key=checkout-http")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Most recent first
    assert data[0]["signal_key"] == "checkout-http"
    assert data[0]["health"] == "up"
    # observed_at of first item must be >= second item
    from datetime import datetime as dt_

    t0 = dt_.fromisoformat(data[0]["observed_at"])
    t1 = dt_.fromisoformat(data[1]["observed_at"])
    assert t0 >= t1


def test_history_empty_window_returns_200_empty_list():
    """AC2: empty window → 200 + []."""
    obs_repo = FakeObservationRepository()
    clock = FakeClock(_NOW)
    client = TestClient(_app(obs_repo, clock))

    response = client.get("/api/v1/history?signal_key=checkout-http")

    assert response.status_code == 200
    assert response.json() == []


def test_history_missing_signal_key_returns_422():
    """AC2: missing required signal_key → 422 before any core call."""
    obs_repo = FakeObservationRepository()
    clock = FakeClock(_NOW)
    client = TestClient(_app(obs_repo, clock))

    response = client.get("/api/v1/history")

    assert response.status_code == 422


def test_history_naive_timestamp_returns_422():
    """Regression: a timezone-naive since/until → 422 (not a 500 from tz-aware compare in core)."""
    obs_repo = FakeObservationRepository()
    clock = FakeClock(_NOW)
    client = TestClient(_app(obs_repo, clock))

    naive_until = client.get(
        "/api/v1/history?signal_key=checkout-http&until=2026-06-28T10:00:00"
    )
    assert naive_until.status_code == 422

    naive_since = client.get(
        "/api/v1/history?signal_key=checkout-http&since=2026-06-28"
    )
    assert naive_since.status_code == 422


def test_history_explicit_since_until_honored():
    """AC3: explicit since/until overrides the 24h default window."""
    since = datetime(2026, 6, 28, 8, 0, 0, tzinfo=timezone.utc)
    until = datetime(2026, 6, 28, 10, 0, 0, tzinfo=timezone.utc)
    obs_inside = _obs(event_id="inside", observed_at=since + timedelta(hours=1))
    obs_before = _obs(event_id="before", observed_at=since - timedelta(hours=1))

    obs_repo = FakeObservationRepository()
    obs_repo.save_new([obs_inside, obs_before])
    clock = FakeClock(_NOW)
    client = TestClient(_app(obs_repo, clock))

    # Use params dict so TestClient handles URL encoding (+ in timezone offset)
    response = client.get(
        "/api/v1/history",
        params={
            "signal_key": "checkout-http",
            "since": since.isoformat(),
            "until": until.isoformat(),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["signal_key"] == "checkout-http"


def test_history_dto_omits_source_and_raw_ref():
    """AC2 / plan B1: DTO omits source/raw_ref/source_event_id from the client view."""
    obs_repo = FakeObservationRepository()
    obs_repo.save_new([_obs(event_id="e1")])
    clock = FakeClock(_NOW)
    client = TestClient(_app(obs_repo, clock))

    response = client.get("/api/v1/history?signal_key=checkout-http")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    item = data[0]
    assert "source" not in item
    assert "raw_ref" not in item
    assert "source_event_id" not in item
    # Required fields
    assert "signal_key" in item
    assert "observed_at" in item
    assert "health" in item
    assert "location" in item


def test_history_dto_carries_response_status_code_and_check_type():
    """STORY-064 AC3: ObservationDTO carries response_status_code (int|null)
    and check_type (from the persisted provenance native_kind)."""
    obs_repo = FakeObservationRepository()
    obs_repo.save_new(
        [
            _obs(event_id="e-with-code", response_status_code=200, native_kind="http"),
            _obs(
                event_id="e-without-code", response_status_code=None, native_kind="http"
            ),
        ]
    )
    clock = FakeClock(_NOW)
    client = TestClient(_app(obs_repo, clock))

    response = client.get("/api/v1/history?signal_key=checkout-http")

    assert response.status_code == 200
    data = response.json()
    by_event = {}
    for item in data:
        assert "response_status_code" in item
        assert "check_type" in item
        assert item["check_type"] == "http"
    for item in data:
        # observed_at differs by event but signal_key is shared; disambiguate
        # via response_status_code presence.
        by_event[item["response_status_code"]] = item

    assert by_event[200]["response_status_code"] == 200
    assert by_event[None]["response_status_code"] is None


def test_history_limit_returns_n_newest():
    """AC1: limit=N (int >= 1) returns at most N observations, newest-first."""
    obs_repo = FakeObservationRepository()
    base = _NOW - timedelta(hours=5)
    obs_repo.save_new(
        [
            _obs(event_id=f"e-{i}", observed_at=base + timedelta(hours=i))
            for i in range(5)
        ]
    )
    clock = FakeClock(_NOW)
    client = TestClient(_app(obs_repo, clock))

    response = client.get("/api/v1/history?signal_key=checkout-http&limit=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # The two newest are e-4 (base+4h) and e-3 (base+3h), most-recent first.
    from datetime import datetime as dt_

    t0 = dt_.fromisoformat(data[0]["observed_at"])
    t1 = dt_.fromisoformat(data[1]["observed_at"])
    assert t0 == base + timedelta(hours=4)
    assert t1 == base + timedelta(hours=3)


def test_history_limit_larger_than_result_set_returns_all():
    """AC1: limit larger than the in-window result set returns everything."""
    obs_repo = FakeObservationRepository()
    base = _NOW - timedelta(hours=5)
    obs_repo.save_new(
        [
            _obs(event_id=f"e-{i}", observed_at=base + timedelta(hours=i))
            for i in range(5)
        ]
    )
    clock = FakeClock(_NOW)
    client = TestClient(_app(obs_repo, clock))

    response = client.get("/api/v1/history?signal_key=checkout-http&limit=100")

    assert response.status_code == 200
    assert len(response.json()) == 5


def test_history_limit_absent_matches_existing_full_window_behavior():
    """AC2: absent limit → identical full-window behavior (no cap applied)."""
    obs_repo = FakeObservationRepository()
    base = _NOW - timedelta(hours=5)
    obs_repo.save_new(
        [
            _obs(event_id=f"e-{i}", observed_at=base + timedelta(hours=i))
            for i in range(5)
        ]
    )
    clock = FakeClock(_NOW)
    client = TestClient(_app(obs_repo, clock))

    response = client.get("/api/v1/history?signal_key=checkout-http")

    assert response.status_code == 200
    assert len(response.json()) == 5


def test_history_limit_zero_returns_422():
    """AC2: limit=0 -> clean 422 via the validation seam (STORY-052 convention)."""
    obs_repo = FakeObservationRepository()
    clock = FakeClock(_NOW)
    client = TestClient(_app(obs_repo, clock))

    response = client.get("/api/v1/history?signal_key=checkout-http&limit=0")

    assert response.status_code == 422


def test_history_limit_negative_returns_422():
    """AC2: limit=-1 -> clean 422."""
    obs_repo = FakeObservationRepository()
    clock = FakeClock(_NOW)
    client = TestClient(_app(obs_repo, clock))

    response = client.get("/api/v1/history?signal_key=checkout-http&limit=-1")

    assert response.status_code == 422


def test_history_limit_non_int_returns_422():
    """AC2: limit=abc (non-int) -> clean 422 (FastAPI's own coercion)."""
    obs_repo = FakeObservationRepository()
    clock = FakeClock(_NOW)
    client = TestClient(_app(obs_repo, clock))

    response = client.get("/api/v1/history?signal_key=checkout-http&limit=abc")

    assert response.status_code == 422


def test_history_limit_against_real_dynamo_repository(
    dynamo_local, dynamo_resource, clean_dynamo_tables
):
    """AC1: limit=N against the real DynamoDB-Local repository path (not the fake)."""
    from src.adapters.persistence.dynamo_observation_repository import (
        DynamoObservationRepository,
    )
    from src.composition.settings import load_settings

    settings = load_settings()
    observation_repo = DynamoObservationRepository(
        dynamo_resource, settings.dynamo_observations_table
    )

    signal_key = "checkout-http-dynamo"
    base = _NOW - timedelta(hours=5)
    observations = [
        _obs(
            signal_key=signal_key,
            event_id=f"evt-dynamo-{i}",
            observed_at=base + timedelta(hours=i),
        )
        for i in range(5)
    ]
    observation_repo.save_new(observations)

    clock = FakeClock(_NOW)
    client = TestClient(_app(observation_repo, clock))

    response = client.get(f"/api/v1/history?signal_key={signal_key}&limit=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    from datetime import datetime as dt_

    t0 = dt_.fromisoformat(data[0]["observed_at"])
    t1 = dt_.fromisoformat(data[1]["observed_at"])
    assert t0 == base + timedelta(hours=4)
    assert t1 == base + timedelta(hours=3)


def test_history_module_five_file_shape():
    """AC4: the history feature follows the five-file convention exactly."""
    from pathlib import Path

    from src.api.v1 import history

    pkg_dir = Path(history.__file__).parent
    py_files = {p.name for p in pkg_dir.glob("*.py")}
    assert py_files == {
        "__init__.py",
        "controller.py",
        "models.py",
        "validation.py",
        "service.py",
    }
