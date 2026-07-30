"""The asyncio pull loop (dossier §8, AC5) — composition zone.

A plain `asyncio` periodic task: no APScheduler, no new scheduling
dependency. The loop holds NO domain logic — it only wires together three
calls per cycle, per signal:

    watermark_repo.get(signal_key)
        -> dynatrace.fetch_observations(watermark=..., overlap=...)
        -> ingest_port.ingest_observations(batch)
        [-> orchestrate_signal(...)]   # dossier §8 step 5, optional

`run_cycle` is the single-cycle coroutine-free function (synchronous, since
none of the three calls it makes are themselves async in this codebase);
`run_periodic` is the thin asyncio driver that calls it on an interval. Both
import from `src.core` (the ingest port + ports) and `src.adapters` (the
Dynatrace adapter) — composition is the one zone allowed to import both
sides of the boundary (dossier §4).

STORY-016a (Sprint 17): when orchestration parameters are supplied,
``run_cycle`` calls ``orchestrate_signal`` after ingest (dossier §8 step 5
"hand rows to the pipeline") and returns ``(IngestResult, DecideAction)``.
Without them it returns only the ``IngestResult`` (backward-compatible).

STORY-050 (Sprint 36, dossier §8): a pull-based monitor loop must ride out
transient per-cycle vendor/network errors (e.g. a Grail HTTP timeout) rather
than let one exception kill the whole process. ``run_periodic`` catches
``Exception`` (never ``BaseException`` -- ``KeyboardInterrupt``/``SystemExit``/
``asyncio.CancelledError`` must still propagate and stop the loop) around
each ``run_cycle`` call, logs it at ERROR with the signal_key + the
per-signal consecutive-failure count, and moves straight on to the next
scheduled cycle. This is LOG-ONLY (PO decision, AC3): the loop never exits
on a cycle failure, however many times in a row it happens. Startup
failures (missing secrets, bad config) are unaffected -- they run in
``composition/run.py::main`` BEFORE any ``run_periodic`` call and still
fail fast (AC2).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import timedelta

from src.adapters.inbound.dynatrace.adapter import DEFAULT_OVERLAP, fetch_observations
from src.adapters.inbound.dynatrace.query import Executor
from src.adapters.system_clock import SystemClock

# Optional orchestration types. `orchestrate_signal` itself is imported lazily
# (inside run_cycle) to keep the no-orchestration path decoupled.
from src.composition.config import Config
from src.core.domain import IngestResult
from src.core.ports import (
    RejectedObservationRepository,
    SignalIngestPort,
    WatermarkRepository,
)
from src.core.ports.clock import ClockPort
from src.core.ports.component_repository import ComponentRepository
from src.core.ports.maintenance_repository import MaintenanceRepository
from src.core.ports.observation_repository import ObservationRepository
from src.core.services.decide import DecideAction, DecideService

logger = logging.getLogger(__name__)


def run_cycle(
    *,
    signal_key: str,
    native_id: str,
    watermark_repo: WatermarkRepository,
    ingest_port: SignalIngestPort,
    executor: Executor,
    overlap: timedelta = DEFAULT_OVERLAP,
    rejected_repo: RejectedObservationRepository | None = None,
    # Orchestration extras (dossier §8 step 5 — optional). The guard below is
    # `all(... is not None)`: supply ALL six to orchestrate after ingest, or
    # none to keep the original ingest-only shape. Supplying SOME-but-not-all
    # silently falls through to the ingest-only path (a known limitation; the
    # async production driver `run_periodic` does not yet thread these — that
    # wiring is deferred to the deployment/live story).
    config: Config | None = None,
    observation_repo: ObservationRepository | None = None,
    maintenance_repo: MaintenanceRepository | None = None,
    component_repo: ComponentRepository | None = None,
    decide_service: DecideService | None = None,
    clock: ClockPort | None = None,
) -> IngestResult | tuple[IngestResult, DecideAction]:
    """Run exactly one pull cycle for one signal and return its result.

    **Without orchestration** (the original STORY-009 shape): returns
    ``IngestResult``. Backward-compatible; all existing ``test_pull_loop.py``
    tests use this path.

    **With orchestration** (STORY-016a, dossier §8 step 5): when ALL six
    orchestration extras are supplied, calls ``orchestrate_signal`` after
    ingest and returns ``(IngestResult, DecideAction)``. The action is the
    result of ``collapse→streak→anti_flap→decide`` — no domain logic lives
    here, only wiring.

    Reads the current watermark, asks the Dynatrace adapter for everything
    newer (with overlap), hands the resulting batch to the ingest port.
    The ingest port (``IngestService``, core/services) owns validation,
    dedupe, persistence, and the watermark advance (dossier §8) — this
    function contains no business logic of its own, only the wiring.
    """
    watermark = watermark_repo.get(signal_key)
    outcome = fetch_observations(
        signal_key=signal_key,
        native_id=native_id,
        watermark=watermark,
        executor=executor,
        overlap=overlap,
    )
    if outcome.failures:
        # `clock` is one of the six OPTIONAL orchestration extras, so the
        # ingest-only call shape can arrive without one. Fall back to the
        # injectable `SystemClock` adapter rather than reading the wall clock
        # directly here: `datetime.now(...)` inline would make `rejected_at`
        # untestable and would be the ONLY direct wall-clock read anywhere in
        # `backend/src/` outside `adapters/system_clock.py` — the project
        # injects `ClockPort` everywhere precisely so time is deterministic.
        # composition is allowed to import adapters (dossier §4).
        quarantine_clock = clock if clock is not None else SystemClock()
        rejected_at = quarantine_clock.now()
        for failure in outcome.failures:
            logger.warning(
                "Quarantining row for signal_key=%r: %s",
                signal_key,
                failure.reason,
            )
            if rejected_repo is not None:
                rejected_repo.save(
                    signal_key=signal_key,
                    reason=failure.reason,
                    payload=failure.row,
                    rejected_at=rejected_at,
                )

    ingest_result = ingest_port.ingest_observations(outcome.observations)

    # Orchestration step (dossier §8 step 5 — only when all six extras supplied)
    orch_params = (
        config,
        observation_repo,
        maintenance_repo,
        component_repo,
        decide_service,
        clock,
    )
    if all(p is not None for p in orch_params):
        from src.composition.orchestrate import orchestrate_signal

        action = orchestrate_signal(
            signal_key=signal_key,
            config=config,  # type: ignore[arg-type]
            observation_repo=observation_repo,  # type: ignore[arg-type]
            maintenance_repo=maintenance_repo,  # type: ignore[arg-type]
            component_repo=component_repo,  # type: ignore[arg-type]
            decide_service=decide_service,  # type: ignore[arg-type]
            clock=clock,  # type: ignore[arg-type]
        )
        return ingest_result, action

    return ingest_result


async def run_periodic(
    *,
    signal_key: str,
    native_id: str,
    watermark_repo: WatermarkRepository,
    ingest_port: SignalIngestPort,
    executor: Executor,
    interval_seconds: float,
    overlap: timedelta = DEFAULT_OVERLAP,
    stop_event: asyncio.Event | None = None,
    on_cycle: Callable[
        [IngestResult | tuple[IngestResult, DecideAction]], Awaitable[None]
    ]
    | None = None,
    rejected_repo: RejectedObservationRepository | None = None,
    config: Config | None = None,
    observation_repo: ObservationRepository | None = None,
    maintenance_repo: MaintenanceRepository | None = None,
    component_repo: ComponentRepository | None = None,
    decide_service: DecideService | None = None,
    clock: ClockPort | None = None,
) -> None:
    """Drive `run_cycle` on a plain `asyncio` periodic loop (dossier §8).

    `while True: run_cycle(); await asyncio.sleep(interval)` is the whole
    shape (dossier §8: "... -> commit -> sleep"); `stop_event` lets a test (or
    a future graceful-shutdown hook) end the loop deterministically instead of
    running forever, and `on_cycle` is an optional hook invoked with each
    cycle's result (e.g. for tests to observe progress, or later for
    logging/metrics).

    STORY-050 (dossier §8): a cycle that raises is SURVIVED, not fatal. Each
    `run_periodic` instance owns one signal and one consecutive-failure
    counter for it: a raised `Exception` is caught, logged at ERROR with the
    signal_key + the cause + the running consecutive-failure count for THIS
    signal, and the loop proceeds straight to the next scheduled cycle
    (LOG-ONLY, AC3 -- never crashes, however many failures in a row). A
    success resets the counter to zero. `on_cycle` is skipped on a failed
    cycle (there is no result to hand it). `Exception`, not `BaseException`,
    is caught deliberately: `KeyboardInterrupt`/`SystemExit`/
    `asyncio.CancelledError` are all `BaseException` subclasses (in Python
    3.13, `CancelledError` included), so a bare `except Exception` already
    lets cancellation propagate and stop the loop untouched. The post-cycle
    `stop_event` re-check (STORY-023) runs whether the cycle succeeded or
    failed, so a stop requested during a failing cycle still takes effect
    immediately instead of waiting another `interval_seconds`.
    """
    consecutive_failures = 0
    while stop_event is None or not stop_event.is_set():
        try:
            result = run_cycle(
                signal_key=signal_key,
                native_id=native_id,
                watermark_repo=watermark_repo,
                ingest_port=ingest_port,
                executor=executor,
                overlap=overlap,
                rejected_repo=rejected_repo,
                config=config,
                observation_repo=observation_repo,
                maintenance_repo=maintenance_repo,
                component_repo=component_repo,
                decide_service=decide_service,
                clock=clock,
            )

        except Exception as exc:
            consecutive_failures += 1
            logger.exception(
                "Cycle failed for signal_key=%r (consecutive_failures=%d): %s",
                signal_key,
                consecutive_failures,
                exc,
            )
        else:
            consecutive_failures = 0
            if on_cycle is not None:
                await on_cycle(result)
        # Re-check stop AFTER the cycle (whether it succeeded or failed) --
        # the `while` guard only catches a stop set before a cycle starts. Without
        # this second check we would always sleep one more `interval_seconds` after a
        # stop requested mid-cycle, delaying shutdown by a full interval (STORY-023;
        # STORY-050 extends the same guarantee to a FAILED cycle).
        if stop_event is not None and stop_event.is_set():
            break
        await asyncio.sleep(interval_seconds)
