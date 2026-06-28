"""Controller for approvals (api/v1/approvals feature).

Cites dossier §13, §17.
"""

from fastapi import APIRouter, Depends

from src.api.v1.approvals.models import ProposalDTO
from src.api.v1.approvals.service import (
    ApprovalsService,
    get_approvals_service,
)

router = APIRouter()


@router.get("/approvals", response_model=list[ProposalDTO])
def list_open_proposals(
    service: ApprovalsService = Depends(get_approvals_service),
) -> list[ProposalDTO]:
    """Retrieve all open status proposals."""
    return service.get_open_proposals()
