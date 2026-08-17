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
import logging
from collections.abc import Sequence
from datetime import datetime, timezone

import pytest
from src.core.domain import Health, IngestResult, SignalObservation
from src.core.ports import SignalIngestPort, WatermarkRepository
from src.core.ports.rejected_observation_repository import (
    RejectedObservationRepository,
)


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
    status_code = "0" if outcome == "success" else "1"
    status_msg = "HEALTHY" if outcome == "success" else "ERROR"
    return {
        "timestamp": ts,
        "event.id": event_id,
        "dt.synthetic.monitor.id": "HTTP_CHECK-9F2A",
        "event.type": "http_monitor_execution",
        "dt.entity.synthetic_location": "us-east-1",
        "result.status.code": status_code,
        "result.status.message": status_msg,
        "result.statistics.duration": "100000000",
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


def test_run_cycle_holds_no_domain_logic_it_only_wires_the_calls(monkeypatch):
    """A loop with domain logic would branch on health/observed_at; this test
    proves the wiring is content-agnostic by feeding it a DOWN observation
    and asserting it still simply passes through to the ingest port
    unmodified (no filtering, no re-interpretation).
    """
    from src.composition.pull_loop import run_cycle

    # Production `map_synthetic_status` is fail-loud on any non-healthy code (the
    # real failure code is captured live in STORY-016b AC6, not guessed). Mock the
    # vendor-mapping edge so this wiring test can drive a DOWN through run_cycle.
    monkeypatch.setattr(
        "src.adapters.inbound.dynatrace.http_normalizer.map_synthetic_status",
        lambda *, code, message: Health.DOWN if message == "ERROR" else Health.UP,
    )

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


# --- Phase C1 (STORY-016a): ingest + orchestrate in one cycle ----------------


def test_run_cycle_with_orchestration_ingests_and_produces_proposal(monkeypatch):
    """AC4: a single run_cycle invocation both ingests observations AND calls
    orchestrate_signal, opening a degradation proposal when ≥ major DOWN
    observations are present.

    Uses all fakes — no DB, no Dynatrace, no Statuspage. This is the
    composition wiring test for dossier §8 step 5.

    PersistingIngestPort: a fake ingest port that writes to obs_repo,
    mirroring how IngestService persists observations to the real Postgres
    obs_repo that orchestrate_signal reads from.
    """
    from collections.abc import Sequence as Seq
    from datetime import timezone

    # Production `map_synthetic_status` is fail-loud on any non-healthy code (the
    # real failure code is captured live in STORY-016b AC6, not guessed). Mock the
    # vendor-mapping edge so this orchestration test can drive DOWN observations.
    monkeypatch.setattr(
        "src.adapters.inbound.dynatrace.http_normalizer.map_synthetic_status",
        lambda *, code, message: Health.DOWN if message == "ERROR" else Health.UP,
    )

    from fakes import (
        FakeClock,
        FakeComponentRepository,
        FakeMaintenanceRepository,
        FakeObservationRepository,
        FakeProposalRepository,
        RecordingStatusPublisher,
    )
    from src.composition.config import AppConfig, ComponentConfig, Config, MonitorConfig
    from src.composition.pull_loop import run_cycle
    from src.core.domain import Component, ComponentStatus
    from src.core.ports import SignalIngestPort
    from src.core.services.decide import DecideAction, DecideService
    from src.core.services.pipeline import AntiFlapThresholds

    # An ingest port that ALSO writes to the shared obs_repo,
    # mirroring IngestService's persist step (dossier §8 step 2).
    class PersistingIngestPort(SignalIngestPort):
        def __init__(self, obs_repo: FakeObservationRepository) -> None:
            self._obs_repo = obs_repo
            self.batches: list = []

        def ingest_observations(self, batch: Seq[SignalObservation]) -> IngestResult:
            self.batches.append(list(batch))
            self._obs_repo.saved.extend(batch)
            return IngestResult(accepted=len(batch), rejected=0)

    signal_key = "checkout-http"
    component_id = "checkout"
    native_id = "HTTP_CHECK-9F2A"

    # Build a minimal Config
    thresholds = AntiFlapThresholds(major=3, partial=2, degraded=2, recovery=2)
    mon = MonitorConfig(
        signal_key=signal_key,
        native_id=native_id,
        name="Checkout HTTP",
        interval_seconds=60,
    )
    comp_cfg = ComponentConfig(id=component_id, name="Checkout", monitors=[mon])
    app = AppConfig(
        id="sockshop",
        name="Sock Shop",
        monitor_provider="dynatrace",
        components=[comp_cfg],
        thresholds=thresholds,
    )
    config = Config([app])

    # The executor returns 3 DOWN rows (one per 60s cycle)
    now_ts = datetime(2026, 6, 24, 10, 4, 0, tzinfo=timezone.utc)

    def fake_executor(query: str) -> list[dict]:
        return [
            {
                "timestamp": "2026-06-24T10:01:30Z",
                "event.id": "evt-1",
                "dt.synthetic.monitor.id": native_id,
                "event.type": "http_monitor_execution",
                "dt.entity.synthetic_location": "us-east-1",
                "result.status.code": "1",
                "result.status.message": "ERROR",
                "result.statistics.duration": "0",
            },
            {
                "timestamp": "2026-06-24T10:02:30Z",
                "event.id": "evt-2",
                "dt.synthetic.monitor.id": native_id,
                "event.type": "http_monitor_execution",
                "dt.entity.synthetic_location": "us-east-1",
                "result.status.code": "1",
                "result.status.message": "ERROR",
                "result.statistics.duration": "0",
            },
            {
                "timestamp": "2026-06-24T10:03:30Z",
                "event.id": "evt-3",
                "dt.synthetic.monitor.id": native_id,
                "event.type": "http_monitor_execution",
                "dt.entity.synthetic_location": "us-east-1",
                "result.status.code": "1",
                "result.status.message": "ERROR",
                "result.statistics.duration": "0",
            },
        ]

    watermark_repo = FakeWatermarkRepository()

    # Shared obs_repo: PersistingIngestPort writes here; orchestrate reads from here.
    obs_repo = FakeObservationRepository()
    ingest_port = PersistingIngestPort(obs_repo)

    comp = Component(
        id=component_id,
        name="Checkout",
        status=ComponentStatus.OPERATIONAL,
        app_id="sockshop",
    )
    component_repo = FakeComponentRepository(components=[comp])
    maintenance_repo = FakeMaintenanceRepository()
    proposal_repo = FakeProposalRepository()
    publisher = RecordingStatusPublisher()
    clock = FakeClock(now_ts)
    decide_service = DecideService(proposal_repo=proposal_repo, publisher=publisher)

    result, action = run_cycle(
        signal_key=signal_key,
        native_id=native_id,
        watermark_repo=watermark_repo,
        ingest_port=ingest_port,
        executor=fake_executor,
        # Orchestration extras (dossier §8 step 5)
        config=config,
        observation_repo=obs_repo,
        maintenance_repo=maintenance_repo,
        component_repo=component_repo,
        decide_service=decide_service,
        clock=clock,
    )

    # Ingest side: 3 observations accepted
    assert isinstance(result, IngestResult)
    assert result.accepted == 3

    # Orchestration side: PROPOSED (3 DOWN in 3 cycles ≥ major=3 threshold)
    assert action == DecideAction.PROPOSED
    open_proposals = proposal_repo.list_open()
    assert len(open_proposals) == 1
    assert open_proposals[0].component_id == component_id


def test_run_periodic_with_orchestration_passes_extras():
    """Verify that run_periodic accepts all six orchestration extras, passes them to run_cycle,
    and returns (IngestResult, DecideAction) to on_cycle (STORY-016 T4).
    """
    from datetime import datetime, timezone

    from fakes import (
        FakeClock,
        FakeComponentRepository,
        FakeMaintenanceRepository,
        FakeObservationRepository,
        FakeProposalRepository,
        RecordingStatusPublisher,
    )
    from src.composition.config import AppConfig, ComponentConfig, Config, MonitorConfig
    from src.composition.pull_loop import run_periodic
    from src.core.domain import Component, ComponentStatus
    from src.core.services.decide import DecideAction, DecideService
    from src.core.services.pipeline import AntiFlapThresholds

    signal_key = "checkout-http"
    native_id = "HTTP_CHECK-1"
    component_id = "checkout"
    now_ts = datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc)

    # Config setup
    mon_cfg = MonitorConfig(
        signal_key=signal_key,
        native_id=native_id,
        name="Checkout Link",
        interval_seconds=60,
    )
    comp_cfg = ComponentConfig(id=component_id, name="Checkout", monitors=[mon_cfg])
    app_cfg = AppConfig(
        id="sockshop",
        name="Sock Shop",
        monitor_provider="dynatrace",
        components=[comp_cfg],
        thresholds=AntiFlapThresholds(major=3, partial=2, degraded=1, recovery=1),
    )
    config = Config([app_cfg])

    # Fakes
    watermark_repo = FakeWatermarkRepository()
    obs_repo = FakeObservationRepository()
    ingest_port = RecordingIngestPort()

    def fake_executor(query: str) -> list[dict]:
        return []

    comp = Component(
        id=component_id,
        name="Checkout",
        status=ComponentStatus.OPERATIONAL,
        app_id="sockshop",
    )
    component_repo = FakeComponentRepository(components=[comp])
    maintenance_repo = FakeMaintenanceRepository()
    proposal_repo = FakeProposalRepository()
    publisher = RecordingStatusPublisher()
    clock = FakeClock(now_ts)
    decide_service = DecideService(proposal_repo=proposal_repo, publisher=publisher)

    called_results = []

    async def run_under_asyncio():
        stop_event = asyncio.Event()

        async def on_cycle(res):
            called_results.append(res)
            stop_event.set()

        await run_periodic(
            signal_key=signal_key,
            native_id=native_id,
            watermark_repo=watermark_repo,
            ingest_port=ingest_port,
            executor=fake_executor,
            interval_seconds=0.01,
            stop_event=stop_event,
            on_cycle=on_cycle,
            # Orchestration extras
            config=config,
            observation_repo=obs_repo,
            maintenance_repo=maintenance_repo,
            component_repo=component_repo,
            decide_service=decide_service,
            clock=clock,
        )

    asyncio.run(asyncio.wait_for(run_under_asyncio(), timeout=5))

    assert len(called_results) == 1
    # Verify that the result is a tuple (IngestResult, DecideAction)
    res = called_results[0]
    assert isinstance(res, tuple)
    assert isinstance(res[0], IngestResult)
    assert res[1] == DecideAction.NOOP


