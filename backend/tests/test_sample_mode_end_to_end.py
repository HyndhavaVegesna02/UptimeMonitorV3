"""End-to-end proof of the sample switch (STORY-048 T5, AC3/AC5 integration).

TEMPORARY feature — see docs/scrum/wiki/sample-mode.md for the REMOVAL
inventory; this whole file is deleted when sample-mode is removed.

This is the story's reason-to-exist regression: observations flow through
the REAL `IngestService` (dossier §8's validate/dedupe/persist/advance
ordering, exercised with in-memory fakes — no DB) wrapped by
`SampleModeIngest`. With the flag ON, the rows actually PERSISTED by the
real ingest chain are DOWN and carry the D5 marker; with the flag OFF, the
persisted rows match the vendor payload exactly (byte-identical, AC7b).
"""

from __future__ import annotations

from datetime import datetime, timezone

from src.composition.sample_mode import SIMULATED_RAW_REF, SampleModeIngest
from src.core.domain import Health, Provenance, SignalObservation
from src.core.ports.rejected_observation_repository import RejectedObservationRepository
from src.core.services.ingest_service import IngestService
from tests.fakes import (
    FakeClock,
    FakeObservationRepository,
    FakeSampleModeRepository,
    FakeWatermarkRepository,
)

_NOW = datetime(2026, 7, 3, 12, 0, 0, tzinfo=timezone.utc)


class _FakeRejectedObservationRepository(RejectedObservationRepository):
    """List-backed quarantine sink (mirrors test_ingest_service.py's local fake)."""

    def __init__(self) -> None:
        self.rejected: list[dict] = []

    def save(
        self,
        *,
        signal_key: str | None,
        reason: str,
        payload: dict,
        rejected_at: datetime,
    ) -> None:
        self.rejected.append(
            {
                "signal_key": signal_key,
                "reason": reason,
                "payload": payload,
                "rejected_at": rejected_at,
            }
        )


def _vendor_batch() -> list[SignalObservation]:
    return [
        SignalObservation(
            signal_key="checkout-http",
            observed_at=datetime(2026, 7, 3, 11, 59, 0, tzinfo=timezone.utc),
            health=Health.UP,
            source_event_id="evt-e2e-1",
            source=Provenance(
                system="dynatrace", native_id="HTTP_CHECK-1", native_kind="http"
            ),
            location="us-east-1",
            latency_ms=85,
        ),
        SignalObservation(
            signal_key="checkout-http",
            observed_at=datetime(2026, 7, 3, 11, 59, 30, tzinfo=timezone.utc),
            health=Health.UP,
            source_event_id="evt-e2e-2",
            source=Provenance(
                system="dynatrace", native_id="HTTP_CHECK-1", native_kind="http"
            ),
            location="us-east-1",
            latency_ms=92,
        ),
    ]


def _build_decorator(observation_repo, sample_mode_enabled: bool):
    real_ingest_service = IngestService(
        observation_repo=observation_repo,
        watermark_repo=FakeWatermarkRepository(),
        rejected_repo=_FakeRejectedObservationRepository(),
        clock=FakeClock(_NOW),
    )
    flag_repo = FakeSampleModeRepository()
    if sample_mode_enabled:
        flag_repo.set_enabled(True)
    return SampleModeIngest(delegate=real_ingest_service, sample_mode_repo=flag_repo)


def test_end_to_end_flag_on_persists_forced_down_marked_rows():
    """AC3/AC5: with the flag ON, rows actually PERSISTED by the real
    IngestService are health=DOWN and raw_ref=SIMULATED_RAW_REF."""
    observation_repo = FakeObservationRepository()
    decorator = _build_decorator(observation_repo, sample_mode_enabled=True)

    vendor_batch = _vendor_batch()
    result = decorator.ingest_observations(vendor_batch)

    assert result.accepted == 2
    assert len(observation_repo.saved) == 2
    for persisted in observation_repo.saved:
        assert persisted.health == Health.DOWN
        assert persisted.raw_ref == SIMULATED_RAW_REF
    # source_event_id/signal_key/observed_at survive unchanged — dedup and
    # watermarks behave identically regardless of the flag.
    persisted_event_ids = {p.source_event_id for p in observation_repo.saved}
    assert persisted_event_ids == {"evt-e2e-1", "evt-e2e-2"}


def test_end_to_end_flag_off_persists_rows_matching_vendor_payload():
    """AC7b: with the flag OFF, persisted rows match the vendor payload
    exactly — byte-identical to today's (pre-story) behavior."""
    observation_repo = FakeObservationRepository()
    decorator = _build_decorator(observation_repo, sample_mode_enabled=False)

    vendor_batch = _vendor_batch()
    result = decorator.ingest_observations(vendor_batch)

    assert result.accepted == 2
    assert len(observation_repo.saved) == 2
    for original, persisted in zip(vendor_batch, observation_repo.saved):
        assert persisted is original  # same instance — never copied when OFF
        assert persisted.health == Health.UP
        assert persisted.raw_ref is None
