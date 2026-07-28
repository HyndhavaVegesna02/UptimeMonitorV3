"""Tests for composition/orchestrate.py — the pipeline orchestrator (STORY-016a B1-B4).

Dossier §8 (step 5: "hand rows to the pipeline"), §10 (collapse→streak→anti_flap),
§12 (decide/proposal reconciliation), T1.1 (commit-first publish).

All tests are PURE FAKE TESTS — no DB, no Statuspage, no live creds.
The orchestrator is composition wiring; no domain logic lives here.

STORY-045 adds: a recovery-trigger write-back test (AC2b — a DecideService wired
with `StatusWritebackPublisher` writes `components.status` back after a recovery
publish) and the AC5 end-to-end regression (degrade → approve → recover, proving
the previously-unreachable recovery branch is now reachable once approve writes
back a degraded `current_status`).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.composition.config import (
    AppConfig,
    ComponentConfig,
    Config,
    MonitorConfig,
)
from src.composition.orchestrate import orchestrate_signal
from src.composition.publish_helper import RecordingPublisher, StatusWritebackPublisher
from src.core.domain import (
    Component,
    ComponentStatus,
    Health,
    Provenance,
    SignalObservation,
    StatusChange,
)
from src.core.domain.proposal import ProposalState
from src.core.services.approval import ApprovalService
from src.core.services.decide import DecideAction, DecideService
from src.core.services.pipeline import AntiFlapThresholds


def _utc(hour: int, minute: int = 0, second: int = 0, day: int = 24) -> datetime:
    return datetime(2026, 6, day, hour, minute, second, tzinfo=timezone.utc)


def _obs(
    signal_key: str,
    observed_at: datetime,
    health: Health = Health.DOWN,
    location: str = "us-east",
    event_id: str | None = None,
) -> SignalObservation:
    eid = event_id or f"evt-{observed_at.isoformat()}-{location}"
    return SignalObservation(
        signal_key=signal_key,
        observed_at=observed_at,
        health=health,
        source_event_id=eid,
        source=Provenance(system="dynatrace", native_id="X-1", native_kind="http"),
        location=location,
    )


def _build_config(
    *,
    signal_key: str = "checkout-http",
    component_id: str = "checkout",
    interval_seconds: int = 60,
    major: int = 3,
    partial: int = 2,
    degraded: int = 2,
    recovery: int = 2,
) -> Config:
    """Build an in-test Config with one signal/component/app."""
    thresholds = AntiFlapThresholds(
        major=major, partial=partial, degraded=degraded, recovery=recovery
    )
    mon = MonitorConfig(
        signal_key=signal_key,
        native_id="SYNTHETIC_TEST-X",
        name="Checkout HTTP",
        interval_seconds=interval_seconds,
    )
    comp = ComponentConfig(id=component_id, name="Checkout", monitors=[mon])
    app = AppConfig(
        id="sockshop",
        name="Sock Shop",
        monitor_provider="dynatrace",
        components=[comp],
        thresholds=thresholds,
    )
    return Config([app])


# ---------------------------------------------------------------------------
# Phase B1 — AC1: degradation → proposal, below-threshold → nothing
# ---------------------------------------------------------------------------


class TestOrchestrateSignalAC1:
    """AC1: a FAILING streak ≥ major threshold opens a degradation proposal;
    a below-threshold streak opens nothing."""

    def test_sustained_failing_streak_opens_degradation_proposal(self):
        """≥ major FAILING observations → orchestrate_signal returns PROPOSED.

        Observations placed in a single cycle (60s window) with major=3 threshold,
        so 3 DOWN observations spanning ≥ 3 cycles triggers a proposal.
        """
        from fakes import (
            FakeClock,
            FakeComponentRepository,
            FakeMaintenanceRepository,
            FakeObservationRepository,
            FakeProposalRepository,
            RecordingStatusPublisher,
        )
        from src.composition.orchestrate import orchestrate_signal

        signal_key = "checkout-http"
        component_id = "checkout"
        cfg = _build_config(signal_key=signal_key, component_id=component_id, major=3)

        # Place one DOWN observation per 60s cycle; need ≥ major=3 consecutive
        now = _utc(10, 4, 0)  # T=10:04:00
        timedelta(seconds=60)
        # Buckets start at: now - (3+2)*60s = 10:04:00 - 300s = 09:59:00
        # We need ≥ 3 cycles of DOWN — put them in cycles 2, 3, 4 (at 10:01, 10:02, 10:03)
        obs_repo = FakeObservationRepository()
        obs_repo.saved = [
            _obs(
                signal_key, _utc(10, 1, 30), Health.DOWN
            ),  # bucket [10:01:00, 10:02:00)
            _obs(
                signal_key, _utc(10, 2, 30), Health.DOWN
            ),  # bucket [10:02:00, 10:03:00)
            _obs(
                signal_key, _utc(10, 3, 30), Health.DOWN
            ),  # bucket [10:03:00, 10:04:00)
        ]

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
        clock = FakeClock(now)
        decide_service = DecideService(proposal_repo=proposal_repo, publisher=publisher)

        action = orchestrate_signal(
            signal_key=signal_key,
            config=cfg,
            observation_repo=obs_repo,
            maintenance_repo=maintenance_repo,
            component_repo=component_repo,
            decide_service=decide_service,
            clock=clock,
        )

        assert action == DecideAction.PROPOSED
        open_proposals = proposal_repo.list_open()
        assert len(open_proposals) == 1
        assert open_proposals[0].component_id == component_id

    def test_below_threshold_streak_opens_no_proposal(self):
        """A FAILING streak of 1 (below major=3) should NOT open a proposal.

        Anti-flap returns nothing/internal-warning for streak < degraded threshold.
        """
        from fakes import (
            FakeClock,
            FakeComponentRepository,
            FakeMaintenanceRepository,
            FakeObservationRepository,
            FakeProposalRepository,
            RecordingStatusPublisher,
        )
        from src.composition.orchestrate import orchestrate_signal

        signal_key = "checkout-http"
        component_id = "checkout"
        # major=3, partial=2, degraded=2, recovery=2 — need ≥2 for anything
        cfg = _build_config(
            signal_key=signal_key,
            component_id=component_id,
            major=3,
            partial=2,
            degraded=2,
        )

        now = _utc(10, 4, 0)
        obs_repo = FakeObservationRepository()
        # Only 1 DOWN obs — streak=1, internal warning, no proposal
        obs_repo.saved = [
            _obs(signal_key, _utc(10, 3, 30), Health.DOWN),
        ]

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
        clock = FakeClock(now)
        decide_service = DecideService(proposal_repo=proposal_repo, publisher=publisher)

        action = orchestrate_signal(
            signal_key=signal_key,
            config=cfg,
            observation_repo=obs_repo,
            maintenance_repo=maintenance_repo,
            component_repo=component_repo,
            decide_service=decide_service,
            clock=clock,
        )

        # streak=1 → internal warning → anti_flap proposes nothing → NOOP
        assert action == DecideAction.NOOP
        assert proposal_repo.list_open() == []

    def test_no_observations_returns_noop(self):
        """No observations → streak() returns None → NOOP (no decide call)."""
        from fakes import (
            FakeClock,
            FakeComponentRepository,
            FakeMaintenanceRepository,
            FakeObservationRepository,
            FakeProposalRepository,
            RecordingStatusPublisher,
        )
        from src.composition.orchestrate import orchestrate_signal

        signal_key = "checkout-http"
        component_id = "checkout"
        cfg = _build_config(signal_key=signal_key, component_id=component_id)

        now = _utc(10, 4, 0)
        obs_repo = FakeObservationRepository()
        # No observations at all
        obs_repo.saved = []

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
        clock = FakeClock(now)
        decide_service = DecideService(proposal_repo=proposal_repo, publisher=publisher)

        action = orchestrate_signal(
            signal_key=signal_key,
            config=cfg,
            observation_repo=obs_repo,
            maintenance_repo=maintenance_repo,
            component_repo=component_repo,
            decide_service=decide_service,
            clock=clock,
        )

        assert action == DecideAction.NOOP
        assert proposal_repo.list_open() == []


# ---------------------------------------------------------------------------
# Phase B3 — AC2: recovery, maintenance, supersession edges
# ---------------------------------------------------------------------------


class TestOrchestrateSignalAC2:
    """AC2: recovery-publish, obsolete, supersede, maintenance-excluded edges."""

    def _make_deps(self, signal_key: str, component_id: str, cfg: Config):
        """Helper to build shared fakes."""
        from fakes import (
            FakeClock,
            FakeComponentRepository,
            FakeMaintenanceRepository,
            FakeObservationRepository,
            FakeProposalRepository,
            RecordingStatusPublisher,
        )

        now = _utc(10, 10, 0)
        obs_repo = FakeObservationRepository()
        proposal_repo = FakeProposalRepository()
        publisher = RecordingStatusPublisher()
        clock = FakeClock(now)

        comp_degraded = Component(
            id=component_id,
            name="Checkout",
            status=ComponentStatus.DEGRADED,  # current published status is degraded
            app_id="sockshop",
        )
        component_repo = FakeComponentRepository(components=[comp_degraded])
        maintenance_repo = FakeMaintenanceRepository()
        decide_service = DecideService(proposal_repo=proposal_repo, publisher=publisher)
        return (
            obs_repo,
            component_repo,
            maintenance_repo,
            proposal_repo,
            publisher,
            clock,
            decide_service,
            now,
        )

    def test_sustained_recovery_publishes_recovery(self):
        """≥ recovery UP observations while current_status is degraded → PUBLISHED_RECOVERY."""
        from fakes import (
            FakeClock,
            FakeComponentRepository,
            FakeMaintenanceRepository,
            FakeObservationRepository,
            FakeProposalRepository,
            RecordingStatusPublisher,
        )
        from src.composition.orchestrate import orchestrate_signal

        signal_key = "checkout-http"
        component_id = "checkout"
        cfg = _build_config(
            signal_key=signal_key, component_id=component_id, recovery=2
        )

        now = _utc(10, 10, 0)
        obs_repo = FakeObservationRepository()
        # 2 UP observations in consecutive cycles → streak=2 ≥ recovery=2
        obs_repo.saved = [
            _obs(signal_key, _utc(10, 8, 30), Health.UP),
            _obs(signal_key, _utc(10, 9, 30), Health.UP),
        ]

        comp = Component(
            id=component_id,
            name="Checkout",
            status=ComponentStatus.DEGRADED,  # current is degraded → UP improves it
            app_id="sockshop",
        )
        component_repo = FakeComponentRepository(components=[comp])
        maintenance_repo = FakeMaintenanceRepository()
        proposal_repo = FakeProposalRepository()
        publisher = RecordingStatusPublisher()
        clock = FakeClock(now)
        decide_service = DecideService(proposal_repo=proposal_repo, publisher=publisher)

        action = orchestrate_signal(
            signal_key=signal_key,
            config=cfg,
            observation_repo=obs_repo,
            maintenance_repo=maintenance_repo,
            component_repo=component_repo,
            decide_service=decide_service,
            clock=clock,
        )

        assert action == DecideAction.PUBLISHED_RECOVERY
        assert len(publisher.published) == 1
        assert publisher.published[0].component_id == component_id
        assert publisher.published[0].status == ComponentStatus.OPERATIONAL

    def test_recovery_publish_writes_back_component_status(self):
        """STORY-045 AC2 (recovery trigger): a DecideService wired with
        StatusWritebackPublisher writes components.status back after the
        recovery publish — the write-back applies at BOTH trigger points, not
        just the approve trigger (see test_decisions.py's HTTP-level proof for
        the approve trigger)."""
        from fakes import (
            FakeClock,
            FakeComponentRepository,
            FakeMaintenanceRepository,
            FakeObservationRepository,
            FakeProposalRepository,
            RecordingStatusPublisher,
        )

        signal_key = "checkout-http"
        component_id = "checkout"
        cfg = _build_config(
            signal_key=signal_key, component_id=component_id, recovery=2
        )

        now = _utc(10, 10, 0)
        obs_repo = FakeObservationRepository()
        obs_repo.saved = [
            _obs(signal_key, _utc(10, 8, 30), Health.UP),
            _obs(signal_key, _utc(10, 9, 30), Health.UP),
        ]

        comp = Component(
            id=component_id,
            name="Checkout",
            status=ComponentStatus.DEGRADED,
            app_id="sockshop",
        )
        component_repo = FakeComponentRepository(components=[comp])
        maintenance_repo = FakeMaintenanceRepository()
        proposal_repo = FakeProposalRepository()
        clock = FakeClock(now)
        delegate = RecordingStatusPublisher()
        publisher = StatusWritebackPublisher(delegate, component_repo)
        decide_service = DecideService(proposal_repo=proposal_repo, publisher=publisher)

        action = orchestrate_signal(
            signal_key=signal_key,
            config=cfg,
            observation_repo=obs_repo,
            maintenance_repo=maintenance_repo,
            component_repo=component_repo,
            decide_service=decide_service,
            clock=clock,
        )

        assert action == DecideAction.PUBLISHED_RECOVERY
        assert component_repo.get(component_id).status == ComponentStatus.OPERATIONAL

    def test_recovery_while_pending_obsoletes_proposal(self):
        """Recovery streak while a degradation is pending → OBSOLETED, nothing published."""
        from fakes import (
            FakeClock,
            FakeComponentRepository,
            FakeMaintenanceRepository,
            FakeObservationRepository,
            FakeProposalRepository,
            RecordingStatusPublisher,
        )
        from src.composition.orchestrate import orchestrate_signal
        from src.core.domain.proposal import StatusProposal

        signal_key = "checkout-http"
        component_id = "checkout"
        cfg = _build_config(
            signal_key=signal_key, component_id=component_id, recovery=2
        )

        now = _utc(10, 10, 0)
        obs_repo = FakeObservationRepository()
        # ≥ recovery UP observations
        obs_repo.saved = [
            _obs(signal_key, _utc(10, 8, 30), Health.UP),
            _obs(signal_key, _utc(10, 9, 30), Health.UP),
        ]

        comp = Component(
            id=component_id,
            name="Checkout",
            status=ComponentStatus.OPERATIONAL,  # current_status = operational
            app_id="sockshop",
        )
        component_repo = FakeComponentRepository(components=[comp])
        maintenance_repo = FakeMaintenanceRepository()
        proposal_repo = FakeProposalRepository()
        # Pre-seed an open degradation proposal
        open_proposal = StatusProposal(
            component_id=component_id,
            from_status=ComponentStatus.OPERATIONAL,
            to_status=ComponentStatus.DEGRADED,
            state=ProposalState.OPEN,
            proposed_at=_utc(10, 5, 0),
        )
        proposal_repo.create_open(open_proposal)

        publisher = RecordingStatusPublisher()
        clock = FakeClock(now)
        decide_service = DecideService(proposal_repo=proposal_repo, publisher=publisher)

        action = orchestrate_signal(
            signal_key=signal_key,
            config=cfg,
            observation_repo=obs_repo,
            maintenance_repo=maintenance_repo,
            component_repo=component_repo,
            decide_service=decide_service,
            clock=clock,
        )

        assert action == DecideAction.OBSOLETED
        # Nothing published (§12 — outage was never shown)
        assert publisher.published == []

    def test_worse_degradation_supersedes_lesser_open_proposal(self):
        """A MAJOR streak while DEGRADED proposal is open → SUPERSEDED."""
        from fakes import (
            FakeClock,
            FakeComponentRepository,
            FakeMaintenanceRepository,
            FakeObservationRepository,
            FakeProposalRepository,
            RecordingStatusPublisher,
        )
        from src.composition.orchestrate import orchestrate_signal
        from src.core.domain.proposal import StatusProposal

        signal_key = "checkout-http"
        component_id = "checkout"
        # major=3 → major_outage proposed after ≥3 DOWN
        cfg = _build_config(
            signal_key=signal_key,
            component_id=component_id,
            major=3,
            partial=2,
            degraded=2,
        )

        now = _utc(10, 10, 0)
        obs_repo = FakeObservationRepository()
        # 3 DOWN observations in 3 consecutive cycles → streak=3 ≥ major=3
        obs_repo.saved = [
            _obs(signal_key, _utc(10, 7, 30), Health.DOWN),
            _obs(signal_key, _utc(10, 8, 30), Health.DOWN),
            _obs(signal_key, _utc(10, 9, 30), Health.DOWN),
        ]

        comp = Component(
            id=component_id,
            name="Checkout",
            status=ComponentStatus.OPERATIONAL,
            app_id="sockshop",
        )
        component_repo = FakeComponentRepository(components=[comp])
        maintenance_repo = FakeMaintenanceRepository()
        proposal_repo = FakeProposalRepository()
        # Pre-seed an open DEGRADED proposal (lesser severity)
        lesser_proposal = StatusProposal(
            component_id=component_id,
            from_status=ComponentStatus.OPERATIONAL,
            to_status=ComponentStatus.DEGRADED,
            state=ProposalState.OPEN,
            proposed_at=_utc(10, 5, 0),
        )
        proposal_repo.create_open(lesser_proposal)

        publisher = RecordingStatusPublisher()
        clock = FakeClock(now)
        decide_service = DecideService(proposal_repo=proposal_repo, publisher=publisher)

        action = orchestrate_signal(
            signal_key=signal_key,
            config=cfg,
            observation_repo=obs_repo,
            maintenance_repo=maintenance_repo,
            component_repo=component_repo,
            decide_service=decide_service,
            clock=clock,
        )

        assert action == DecideAction.SUPERSEDED
        # The new open proposal is for MAJOR_OUTAGE
        open_proposals = proposal_repo.list_open()
        assert len(open_proposals) == 1
        assert open_proposals[0].to_status == ComponentStatus.MAJOR_OUTAGE

    def test_maintenance_cycle_excluded_does_not_drive_degradation(self):
        """A cycle under maintenance is excluded; doesn't by itself drive degradation."""
        from fakes import (
            FakeClock,
            FakeComponentRepository,
            FakeMaintenanceRepository,
            FakeObservationRepository,
            FakeProposalRepository,
            RecordingStatusPublisher,
        )
        from src.composition.orchestrate import orchestrate_signal
        from src.core.domain.maintenance import MaintenanceWindow

        signal_key = "checkout-http"
        component_id = "checkout"
        cfg = _build_config(
            signal_key=signal_key, component_id=component_id, major=2, degraded=2
        )

        now = _utc(10, 4, 0)
        obs_repo = FakeObservationRepository()
        # 2 DOWN observations — but they land in maintenance windows
        obs_repo.saved = [
            _obs(signal_key, _utc(10, 2, 30), Health.DOWN),
            _obs(signal_key, _utc(10, 3, 30), Health.DOWN),
        ]

        comp = Component(
            id=component_id,
            name="Checkout",
            status=ComponentStatus.OPERATIONAL,
            app_id="sockshop",
        )
        component_repo = FakeComponentRepository(components=[comp])

        # Maintenance window covers both cycles (10:02:00-10:04:00)
        maintenance_repo = FakeMaintenanceRepository(
            windows=[
                MaintenanceWindow(
                    component_id=component_id,
                    starts_at=_utc(10, 1, 0),
                    ends_at=_utc(10, 5, 0),
                )
            ]
        )
        proposal_repo = FakeProposalRepository()
        publisher = RecordingStatusPublisher()
        clock = FakeClock(now)
        decide_service = DecideService(proposal_repo=proposal_repo, publisher=publisher)

        action = orchestrate_signal(
            signal_key=signal_key,
            config=cfg,
            observation_repo=obs_repo,
            maintenance_repo=maintenance_repo,
            component_repo=component_repo,
            decide_service=decide_service,
            clock=clock,
        )

        # Maintenance verdicts are excluded from streak → streak returns None → NOOP
        assert action == DecideAction.NOOP
        assert proposal_repo.list_open() == []


