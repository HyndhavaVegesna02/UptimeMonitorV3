from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.ports import (
    ClockPort,
    ComponentRepository,
    MaintenanceRepository,
    ObservationRepository,
    ProposalRepository,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for resource setup and teardown (STORY-035.1)."""
    # Seeding topology at boot time (dossier §7, §17)
    seed_config = getattr(app.state, "seed_config", None)
    db_engine = getattr(app.state, "db_engine", None)
    if seed_config is not None and db_engine is not None:
        from src.composition.seed import seed_topology
        seed_topology(seed_config, db_engine)
    yield
    # Dispose of the DB engine on shutdown if it was constructed
    if hasattr(app.state, "db_engine") and app.state.db_engine is not None:
        app.state.db_engine.dispose()


def create_app(
    *,
    database_url: str | None = None,
    proposal_repo: ProposalRepository | None = None,
    component_repo: ComponentRepository | None = None,
    maintenance_repo: MaintenanceRepository | None = None,
    observation_repo: ObservationRepository | None = None,
    clock: ClockPort | None = None,
    config_dir: str | None = None,
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
        from src.adapters.persistence.maintenance_repository import (
            PostgresMaintenanceRepository,
        )
        from src.adapters.persistence.observation_repository import (
            PostgresObservationRepository,
        )
        from src.adapters.persistence.proposal_repository import (
            PostgresProposalRepository,
        )
        from src.composition.settings import load_settings
        from src.composition.config import load_config

        settings = load_settings()
        db_url = database_url or settings.database_url
        if db_url.startswith("postgresql://"):
            db_url = "postgresql+psycopg://" + db_url[len("postgresql://") :]
        engine = sa.create_engine(db_url)
        proposal_repo = PostgresProposalRepository(engine)
        if component_repo is None:
            component_repo = PostgresComponentRepository(engine)
        if maintenance_repo is None:
            maintenance_repo = PostgresMaintenanceRepository(engine)
        if observation_repo is None:
            observation_repo = PostgresObservationRepository(engine)
        app.state.db_engine = engine

        # Load and validate config (fail-fast: raises if invalid)
        cfg_dir = config_dir or settings.config_dir
        app.state.seed_config = load_config(cfg_dir)
    else:
        # Repos were injected (e.g. fakes in tests). Leave component_repo,
        # maintenance_repo, and observation_repo as-passed — possibly None —
        # symmetric with proposal_repo. Production code never imports the tests
        # package; callers that exercise /components, /maintenance,
        # /availability, or /history inject them explicitly.
        app.state.db_engine = None
        app.state.seed_config = None

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
    app.state.maintenance_repo = maintenance_repo
    app.state.observation_repo = observation_repo
    app.state.clock = clock
    app.state.approval_service = approval_service

    # Mount routers
    from src.api.v1 import router as v1_router

    app.include_router(v1_router, prefix="/api/v1")

    return app
