"""App factory and composition root (composition zone)."""

from fastapi import FastAPI

from src.core.ports import ClockPort, ProposalRepository


def create_app(
    *,
    database_url: str | None = None,
    proposal_repo: ProposalRepository | None = None,
    clock: ClockPort | None = None,
) -> FastAPI:
    """Create and wire the FastAPI application (composition root).

    Accepts optional injected dependencies (like a FakeProposalRepository) for testing.
    """
    app = FastAPI(title="Uptime Monitor V3 API")

    # Wire database engine and repository
    if proposal_repo is None:
        import sqlalchemy as sa

        from src.adapters.persistence.proposal_repository import (
            PostgresProposalRepository,
        )
        from src.composition.settings import load_settings

        db_url = database_url or load_settings().database_url
        engine = sa.create_engine(db_url)
        proposal_repo = PostgresProposalRepository(engine)
        app.state.db_engine = engine
    else:
        app.state.db_engine = None

    # Wire clock
    if clock is None:
        from src.adapters.system_clock import SystemClock

        clock = SystemClock()

    # Wire ApprovalService
    from src.core.services.approval import ApprovalService

    approval_service = ApprovalService(proposal_repo=proposal_repo, clock=clock)

    # Store in app state for dependencies to resolve
    app.state.proposal_repo = proposal_repo
    app.state.clock = clock
    app.state.approval_service = approval_service

    # Mount routers
    from src.api.v1 import router as v1_router

    app.include_router(v1_router, prefix="/api/v1")

    return app