# --- STORY-050: a failed cycle is logged and survived, never fatal ----------


def test_run_periodic_survives_one_failed_cycle_then_continues(caplog):
    """AC1 (STORY-050): a cycle that raises (e.g. `GrailQueryError` from a
    network timeout) must not crash `run_periodic` -- the failure is logged
    at ERROR (with the signal_key + cause) and the NEXT cycle runs on
    schedule. Uses a fake executor that fails once then succeeds, and
    asserts the SECOND cycle's ingest actually ran.
    """
    from src.adapters.inbound.dynatrace.grail_executor import GrailQueryError
    from src.composition.pull_loop import run_periodic

    watermark_repo = FakeWatermarkRepository()
    ingest_port = RecordingIngestPort()
    call_count = {"n": 0}

    def flaky_executor(query: str) -> list[dict]:
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise GrailQueryError(
                "HTTP request to Grail failed: _ssl.c:1015: "
                "The handshake operation timed out"
            )
        return [_row(f"evt-{call_count['n']}", "2026-06-24T10:00:00Z")]

    async def run_until_one_success_then_stop():
        stop_event = asyncio.Event()

        async def on_tick(result: IngestResult) -> None:
            # A failed cycle never calls on_cycle (no result to hand it) --
            # so this fires only once, on the SECOND (successful) cycle.
            stop_event.set()

        with caplog.at_level(logging.ERROR, logger="src.composition.pull_loop"):
            await run_periodic(
                signal_key="checkout-http",
                native_id="HTTP_CHECK-9F2A",
                watermark_repo=watermark_repo,
                ingest_port=ingest_port,
                executor=flaky_executor,
                interval_seconds=0,
                stop_event=stop_event,
                on_cycle=on_tick,
            )

    asyncio.run(asyncio.wait_for(run_until_one_success_then_stop(), timeout=5))

    # Both cycles ran: the first failed, the second succeeded.
    assert call_count["n"] == 2
    # The SECOND cycle's ingest actually ran.
    assert len(ingest_port.batches) == 1
    assert ingest_port.batches[0][0].source_event_id == "evt-2"

    error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(error_records) == 1
    message = error_records[0].getMessage()
    assert "checkout-http" in message
    assert "handshake operation timed out" in message


