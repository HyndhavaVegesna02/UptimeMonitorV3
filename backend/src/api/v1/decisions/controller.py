"""HTTP controller for decisions (api/v1/decisions zone).

Cites dossier §13: routes and status codes only, no business logic. Imports only
this feature's models and service (the service owns the container wiring).
"""

from fastapi import APIRouter, Depends

from src.api.v1.decisions.models import DecisionRequest, DecisionResponse
from src.api.v1.decisions.service import DecisionService, get_decision_service

router = APIRouter()


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
