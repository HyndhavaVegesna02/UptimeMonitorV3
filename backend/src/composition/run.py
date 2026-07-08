"""Live composition driver and entrypoint (dossier §17, spec §8).

Seeds the topology read model from configuration files, constructs all live
Postgres repository adapters, HTTP executors, publishers, and services,
and gathers the per-signal asyncio periodic pull loops.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Coroutine

import sqlalchemy as sa
from dotenv import load_dotenv

from src.adapters.inbound.dynatrace.grail_executor import make_grail_executor
from src.adapters.persistence.component_repository import PostgresComponentRepository
from src.adapters.persistence.maintenance_repository import (
    PostgresMaintenanceRepository,
)
from src.adapters.persistence.observation_repository import (
    PostgresObservationRepository,
)
from src.adapters.persistence.proposal_repository import PostgresProposalRepository
from src.adapters.persistence.publication_repository import (
    PostgresPublicationRepository,
)
from src.adapters.persistence.rejected_observation_repository import (
    PostgresRejectedObservationRepository,
)

# STORY-048 sample-mode seam (temporary — see docs/scrum/wiki/sample-mode.md)
from src.adapters.persistence.sample_mode_repository import (
    PostgresSampleModeRepository,
)
from src.adapters.persistence.watermark_repository import PostgresWatermarkRepository
from src.composition.config import Config, load_config
from src.composition.publish_helper import build_publisher
from src.composition.pull_loop import run_periodic
from src.composition.sample_mode import SampleModeIngest
from src.composition.seed import seed_topology
from src.composition.settings import (
    LiveSecrets,
    Settings,
    load_live_secrets,
    load_settings,
    to_psycopg_url,
)
from src.composition.vendor_health import check_vendor_id_health
from src.core.ports.clock import ClockPort
from src.core.services.decide import DecideService
from src.core.services.ingest_service import IngestService

logger = logging.getLogger(__name__)


def build_live_loop(
    *,
    settings: Settings,
    secrets: LiveSecrets,
    config: Config,
    engine: sa.Engine,
    clock: ClockPort,
) -> list[Coroutine]:
    """Assemble and return the list of coroutines running the periodic loops (dossier §17).

    Wires the Postgres database repositories, Grail executor, the shared
    `build_publisher` chain (STORY-045, D2 — write-back + best-effort Statuspage,
    or write-back + logging fallback), and the decide service.
    """
    # 1. Wire repositories
    observation_repo = PostgresObservationRepository(engine)
    watermark_repo = PostgresWatermarkRepository(engine)
    rejected_repo = PostgresRejectedObservationRepository(engine)
    maintenance_repo = PostgresMaintenanceRepository(engine)
    component_repo = PostgresComponentRepository(engine)
    proposal_repo = PostgresProposalRepository(engine)
    publication_repo = PostgresPublicationRepository(engine)

    # 2. Ingest Service
    # STORY-048 sample-mode seam (temporary — see docs/scrum/wiki/sample-mode.md):
    # wrapped by SampleModeIngest, which reads the persisted flag once per
    # cycle (D4) and forces every observation to DOWN + marks it while ON;
    # OFF is a byte-identical passthrough to the real IngestService below.
    ingest_port = SampleModeIngest(
        delegate=IngestService(
            observation_repo=observation_repo,
            watermark_repo=watermark_repo,
            rejected_repo=rejected_repo,
            clock=clock,
        ),
        sample_mode_repo=PostgresSampleModeRepository(engine),
    )

    # 3. Dynatrace DQL Executor
    dynatrace_executor = make_grail_executor(
        env_url=secrets.dynatrace_env_url,
        api_token=secrets.dynatrace_api_token,
    )

    # 4. Shared publisher chain (STORY-045, D2 — the ONE assembly both
    # composition roots use; see composition/publish_helper.py::build_publisher).
    publisher = build_publisher(
        component_repo=component_repo,
        publication_repo=publication_repo,
        clock=clock,
        statuspage_page_id=secrets.statuspage_page_id,
        statuspage_api_token=secrets.statuspage_api_token,
        component_mapping=config.statuspage_mapping(),
    )

    # 5. Decide Service
    decide_service = DecideService(proposal_repo=proposal_repo, publisher=publisher)

    # 6. One run_periodic per signal
    coroutines = []
    for app in config.apps:
        for signal in app.signals:
            coro = run_periodic(
                signal_key=signal.signal_key,
                native_id=signal.native_id,
                watermark_repo=watermark_repo,
                ingest_port=ingest_port,
                executor=dynatrace_executor,
                interval_seconds=signal.interval_seconds,
                config=config,
                observation_repo=observation_repo,
                maintenance_repo=maintenance_repo,
                component_repo=component_repo,
                decide_service=decide_service,
                clock=clock,
            )
            coroutines.append(coro)

    return coroutines


async def main() -> None:
    """Live loop execution entrypoint (dossier §17, STORY-043).

    Loads a repo-root ``.env`` (see the ``load_dotenv()`` call below), then
    settings, secrets, config; seeds the database topology; gathers and runs
    the asyncio loops; and ensures database engine disposal.
    """
    logging.basicConfig(level=logging.INFO)

    from src.adapters.system_clock import SystemClock

    # STORY-043: load a repo-root `.env` BEFORE reading settings/secrets, so
    # the documented local recipe ("Run the app locally", CLAUDE.md) — which
    # runs this entrypoint from the repo root — can supply
    # DYNATRACE_*/STATUSPAGE_*/DATABASE_URL from a gitignored `.env` file
    # instead of requiring them to be exported into the shell first. No
    # explicit path is passed: `load_dotenv()`'s default discovery walks
    # upward from THIS file's own location (not the process CWD) to find the
    # repo-root `.env` — the assumption is that the repo layout on disk is
    # intact (not that CWD is any particular directory). Default
    # `override=False` semantics mean an already-exported var always wins
    # (AC3), so production (Railway, no `.env` file present) is unaffected.
    load_dotenv()

    settings = load_settings()
    secrets = load_live_secrets()
    config = load_config(settings.config_dir)
    clock = SystemClock()

    # STORY-070: loud (NOT fail-fast) vendor-id drift probe, run once here
    # before the engine/loops are built, so a configured-but-empty Dynatrace
    # monitor id surfaces as early in startup as possible. Uses its own Grail
    # executor instance (cheap: just a closure over the endpoint/headers, no
    # network call until invoked) so this never depends on `build_live_loop`
    # having run yet. `check_vendor_id_health` never raises -- a probe error
    # for one monitor is caught and logged internally, never propagated here.
    health_executor = make_grail_executor(
        env_url=secrets.dynatrace_env_url,
        api_token=secrets.dynatrace_api_token,
    )
    check_vendor_id_health(config=config, executor=health_executor)

    db_url = to_psycopg_url(settings.database_url)
    engine = sa.create_engine(db_url)

    try:
        # Seed topology read model once before starting loops
        logger.info("Seeding topology read model...")
        seed_topology(config, engine)

        # Build and run loops
        loops = build_live_loop(
            settings=settings,
            secrets=secrets,
            config=config,
            engine=engine,
            clock=clock,
        )
        if not loops:
            logger.warning("No signals configured to monitor. Exiting.")
            return

        logger.info(f"Starting {len(loops)} periodic monitoring loop(s)...")
        await asyncio.gather(*loops)
    finally:
        logger.info("Disposing database engine...")
        engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