def test_run_periodic_consecutive_failure_counts_increase_and_reset_on_success(
    caplog,
):
    """AC3 (STORY-050): the per-signal consecutive-failure counter increases
    with each successive failure, a success resets it to zero, and the loop
    NEVER exits on cycle failures. Sequence fail, fail, succeed, fail ->
    logged counts 1, 2, (reset), 1.
    """
    from src.composition.pull_loop import run_periodic

    watermark_repo = FakeWatermarkRepository()
    ingest_port = RecordingIngestPort()
    outcomes = ["fail", "fail", "success", "fail"]
    call_count = {"n": 0}

    async def run_scripted_sequence():
        stop_event = asyncio.Event()

        def scripted_executor(query: str) -> list[dict]:
            idx = call_count["n"]
            call_count["n"] += 1
            if idx == len(outcomes) - 1:
                # Set stop_event from inside the LAST (failing) cycle --
                # proves the loop keeps scheduling failed cycles past the
                # first one, right up to the point we ask it to stop.
                stop_event.set()
            if outcomes[idx] == "fail":
                raise RuntimeError(f"transient failure #{idx}")
            return [_row(f"evt-{idx}", "2026-06-24T10:00:00Z")]

        with caplog.at_level(logging.ERROR, logger="src.composition.pull_loop"):
            await run_periodic(
                signal_key="checkout-http",
                native_id="HTTP_CHECK-9F2A",
                watermark_repo=watermark_repo,
                ingest_port=ingest_port,
                executor=scripted_executor,
                interval_seconds=0,
                stop_event=stop_event,
            )

    asyncio.run(asyncio.wait_for(run_scripted_sequence(), timeout=5))

    # All four scripted cycles ran -- the loop never exited on failure.
    assert call_count["n"] == 4

    error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(error_records) == 3  # the 3 "fail" outcomes; success logs nothing
    assert "consecutive_failures=1" in error_records[0].getMessage()
    assert "consecutive_failures=2" in error_records[1].getMessage()
    # Reset by the intervening success -- back to 1, not 3.
    assert "consecutive_failures=1" in error_records[2].getMessage()


