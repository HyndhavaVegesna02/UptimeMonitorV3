import pytest
from datetime import datetime, timezone
from src.core.domain import ComponentStatus, StatusChange
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
