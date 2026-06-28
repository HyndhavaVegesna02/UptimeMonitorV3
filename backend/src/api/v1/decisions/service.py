"""Thin edge service for decisions (api/v1/decisions zone).

Cites dossier §13: the edge service validates HTTP input, delegates to a core
service via the composition container, and shapes the HTTP result — it holds no
business logic and imports no other feature.
"""

from fastapi import Depends, HTTPException

from src.api.dependencies import get_approval_service
from src.api.v1.decisions.models import DecisionRequest, DecisionResponse
from src.api.v1.decisions.validation import (
    SyntacticValidationError,
    validate_decision_request,
)
from src.core.services.approval import (
    ApprovalService,
    ProposalNotFoundError,
    ProposalNotOpenError,
)


class DecisionService:
    """Thin edge service to handle decision requests."""

    def __init__(self, approval_service: ApprovalService) -> None:
        self._approval_service = approval_service

    def record_decision(
        self, proposal_id: int, request: DecisionRequest
    ) -> DecisionResponse:
        """Validate, delegate to ApprovalService, and shape the HTTP response."""
        # 1. Syntactic validation
        try:
            validate_decision_request(action=request.action, actor=request.actor)
        except SyntacticValidationError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e

        # 2. Delegate to ApprovalService & map domain errors
        try:
            if request.action == "approve":
                result = self._approval_service.approve(
                    proposal_id=proposal_id,
                    actor=request.actor,
                    notes=request.notes,
                )
            else:
                result = self._approval_service.reject(
                    proposal_id=proposal_id,
                    actor=request.actor,
                    notes=request.notes,
                )
        except ProposalNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        except ProposalNotOpenError as e:
            # Covers both the up-front guard and a lost-race resolve (concurrent
            # double-submit) surfaced by the repository — both map to 409.
            raise HTTPException(status_code=409, detail=str(e)) from e

        # 3. Shape the HTTP result (result is the persisted proposal, id present)
        return DecisionResponse(
            proposal_id=result.id,
            state=result.state.value,
            resolved_at=result.resolved_at,
        )


def get_decision_service(
    approval_service: ApprovalService = Depends(get_approval_service),
) -> DecisionService:
    """Provide a DecisionService wired to the ApprovalService via the container.

    Lives in the feature's service module (dossier §13: service.py may import the
    container) so the controller imports only this feature's models + service.
    """
    return DecisionService(approval_service)