def test_run_periodic_three_consecutive_failures_keep_scheduling(caplog):
    """AC3 (STORY-050): >= 3 CONSECUTIVE failures (the AC's literal bar,
    spec-review follow-up) -- counts climb 1, 2, 3 with no reset in between,
    and the loop is STILL scheduling afterwards (the 4th cycle runs).
    """
    from src.composition.pull_loop import run_periodic

    watermark_repo = FakeWatermarkRepository()
    ingest_port = RecordingIngestPort()
    outcomes = ["fail", "fail", "fail", "success"]
    call_count = {"n": 0}

    async def run_scripted_sequence():
        stop_event = asyncio.Event()

        def scripted_executor(query: str) -> list[dict]:
            idx = call_count["n"]
            call_count["n"] += 1
            if idx == len(outcomes) - 1:
                stop_event.set()
            if outcomes[idx] == "fail":
                raise RuntimeError(f"transient failure #{idx}")
            return [_row(f"evt-{idx}", "2026-06-24T10:00:00Z")]

        with caplog.at_level(logging.ERROR, logger="src.composition.pull_loop"):
            await run_periodic(
                signal_key="checkout-http",
                native_id="HTTP_CHECK-9F2A",
                watermark_repo=watermark_repo,
                ingest_port=ingest_port,
                executor=scripted_executor,
                interval_seconds=0,
                stop_event=stop_event,
            )

    asyncio.run(asyncio.wait_for(run_scripted_sequence(), timeout=5))

    # All four cycles ran: three consecutive failures never exited the loop,
    # and the 4th (successful) cycle actually ingested.
    assert call_count["n"] == 4
    assert len(ingest_port.batches) == 1

    error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(error_records) == 3
    assert "consecutive_failures=1" in error_records[0].getMessage()
    assert "consecutive_failures=2" in error_records[1].getMessage()
    assert "consecutive_failures=3" in error_records[2].getMessage()