# ---------------------------------------------------------------------------
# Phase B4 — AC3: commit-first / best-effort (raising publisher)
# ---------------------------------------------------------------------------


class TestOrchestrateSignalAC3:
    """AC3: a raising publisher doesn't crash the cycle or roll back the proposal."""

    def test_raising_publisher_on_recovery_does_not_crash_cycle(self, caplog):
        """AC3 / T1.1: the recovery-publish path is the one that calls the
        publisher. With a `BestEffortPublisher`-wrapped raising delegate, a dead
        Statuspage is LOGGED and SWALLOWED — `orchestrate_signal` returns
        `PUBLISHED_RECOVERY` without crashing the cycle."""
        import logging

        from fakes import (
            FakeClock,
            FakeComponentRepository,
            FakeMaintenanceRepository,
            FakeObservationRepository,
            FakeProposalRepository,
        )
        from src.composition.orchestrate import orchestrate_signal
        from src.composition.publish_helper import BestEffortPublisher
        from src.core.ports import StatusPublisherPort

        class RaisingPublisher(StatusPublisherPort):
            """Always raises — simulates a dead Statuspage."""

            def publish(self, change):
                raise RuntimeError("simulated statuspage failure")

        signal_key = "checkout-http"
        component_id = "checkout"
        # recovery=2: two sustained UP cycles propose OPERATIONAL, which is BETTER
        # than the component's current DEGRADED status -> the publish branch fires.
        cfg = _build_config(
            signal_key=signal_key, component_id=component_id, recovery=2
        )

        now = _utc(10, 10, 0)
        obs_repo = FakeObservationRepository()
        obs_repo.saved = [
            _obs(signal_key, _utc(10, 8, 30), Health.UP),
            _obs(signal_key, _utc(10, 9, 30), Health.UP),
        ]
        comp = Component(
            id=component_id,
            name="Checkout",
            status=ComponentStatus.DEGRADED,  # currently degraded -> recovery improves it
            app_id="sockshop",
        )
        component_repo = FakeComponentRepository(components=[comp])
        maintenance_repo = FakeMaintenanceRepository()
        proposal_repo = FakeProposalRepository()
        clock = FakeClock(now)

        # The orchestration's DecideService is wired with a BEST-EFFORT publisher
        # (T1.1): a publish failure is logged, not raised.
        decide_service = DecideService(
            proposal_repo=proposal_repo,
            publisher=BestEffortPublisher(RaisingPublisher()),
        )

        with caplog.at_level(logging.ERROR):
            action = orchestrate_signal(
                signal_key=signal_key,
                config=cfg,
                observation_repo=obs_repo,
                maintenance_repo=maintenance_repo,
                component_repo=component_repo,
                decide_service=decide_service,
                clock=clock,
            )

        # The cycle did NOT crash, and decide reached the publish branch.
        assert action == DecideAction.PUBLISHED_RECOVERY
        # The Statuspage failure was logged best-effort, not raised.
        assert any(
            "Failed to publish status change" in rec.message for rec in caplog.records
        )


