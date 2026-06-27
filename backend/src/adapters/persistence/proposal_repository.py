"""Postgres-backed `ProposalRepository` (dossier §12, §9)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine

from src.core.domain.proposal import ProposalState, StatusProposal
from src.core.domain.status import ComponentStatus
from src.core.ports.proposal_repository import ProposalRepository

logger = logging.getLogger(__name__)

_STATUS_PROPOSALS = sa.table(
    "status_proposals",
    sa.column("id"),
    sa.column("component_id"),
    sa.column("from_status"),
    sa.column("to_status"),
    sa.column("state"),
    sa.column("reason"),
    sa.column("proposed_at"),
    sa.column("resolved_at"),
)

_APPROVAL_EVENTS = sa.table(
    "approval_events",
    sa.column("id"),
    sa.column("proposal_id"),
    sa.column("actor"),
    sa.column("action"),
    sa.column("notes"),
    sa.column("occurred_at"),
)


class PostgresProposalRepository(ProposalRepository):
    """Concrete Postgres adapter for managing status proposals and events (dossier §12)."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_open(self, proposal: StatusProposal) -> StatusProposal | None:
        """Persist a new open status proposal using ON CONFLICT DO NOTHING.

        If a conflict on uq_status_proposals_active_component occurs, returns None
        and logs a debug line.
        """
        stmt = (
            pg_insert(_STATUS_PROPOSALS)
            .values(
                {
                    "component_id": proposal.component_id,
                    "from_status": proposal.from_status.value
                    if proposal.from_status is not None
                    else None,
                    "to_status": proposal.to_status.value,
                    "state": proposal.state.value,
                    "reason": proposal.reason,
                    "proposed_at": proposal.proposed_at,
                    "resolved_at": proposal.resolved_at,
                }
            )
            .on_conflict_do_nothing(
                index_elements=["component_id"],
                index_where=sa.text("state = 'open'"),
            )
            .returning(_STATUS_PROPOSALS.c.id)
        )

        with self._engine.begin() as conn:
            result = conn.execute(stmt)
            row = result.fetchone()
            if row is None:
                logger.debug(
                    "Open proposal already exists for component %s. Skipping insert.",
                    proposal.component_id,
                )
                return None
            assigned_id = row[0]

        return proposal.model_copy(update={"id": assigned_id})

    def get_open(self, component_id: str) -> StatusProposal | None:
        """Retrieve the open status proposal for a component, if any."""
        stmt = sa.select(
            _STATUS_PROPOSALS.c.id,
            _STATUS_PROPOSALS.c.component_id,
            _STATUS_PROPOSALS.c.from_status,
            _STATUS_PROPOSALS.c.to_status,
            _STATUS_PROPOSALS.c.state,
            _STATUS_PROPOSALS.c.reason,
            _STATUS_PROPOSALS.c.proposed_at,
            _STATUS_PROPOSALS.c.resolved_at,
        ).where(
            _STATUS_PROPOSALS.c.component_id == component_id,
            _STATUS_PROPOSALS.c.state == ProposalState.OPEN.value,
        )

        with self._engine.connect() as conn:
            row = conn.execute(stmt).fetchone()

        if row is None:
            return None

        # Reconstruct ComponentStatus enums
        from_status = (
            ComponentStatus(row.from_status) if row.from_status is not None else None
        )
        to_status = ComponentStatus(row.to_status)

        return StatusProposal(
            id=row.id,
            component_id=row.component_id,
            from_status=from_status,
            to_status=to_status,
            state=ProposalState(row.state),
            reason=row.reason,
            proposed_at=row.proposed_at.astimezone(timezone.utc),
            resolved_at=(
                row.resolved_at.astimezone(timezone.utc)
                if row.resolved_at is not None
                else None
            ),
        )

    def resolve(
        self,
        proposal_id: int,
        *,
        to_state: ProposalState,
        reason: str | None,
        resolved_at: datetime,
    ) -> None:
        """Move an open status proposal to a terminal state."""
        stmt = (
            sa.update(_STATUS_PROPOSALS)
            .where(
                _STATUS_PROPOSALS.c.id == proposal_id,
                _STATUS_PROPOSALS.c.state == ProposalState.OPEN.value,
            )
            .values(
                state=to_state.value,
                reason=reason,
                resolved_at=resolved_at,
            )
        )
        with self._engine.begin() as conn:
            result = conn.execute(stmt)
            if result.rowcount != 1:
                raise ValueError(
                    f"Proposal {proposal_id} not found or not in open state."
                )

    def record_approval_event(
        self,
        proposal_id: int,
        *,
        actor: str,
        action: str,
        notes: str | None,
        occurred_at: datetime,
    ) -> None:
        """Record an approval or rejection event for a proposal."""
        stmt = sa.insert(_APPROVAL_EVENTS).values(
            proposal_id=proposal_id,
            actor=actor,
            action=action,
            notes=notes,
            occurred_at=occurred_at,
        )
        with self._engine.begin() as conn:
            conn.execute(stmt)
