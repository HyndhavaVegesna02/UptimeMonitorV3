"""Service layer for approvals (api/v1/approvals feature).

Cites dossier §13, §17.
"""

from fastapi import Depends

from src.api.dependencies import get_proposal_repo
from src.api.v1.approvals.models import ProposalDTO
from src.core.ports import ProposalRepository


class ApprovalsService:
    """Service handling retrieval and formatting of open status proposals."""

    def __init__(self, proposal_repo: ProposalRepository) -> None:
        self._proposal_repo = proposal_repo

    def get_open_proposals(self) -> list[ProposalDTO]:
        """Fetch all open proposals and map them to DTOs."""
        proposals = self._proposal_repo.list_open()
        return [
            ProposalDTO(
                id=p.id if p.id is not None else 0,
                component_id=p.component_id,
                from_status=p.from_status.value if p.from_status is not None else None,
                to_status=p.to_status.value,
                state=p.state.value,
                proposed_at=p.proposed_at,
            )
            for p in proposals
        ]


def get_approvals_service(
    proposal_repo: ProposalRepository = Depends(get_proposal_repo),
) -> ApprovalsService:
    """Dependency provider for ApprovalsService."""
    return ApprovalsService(proposal_repo)