# ---------------------------------------------------------------------------
# Edge: unseeded component (component_repo.get returns None) → NOOP
# ---------------------------------------------------------------------------


def test_orchestrate_signal_noop_when_component_not_found():
    """When component_repo.get returns None (unseeded component), return NOOP.

    The orchestrator skips decide when there's no component to compare status
    against — plan.md step 5: 'if current is None → skip with a clear log / NOOP'.
    """
    from fakes import (
        FakeClock,
        FakeComponentRepository,
        FakeMaintenanceRepository,
        FakeObservationRepository,
        FakeProposalRepository,
        RecordingStatusPublisher,
    )
    from src.composition.orchestrate import orchestrate_signal

    signal_key = "checkout-http"
    component_id = "checkout"
    cfg = _build_config(signal_key=signal_key, component_id=component_id, major=2)

    now = _utc(10, 4, 0)
    obs_repo = FakeObservationRepository()
    obs_repo.saved = [
        _obs(signal_key, _utc(10, 2, 30), Health.DOWN),
        _obs(signal_key, _utc(10, 3, 30), Health.DOWN),
    ]

    # Empty component repo → get returns None
    component_repo = FakeComponentRepository(components=[])
    maintenance_repo = FakeMaintenanceRepository()
    proposal_repo = FakeProposalRepository()
    publisher = RecordingStatusPublisher()
    clock = FakeClock(now)
    decide_service = DecideService(proposal_repo=proposal_repo, publisher=publisher)

    action = orchestrate_signal(
        signal_key=signal_key,
        config=cfg,
        observation_repo=obs_repo,
        maintenance_repo=maintenance_repo,
        component_repo=component_repo,
        decide_service=decide_service,
        clock=clock,
    )

    assert action == DecideAction.NOOP
    assert proposal_repo.list_open() == []


