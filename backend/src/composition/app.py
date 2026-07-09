from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.ports import (
    ClockPort,
    ComponentRepository,
    MaintenanceRepository,
    ObservationRepository,
    ProposalRepository,
    PublicationRepository,
    SignalRepository,
    StatusPublisherPort,
)

# STORY-048 sample-mode seam (temporary — see docs/scrum/wiki/sample-mode.md)
from src.core.ports.sample_mode_repository import SampleModeRepository


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
    publication_repo: PublicationRepository | None = None,
    signal_repo: SignalRepository | None = None,
    # STORY-048 sample-mode seam (temporary — see docs/scrum/wiki/sample-mode.md)
    sample_mode_repo: SampleModeRepository | None = None,
    clock: ClockPort | None = None,
    publisher: StatusPublisherPort | None = None,
    config_dir: str | None = None,
) -> FastAPI:
    """Create and wire the FastAPI application (composition root).

    Accepts optional injected dependencies (like a FakeProposalRepository) for
    testing. `publisher` (STORY-045) is symmetric with the repo params: pass an
    explicit chain (e.g. one built from fakes) to control exactly what the
    approve trigger publishes to; leave it `None` to get the default — the
    shared `build_publisher` (dossier §12, §17, D2) chain wired against
    whatever `component_repo`/`publication_repo` this call resolved.

    Whenever a `component_repo` is available (injected or real), the wired
    publisher performs status write-back (STORY-047 AC1): a `component_repo`
    without a `publication_repo` yields `StatusWritebackPublisher(
    LoggingPublisher())` — write-back still applies, just without the
    publications-table recording that needs a `publication_repo` — never a
    bare `LoggingPublisher` that silently skips write-back. Only when NO
    `component_repo` is available at all (nothing to write back to — e.g. a
    proposal-only injected test) does this fall back to a bare
    `LoggingPublisher`.
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
        from src.adapters.persistence.sample_mode_repository import (
            PostgresSampleModeRepository,
        )
        from src.adapters.persistence.signal_repository import (
            PostgresSignalRepository,
        )
        from src.composition.config import load_config
        from src.composition.settings import load_settings, to_psycopg_url

        settings = load_settings()
        db_url = to_psycopg_url(database_url or settings.database_url)
        engine = sa.create_engine(db_url)
        proposal_repo = PostgresProposalRepository(engine)
        if component_repo is None:
            component_repo = PostgresComponentRepository(engine)
        if maintenance_repo is None:
            maintenance_repo = PostgresMaintenanceRepository(engine)
        if observation_repo is None:
            observation_repo = PostgresObservationRepository(engine)
        if publication_repo is None:
            from src.adapters.persistence.publication_repository import (
                PostgresPublicationRepository,
            )

            publication_repo = PostgresPublicationRepository(engine)
        if signal_repo is None:
            signal_repo = PostgresSignalRepository(engine)
        # STORY-048 sample-mode seam (temporary — see docs/scrum/wiki/sample-mode.md)
        if sample_mode_repo is None:
            sample_mode_repo = PostgresSampleModeRepository(engine)
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

    # Wire the publisher chain (STORY-045, D2, AC1/AC2). The approve trigger
    # runs in THIS process, so the same shared `build_publisher` assembly
    # `composition/run.py::build_live_loop` uses is built here too — the
    # write-back-first / best-effort-external-call chain, or its LoggingPublisher
    # fallback when Statuspage credentials or the config mapping are absent.
    if publisher is None:
        from src.composition.publish_helper import (
            LoggingPublisher,
            StatusWritebackPublisher,
            build_publisher,
        )

        if component_repo is not None and publication_repo is not None:
            from src.composition.settings import load_statuspage_secrets

            statuspage_secrets = load_statuspage_secrets()
            mapping = (
                app.state.seed_config.statuspage_mapping()
                if app.state.seed_config is not None
                else {}
            )
            publisher = build_publisher(
                component_repo=component_repo,
                publication_repo=publication_repo,
                clock=clock,
                statuspage_page_id=statuspage_secrets.page_id,
                statuspage_api_token=statuspage_secrets.api_token,
                component_mapping=mapping,
            )
        elif component_repo is not None:
            # A component_repo is available but publication_repo is not
            # (STORY-047 AC1): write-back still applies (there IS a repo to
            # write back to), just without the publications-table recording
            # that needs a publication_repo — never a bare LoggingPublisher
            # that silently skips write-back.
            publisher = StatusWritebackPublisher(LoggingPublisher(), component_repo)
        else:
            # No component_repo wired at all — nothing to write back to
            # (e.g. a proposal-only injected test). Falls back to a bare
            # no-op publisher; never attempts write-back against an absent
            # repo.
            publisher = LoggingPublisher()

    # Wire ApprovalService
    from src.core.services.approval import ApprovalService

    approval_service = ApprovalService(
        proposal_repo=proposal_repo, clock=clock, publisher=publisher
    )

    # Store in app state for dependencies to resolve
    app.state.proposal_repo = proposal_repo
    app.state.component_repo = component_repo
    app.state.maintenance_repo = maintenance_repo
    app.state.observation_repo = observation_repo
    app.state.publication_repo = publication_repo
    app.state.signal_repo = signal_repo
    # STORY-048 sample-mode seam (temporary — see docs/scrum/wiki/sample-mode.md)
    app.state.sample_mode_repo = sample_mode_repo
    app.state.clock = clock
    app.state.publisher = publisher
    app.state.approval_service = approval_service

    # Mount routers
    from src.api.v1 import router as v1_router

    app.include_router(v1_router, prefix="/api/v1")

    # Install exception handlers (STORY-075)
    from src.api.v1._shared.errors import install_error_handlers

    install_error_handlers(app)

    return app
