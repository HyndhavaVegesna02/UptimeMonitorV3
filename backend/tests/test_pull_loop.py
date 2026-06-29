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
    status_code = "0" if outcome == "success" else "1"
    status_msg = "HEALTHY" if outcome == "success" else "ERROR"
    return {
        "timestamp": ts,
        "event.id": event_id,
        "dt.synthetic.monitor.id": "HTTP_CHECK-9F2A",
        "event.type": "http_step_execution",
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


# --- Phase C1 (STORY-016a): ingest + orchestrate in one cycle ----------------


def test_run_cycle_with_orchestration_ingests_and_produces_proposal():
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

    from fakes import (
        FakeClock,
        FakeComponentRepository,
        FakeMaintenanceRepository,
        FakeObservationRepository,
        FakeProposalRepository,
        RecordingStatusPublisher,
    )
    from src.composition.config import AppConfig, ComponentConfig, Config, SignalConfig
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
    sig = SignalConfig(
        signal_key=signal_key,
        native_id=native_id,
        name="Checkout HTTP",
        component_id=component_id,
        interval_seconds=60,
    )
    comp_cfg = ComponentConfig(id=component_id, name="Checkout")
    app = AppConfig(
        id="sockshop",
        name="Sock Shop",
        monitor_provider="dynatrace",
        components=[comp_cfg],
        signals=[sig],
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
                "event.type": "http_step_execution",
                "dt.entity.synthetic_location": "us-east-1",
                "result.status.code": "1",
                "result.status.message": "ERROR",
                "result.statistics.duration": "0",
            },
            {
                "timestamp": "2026-06-24T10:02:30Z",
                "event.id": "evt-2",
                "dt.synthetic.monitor.id": native_id,
                "event.type": "http_step_execution",
                "dt.entity.synthetic_location": "us-east-1",
                "result.status.code": "1",
                "result.status.message": "ERROR",
                "result.statistics.duration": "0",
            },
            {
                "timestamp": "2026-06-24T10:03:30Z",
                "event.id": "evt-3",
                "dt.synthetic.monitor.id": native_id,
                "event.type": "http_step_execution",
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
    from src.composition.config import AppConfig, ComponentConfig, Config, SignalConfig
    from src.composition.pull_loop import run_periodic
    from src.core.domain import Component, ComponentStatus
    from src.core.services.decide import DecideAction, DecideService
    from src.core.services.pipeline import AntiFlapThresholds

    signal_key = "checkout-http"
    native_id = "HTTP_CHECK-1"
    component_id = "checkout"
    now_ts = datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc)

    # Config setup
    comp_cfg = ComponentConfig(id=component_id, name="Checkout")
    sig_cfg = SignalConfig(
        signal_key=signal_key,
        native_id=native_id,
        name="Checkout Link",
        component_id=component_id,
        interval_seconds=60,
    )
    app_cfg = AppConfig(
        id="sockshop",
        name="Sock Shop",
        monitor_provider="dynatrace",
        components=[comp_cfg],
        signals=[sig_cfg],
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