# ---------------------------------------------------------------------------
# STORY-045 AC5 — end-to-end regression: degrade → approve → recover
# ---------------------------------------------------------------------------


def test_degrade_approve_recover_end_to_end():
    """AC5: the previously-unreachable recovery branch is now reachable.

    Before STORY-045, `components.status` was never written after seeding, so
    `decide`'s current_status was frozen at OPERATIONAL and a recovery could
    never fire (nothing is better than operational). This drives the full loop
    through fakes only, sharing ONE publisher chain (StatusWritebackPublisher(
    RecordingPublisher(statuspage_stand_in), component_repo)) between
    `DecideService` (the recovery trigger) and `ApprovalService` (the approve
    trigger) — exactly as both composition roots do in production (D2):

      1. Cycle 1 — sustained DOWN: a degradation proposal opens; nothing is
         published; components.status is untouched.
      2. Approve — the operator approves: publish observed + a publications
         row recorded + components.status now DEGRADED.
      3. Cycle 2 — sustained UP: decide reads current_status=DEGRADED (written
         back at step 2), so the UP streak is a RECOVERY — PUBLISHED_RECOVERY —
         and components.status returns to OPERATIONAL.
    """
    from fakes import (
        FakeClock,
        FakeComponentRepository,
        FakeMaintenanceRepository,
        FakeObservationRepository,
        FakeProposalRepository,
        FakePublicationRepository,
        RecordingStatusPublisher,
    )

    signal_key = "checkout-http"
    component_id = "checkout"
    # major=5, partial=4, degraded=2, recovery=2: 2 consecutive DOWN cycles
    # clears `degraded` but neither `partial` nor `major` — a plain DEGRADED
    # proposal (not the MAJOR_OUTAGE the other AC1 tests exercise).
    cfg = _build_config(
        signal_key=signal_key,
        component_id=component_id,
        major=5,
        partial=4,
        degraded=2,
        recovery=2,
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
    publication_repo = FakePublicationRepository()

    # ONE shared chain — the D2 shape, built from fakes standing in for the
    # DB (component/publication repos) and the Statuspage HTTP edge.
    publish_clock = FakeClock(_utc(9, day=24))
    statuspage_stand_in = RecordingStatusPublisher()
    publisher = StatusWritebackPublisher(
        RecordingPublisher(statuspage_stand_in, publication_repo, publish_clock),
        component_repo,
    )

    decide_service = DecideService(proposal_repo=proposal_repo, publisher=publisher)
    approval_service = ApprovalService(
        proposal_repo=proposal_repo, clock=publish_clock, publisher=publisher
    )

    # --- Cycle 1: sustained DOWN -> degradation proposal opened, nothing
    # published, status unchanged. ---
    obs_repo_1 = FakeObservationRepository()
    obs_repo_1.saved = [
        _obs(signal_key, _utc(10, 2, 30), Health.DOWN),
        _obs(signal_key, _utc(10, 3, 30), Health.DOWN),
    ]
    clock_1 = FakeClock(_utc(10, 4, 0))

    action_1 = orchestrate_signal(
        signal_key=signal_key,
        config=cfg,
        observation_repo=obs_repo_1,
        maintenance_repo=maintenance_repo,
        component_repo=component_repo,
        decide_service=decide_service,
        clock=clock_1,
    )

    assert action_1 == DecideAction.PROPOSED
    assert statuspage_stand_in.published == []
    assert publication_repo.list_recent() == []
    assert component_repo.get(component_id).status == ComponentStatus.OPERATIONAL

    open_proposals = proposal_repo.list_open()
    assert len(open_proposals) == 1
    proposal = open_proposals[0]
    assert proposal.to_status == ComponentStatus.DEGRADED

    # --- Approve: publish observed + publications row recorded + status now
    # DEGRADED (AC1/AC2 approve trigger). ---
    approval_service.approve(
        proposal_id=proposal.id, actor="ops-1", notes="confirmed outage"
    )

    assert statuspage_stand_in.published == [
        StatusChange(component_id=component_id, status=ComponentStatus.DEGRADED)
    ]
    pubs = publication_repo.list_recent()
    assert len(pubs) == 1
    assert pubs[0].component_id == component_id
    assert pubs[0].status == ComponentStatus.DEGRADED
    assert component_repo.get(component_id).status == ComponentStatus.DEGRADED

    # --- Cycle 2: sustained UP while current_status=DEGRADED -> the
    # previously-unreachable recovery branch fires (AC5). ---
    obs_repo_2 = FakeObservationRepository()
    obs_repo_2.saved = [
        _obs(signal_key, _utc(10, 18, 30), Health.UP),
        _obs(signal_key, _utc(10, 19, 30), Health.UP),
    ]
    clock_2 = FakeClock(_utc(10, 20, 0))

    action_2 = orchestrate_signal(
        signal_key=signal_key,
        config=cfg,
        observation_repo=obs_repo_2,
        maintenance_repo=maintenance_repo,
        component_repo=component_repo,
        decide_service=decide_service,
        clock=clock_2,
    )

    assert action_2 == DecideAction.PUBLISHED_RECOVERY
    assert statuspage_stand_in.published[-1] == StatusChange(
        component_id=component_id, status=ComponentStatus.OPERATIONAL
    )
    assert len(publication_repo.list_recent()) == 2
    assert component_repo.get(component_id).status == ComponentStatus.OPERATIONAL
