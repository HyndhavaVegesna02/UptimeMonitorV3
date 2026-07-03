"""Tests for `SampleModeIngest` (dossier §6/§8, STORY-048 D4/D5, AC3/AC5).

TEMPORARY feature — see docs/scrum/wiki/sample-mode.md for the REMOVAL
inventory; this whole file is deleted when sample-mode is removed.

All fake-driven: a fake delegate captures whatever batch it receives, and a
fake flag repo drives OFF/ON. Covers:
  - OFF: the delegate receives the IDENTICAL batch objects (identity, not
    equality — AC7b byte-identical passthrough)
  - ON: the delegate receives copies with health=DOWN + raw_ref=
    SIMULATED_RAW_REF, all other fields unchanged
  - ON with an already-DOWN observation: still DOWN + marker (no double-flip
    weirdness)
  - empty batch passes through under both states
  - a sample-mode repo read failure propagates (never swallowed)
  - AC5 distinguishability: a simulated row (raw_ref set) vs a genuine DOWN
    (raw_ref is None) differ
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from src.composition.sample_mode import SIMULATED_RAW_REF, SampleModeIngest
from src.core.domain import Health, IngestResult, Provenance, SignalObservation
from src.core.ports import SignalIngestPort
from tests.fakes import FakeSampleModeRepository, FakeSignalIngestPort

_OBSERVED_AT = datetime(2026, 7, 3, 12, 0, 0, tzinfo=timezone.utc)


def _observation(health: Health = Health.UP, raw_ref: str | None = None):
    return SignalObservation(
        signal_key="checkout-http",
        observed_at=_OBSERVED_AT,
        health=health,
        source_event_id="evt-1",
        source=Provenance(system="dynatrace", native_id="N-1", native_kind="http"),
        location="us-east-1",
        latency_ms=120,
        raw_ref=raw_ref,
    )


def test_flag_off_delegate_receives_identical_batch_objects():
    """OFF: byte-identical passthrough — same instances, not just equal ones."""
    delegate = FakeSignalIngestPort()
    flag_repo = FakeSampleModeRepository()  # never set -> False
    decorator = SampleModeIngest(delegate=delegate, sample_mode_repo=flag_repo)

    obs = _observation()
    batch = [obs]

    decorator.ingest_observations(batch)

    assert len(delegate.received) == 1
    assert delegate.received[0] is obs  # identity, not equality


def test_flag_on_delegate_receives_forced_down_marked_copies():
    """ON: delegate gets copies with health=DOWN + raw_ref=SIMULATED_RAW_REF;
    every other field is unchanged."""
    delegate = FakeSignalIngestPort()
    flag_repo = FakeSampleModeRepository()
    flag_repo.set_enabled(True)
    decorator = SampleModeIngest(delegate=delegate, sample_mode_repo=flag_repo)

    obs = _observation(health=Health.UP)
    decorator.ingest_observations([obs])

    assert len(delegate.received) == 1
    forced = delegate.received[0]
    assert forced is not obs  # a copy, not the same instance
    assert forced.health == Health.DOWN
    assert forced.raw_ref == SIMULATED_RAW_REF
    assert forced.signal_key == obs.signal_key
    assert forced.observed_at == obs.observed_at
    assert forced.source_event_id == obs.source_event_id
    assert forced.source == obs.source
    assert forced.location == obs.location
    assert forced.latency_ms == obs.latency_ms


def test_flag_on_with_vendor_down_observation_stays_down_and_marked():
    """ON with an already-DOWN observation: still DOWN + marker, no
    double-flip weirdness."""
    delegate = FakeSignalIngestPort()
    flag_repo = FakeSampleModeRepository()
    flag_repo.set_enabled(True)
    decorator = SampleModeIngest(delegate=delegate, sample_mode_repo=flag_repo)

    obs = _observation(health=Health.DOWN)
    decorator.ingest_observations([obs])

    forced = delegate.received[0]
    assert forced.health == Health.DOWN
    assert forced.raw_ref == SIMULATED_RAW_REF


def test_empty_batch_passes_through_flag_off():
    delegate = FakeSignalIngestPort()
    flag_repo = FakeSampleModeRepository()
    decorator = SampleModeIngest(delegate=delegate, sample_mode_repo=flag_repo)

    result = decorator.ingest_observations([])

    assert delegate.received == []
    assert result == IngestResult(accepted=0, rejected=0)


def test_empty_batch_passes_through_flag_on():
    delegate = FakeSignalIngestPort()
    flag_repo = FakeSampleModeRepository()
    flag_repo.set_enabled(True)
    decorator = SampleModeIngest(delegate=delegate, sample_mode_repo=flag_repo)

    result = decorator.ingest_observations([])

    assert delegate.received == []
    assert result == IngestResult(accepted=0, rejected=0)


def test_repo_read_failure_propagates():
    """A sample-mode repo read failure is never swallowed — it propagates,
    consistent with the loop's existing cycle-failure handling (the cycle
    already depends on the same DB)."""

    class RaisingSampleModeRepo:
        def is_enabled(self) -> bool:
            raise RuntimeError("db unavailable")

        def set_enabled(self, enabled: bool) -> None:
            raise NotImplementedError

    delegate = FakeSignalIngestPort()
    decorator = SampleModeIngest(
        delegate=delegate, sample_mode_repo=RaisingSampleModeRepo()
    )

    with pytest.raises(RuntimeError, match="db unavailable"):
        decorator.ingest_observations([_observation()])

    assert delegate.received == []  # never reached the delegate


def test_simulated_row_distinguishable_from_genuine_down():
    """AC5: with the flag ON, the persisted row is DOWN + raw_ref marked; a
    genuine DOWN (flag OFF, vendor reports down) has raw_ref is None — the
    two are distinguishable."""
    delegate = FakeSignalIngestPort()

    # Genuine DOWN, flag OFF.
    off_repo = FakeSampleModeRepository()
    off_decorator = SampleModeIngest(delegate=delegate, sample_mode_repo=off_repo)
    genuine = _observation(health=Health.DOWN)
    off_decorator.ingest_observations([genuine])

    # Simulated DOWN, flag ON.
    on_repo = FakeSampleModeRepository()
    on_repo.set_enabled(True)
    on_decorator = SampleModeIngest(delegate=delegate, sample_mode_repo=on_repo)
    on_decorator.ingest_observations([_observation(health=Health.UP)])

    genuine_received, simulated_received = delegate.received
    assert genuine_received.health == Health.DOWN
    assert genuine_received.raw_ref is None
    assert simulated_received.health == Health.DOWN
    assert simulated_received.raw_ref == SIMULATED_RAW_REF
    assert genuine_received.raw_ref != simulated_received.raw_ref


def test_decorator_is_a_signal_ingest_port():
    """SampleModeIngest satisfies the SignalIngestPort ABC (dossier §6)."""
    delegate = FakeSignalIngestPort()
    flag_repo = FakeSampleModeRepository()
    decorator = SampleModeIngest(delegate=delegate, sample_mode_repo=flag_repo)
    assert isinstance(decorator, SignalIngestPort)
