"""The concrete `SignalIngestPort` (dossier §6, §8, §14 T1.3) — pure core.

`IngestService` is the front door's implementation: it owns the §8 ingest
ordering so every adapter that ever feeds the core (the Dynatrace poller now,
a push adapter later) inherits the same guarantees for free.

Ordering (dossier §8): **validate -> dedupe -> persist -> advance watermark
(accepted-only) -> [hand to pipeline: Zone 4, out of scope here] -> commit ->
sleep**. The last two steps (commit/sleep) belong to the composition-zone
pull loop; this service's responsibility ends at "advance the watermark only
after persistence has succeeded."

This module imports ONLY `src.core.*` (ports + domain) — no SQL, no vendor
types, no globals. The four ports are injected via the constructor so the
service is fully exercisable with in-memory fakes (no DB, no Dynatrace).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta

from src.core.domain import IngestResult, SignalObservation
from src.core.ports import (
    ClockPort,
    ObservationRepository,
    RejectedObservationRepository,
    SignalIngestPort,
    WatermarkRepository,
)

#: How far into the future an observation's `observed_at` may plausibly sit
#: relative to the injected clock before the validation gate quarantines it
#: (dossier §14 T1.3 — the "year-2099" guard). A few minutes of tolerance
#: absorbs clock skew between the source system and this process without
#: opening the door to a malformed timestamp leaping the watermark cursor.
FUTURE_TOLERANCE = timedelta(minutes=5)

#: Recorded as the rejection reason for an implausibly-future `observed_at`.
FUTURE_TIMESTAMP_REASON = "observed_at is implausibly in the future"


class MixedSignalBatchError(ValueError):
    """Raised when a batch spans more than one distinct `signal_key` (STORY-022).

    The §8 ordering's watermark-advance step assumes a batch is scoped to one
    signal per pull cycle (per `IngestService`'s docstring) — the only current
    producer, the Dynatrace adapter's `fetch_observations`, satisfies that
    assumption. Trusting it silently would mean a future mixed-signal batch
    (e.g. a push webhook batching several monitors) advances only the FIRST
    signal's watermark using `max(observed_at)` computed across OTHER
    signals' timestamps — over-advancing one cursor while freezing the rest.
    This error makes that programming error fail loud, up front, before any
    validation, persistence, or watermark work happens.
    """

    def __init__(self, signal_keys: Sequence[str]) -> None:
        self.signal_keys = sorted(set(signal_keys))
        super().__init__(
            "ingest_observations received a batch spanning more than one "
            f"signal_key: {self.signal_keys!r}"
        )


class IngestService(SignalIngestPort):
    """Validates, dedupes, persists a batch, and advances the watermark (dossier §8).

    Constructed with the four core ports the ordering depends on — no
    globals, no SQL. `signal_key` is taken from the observations themselves;
    a batch is assumed (per dossier §8) to be scoped to one signal per pull
    cycle, as the Dynatrace adapter's `fetch_observations` produces.
    """

    def __init__(
        self,
        *,
        observation_repo: ObservationRepository,
        watermark_repo: WatermarkRepository,
        rejected_repo: RejectedObservationRepository,
        clock: ClockPort,
    ) -> None:
        self._observation_repo = observation_repo
        self._watermark_repo = watermark_repo
        self._rejected_repo = rejected_repo
        self._clock = clock

    def ingest_observations(self, batch: Sequence[SignalObservation]) -> IngestResult:
        """Run the §8 ordering for one batch and return the accepted/rejected counts.

        Step order is significant for both AC1 and AC4:
        0. **Guard the whole batch up front** (STORY-022): if the batch spans
           more than one distinct `signal_key`, raise `MixedSignalBatchError`
           naming the offending keys BEFORE any validation, persistence, or
           watermark work — so a mixed-signal batch can never silently
           advance one signal's watermark using another's timestamps. An
           empty batch is unaffected (still a clean no-op, below).
        1. **Validate** every observation against the future-timestamp gate,
           quarantining failures to the rejected repo (reason + payload) —
           the rest of the batch proceeds (no poison pill).
        2. **Dedupe + persist** only the observations that passed validation,
           via `observation_repo.save_new` (idempotent insert — never a
           duplicate on replay; the returned count is the TRUE newly-inserted
           count).
        3. **Advance the watermark** to `max(observed_at)` over the
           VALIDATED observations only, and only after `save_new` has
           returned successfully — if it raises, the exception propagates
           and the watermark is left untouched, so a half-applied cycle can
           never leave the cursor ahead of what's actually persisted (AC4).
        """
        if not batch:
            return IngestResult(accepted=0, rejected=0)

        signal_keys = {observation.signal_key for observation in batch}
        if len(signal_keys) > 1:
            raise MixedSignalBatchError(signal_keys)

        now = self._clock.now()
        valid: list[SignalObservation] = []
        for observation in batch:
            if self._is_implausibly_future(observation.observed_at, now):
                self._rejected_repo.save(
                    signal_key=observation.signal_key,
                    reason=FUTURE_TIMESTAMP_REASON,
                    payload=observation.model_dump(mode="json"),
                    rejected_at=now,
                )
            else:
                valid.append(observation)

        rejected_count = len(batch) - len(valid)

        if not valid:
            return IngestResult(accepted=0, rejected=rejected_count)

        accepted_count = self._observation_repo.save_new(valid)

        watermark_target = max(observation.observed_at for observation in valid)
        signal_key = valid[0].signal_key
        self._watermark_repo.advance(signal_key, watermark_target)

        return IngestResult(accepted=accepted_count, rejected=rejected_count)

    def _is_implausibly_future(self, observed_at: datetime, now: datetime) -> bool:
        return observed_at > now + FUTURE_TOLERANCE
