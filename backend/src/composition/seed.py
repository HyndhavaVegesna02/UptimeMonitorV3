"""Topology seeding logic (STORY-040 Phase B).

Neon serves as a read model seeded from Git configuration at boot time (dossier §7
Option C). This module implements the idempotent upsert logic in the correct
foreign key order (apps -> components -> signals) to ensure referential
integrity (dossier §9, §17).
"""

from __future__ import annotations

import logging

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.engine import Engine

from src.composition.config import Config

logger = logging.getLogger(__name__)

_APPS = sa.table(
    "apps",
    sa.column("id"),
    sa.column("name"),
    sa.column("config", JSONB),
    sa.column("updated_at"),
)

_COMPONENTS = sa.table(
    "components",
    sa.column("id"),
    sa.column("app_id"),
    sa.column("name"),
    sa.column("updated_at"),
)

_SIGNALS = sa.table(
    "signals",
    sa.column("signal_key"),
    sa.column("app_id"),
    sa.column("name"),
    sa.column("component_id"),
    sa.column("interval_seconds"),
    sa.column("updated_at"),
)


def seed_topology(config: Config, engine: Engine) -> None:
    """Idempotently seed the topology from config into the database (dossier §7, §17).

    Upserts seeded topology in referential order (apps -> components -> signals).
    We use transaction blocks (engine.begin()) to ensure ACID updates.

    - Apps: config stores the thresholds JSON (NOT NULL).
    - Components: upsert updates metadata (name, app_id), NEVER runtime status.
    - Signals: carries nullable component_id.
    """
    logger.info("Starting topology seeding from Git configuration...")

    with engine.begin() as conn:
        # 1. Upsert Apps
        for app in config.apps:
            app_stmt = insert(_APPS).values(
                id=app.id,
                name=app.name,
                config={"thresholds": app.thresholds.model_dump()},
            )
            app_upsert = app_stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "name": app_stmt.excluded.name,
                    "config": app_stmt.excluded.config,
                    "updated_at": sa.func.now(),
                },
            )
            conn.execute(app_upsert)

        # 2. Upsert Components
        for app in config.apps:
            for comp in app.components:
                comp_stmt = insert(_COMPONENTS).values(
                    id=comp.id,
                    app_id=app.id,
                    name=comp.name,
                )
                comp_upsert = comp_stmt.on_conflict_do_update(
                    index_elements=["id"],
                    set_={
                        "name": comp_stmt.excluded.name,
                        "app_id": comp_stmt.excluded.app_id,
                        "updated_at": sa.func.now(),
                    },
                )
                conn.execute(comp_upsert)

        # 3. Upsert Signals
        for app in config.apps:
            for sig in app.signals:
                sig_stmt = insert(_SIGNALS).values(
                    signal_key=sig.signal_key,
                    app_id=app.id,
                    name=sig.name,
                    component_id=sig.component_id,
                    interval_seconds=sig.interval_seconds,
                )
                sig_upsert = sig_stmt.on_conflict_do_update(
                    index_elements=["signal_key"],
                    set_={
                        "app_id": sig_stmt.excluded.app_id,
                        "name": sig_stmt.excluded.name,
                        "component_id": sig_stmt.excluded.component_id,
                        "interval_seconds": sig_stmt.excluded.interval_seconds,
                        "updated_at": sa.func.now(),
                    },
                )
                conn.execute(sig_upsert)

    logger.info("Topology seeding completed successfully.")
