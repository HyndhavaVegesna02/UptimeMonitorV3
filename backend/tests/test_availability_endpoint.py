"""Tests for the availability API feature (dossier §11, §13).

Exercises GET /api/v1/availability?signal_key=... via TestClient with
FakeObservationRepository (in-memory). Covers:
  - 200 with AvailabilityDTO when observations exist (AC1)
  - 200 with availability_pct=None / completeness_pct=None for empty window (AC1)
  - 200 with explicit since/until honored (AC3)
  - 422 when signal_key is missing (AC2 / AC4)
  - Five-file shape assertion (AC4)
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
) -> SignalObservation:
    return SignalObservation(
        signal_key=signal_key,
        observed_at=observed_at or (_NOW - timedelta(hours=1)),
        health=health,
        source_event_id=event_id,
        source=Provenance(system="dynatrace", native_id="X-1", native_kind="http"),
        location=location,
    )


def _app(observation_repo: FakeObservationRepository, clock: FakeClock):
    return create_app(
        proposal_repo=FakeProposalRepository(),
        component_repo=FakeComponentRepository(),
        maintenance_repo=FakeMaintenanceRepository(),
        observation_repo=observation_repo,
        clock=clock,
    )


def test_availability_with_observations_returns_200_with_dto():
    """AC1: signal with observations → 200 + AvailabilityDTO with percentages."""
    obs_repo = FakeObservationRepository()
    obs_repo.save_new(
        [
            _obs(event_id="e1", observed_at=_NOW - timedelta(hours=2)),
            _obs(event_id="e2", observed_at=_NOW - timedelta(hours=1)),
        ]
    )
    clock = FakeClock(_NOW)
    client = TestClient(_app(obs_repo, clock))

    response = client.get("/api/v1/availability?signal_key=checkout-http")

    assert response.status_code == 200
    data = response.json()
    assert data["availability_pct"] is not None
    assert data["completeness_pct"] is not None
    assert data["total_verdicts"] >= 1
    assert data["window"] == "24h"
    assert "computed_at" in data


def test_availability_no_observations_returns_200_with_none_pcts():
    """AC1: empty window → 200 with availability_pct=None / completeness_pct=None (not 500)."""
    obs_repo = FakeObservationRepository()
    clock = FakeClock(_NOW)
    client = TestClient(_app(obs_repo, clock))

    response = client.get("/api/v1/availability?signal_key=checkout-http")

    assert response.status_code == 200
    data = response.json()
    assert data["availability_pct"] is None
    assert data["completeness_pct"] is None
    assert data["total_verdicts"] == 0
    assert data["distinct_locations"] == 0


def test_availability_missing_signal_key_returns_422():
    """AC2 / AC4: missing required signal_key → 422 before any core call."""
    obs_repo = FakeObservationRepository()
    clock = FakeClock(_NOW)
    client = TestClient(_app(obs_repo, clock))

    response = client.get("/api/v1/availability")

    assert response.status_code == 422


def test_availability_naive_timestamp_returns_422():
    """Regression: a timezone-naive since/until → 422 (not a 500 from tz-aware compare in core)."""
    obs_repo = FakeObservationRepository()
    clock = FakeClock(_NOW)
    client = TestClient(_app(obs_repo, clock))

    naive_until = client.get(
        "/api/v1/availability?signal_key=checkout-http&until=2026-06-28T10:00:00"
    )
    assert naive_until.status_code == 422

    naive_since = client.get(
        "/api/v1/availability?signal_key=checkout-http&since=2026-06-28"
    )
    assert naive_since.status_code == 422


def test_availability_explicit_since_until_honored():
    """AC3: explicit since/until overrides the default 24h window."""
    since = datetime(2026, 6, 28, 8, 0, 0, tzinfo=timezone.utc)
    until = datetime(2026, 6, 28, 10, 0, 0, tzinfo=timezone.utc)
    # Observation inside the explicit window
    obs_inside = _obs(event_id="inside", observed_at=since + timedelta(hours=1))
    # Observation outside the explicit window (before since)
    obs_before = _obs(event_id="before", observed_at=since - timedelta(hours=1))

    obs_repo = FakeObservationRepository()
    obs_repo.save_new([obs_inside, obs_before])
    clock = FakeClock(_NOW)
    client = TestClient(_app(obs_repo, clock))

    # Use params dict so TestClient handles URL encoding (+ in timezone offset)
    response = client.get(
        "/api/v1/availability",
        params={
            "signal_key": "checkout-http",
            "since": since.isoformat(),
            "until": until.isoformat(),
        },
    )

    assert response.status_code == 200
    data = response.json()
    # Only one observation inside the explicit window → exactly 1 cycle observed
    assert data["total_verdicts"] == 1


def test_availability_interval_seconds_param_honored():
    """AC3 / stopgap: interval_seconds changes cycle bucketing."""
    since = datetime(2026, 6, 28, 10, 0, 0, tzinfo=timezone.utc)
    until = datetime(2026, 6, 28, 10, 5, 0, tzinfo=timezone.utc)  # 5-min window
    # Two observations, 2 min apart — with 60s interval they land in different cycles
    obs1 = _obs(event_id="e1", observed_at=since)
    obs2 = _obs(event_id="e2", observed_at=since + timedelta(minutes=2))

    obs_repo = FakeObservationRepository()
    obs_repo.save_new([obs1, obs2])
    clock = FakeClock(_NOW)
    client = TestClient(_app(obs_repo, clock))

    # 60-second intervals: 2 observations in 2 different cycles
    response = client.get(
        "/api/v1/availability",
        params={
            "signal_key": "checkout-http",
            "since": since.isoformat(),
            "until": until.isoformat(),
            "interval_seconds": 60,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_verdicts"] == 2


def test_availability_module_five_file_shape():
    """AC4: the availability feature follows the five-file convention exactly."""
    from pathlib import Path

    from src.api.v1 import availability

    pkg_dir = Path(availability.__file__).parent
    py_files = {p.name for p in pkg_dir.glob("*.py")}
    assert py_files == {
        "__init__.py",
        "controller.py",
        "models.py",
        "validation.py",
        "service.py",
    }
