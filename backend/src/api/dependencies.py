"""API dependencies (api zone)."""

from fastapi import Request
from src.core.services.approval import ApprovalService


def get_approval_service(request: Request) -> ApprovalService:
    """FastAPI dependency to retrieve the ApprovalService from app state."""
    return request.app.state.approval_service
