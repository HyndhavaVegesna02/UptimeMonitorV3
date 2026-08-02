from __future__ import annotations

from datetime import datetime, timezone

import pytest
from src.adapters.persistence.dynamo_proposal_repository import DynamoProposalRepository
from src.composition.settings import load_settings
from src.core.domain.proposal import (
    ProposalNotOpenError,
    ProposalState,
    StatusProposal,
)
from src.core.domain.status import ComponentStatus


def test_dynamo_proposal_repository_create_open_enforces_one_open_per_component(
    dynamo_resource,
):
    settings = load_settings()
    repo = DynamoProposalRepository(dynamo_resource, settings.dynamo_control_table)

    prop1 = StatusProposal(
        component_id="checkout-comp",
        from_status=None,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
    )

    # First succeeds
    saved1 = repo.create_open(prop1)
    assert saved1 is not None
    assert saved1.id is not None
    assert saved1.state == ProposalState.OPEN

    # Second open proposal for same component returns None
    prop2 = StatusProposal(
        component_id="checkout-comp",
        from_status=ComponentStatus.DEGRADED,
        to_status=ComponentStatus.MAJOR_OUTAGE,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 26, 12, 1, 0, tzinfo=timezone.utc),
    )
    saved2 = repo.create_open(prop2)
    assert saved2 is None

    # Different component succeeds
    prop3 = StatusProposal(
        component_id="other-comp",
        from_status=None,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 26, 12, 2, 0, tzinfo=timezone.utc),
    )
    saved3 = repo.create_open(prop3)
    assert saved3 is not None
    assert saved3.id > saved1.id


def test_dynamo_proposal_repository_counter_ids(dynamo_resource):
    settings = load_settings()
    repo = DynamoProposalRepository(dynamo_resource, settings.dynamo_control_table)

    ids = []
    for i in range(5):
        prop = StatusProposal(
            component_id=f"comp-{i}",
            from_status=None,
            to_status=ComponentStatus.DEGRADED,
            state=ProposalState.OPEN,
            proposed_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
        )
        saved = repo.create_open(prop)
        assert saved is not None
        ids.append(saved.id)

    # IDs must be strictly increasing and unique
    assert ids == sorted(ids)
    assert len(set(ids)) == 5


def test_dynamo_proposal_repository_get_open_and_get_and_list_open(dynamo_resource):
    settings = load_settings()
    repo = DynamoProposalRepository(dynamo_resource, settings.dynamo_control_table)

    assert repo.get_open("comp-x") is None
    assert repo.get(9999) is None
    assert repo.list_open() == []

    prop = StatusProposal(
        component_id="comp-x",
        from_status=ComponentStatus.OPERATIONAL,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
        reason="Test reason",
    )
    saved = repo.create_open(prop)
    assert saved is not None

    # Test get_open
    fetched_open = repo.get_open("comp-x")
    assert fetched_open is not None
    assert fetched_open.id == saved.id
    assert fetched_open.component_id == "comp-x"
    assert fetched_open.from_status == ComponentStatus.OPERATIONAL
    assert fetched_open.to_status == ComponentStatus.DEGRADED
    assert fetched_open.state == ProposalState.OPEN
    assert fetched_open.reason == "Test reason"
    assert fetched_open.proposed_at == datetime(
        2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc
    )
    assert fetched_open.resolved_at is None

    # Test get (META)
    fetched_meta = repo.get(saved.id)
    assert fetched_meta == fetched_open

    # Test list_open
    open_list = repo.list_open()
    assert len(open_list) == 1
    assert open_list[0] == fetched_open


def test_dynamo_proposal_repository_list_open_paginates(dynamo_resource):
    """STORY-199 AC2: forcing a small page size must not truncate list_open
    against proposal_repository.py's 'retrieve all OPEN status proposals'
    contract."""
    settings = load_settings()
    repo = DynamoProposalRepository(dynamo_resource, settings.dynamo_control_table)

    saved_ids = []
    for i in range(10):
        prop = StatusProposal(
            component_id=f"comp-page-{i}",
            from_status=None,
            to_status=ComponentStatus.DEGRADED,
            state=ProposalState.OPEN,
            proposed_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
        )
        saved = repo.create_open(prop)
        assert saved is not None
        saved_ids.append(saved.id)

    repo._limit = 2

    open_proposals = repo.list_open()
    assert {p.id for p in open_proposals} == set(saved_ids)


