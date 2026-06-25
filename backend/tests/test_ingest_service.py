"""STORY-009: the core ingest service — the concrete `SignalIngestPort`.

Pure core, tested with IN-MEMORY FAKE repositories only (no DB, no Dynatrace —
working agreement). Exercises the dossier §8 ordering: validate -> dedupe ->
persist -> advance watermark (accepted-only) -> commit -> sleep (sleep/commit
are the pull loop's concern, out of scope here; this module proves the
ordering up to "advance watermark").

Fakes are local to this module (not `tests/fakes.py`, which is STORY-005
substrate): `FakeObservationRepository` here honors `source_event_id` dedupe
(STORY-005's fake does not, since that story only had to prove the interface
shape), which this story's AC3 needs.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta, timezone

import pytest

from src.core.domain import Health, IngestResult, Provenance, SignalObservation
from src.core.ports import (
    ClockPort,
    ObservationRepository,
    RejectedObservationRepository,
    WatermarkRepository,
)


def _observation(
    signal_key: str = "checkout-http",
    event_id: str = "evt-1",
    observed_at: datetime | None = None,
    health: Health = Health.UP,
) -> SignalObservation:
    return SignalObservation(
        signal_key=signal_key,
        observed_at=observed_at or datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc),
        health=health,
        source_event_id=event_id,
        source=Provenance(system="dynatrace", native_id="X-1", native_kind="http"),
        location="us-east",
    )


# --- local in-memory fakes ---------------------------------------------------


class DedupingObservationRepository(ObservationRepository):
    """List-backed observation repo honoring `source_event_id` dedupe.

    Mirrors the real `PostgresObservationRepository`'s `ON CONFLICT DO
    NOTHING` semantics in memory: `save_new` returns only the count of rows
    NEWLY inserted, and re-saving an already-seen `source_event_id` is a
    no-op (AC3).
    """

    def __init__(self) -> None:
        self.saved: list[SignalObservation] = []
        self._seen_event_ids: set[str] = set()
        self.save_new_calls: list[list[SignalObservation]] = []
        self.raise_on_save: Exception | None = None

    def save_new(self, batch: Sequence[SignalObservation]) -> int:
        self.save_new_calls.append(list(batch))
        if self.raise_on_save is not None:
            raise self.raise_on_save
        inserted = 0
        for observation in batch:
            if observation.source_event_id in self._seen_event_ids:
                continue
            self._seen_event_ids.add(observation.source_event_id)
            self.saved.append(observation)
            inserted += 1
        return inserted


class FakeWatermarkRepository(WatermarkRepository):
    """Dict-backed per-signal watermark; records every `advance` call."""

    def __init__(self) -> None:
        self._marks: dict[str, datetime] = {}
        self.advance_calls: list[tuple[str, datetime]] = []

    def get(self, signal_key: str) -> datetime | None:
        return self._marks.get(signal_key)

    def advance(self, signal_key: str, to: datetime) -> None:
        self.advance_calls.append((signal_key, to))
        self._marks[signal_key] = to


class FakeRejectedObservationRepository(RejectedObservationRepository):
    """List-backed quarantine sink."""

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


class FakeClock(ClockPort):
    """A clock frozen at an injected instant."""

    def __init__(self, fixed: datetime) -> None:
        self._fixed = fixed

    def now(self) -> datetime:
        return self._fixed


_NOW = datetime(2026, 6, 24, 12, 0, 0, tzinfo=timezone.utc)


def _make_service(
    observation_repo: ObservationRepository | None = None,
    watermark_repo: WatermarkRepository | None = None,
    rejected_repo: RejectedObservationRepository | None = None,
    clock: ClockPort | None = None,
):
    from src.core.services.ingest_service import IngestService

    return IngestService(
        observation_repo=observation_repo or DedupingObservationRepository(),
        watermark_repo=watermark_repo or FakeWatermarkRepository(),
        rejected_repo=rejected_repo or FakeRejectedObservationRepository(),
        clock=clock or FakeClock(_NOW),
    )


# --- Step 1: the service IS-A SignalIngestPort ------------------------------


def test_ingest_service_is_a_signal_ingest_port():
    from src.core.ports import SignalIngestPort
    from src.core.services.ingest_service import IngestService

    assert issubclass(IngestService, SignalIngestPort)


# --- Step 2: happy path — all valid -> save_new -> advance watermark --------


def test_all_valid_batch_is_accepted_and_advances_watermark_to_max_observed_at():
    observation_repo = DedupingObservationRepository()
    watermark_repo = FakeWatermarkRepository()
    service = _make_service(observation_repo=observation_repo, watermark_repo=watermark_repo)

    earlier = datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc)
    later = datetime(2026, 6, 24, 11, 0, 0, tzinfo=timezone.utc)
    batch = [
        _observation(event_id="evt-1", observed_at=earlier),
        _observation(event_id="evt-2", observed_at=later),
    ]

    result = service.ingest_observations(batch)

    assert isinstance(result, IngestResult)
    assert result.accepted == 2
    assert result.rejected == 0
    assert {o.source_event_id for o in observation_repo.saved} == {"evt-1", "evt-2"}
    assert watermark_repo.get("checkout-http") == later


def test_empty_batch_is_a_no_op():
    observation_repo = DedupingObservationRepository()
    watermark_repo = FakeWatermarkRepository()
    service = _make_service(observation_repo=observation_repo, watermark_repo=watermark_repo)

    result = service.ingest_observations([])

    assert result == IngestResult(accepted=0, rejected=0)
    assert observation_repo.saved == []
    assert watermark_repo.advance_calls == []


# --- Step 3: validation gate quarantines a future-timestamp observation (AC1) --


def test_implausibly_future_observation_is_quarantined_not_passed_to_save_new():
    """The 'year-2099' case: an observation far in the future relative to the
    injected clock is rejected, recorded with a reason + payload, and excluded
    from what reaches `save_new` — while the rest of the batch still proceeds
    (no poison pill).
    """
    observation_repo = DedupingObservationRepository()
    rejected_repo = FakeRejectedObservationRepository()
    clock = FakeClock(_NOW)
    service = _make_service(
        observation_repo=observation_repo, rejected_repo=rejected_repo, clock=clock
    )

    good = _observation(event_id="evt-good", observed_at=_NOW)
    future = _observation(
        event_id="evt-future",
        observed_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
    )
    batch = [good, future]

    result = service.ingest_observations(batch)

    assert result.accepted == 1
    assert result.rejected == 1
    assert [o.source_event_id for o in observation_repo.saved] == ["evt-good"]
    # The future observation never reached save_new at all.
    saved_event_ids = {
        o.source_event_id for call in observation_repo.save_new_calls for o in call
    }
    assert "evt-future" not in saved_event_ids

    assert len(rejected_repo.rejected) == 1
    rejection = rejected_repo.rejected[0]
    assert rejection["signal_key"] == "checkout-http"
    assert rejection["reason"]  # non-empty reason recorded
    assert rejection["payload"]["source_event_id"] == "evt-future"
    assert rejection["rejected_at"] == _NOW


def test_validate_happens_before_dedupe_so_a_bad_row_is_rejected_not_deduped():
    """Order matters: validate THEN dedupe. A future-timestamp row that
    duplicates an event id already 'seen' must still surface as a rejection,
    not silently vanish via dedupe.
    """
    observation_repo = DedupingObservationRepository()
    rejected_repo = FakeRejectedObservationRepository()
    service = _make_service(observation_repo=observation_repo, rejected_repo=rejected_repo)

    future = _observation(
        event_id="evt-dup-future",
        observed_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
    )

    result = service.ingest_observations([future, future])

    # Both copies are individually validated before any dedupe step runs;
    # both are rejected (validation gate doesn't dedupe rejects either way).
    assert result.accepted == 0
    assert result.rejected == 2
    assert observation_repo.saved == []


# --- Step 4: accepted-only watermark advance (AC2) ---------------------------


def test_future_timestamp_reject_cannot_leap_the_watermark_cursor():
    watermark_repo = FakeWatermarkRepository()
    service = _make_service(watermark_repo=watermark_repo)

    accepted_at = datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc)
    good = _observation(event_id="evt-good", observed_at=accepted_at)
    future = _observation(
        event_id="evt-future",
        observed_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
    )

    service.ingest_observations([good, future])

    # The watermark advances to the accepted max, NOT the year-2099 reject.
    assert watermark_repo.get("checkout-http") == accepted_at


def test_watermark_does_not_advance_when_everything_is_rejected():
    watermark_repo = FakeWatermarkRepository()
    service = _make_service(watermark_repo=watermark_repo)

    future = _observation(
        event_id="evt-future",
        observed_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
    )

    result = service.ingest_observations([future])

    assert result.accepted == 0
    assert result.rejected == 1
    assert watermark_repo.get("checkout-http") is None
    assert watermark_repo.advance_calls == []


# --- Step 5: dedupe -> true newly-inserted count (AC3) -----------------------


def test_duplicate_source_event_id_within_batch_is_a_no_op_for_the_dup():
    observation_repo = DedupingObservationRepository()
    service = _make_service(observation_repo=observation_repo)

    obs = _observation(event_id="evt-1")

    result = service.ingest_observations([obs])
    assert result.accepted == 1

    # Re-ingesting the very same observation a second time: dedupe makes it a no-op.
    result2 = service.ingest_observations([obs])
    assert result2.accepted == 0
    assert result2.rejected == 0
    assert len(observation_repo.saved) == 1


def test_mixed_batch_accepted_count_reflects_true_newly_inserted_not_len_valid():
    observation_repo = DedupingObservationRepository()
    service = _make_service(observation_repo=observation_repo)

    first = _observation(event_id="evt-1")
    service.ingest_observations([first])

    duplicate = _observation(event_id="evt-1")
    new_one = _observation(event_id="evt-2")
    result = service.ingest_observations([duplicate, new_one])

    # len(valid) would be 2; the TRUE newly-inserted count (from save_new) is 1.
    assert result.accepted == 1
    assert result.rejected == 0


# --- Step 6: commit-before-advance ordering + idempotent replay (AC4) -------


def test_watermark_is_not_advanced_when_save_new_raises():
    observation_repo = DedupingObservationRepository()
    observation_repo.raise_on_save = RuntimeError("simulated persist failure")
    watermark_repo = FakeWatermarkRepository()
    service = _make_service(observation_repo=observation_repo, watermark_repo=watermark_repo)

    batch = [_observation(event_id="evt-1")]

    with pytest.raises(RuntimeError):
        service.ingest_observations(batch)

    assert watermark_repo.advance_calls == []
    assert watermark_repo.get("checkout-http") is None


def test_idempotent_replay_after_crash_loses_nothing_and_double_counts_nothing():
    """Simulates AC4's crash-mid-loop scenario at the service level: a batch
    is ingested once (the 'crash' would happen after this, before the pull
    loop advances to the next cycle), then the SAME batch (overlap window) is
    replayed. The replay must insert 0 new rows and must not move the
    watermark backward or double-advance it.
    """
    observation_repo = DedupingObservationRepository()
    watermark_repo = FakeWatermarkRepository()
    service = _make_service(observation_repo=observation_repo, watermark_repo=watermark_repo)

    t1 = datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 6, 24, 10, 5, 0, tzinfo=timezone.utc)
    batch = [
        _observation(event_id="evt-1", observed_at=t1),
        _observation(event_id="evt-2", observed_at=t2),
    ]

    first_result = service.ingest_observations(batch)
    assert first_result.accepted == 2
    assert watermark_repo.get("checkout-http") == t2

    # Replay the identical batch (as overlap-on-read would re-fetch it).
    second_result = service.ingest_observations(batch)

    assert second_result.accepted == 0  # no double-count
    assert second_result.rejected == 0
    assert len(observation_repo.saved) == 2  # no loss, no duplication
    assert watermark_repo.get("checkout-http") == t2  # unchanged, not regressed
