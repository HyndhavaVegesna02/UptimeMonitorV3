"""The asyncio pull loop (dossier §8, AC5) — composition zone.

A plain `asyncio` periodic task: no APScheduler, no new scheduling
dependency. The loop holds NO domain logic — it only wires together three
calls per cycle, per signal:

    watermark_repo.get(signal_key)
        -> dynatrace.fetch_observations(watermark=..., overlap=...)
        -> ingest_port.ingest_observations(batch)

`run_cycle` is the single-cycle coroutine-free function (synchronous, since
none of the three calls it makes are themselves async in this codebase);
`run_periodic` is the thin asyncio driver that calls it on an interval. Both
import from `src.core` (the ingest port + ports) and `src.adapters` (the
Dynatrace adapter) — composition is the one zone allowed to import both
sides of the boundary (dossier §4).
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import timedelta

from src.adapters.inbound.dynatrace.adapter import DEFAULT_OVERLAP, fetch_observations
from src.adapters.inbound.dynatrace.query import Executor
from src.core.domain import IngestResult
from src.core.ports import SignalIngestPort, WatermarkRepository


def run_cycle(
    *,
    signal_key: str,
    native_id: str,
    watermark_repo: WatermarkRepository,
    ingest_port: SignalIngestPort,
    executor: Executor,
    overlap: timedelta = DEFAULT_OVERLAP,
) -> IngestResult:
    """Run exactly one pull cycle for one signal and return its `IngestResult`.

    Reads the current watermark, asks the Dynatrace adapter for everything
    newer (with overlap), and hands the resulting batch to the ingest port.
    The ingest port (`IngestService`, core/services) owns validation, dedupe,
    persistence, and the watermark advance (dossier §8) — this function
    contains no business logic of its own, only the wiring.
    """
    watermark = watermark_repo.get(signal_key)
    batch = fetch_observations(
        signal_key=signal_key,
        native_id=native_id,
        watermark=watermark,
        executor=executor,
        overlap=overlap,
    )
    return ingest_port.ingest_observations(batch)


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