def test_run_periodic_cancellation_still_propagates_and_stops_loop():
    """Guard (STORY-050): `asyncio.CancelledError` is a `BaseException`, not
    an `Exception`, in Python 3.13 -- so the bare `except Exception` added
    for AC1/AC3 must NOT swallow it. Cancelling the task must still stop
    the loop.
    """
    from src.composition.pull_loop import run_periodic

    watermark_repo = FakeWatermarkRepository()
    ingest_port = RecordingIngestPort()

    def fake_executor(query: str) -> list[dict]:
        return []

    async def run_and_cancel():
        task = asyncio.ensure_future(
            run_periodic(
                signal_key="checkout-http",
                native_id="HTTP_CHECK-9F2A",
                watermark_repo=watermark_repo,
                ingest_port=ingest_port,
                executor=fake_executor,
                interval_seconds=10,  # long sleep so cancel lands mid-sleep
            )
        )
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert task.cancelled()

    asyncio.run(run_and_cancel())


def test_run_periodic_stop_event_honored_after_a_failed_cycle():
    """Guard (STORY-050): a stop_event set during a FAILING cycle must not
    wait another `interval_seconds` before stopping -- mirrors STORY-023's
    existing success-path guarantee, now extended to the failure path.
    """
    from src.composition.pull_loop import run_periodic

    watermark_repo = FakeWatermarkRepository()
    ingest_port = RecordingIngestPort()
    call_count = {"n": 0}

    async def run_and_measure():
        stop_event = asyncio.Event()

        def failing_executor(query: str) -> list[dict]:
            call_count["n"] += 1
            stop_event.set()
            raise RuntimeError("transient failure")

        await run_periodic(
            signal_key="checkout-http",
            native_id="HTTP_CHECK-9F2A",
            watermark_repo=watermark_repo,
            ingest_port=ingest_port,
            executor=failing_executor,
            interval_seconds=10,  # would blow the outer timeout if not honored
            stop_event=stop_event,
        )

    asyncio.run(asyncio.wait_for(run_and_measure(), timeout=5))
    assert call_count["n"] == 1


# --- STORY-190: partial batch resilience & bad row quarantine -------------------


class FakeRejectedObservationRepository(RejectedObservationRepository):
    def __init__(self) -> None:
        self.saved: list[dict] = []

    def save(
        self,
        *,
        signal_key: str | None,
        reason: str,
        payload: dict,
        rejected_at: datetime,
    ) -> None:
        self.saved.append(
            {
                "signal_key": signal_key,
                "reason": reason,
                "payload": payload,
                "rejected_at": rejected_at,
            }
        )


def test_quarantine_bad_row_allows_watermark_to_advance_across_consecutive_cycles(
    caplog,
):
    """AC2 (STORY-190): proves that a single unmappable row does NOT stall the signal,
    quarantines the bad row into rejected_repo (with a WARNING log), and permits the
    watermark to advance across consecutive cycles.
    """
    from fakes import FakeObservationRepository
    from src.adapters.system_clock import SystemClock
    from src.composition.pull_loop import run_cycle
    from src.core.services.ingest_service import IngestService

    watermark_repo = FakeWatermarkRepository({"checkout-http": None})
    obs_repo = FakeObservationRepository()
    rejected_repo = FakeRejectedObservationRepository()
    clock = SystemClock()

    ingest_service = IngestService(
        observation_repo=obs_repo,
        watermark_repo=watermark_repo,
        rejected_repo=rejected_repo,
        clock=clock,
    )

    bad_row_1 = {
        "timestamp": "2026-06-24T10:00:00Z",
        "event.id": "evt-bad-1",
        "event.type": "UNSUPPORTED_TYPE",
    }
    good_row_1 = _row("evt-good-1", "2026-06-24T10:01:00Z")

    def cycle_1_executor(query: str) -> list[dict]:
        return [bad_row_1, good_row_1]

    with caplog.at_level(logging.WARNING, logger="src.composition.pull_loop"):
        result1 = run_cycle(
            signal_key="checkout-http",
            native_id="HTTP_CHECK-9F2A",
            watermark_repo=watermark_repo,
            ingest_port=ingest_service,
            executor=cycle_1_executor,
            rejected_repo=rejected_repo,
        )

    assert result1.accepted == 1
    assert len(rejected_repo.saved) == 1
    assert rejected_repo.saved[0]["signal_key"] == "checkout-http"
    assert rejected_repo.saved[0]["payload"] == bad_row_1
    assert "UNSUPPORTED_TYPE" in rejected_repo.saved[0]["reason"]
    # Watermark advanced to good_row_1 timestamp!
    wm_after_cycle_1 = watermark_repo.get("checkout-http")
    assert wm_after_cycle_1 == datetime(2026, 6, 24, 10, 1, 0, tzinfo=timezone.utc)
    assert any(
        "Quarantining row for signal_key='checkout-http'" in r.getMessage()
        for r in caplog.records
    )

    # Cycle 2: watermark advanced further with another bad row present
    bad_row_2 = {
        "timestamp": "2026-06-24T10:02:00Z",
        "event.id": "evt-bad-2",
        "event.type": "http_monitor_execution",
        "result.status.code": "999",
        "result.status.message": "UNKNOWN",
    }
    good_row_2 = _row("evt-good-2", "2026-06-24T10:03:00Z")

    def cycle_2_executor(query: str) -> list[dict]:
        return [good_row_2, bad_row_2]

    result2 = run_cycle(
        signal_key="checkout-http",
        native_id="HTTP_CHECK-9F2A",
        watermark_repo=watermark_repo,
        ingest_port=ingest_service,
        executor=cycle_2_executor,
        rejected_repo=rejected_repo,
    )

    assert result2.accepted == 1
    assert len(rejected_repo.saved) == 2
    wm_after_cycle_2 = watermark_repo.get("checkout-http")
    assert wm_after_cycle_2 == datetime(2026, 6, 24, 10, 3, 0, tzinfo=timezone.utc)
    assert wm_after_cycle_2 > wm_after_cycle_1