def test_dynamo_proposal_repository_resolve_guard_and_atomicity(dynamo_resource):
    settings = load_settings()
    repo = DynamoProposalRepository(dynamo_resource, settings.dynamo_control_table)

    prop = StatusProposal(
        component_id="comp-resolve",
        from_status=None,
        to_status=ComponentStatus.MAJOR_OUTAGE,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
    )
    saved = repo.create_open(prop)
    assert saved is not None

    resolved_time = datetime(2026, 6, 26, 12, 10, 0, tzinfo=timezone.utc)
    repo.resolve(
        saved.id,
        to_state=ProposalState.APPROVED,
        reason="Incident verified",
        resolved_at=resolved_time,
    )

    # get_open returns None (slot delete)
    assert repo.get_open("comp-resolve") is None
    # list_open is empty (GSI removal)
    assert repo.list_open() == []

    # get returns updated META
    resolved_prop = repo.get(saved.id)
    assert resolved_prop is not None
    assert resolved_prop.state == ProposalState.APPROVED
    assert resolved_prop.reason == "Incident verified"
    assert resolved_prop.resolved_at == resolved_time

    # Resolve again raises ProposalNotOpenError
    with pytest.raises(ProposalNotOpenError):
        repo.resolve(
            saved.id,
            to_state=ProposalState.APPROVED,
            reason="Another try",
            resolved_at=resolved_time,
        )

    # Resolve missing id raises ProposalNotOpenError
    with pytest.raises(ProposalNotOpenError):
        repo.resolve(
            9999,
            to_state=ProposalState.APPROVED,
            reason="Missing",
            resolved_at=resolved_time,
        )


def test_dynamo_proposal_repository_record_approval_event(dynamo_resource):
    settings = load_settings()
    repo = DynamoProposalRepository(dynamo_resource, settings.dynamo_control_table)

    prop = StatusProposal(
        component_id="comp-event",
        from_status=None,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
    )
    saved = repo.create_open(prop)
    assert saved is not None

    occurred_time = datetime(2026, 6, 26, 12, 5, 0, tzinfo=timezone.utc)
    repo.record_approval_event(
        saved.id,
        actor="ops-admin",
        action="approved",
        notes="Checked dashboard, confirmed",
        occurred_at=occurred_time,
    )

    # Check event item in DB directly
    response = repo._table.get_item(
        Key={
            "pk": f"PROPOSAL#{saved.id}",
            "sk": "EVENT#2026-06-26T12:05:00.000000+00:00#approved",
        }
    )
    event_item = response.get("Item")
    assert event_item is not None
    assert event_item["proposal_id"] == saved.id
    assert event_item["actor"] == "ops-admin"
    assert event_item["action"] == "approved"
    assert event_item["notes"] == "Checked dashboard, confirmed"

    # approved_actor is denormalized onto META
    meta_item = repo._table.get_item(
        Key={"pk": f"PROPOSAL#{saved.id}", "sk": "META"}
    ).get("Item")
    assert meta_item.get("approved_actor") == "ops-admin"


def test_dynamo_proposal_repository_orphan_event_guard(dynamo_resource):
    from botocore.exceptions import ClientError

    settings = load_settings()
    repo = DynamoProposalRepository(dynamo_resource, settings.dynamo_control_table)

    missing_proposal_id = 99999
    occurred_time = datetime(2026, 6, 26, 12, 5, 0, tzinfo=timezone.utc)

    # 1. Recording an event (e.g. rejection) against a non-existent proposal must fail
    with pytest.raises(ClientError) as exc_info:
        repo.record_approval_event(
            missing_proposal_id,
            actor="ops-admin",
            action="rejected",
            notes="Should fail",
            occurred_at=occurred_time,
        )
    assert exc_info.value.response["Error"]["Code"] == "TransactionCanceledException"

    # Verify no event item was written
    response = repo._table.get_item(
        Key={
            "pk": f"PROPOSAL#{missing_proposal_id}",
            "sk": "EVENT#2026-06-26T12:05:00.000000+00:00#rejected",
        }
    )
    assert "Item" not in response

    # 2. Assert the happy path (event against a real proposal) still succeeds
    prop = StatusProposal(
        component_id="comp-happy",
        from_status=None,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
    )
    saved = repo.create_open(prop)
    assert saved is not None

    repo.record_approval_event(
        saved.id,
        actor="ops-admin",
        action="rejected",
        notes="Should succeed",
        occurred_at=occurred_time,
    )

    # Verify the event item exists for the real proposal
    response = repo._table.get_item(
        Key={
            "pk": f"PROPOSAL#{saved.id}",
            "sk": "EVENT#2026-06-26T12:05:00.000000+00:00#rejected",
        }
    )
    assert "Item" in response
    assert response["Item"]["notes"] == "Should succeed"
