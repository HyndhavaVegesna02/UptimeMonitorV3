"""Thin edge service for decisions (api/v1/decisions zone).

Cites dossier §13: the edge service validates HTTP input, delegates to a core
service via the composition container, and shapes the HTTP result — it holds no
business logic and imports no other feature.
"""

from fastapi import Depends

from src.api.dependencies import get_approval_service
from src.api.v1.decisions.models import DecisionRequest, DecisionResponse
from src.api.v1.decisions.validation import (
    validate_decision_request,
)
from src.core.services.approval import (
    ApprovalService,
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
        validate_decision_request(action=request.action, actor=request.actor)

        # 2. Delegate to ApprovalService
        # NOTE: ProposalNotOpenError -> HTTP 409 covers both the up-front open-state
        # guard and a lost-race resolve (concurrent double-submit surfaced by the
        # repository, per the 2026-06-28 TOCTOU agreement).
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
