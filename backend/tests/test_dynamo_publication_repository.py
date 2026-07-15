from __future__ import annotations

from datetime import datetime, timezone

from src.adapters.persistence.dynamo_proposal_repository import DynamoProposalRepository
from src.adapters.persistence.dynamo_publication_repository import (
    DynamoPublicationRepository,
)
from src.composition.settings import load_settings
from src.core.domain.proposal import ProposalState, StatusProposal
from src.core.domain.publication import Publication, PublicationOutcome
from src.core.domain.status import ComponentStatus


def test_dynamo_publication_repository_record_and_list_recent(dynamo_resource):
    settings = load_settings()
    repo = DynamoPublicationRepository(dynamo_resource, settings.dynamo_control_table)

    pub1 = Publication(
        component_id="checkout-comp",
        status=ComponentStatus.DEGRADED,
        published_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
        outcome=PublicationOutcome.SUCCEEDED,
    )

    pub2 = Publication(
        component_id="checkout-comp",
        status=ComponentStatus.MAJOR_OUTAGE,
        published_at=datetime(2026, 6, 26, 12, 5, 0, tzinfo=timezone.utc),
        outcome=PublicationOutcome.FAILED,
    )

    # Record first (succeeded)
    saved1 = repo.record(pub1)
    assert saved1.id is not None
    assert saved1.outcome == PublicationOutcome.SUCCEEDED

    # Record second (failed)
    saved2 = repo.record(pub2)
    assert saved2.id is not None
    assert saved2.id > saved1.id
    assert saved2.outcome == PublicationOutcome.FAILED

    # List recent
    recent = repo.list_recent(limit=10)
    assert len(recent) == 2
    # descending order by published_at
    assert recent[0].id == saved2.id
    assert recent[0].outcome == PublicationOutcome.FAILED
    assert recent[1].id == saved1.id
    assert recent[1].outcome == PublicationOutcome.SUCCEEDED

    # Test limit cap
    recent_cap = repo.list_recent(limit=1)
    assert len(recent_cap) == 1
    assert recent_cap[0].id == saved2.id


def test_dynamo_publication_repository_author_parity(dynamo_resource):
    settings = load_settings()
    proposal_repo = DynamoProposalRepository(
        dynamo_resource, settings.dynamo_control_table
    )
    pub_repo = DynamoPublicationRepository(
        dynamo_resource, settings.dynamo_control_table
    )

    # 1. Proposal with approved approval event (author: alice)
    prop1 = StatusProposal(
        component_id="comp-1",
        from_status=None,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
    )
    saved_prop1 = proposal_repo.create_open(prop1)
    assert saved_prop1 is not None

    proposal_repo.record_approval_event(
        saved_prop1.id,
        actor="alice",
        action="approved",
        notes="Looks good",
        occurred_at=datetime(2026, 6, 26, 12, 2, 0, tzinfo=timezone.utc),
    )

    pub1 = Publication(
        component_id="comp-1",
        status=ComponentStatus.DEGRADED,
        published_at=datetime(2026, 6, 26, 12, 3, 0, tzinfo=timezone.utc),
        proposal_id=saved_prop1.id,
        outcome=PublicationOutcome.SUCCEEDED,
    )
    pub_repo.record(pub1)

    # 2. Publication without proposal_id (author should be None)
    pub2 = Publication(
        component_id="comp-2",
        status=ComponentStatus.OPERATIONAL,
        published_at=datetime(2026, 6, 26, 12, 4, 0, tzinfo=timezone.utc),
        proposal_id=None,
        outcome=PublicationOutcome.SUCCEEDED,
    )
    pub_repo.record(pub2)

    # 3. Proposal without approval (author should be None)
    prop3 = StatusProposal(
        component_id="comp-3",
        from_status=None,
        to_status=ComponentStatus.MAJOR_OUTAGE,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
    )
    saved_prop3 = proposal_repo.create_open(prop3)
    assert saved_prop3 is not None

    pub3 = Publication(
        component_id="comp-3",
        status=ComponentStatus.MAJOR_OUTAGE,
        published_at=datetime(2026, 6, 26, 12, 5, 0, tzinfo=timezone.utc),
        proposal_id=saved_prop3.id,
        outcome=PublicationOutcome.SUCCEEDED,
    )
    pub_repo.record(pub3)

    recent = pub_repo.list_recent(limit=10)
    assert len(recent) == 3

    # Order (descending by published_at): pub3 (comp-3), pub2 (comp-2), pub1 (comp-1)
    assert recent[0].component_id == "comp-3"
    assert recent[0].author is None

    assert recent[1].component_id == "comp-2"
    assert recent[1].author is None

    assert recent[2].component_id == "comp-1"
    assert recent[2].author == "alice"


def test_dynamo_publication_repository_empty(dynamo_resource):
    settings = load_settings()
    repo = DynamoPublicationRepository(dynamo_resource, settings.dynamo_control_table)
    assert repo.list_recent() == []
