"""Postgres-backed `ProposalRepository` (dossier §12, §9)."""

import logging
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine
import sqlalchemy as sa

from src.core.domain.proposal import ProposalState, StatusProposal
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
                    "from_status": proposal.from_status.value if proposal.from_status else None,
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
        raise NotImplementedError

    def resolve(
        self,
        proposal_id: int,
        *,
        to_state: ProposalState,
        reason: str | None,
        resolved_at: datetime,
    ) -> None:
        raise NotImplementedError

    def record_approval_event(
        self,
        proposal_id: int,
        *,
        actor: str,
        action: str,
        notes: str | None,
        occurred_at: datetime,
    ) -> None:
        raise NotImplementedError
