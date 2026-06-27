import pytest
from datetime import datetime, timezone
from src.core.domain import ComponentStatus, StatusChange, ProposalState, StatusProposal
from src.core.services.decide import DecideAction, DecideService
from tests.fakes import FakeProposalRepository, RecordingStatusPublisher


def test_decide_action_enum():
    assert DecideAction.NOOP == "noop"
    assert DecideAction.PROPOSED == "proposed"
    assert DecideAction.SUPERSEDED == "superseded"
    assert DecideAction.OBSOLETED == "obsoleted"
    assert DecideAction.PUBLISHED_RECOVERY == "published_recovery"


def test_decide_noop_when_proposed_equals_current_and_no_open_proposal():
    proposal_repo = FakeProposalRepository()
    publisher = RecordingStatusPublisher()
    service = DecideService(proposal_repo=proposal_repo, publisher=publisher)

    now = datetime(2026, 6, 27, 12, 0, 0, tzinfo=timezone.utc)
    result = service.decide(
        component_id="checkout",
        proposed_status=ComponentStatus.OPERATIONAL,
        current_status=ComponentStatus.OPERATIONAL,
        now=now,
    )

    assert result == DecideAction.NOOP
    assert len(publisher.published) == 0
    assert len(proposal_repo.proposals) == 0


def test_decide_worse_no_open_proposal_creates_proposal_and_returns_proposed():
    proposal_repo = FakeProposalRepository()
    publisher = RecordingStatusPublisher()
    service = DecideService(proposal_repo=proposal_repo, publisher=publisher)

    now = datetime(2026, 6, 27, 12, 0, 0, tzinfo=timezone.utc)
    result = service.decide(
        component_id="checkout",
        proposed_status=ComponentStatus.MAJOR_OUTAGE,
        current_status=ComponentStatus.OPERATIONAL,
        now=now,
    )

    assert result == DecideAction.PROPOSED
    assert len(publisher.published) == 0
    assert len(proposal_repo.proposals) == 1

    prop = list(proposal_repo.proposals.values())[0]
    assert prop.component_id == "checkout"
    assert prop.from_status == ComponentStatus.OPERATIONAL
    assert prop.to_status == ComponentStatus.MAJOR_OUTAGE
    assert prop.state == ProposalState.OPEN
    assert prop.proposed_at == now
    assert prop.resolved_at is None


def test_decide_worse_open_proposal_exists_supersede_and_create():
    proposal_repo = FakeProposalRepository()
    publisher = RecordingStatusPublisher()
    service = DecideService(proposal_repo=proposal_repo, publisher=publisher)

    now = datetime(2026, 6, 27, 12, 0, 0, tzinfo=timezone.utc)
    # pre-create degraded open proposal
    open_prop = StatusProposal(
        component_id="checkout",
        from_status=ComponentStatus.OPERATIONAL,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=now,
    )
    open_prop = proposal_repo.create_open(open_prop)

    later = datetime(2026, 6, 27, 12, 5, 0, tzinfo=timezone.utc)
    result = service.decide(
        component_id="checkout",
        proposed_status=ComponentStatus.MAJOR_OUTAGE,
        current_status=ComponentStatus.OPERATIONAL,
        now=later,
        reason="Super-outage",
    )

    assert result == DecideAction.SUPERSEDED
    assert len(publisher.published) == 0
    # There should be 2 total proposals in repo (one superseded, one open)
    assert len(proposal_repo.proposals) == 2

    # Check superseded proposal
    old_prop = proposal_repo.proposals[open_prop.id]
    assert old_prop.state == ProposalState.SUPERSEDED
    assert old_prop.resolved_at == later
    assert old_prop.reason == "Super-outage"

    # Check new open proposal
    new_prop = proposal_repo.get_open("checkout")
    assert new_prop is not None
    assert new_prop.id != open_prop.id
    assert new_prop.from_status == ComponentStatus.OPERATIONAL
    assert new_prop.to_status == ComponentStatus.MAJOR_OUTAGE
    assert new_prop.state == ProposalState.OPEN
    assert new_prop.proposed_at == later
    assert new_prop.resolved_at is None


