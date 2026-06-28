"""Thin edge service for decisions (api/v1/decisions zone).

Cites dossier §13.
"""

from fastapi import HTTPException
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
            raise HTTPException(status_code=422, detail=str(e))

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
            raise HTTPException(status_code=404, detail=str(e))
        except ProposalNotOpenError as e:
            raise HTTPException(status_code=409, detail=str(e))

        # 3. Shape the HTTP result
        return DecisionResponse(
            proposal_id=result.id if result.id is not None else proposal_id,
            state=result.state.value,
            resolved_at=result.resolved_at,
        )