def test_pre_fix_strict_normalization_stalls_the_signal_permanently(monkeypatch):
    """AC3 (STORY-190): REPRODUCE the pre-fix defect through the real pipeline.

    REWRITTEN in the sprint-65 fix round. The first version of this test was
    TAUTOLOGICAL and proved nothing: it built a `watermark_repo`, never passed
    it to anything, called `normalize_rows` directly, and then asserted the
    watermark was still `None` -- an assertion that holds whether or not
    `normalize_rows` raises, because nothing in the test could ever have
    advanced it. Caught by `yt-spec-reviewer`.

    What the defect actually is, and therefore what this must show: the raise
    happens inside `fetch_observations`, which `run_cycle` calls BEFORE
    `ingest_port.ingest_observations`, so `IngestService`'s watermark advance is
    never reached; the next cycle then re-reads the SAME unadvanced watermark
    and re-queries the SAME window, still containing the same bad row. The cost
    is not one lost batch -- the signal never advances again.

    So this drives the STRICT (pre-fix) path through the REAL `run_cycle` by
    substituting the old strict `fetch_observations`, runs TWO cycles against
    ONE `watermark_repo`, and asserts:
      1. each cycle raises,
      2. the watermark is STILL unadvanced after both, and
      3. cycle 2 was handed the SAME watermark value as cycle 1 -- the actual
         stall, not merely "an exception happened".
    """
    from fakes import FakeObservationRepository
    from src.adapters.inbound.dynatrace.dispatch import (
        UnsupportedMonitorTypeError,
        normalize_rows,
    )
    from src.adapters.system_clock import SystemClock
    from src.composition import pull_loop as pull_loop_module
    from src.composition.pull_loop import run_cycle
    from src.core.services.ingest_service import IngestService

    watermark_repo = FakeWatermarkRepository({"checkout-http": None})
    ingest_service = IngestService(
        observation_repo=FakeObservationRepository(),
        watermark_repo=watermark_repo,
        rejected_repo=FakeRejectedObservationRepository(),
        clock=SystemClock(),
    )

    bad_row = {
        "timestamp": "2026-06-24T10:00:00Z",
        "event.id": "evt-bad-1",
        "event.type": "UNSUPPORTED_TYPE",
    }
    good_row = _row("evt-good-1", "2026-06-24T10:01:00Z")

    # The PRE-FIX `fetch_observations`: strict `normalize_rows`, so the first
    # bad row aborts the whole batch before ingest ever runs.
    def strict_fetch_observations(*, signal_key, native_id, watermark, executor, **_):
        return normalize_rows(executor("<query>"), signal_key=signal_key)

    monkeypatch.setattr(
        pull_loop_module, "fetch_observations", strict_fetch_observations
    )

    watermarks_seen: list[datetime | None] = []

    def executor(query: str) -> list[dict]:
        watermarks_seen.append(watermark_repo.get("checkout-http"))
        return [bad_row, good_row]

    for _ in range(2):
        with pytest.raises(UnsupportedMonitorTypeError):
            run_cycle(
                signal_key="checkout-http",
                native_id="HTTP_CHECK-9F2A",
                watermark_repo=watermark_repo,
                ingest_port=ingest_service,
                executor=executor,
            )

    # (2) never advanced, despite a perfectly good row sitting behind the bad one
    assert watermark_repo.get("checkout-http") is None
    # (3) THE STALL: cycle 2 started from exactly where cycle 1 did
    assert watermarks_seen == [None, None]