def test_decide_worse_open_proposal_exists_leave_when_equal():
    proposal_repo = FakeProposalRepository()
    publisher = RecordingStatusPublisher()
    service = DecideService(proposal_repo=proposal_repo, publisher=publisher)

    now = datetime(2026, 6, 27, 12, 0, 0, tzinfo=timezone.utc)
    # pre-create major_outage open proposal
    open_prop = StatusProposal(
        component_id="checkout",
        from_status=ComponentStatus.OPERATIONAL,
        to_status=ComponentStatus.MAJOR_OUTAGE,
        state=ProposalState.OPEN,
        proposed_at=now,
    )
    open_prop = proposal_repo.create_open(open_prop)

    later = datetime(2026, 6, 27, 12, 5, 0, tzinfo=timezone.utc)
    result = service.decide(
        component_id="checkout",
        proposed_status=ComponentStatus.MAJOR_OUTAGE,
        current_status=ComponentStatus.OPERATIONAL,
        now=later,
        reason="Still major",
    )

    assert result == DecideAction.NOOP
    assert len(publisher.published) == 0
    assert len(proposal_repo.proposals) == 1

    current_prop = proposal_repo.get_open("checkout")
    assert current_prop is not None
    assert current_prop.id == open_prop.id
    assert current_prop.to_status == ComponentStatus.MAJOR_OUTAGE
    assert current_prop.state == ProposalState.OPEN
    assert current_prop.resolved_at is None


def test_decide_recovery_no_open_proposal_publishes_recovery():
    proposal_repo = FakeProposalRepository()
    publisher = RecordingStatusPublisher()
    service = DecideService(proposal_repo=proposal_repo, publisher=publisher)

    now = datetime(2026, 6, 27, 12, 0, 0, tzinfo=timezone.utc)
    result = service.decide(
        component_id="checkout",
        proposed_status=ComponentStatus.OPERATIONAL,
        current_status=ComponentStatus.MAJOR_OUTAGE,
        now=now,
    )

    assert result == DecideAction.PUBLISHED_RECOVERY
    assert len(proposal_repo.proposals) == 0
    assert len(publisher.published) == 1
    assert publisher.published[0] == StatusChange(
        component_id="checkout", status=ComponentStatus.OPERATIONAL
    )


def test_decide_recovery_open_proposal_exists_obsoletes_and_nothing_published():
    proposal_repo = FakeProposalRepository()
    publisher = RecordingStatusPublisher()
    service = DecideService(proposal_repo=proposal_repo, publisher=publisher)

    now = datetime(2026, 6, 27, 12, 0, 0, tzinfo=timezone.utc)
    # pre-create open proposal (major outage)
    open_prop = StatusProposal(
        component_id="checkout",
        from_status=ComponentStatus.OPERATIONAL,
        to_status=ComponentStatus.MAJOR_OUTAGE,
        state=ProposalState.OPEN,
        proposed_at=now,
    )
    open_prop = proposal_repo.create_open(open_prop)

    later = datetime(2026, 6, 27, 12, 5, 0, tzinfo=timezone.utc)
    result = service.decide(
        component_id="checkout",
        proposed_status=ComponentStatus.OPERATIONAL,
        current_status=ComponentStatus.OPERATIONAL,
        now=later,
        reason="Recovered before approval",
    )

    assert result == DecideAction.OBSOLETED
    assert len(publisher.published) == 0
    assert len(proposal_repo.proposals) == 1

    resolved = proposal_repo.proposals[open_prop.id]
    assert resolved.state == ProposalState.OBSOLETED
    assert resolved.resolved_at == later
    assert resolved.reason == "Recovered before approval"



