"""STORY-009: the asyncio pull loop (composition zone, dossier §8, AC5).

The loop is plain `asyncio` (no APScheduler, no new dependency) and holds NO
domain logic: it only reads the watermark, asks the Dynatrace adapter for
everything newer (with overlap), and hands the batch to the ingest port. This
module proves that wiring with a fake `Executor` (never live Dynatrace) and a
fake `SignalIngestPort` (never a live DB) — both substrates already used by
STORY-008/STORY-005's own test suites.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from datetime import datetime, timezone

from src.core.domain import Health, IngestResult, SignalObservation
from src.core.ports import SignalIngestPort, WatermarkRepository


class FakeWatermarkRepository(WatermarkRepository):
    def __init__(self, initial: dict[str, datetime] | None = None) -> None:
        self._marks: dict[str, datetime] = dict(initial or {})
        self.get_calls: list[str] = []

    def get(self, signal_key: str) -> datetime | None:
        self.get_calls.append(signal_key)
        return self._marks.get(signal_key)

    def advance(self, signal_key: str, to: datetime) -> None:
        self._marks[signal_key] = to


class RecordingIngestPort(SignalIngestPort):
    """Records every batch handed to it; returns a canned IngestResult."""

    def __init__(self) -> None:
        self.batches: list[Sequence[SignalObservation]] = []

    def ingest_observations(self, batch: Sequence[SignalObservation]) -> IngestResult:
        self.batches.append(batch)
        return IngestResult(accepted=len(batch), rejected=0)


def _row(event_id: str, ts: str, outcome: str = "success") -> dict:
    return {
        "timestamp": ts,
        "event.id": event_id,
        "synthetic_test.id": "HTTP_CHECK-9F2A",
        "synthetic_test.type": "HTTP_CHECK",
        "synthetic_location.name": "us-east-1",
        "execution.outcome": outcome,
        "request.response_time_ms": 100,
    }


def test_single_cycle_reads_watermark_fetches_and_ingests_without_domain_logic():
    """One cycle: watermark.get -> dynatrace.fetch_observations (via the
    injected fake Executor) -> ingest_port.ingest_observations. The loop
    itself must not branch on observation content -- it only wires the three
    calls together.
    """
    from src.composition.pull_loop import run_cycle

    watermark_repo = FakeWatermarkRepository(
        {"checkout-http": None}.get("checkout-http")
    )
    ingest_port = RecordingIngestPort()

    captured_queries: list[str] = []

    def fake_executor(query: str) -> list[dict]:
        captured_queries.append(query)
        return [_row("evt-1", "2026-06-24T10:00:00Z")]

    result = run_cycle(
        signal_key="checkout-http",
        native_id="HTTP_CHECK-9F2A",
        watermark_repo=watermark_repo,
        ingest_port=ingest_port,
        executor=fake_executor,
    )

    assert isinstance(result, IngestResult)
    assert result.accepted == 1
    assert watermark_repo.get_calls == ["checkout-http"]
    assert len(captured_queries) == 1
    assert "HTTP_CHECK-9F2A" in captured_queries[0]

    assert len(ingest_port.batches) == 1
    (batch,) = ingest_port.batches
    assert len(batch) == 1
    assert batch[0].source_event_id == "evt-1"
    assert batch[0].signal_key == "checkout-http"


def test_single_cycle_uses_existing_watermark_with_overlap():
    """When a watermark already exists, fetch_observations must be asked with
    that watermark (the overlap window is the adapter's concern, already
    proven by STORY-008's own tests) -- the loop just passes it through.
    """
    from src.composition.pull_loop import run_cycle

    existing = datetime(2026, 6, 24, 9, 0, 0, tzinfo=timezone.utc)
    watermark_repo = FakeWatermarkRepository({"checkout-http": existing})
    ingest_port = RecordingIngestPort()

    def fake_executor(query: str) -> list[dict]:
        # The overlap window means the query's lower bound is < watermark.
        assert "2026-06-24T08:55:00Z" in query  # existing - DEFAULT_OVERLAP(5m)
        return []

    result = run_cycle(
        signal_key="checkout-http",
        native_id="HTTP_CHECK-9F2A",
        watermark_repo=watermark_repo,
        ingest_port=ingest_port,
        executor=fake_executor,
    )

    assert result.accepted == 0
    assert result.rejected == 0
    assert ingest_port.batches == [[]]


def test_run_cycle_holds_no_domain_logic_it_only_wires_the_calls():
    """A loop with domain logic would branch on health/observed_at; this test
    proves the wiring is content-agnostic by feeding it a DOWN observation
    and asserting it still simply passes through to the ingest port
    unmodified (no filtering, no re-interpretation).
    """
    from src.composition.pull_loop import run_cycle

    watermark_repo = FakeWatermarkRepository()
    ingest_port = RecordingIngestPort()

    def fake_executor(query: str) -> list[dict]:
        return [_row("evt-down", "2026-06-24T10:00:00Z", outcome="failure")]

    run_cycle(
        signal_key="checkout-http",
        native_id="HTTP_CHECK-9F2A",
        watermark_repo=watermark_repo,
        ingest_port=ingest_port,
        executor=fake_executor,
    )

    (batch,) = ingest_port.batches
    assert batch[0].health is Health.DOWN  # passed through, not reinterpreted


# --- periodic wrapper: plain asyncio, no new scheduling dependency ----------


def test_periodic_loop_runs_one_cycle_per_tick_then_can_be_stopped():
    from src.composition.pull_loop import run_periodic

    watermark_repo = FakeWatermarkRepository()
    ingest_port = RecordingIngestPort()
    call_count = {"n": 0}

    def fake_executor(query: str) -> list[dict]:
        call_count["n"] += 1
        return [_row(f"evt-{call_count['n']}", "2026-06-24T10:00:00Z")]

    async def run_two_then_stop():
        stop_event = asyncio.Event()
        ticks = {"n": 0}

        async def on_tick(result: IngestResult) -> None:
            ticks["n"] += 1
            if ticks["n"] >= 2:
                stop_event.set()

        await run_periodic(
            signal_key="checkout-http",
            native_id="HTTP_CHECK-9F2A",
            watermark_repo=watermark_repo,
            ingest_port=ingest_port,
            executor=fake_executor,
            interval_seconds=0,
            stop_event=stop_event,
            on_cycle=on_tick,
        )

    asyncio.run(asyncio.wait_for(run_two_then_stop(), timeout=5))

    assert len(ingest_port.batches) == 2
    assert call_count["n"] == 2


def test_periodic_loop_is_plain_asyncio_no_new_dependency():
    """Guards AC5's "no new scheduling dependency": the periodic driver must
    be implementable with nothing beyond stdlib asyncio (no APScheduler or
    other scheduler library actually IMPORTED by the module).
    """
    import ast
    import inspect

    from src.composition import pull_loop

    tree = ast.parse(inspect.getsource(pull_loop))
    imported_modules = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }

    assert "apscheduler" not in imported_modules
    assert "asyncio" in imported_modules
