from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.ports import ClockPort, ComponentRepository, ProposalRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for resource setup and teardown (STORY-035.1)."""
    yield
    # Dispose of the DB engine on shutdown if it was constructed
    if hasattr(app.state, "db_engine") and app.state.db_engine is not None:
        app.state.db_engine.dispose()


def create_app(
    *,
    database_url: str | None = None,
    proposal_repo: ProposalRepository | None = None,
    component_repo: ComponentRepository | None = None,
    clock: ClockPort | None = None,
) -> FastAPI:
    """Create and wire the FastAPI application (composition root).

    Accepts optional injected dependencies (like a FakeProposalRepository) for testing.
    """
    app = FastAPI(title="Uptime Monitor V3 API", lifespan=lifespan)

    # Wire database engine and repositories
    if proposal_repo is None:
        import sqlalchemy as sa

        from src.adapters.persistence.component_repository import (
            PostgresComponentRepository,
        )
        from src.adapters.persistence.proposal_repository import (
            PostgresProposalRepository,
        )
        from src.composition.settings import load_settings

        db_url = database_url or load_settings().database_url
        engine = sa.create_engine(db_url)
        proposal_repo = PostgresProposalRepository(engine)
        if component_repo is None:
            component_repo = PostgresComponentRepository(engine)
        app.state.db_engine = engine
    else:
        app.state.db_engine = None
        if component_repo is None:
            from tests.fakes import FakeComponentRepository

            component_repo = FakeComponentRepository()

    # Wire clock
    if clock is None:
        from src.adapters.system_clock import SystemClock

        clock = SystemClock()

    # Wire ApprovalService
    from src.core.services.approval import ApprovalService

    approval_service = ApprovalService(proposal_repo=proposal_repo, clock=clock)

    # Store in app state for dependencies to resolve
    app.state.proposal_repo = proposal_repo
    app.state.component_repo = component_repo
    app.state.clock = clock
    app.state.approval_service = approval_service

    # Mount routers
    from src.api.v1 import router as v1_router

    app.include_router(v1_router, prefix="/api/v1")

    return app