def test_healthy_batch_logs_no_quarantine_warning(caplog):
    """AC5 (STORY-190), negative half: a clean batch must log NO quarantine WARNING.

    Without this, "quarantining logs a WARNING" is only half a claim -- a
    implementation that logged on EVERY cycle would satisfy the positive
    assertion while making the warning meaningless as a signal.
    """
    from fakes import FakeObservationRepository
    from src.adapters.system_clock import SystemClock
    from src.composition.pull_loop import run_cycle
    from src.core.services.ingest_service import IngestService

    watermark_repo = FakeWatermarkRepository({"checkout-http": None})
    rejected_repo = FakeRejectedObservationRepository()
    ingest_service = IngestService(
        observation_repo=FakeObservationRepository(),
        watermark_repo=watermark_repo,
        rejected_repo=rejected_repo,
        clock=SystemClock(),
    )

    with caplog.at_level(logging.WARNING, logger="src.composition.pull_loop"):
        result = run_cycle(
            signal_key="checkout-http",
            native_id="HTTP_CHECK-9F2A",
            watermark_repo=watermark_repo,
            ingest_port=ingest_service,
            executor=lambda q: [
                _row("evt-good-1", "2026-06-24T10:00:00Z"),
                _row("evt-good-2", "2026-06-24T10:01:00Z"),
            ],
            rejected_repo=rejected_repo,
        )

    assert result.accepted == 2
    assert rejected_repo.saved == []
    assert not [r for r in caplog.records if "Quarantining row" in r.getMessage()]


# --- STORY-155b AC1: the live ingest path is provably unchanged with the
# SampleModeIngest decorator removed -------------------------------------


