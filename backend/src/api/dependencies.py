from fastapi import Request

from src.core.ports import (
    ClockPort,
    ComponentRepository,
    MaintenanceRepository,
    ObservationRepository,
    ProposalRepository,
)
from src.core.services.approval import ApprovalService


def get_approval_service(request: Request) -> ApprovalService:
    """FastAPI dependency to retrieve the ApprovalService from app state."""
    return request.app.state.approval_service


def get_component_repo(request: Request) -> ComponentRepository:
    """FastAPI dependency to retrieve the ComponentRepository from app state."""
    return request.app.state.component_repo


def get_proposal_repo(request: Request) -> ProposalRepository:
    """FastAPI dependency to retrieve the ProposalRepository from app state."""
    return request.app.state.proposal_repo


def get_maintenance_repo(request: Request) -> MaintenanceRepository:
    """FastAPI dependency to retrieve the MaintenanceRepository from app state."""
    return request.app.state.maintenance_repo


def get_observation_repo(request: Request) -> ObservationRepository:
    """FastAPI dependency to retrieve the ObservationRepository from app state."""
    return request.app.state.observation_repo


def get_clock(request: Request) -> ClockPort:
    """FastAPI dependency to retrieve the ClockPort from app state."""
    return request.app.state.clock
