"""HTTP controller for decisions (api/v1/decisions zone).

Cites dossier §13.
"""

from fastapi import APIRouter, Depends
from src.api.dependencies import get_approval_service
from src.api.v1.decisions.models import DecisionRequest, DecisionResponse
from src.api.v1.decisions.service import DecisionService
from src.core.services.approval import ApprovalService

router = APIRouter()


def get_decision_service(
    approval_service: ApprovalService = Depends(get_approval_service),
) -> DecisionService:
    """Dependency to instantiate the DecisionService."""
    return DecisionService(approval_service)


@router.post(
    "/decisions/{proposal_id}",
    response_model=DecisionResponse,
    status_code=200,
)
def create_decision(
    proposal_id: int,
    request: DecisionRequest,
    service: DecisionService = Depends(get_decision_service),
) -> DecisionResponse:
    """Record a decision (approve or reject) for a status proposal."""
    return service.record_decision(proposal_id, request)
