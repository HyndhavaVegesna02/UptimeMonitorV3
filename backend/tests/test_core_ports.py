"""STORY-005: the core's owned port interfaces (dossier §6, §8).

Zone 1 / pure core. Ports are ABCs the core OWNS but does not implement. Each
test proves two things: the ABC cannot be instantiated directly (it is abstract),
and the in-memory fake under `tests/fakes.py` satisfies the interface and behaves.
No Dynatrace, Statuspage, Neon, DB, or network anywhere here.
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.core.domain import (
    ComponentStatus,
    Health,
    IngestResult,
    Provenance,
    SignalObservation,
    StatusChange,
)
from src.core.ports import (
    ClockPort,
    ObservationRepository,
    SignalIngestPort,
    StatusPublisherPort,
    WatermarkRepository,
)


def _observation(signal_key: str = "checkout-http", event_id: str = "evt-1"):
    """A valid canonical observation for exercising the persistence/ingest fakes."""
    return SignalObservation(
        signal_key=signal_key,
        observed_at=datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc),
        health=Health.UP,
        source_event_id=event_id,
        source=Provenance(system="dynatrace", native_id="X-1", native_kind="http"),
        location="us-east",
    )


# --- ClockPort (AC1, AC3) -------------------------------------------------------


def test_clock_port_is_abstract_and_cannot_be_instantiated():
    with pytest.raises(TypeError):
        ClockPort()  # type: ignore[abstract]


def test_fake_clock_returns_injected_fixed_tz_aware_utc_time():
    from fakes import FakeClock

    fixed = datetime(2026, 6, 24, 9, 30, 0, tzinfo=timezone.utc)
    clock = FakeClock(fixed)

    now = clock.now()
    assert now == fixed
    assert now.tzinfo is not None  # tz-aware
    assert now.utcoffset() == timedelta(0)  # UTC
    assert clock.now() == fixed  # frozen: stable across calls


# --- WatermarkRepository (AC1, AC4) ---------------------------------------------


def test_watermark_repository_is_abstract_and_cannot_be_instantiated():
    with pytest.raises(TypeError):
        WatermarkRepository()  # type: ignore[abstract]


def test_fake_watermark_get_returns_none_when_unset():
    from fakes import FakeWatermarkRepository

    repo = FakeWatermarkRepository()
    assert repo.get("checkout-http") is None


def test_fake_watermark_advance_then_get_round_trips():
    from fakes import FakeWatermarkRepository

    repo = FakeWatermarkRepository()
    mark = datetime(2026, 6, 24, 10, 5, 0, tzinfo=timezone.utc)

    repo.advance("checkout-http", mark)

    assert repo.get("checkout-http") == mark
    # A watermark is per-signal: advancing one leaves others unset.
    assert repo.get("login-http") is None


# --- ObservationRepository (AC1) ------------------------------------------------


def test_observation_repository_is_abstract_and_cannot_be_instantiated():
    with pytest.raises(TypeError):
        ObservationRepository()  # type: ignore[abstract]


def test_fake_observation_repository_save_new_returns_insert_count():
    from fakes import FakeObservationRepository

    repo = FakeObservationRepository()
    batch = [_observation(event_id="evt-1"), _observation(event_id="evt-2")]

    inserted = repo.save_new(batch)

    assert inserted == 2
    assert repo.saved == batch


def test_fake_observation_repository_save_new_of_empty_batch_is_zero():
    from fakes import FakeObservationRepository

    repo = FakeObservationRepository()
    assert repo.save_new([]) == 0


# --- StatusPublisherPort (AC1) --------------------------------------------------


def test_status_publisher_port_is_abstract_and_cannot_be_instantiated():
    with pytest.raises(TypeError):
        StatusPublisherPort()  # type: ignore[abstract]


def test_recording_status_publisher_records_each_canonical_change():
    from fakes import RecordingStatusPublisher

    publisher = RecordingStatusPublisher()
    change = StatusChange(
        component_id="checkout", status=ComponentStatus.MAJOR_OUTAGE
    )

    result = publisher.publish(change)

    assert result is None  # publish returns None by contract
    assert publisher.published == [change]


# --- SignalIngestPort (AC1) -----------------------------------------------------


def test_signal_ingest_port_is_abstract_and_cannot_be_instantiated():
    with pytest.raises(TypeError):
        SignalIngestPort()  # type: ignore[abstract]


def test_fake_signal_ingest_returns_ingest_result_over_canonical_batch():
    from fakes import FakeSignalIngestPort

    port = FakeSignalIngestPort()
    batch = [_observation(event_id="evt-1"), _observation(event_id="evt-2")]

    result = port.ingest_observations(batch)

    assert isinstance(result, IngestResult)
    assert result.accepted == 2
    assert result.rejected == 0
    assert port.received == batch
