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
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import timedelta

from src.adapters.inbound.dynatrace.adapter import DEFAULT_OVERLAP, fetch_observations
from src.adapters.inbound.dynatrace.query import Executor

# Optional orchestration types (imported lazily to keep the no-orchestration
# path decoupled; a static-analysis-friendly TYPE_CHECKING guard would work
# too but runtime isinstance checks are cleaner here).
from src.composition.config import Config
from src.core.domain import IngestResult
from src.core.ports import SignalIngestPort, WatermarkRepository
from src.core.ports.clock import ClockPort
from src.core.ports.component_repository import ComponentRepository
from src.core.ports.maintenance_repository import MaintenanceRepository
from src.core.ports.observation_repository import ObservationRepository
from src.core.services.decide import DecideAction, DecideService


def run_cycle(
    *,
    signal_key: str,
    native_id: str,
    watermark_repo: WatermarkRepository,
    ingest_port: SignalIngestPort,
    executor: Executor,
    overlap: timedelta = DEFAULT_OVERLAP,
    # Orchestration extras (dossier §8 step 5 — optional; all must be supplied
    # together or none at all; supplying some but not all is a programmer error
    # caught at runtime by the inner isinstance checks).
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
    batch = fetch_observations(
        signal_key=signal_key,
        native_id=native_id,
        watermark=watermark,
        executor=executor,
        overlap=overlap,
    )
    ingest_result = ingest_port.ingest_observations(batch)

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
    on_cycle: Callable[[IngestResult], Awaitable[None]] | None = None,
) -> None:
    """Drive `run_cycle` on a plain `asyncio` periodic loop.

    `while True: run_cycle(); await asyncio.sleep(interval)` is the whole
    shape (dossier §8: "... -> commit -> sleep"); `stop_event` lets a test (or
    a future graceful-shutdown hook) end the loop deterministically instead of
    running forever, and `on_cycle` is an optional hook invoked with each
    cycle's `IngestResult` (e.g. for tests to observe progress, or later for
    logging/metrics) — neither parameter carries domain logic, they only
    control the loop's own lifecycle.
    """
    while stop_event is None or not stop_event.is_set():
        result = run_cycle(
            signal_key=signal_key,
            native_id=native_id,
            watermark_repo=watermark_repo,
            ingest_port=ingest_port,
            executor=executor,
            overlap=overlap,
        )
        if on_cycle is not None:
            await on_cycle(result)
        # Re-check stop AFTER the cycle (and after on_cycle, which may request it):
        # the `while` guard only catches a stop set before a cycle starts. Without
        # this second check we would always sleep one more `interval_seconds` after a
        # stop requested mid-cycle, delaying shutdown by a full interval (STORY-023).
        if stop_event is not None and stop_event.is_set():
            break
        await asyncio.sleep(interval_seconds)
