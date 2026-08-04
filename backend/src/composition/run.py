"""Live composition driver and entrypoint (dossier §17, spec §8).

Seeds the topology read model from configuration files, constructs all live
DynamoDB repository adapters, HTTP executors, publishers, and services,
and gathers the per-signal asyncio periodic pull loops.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Coroutine

from dotenv import load_dotenv

from src.adapters.inbound.dynatrace.grail_executor import make_grail_executor
from src.adapters.persistence.dynamo_component_repository import (
    DynamoComponentRepository,
)
from src.adapters.persistence.dynamo_maintenance_repository import (
    DynamoMaintenanceRepository,
)
from src.adapters.persistence.dynamo_observation_repository import (
    DynamoObservationRepository,
)
from src.adapters.persistence.dynamo_proposal_repository import DynamoProposalRepository
from src.adapters.persistence.dynamo_publication_repository import (
    DynamoPublicationRepository,
)
from src.adapters.persistence.dynamo_rejected_observation_repository import (
    DynamoRejectedObservationRepository,
)

# STORY-048 sample-mode seam (temporary — see docs/scrum/wiki/sample-mode.md)
from src.adapters.persistence.dynamo_sample_mode_repository import (
    DynamoSampleModeRepository,
)
from src.adapters.persistence.dynamo_watermark_repository import (
    DynamoWatermarkRepository,
)
from src.composition.config import Config, load_config
from src.composition.dynamo import make_dynamo_resource
from src.composition.publish_helper import build_publisher
from src.composition.pull_loop import run_periodic
from src.composition.sample_mode import SampleModeIngest
from src.composition.seed_dynamo import seed_topology_dynamo
from src.composition.settings import (
    LiveSecrets,
    Settings,
    load_live_secrets,
    load_settings,
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
    db_resource,
    clock: ClockPort,
) -> list[Coroutine]:
    """Assemble and return the list of coroutines running the periodic loops (dossier §17).

    Wires the DynamoDB database repositories, Grail executor, the shared
    `build_publisher` chain (STORY-045, D2 — write-back + best-effort Statuspage,
    or write-back + logging fallback), and the decide service.
    """
    # 1. Wire repositories
    observation_repo = DynamoObservationRepository(
        db_resource, settings.dynamo_observations_table
    )
    watermark_repo = DynamoWatermarkRepository(
        db_resource, settings.dynamo_control_table
    )
    rejected_repo = DynamoRejectedObservationRepository(
        db_resource, settings.dynamo_control_table
    )
    maintenance_repo = DynamoMaintenanceRepository(
        db_resource, settings.dynamo_control_table
    )
    component_repo = DynamoComponentRepository(
        db_resource, settings.dynamo_control_table
    )
    proposal_repo = DynamoProposalRepository(db_resource, settings.dynamo_control_table)
    publication_repo = DynamoPublicationRepository(
        db_resource, settings.dynamo_control_table
    )

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
        sample_mode_repo=DynamoSampleModeRepository(
            db_resource, settings.dynamo_control_table
        ),
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
                rejected_repo=rejected_repo,
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
    the asyncio loops.
    """
    logging.basicConfig(level=logging.INFO)

    from src.adapters.system_clock import SystemClock

    # STORY-043: load a repo-root `.env` BEFORE reading settings/secrets, so
    # the documented local recipe ("Run the app locally", CLAUDE.md) — which
    # runs this entrypoint from the repo root — can supply
    # DYNATRACE_*/STATUSPAGE_* secrets from a gitignored `.env` file
    # instead of requiring them to be exported into the shell first. No
    # explicit path is passed: `load_dotenv()`'s default discovery walks
    # upward from THIS file's own location (not the process CWD) to find the
    # repo-root `.env` — the assumption is that the repo layout on disk is
    # intact (not that CWD is any particular directory). Default
    # `override=False` semantics mean an already-exported var always wins
    # (AC3), so production (AWS ECS Fargate, no `.env` file present) is
    # unaffected.
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
    # having run yet. `check_vendor_id_health` is NOT fail-fast for the
    # EXECUTOR -- a probe error for one monitor (HTTP failure, timeout) is
    # caught and logged internally, never propagated here. It IS fail-fast
    # for a misconfigured `native_id` (STORY-204): the query-build call sits
    # outside that try/except, so a DQL-breaking character raises
    # `InvalidNativeIdError` HERE and aborts `main()` before
    # `seed_topology_dynamo`/`build_live_loop` ever run. This is NOT the same
    # blast radius as the ingest path: there, `run_periodic`
    # (`pull_loop.py::run_periodic`) catches the identical raise per-cycle,
    # so a bad `native_id` degrades only that one signal and the rest keep
    # ingesting. Here, one bad `native_id` in config crash-loops the ENTIRE
    # loop process, not just one signal.
    health_executor = make_grail_executor(
        env_url=secrets.dynatrace_env_url,
        api_token=secrets.dynatrace_api_token,
    )
    check_vendor_id_health(config=config, executor=health_executor)

    db_resource = make_dynamo_resource(settings)

    # Seed topology read model once before starting loops
    logger.info("Seeding topology read model...")
    seed_topology_dynamo(config, db_resource, settings.dynamo_control_table)

    # Build and run loops
    loops = build_live_loop(
        settings=settings,
        secrets=secrets,
        config=config,
        db_resource=db_resource,
        clock=clock,
    )
    if not loops:
        logger.warning("No signals configured to monitor. Exiting.")
        return

    logger.info(f"Starting {len(loops)} periodic monitoring loop(s)...")
    await asyncio.gather(*loops)


if __name__ == "__main__":
    asyncio.run(main())
