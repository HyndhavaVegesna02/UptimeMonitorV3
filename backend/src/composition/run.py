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

from src.adapters.inbound.dynatrace.grail_executor import make_grail_executor
from src.adapters.outbound.statuspage import StatuspagePublisher
from src.adapters.outbound.statuspage.http_executor import make_statuspage_executor
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
from src.adapters.persistence.watermark_repository import PostgresWatermarkRepository
from src.composition.config import Config, load_config
from src.composition.publish_helper import (
    BestEffortPublisher,
    LoggingPublisher,
    RecordingPublisher,
)
from src.composition.pull_loop import run_periodic
from src.composition.seed import seed_topology
from src.composition.settings import (
    LiveSecrets,
    Settings,
    load_live_secrets,
    load_settings,
    to_psycopg_url,
)
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

    Wires the Postgres database repositories, Grail and Statuspage executors,
    the best-effort publisher, and the decide service.
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
    ingest_port = IngestService(
        observation_repo=observation_repo,
        watermark_repo=watermark_repo,
        rejected_repo=rejected_repo,
        clock=clock,
    )

    # 3. Dynatrace DQL Executor
    dynatrace_executor = make_grail_executor(
        env_url=secrets.dynatrace_env_url,
        api_token=secrets.dynatrace_api_token,
    )

    # 4. Statuspage Publisher or Logging Fallback
    if (
        secrets.statuspage_page_id
        and secrets.statuspage_api_token
        and config.statuspage_mapping()
    ):
        statuspage_publisher = StatuspagePublisher(
            page_id=secrets.statuspage_page_id,
            api_token=secrets.statuspage_api_token,
            component_mapping=config.statuspage_mapping(),
            executor=make_statuspage_executor(),
        )

        # 5. BestEffort + Recording Publisher
        recording_publisher = RecordingPublisher(
            delegate=statuspage_publisher,
            publication_repo=publication_repo,
            clock=clock,
        )
        publisher = BestEffortPublisher(delegate=recording_publisher)
    else:
        publisher = LoggingPublisher()

    # 6. Decide Service
    decide_service = DecideService(proposal_repo=proposal_repo, publisher=publisher)

    # 7. One run_periodic per signal
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
    """Live loop execution entrypoint (dossier §17).

    Loads settings, secrets, config, seeds the database topology, gathers and
    runs the asyncio loops, and ensures database engine disposal.
    """
    logging.basicConfig(level=logging.INFO)

    from src.adapters.system_clock import SystemClock

    settings = load_settings()
    secrets = load_live_secrets()
    config = load_config(settings.config_dir)
    clock = SystemClock()

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