def test_run_periodic_records_same_observations_with_ingest_decorator_removed():
    """AC1: drives `run_periodic` with the REAL, un-decorated `IngestService`
    (the shape `composition/run.py::build_live_loop` has after this story
    removes the `SampleModeIngest` wrapper) and asserts the recorded
    observations match, byte-for-byte, a REAL "before" capture.

    The "before" arm cannot live in this suite (this same story deletes
    `SampleModeIngest` and its dedicated end-to-end test), so it is recorded
    here instead: this is the ACTUAL output of running this exact harness
    (this same config/executor/fakes shape) through
    `SampleModeIngest(delegate=IngestService(...), <flag repo left unset,
    i.e. OFF>)` before the decorator was deleted -- not an invented fixture.
    The now-deleted end-to-end test already proved OFF is a byte-identical
    passthrough at the direct `ingest_observations` level; this test
    re-proves the same invariant one layer up, through the actual
    `run_periodic` scheduling loop, so the claim survives the decorator's
    deletion instead of dying with it.

    Comparison is at the OBSERVATION level (fields below), never a DB-call
    count -- the decorator's per-cycle flag-repository read legitimately
    disappears along with it, and a call-count comparison would prove
    nothing (the AC's own warning).
    """
    from fakes import (
        FakeClock,
        FakeComponentRepository,
        FakeMaintenanceRepository,
        FakeObservationRepository,
        FakeProposalRepository,
        RecordingStatusPublisher,
    )
    from src.composition.config import AppConfig, ComponentConfig, Config, MonitorConfig
    from src.composition.pull_loop import run_periodic
    from src.core.domain import Component, ComponentStatus, Health
    from src.core.services.decide import DecideService
    from src.core.services.ingest_service import IngestService
    from src.core.services.pipeline import AntiFlapThresholds

    signal_key = "checkout-http"
    native_id = "HTTP_CHECK-9F2A"
    component_id = "checkout"
    now_ts = datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc)

    mon_cfg = MonitorConfig(
        signal_key=signal_key,
        native_id=native_id,
        name="Checkout Link",
        interval_seconds=60,
    )
    comp_cfg = ComponentConfig(id=component_id, name="Checkout", monitors=[mon_cfg])
    app_cfg = AppConfig(
        id="sockshop",
        name="Sock Shop",
        monitor_provider="dynatrace",
        components=[comp_cfg],
        thresholds=AntiFlapThresholds(major=3, partial=2, degraded=1, recovery=1),
    )
    config = Config([app_cfg])

    watermark_repo = FakeWatermarkRepository()
    obs_repo = FakeObservationRepository()
    rejected_repo = FakeRejectedObservationRepository()
    clock = FakeClock(now_ts)

    # POST-removal shape: the bare, un-decorated IngestService -- no
    # SampleModeIngest wrapper. This is what build_live_loop wires today.
    ingest_port = IngestService(
        observation_repo=obs_repo,
        watermark_repo=watermark_repo,
        rejected_repo=rejected_repo,
        clock=clock,
    )

    comp = Component(
        id=component_id,
        name="Checkout",
        status=ComponentStatus.OPERATIONAL,
        app_id="sockshop",
    )
    component_repo = FakeComponentRepository(components=[comp])
    maintenance_repo = FakeMaintenanceRepository()
    proposal_repo = FakeProposalRepository()
    publisher = RecordingStatusPublisher()
    decide_service = DecideService(proposal_repo=proposal_repo, publisher=publisher)

    async def run_once():
        stop_event = asyncio.Event()
        results = []

        async def on_cycle(res):
            results.append(res)
            stop_event.set()

        await run_periodic(
            signal_key=signal_key,
            native_id=native_id,
            watermark_repo=watermark_repo,
            ingest_port=ingest_port,
            executor=lambda q: [
                _row("evt-cap-1", "2026-06-24T09:59:00Z"),
                _row("evt-cap-2", "2026-06-24T09:59:30Z"),
            ],
            interval_seconds=0.01,
            stop_event=stop_event,
            on_cycle=on_cycle,
            config=config,
            observation_repo=obs_repo,
            maintenance_repo=maintenance_repo,
            component_repo=component_repo,
            decide_service=decide_service,
            clock=clock,
        )
        return results

    results = asyncio.run(asyncio.wait_for(run_once(), timeout=5))

    assert len(results) == 1
    (ingest_result, decide_action) = results[0]
    assert isinstance(ingest_result, IngestResult)
    assert ingest_result.accepted == 2

    # The RECORDED "before" evidence (captured 2026-08-16, pre-removal, via
    # SampleModeIngest(delegate=IngestService(...), <flag repo left unset,
    # i.e. OFF>) driven through this identical run_periodic harness).
    assert len(obs_repo.saved) == 2
    saved = [
        {
            "signal_key": o.signal_key,
            "observed_at": o.observed_at.isoformat(),
            "health": o.health,
            "source_event_id": o.source_event_id,
            "raw_ref": o.raw_ref,
            "location": o.location,
            "latency_ms": o.latency_ms,
            "source_system": o.source.system,
            "source_native_id": o.source.native_id,
            "source_native_kind": o.source.native_kind,
            "response_status_code": o.response_status_code,
        }
        for o in obs_repo.saved
    ]
    assert saved == [
        {
            "signal_key": "checkout-http",
            "observed_at": "2026-06-24T09:59:00+00:00",
            "health": Health.UP,
            "source_event_id": "evt-cap-1",
            "raw_ref": None,
            "location": "us-east-1",
            "latency_ms": 100,
            "source_system": "dynatrace",
            "source_native_id": "HTTP_CHECK-9F2A",
            "source_native_kind": "http",
            "response_status_code": None,
        },
        {
            "signal_key": "checkout-http",
            "observed_at": "2026-06-24T09:59:30+00:00",
            "health": Health.UP,
            "source_event_id": "evt-cap-2",
            "raw_ref": None,
            "location": "us-east-1",
            "latency_ms": 100,
            "source_system": "dynatrace",
            "source_native_id": "HTTP_CHECK-9F2A",
            "source_native_kind": "http",
            "response_status_code": None,
        },
    ]
