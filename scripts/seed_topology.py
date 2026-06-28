#!/usr/bin/env python
"""Topology seeding CLI tool (dossier §7, §17).

Idempotently seeds the Postgres database from YAML configuration files under
config/apps/ (or CONFIG_DIR). Builds a SQLAlchemy Engine from DATABASE_URL and
delegates to composition/seed.py::seed_topology.

If config loading or validation fails, exits with a nonzero status and a clear
error message (AC5).
"""

from __future__ import annotations

import os
import sys
import sqlalchemy as sa

# Ensure we can import from src/
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/backend"))

from src.composition.config import load_config
from src.composition.seed import seed_topology


def _engine_url(database_url: str) -> str:
    """Format plain postgresql:// URL to postgresql+psycopg:// dialect for SQLAlchemy 2."""
    if database_url.startswith("postgresql://"):
        return "postgresql+psycopg://" + database_url[len("postgresql://") :]
    return database_url


def main() -> int:
    # 1. Load config
    config_dir = os.environ.get("CONFIG_DIR", "config/apps")
    try:
        config = load_config(config_dir)
    except (ValueError, TypeError) as exc:
        print(f"Topology Config Load Failure: {exc}", file=sys.stderr)
        return 1

    # 2. Get database URL
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print(
            "ERROR: DATABASE_URL is not set. Point it at the database, "
            "e.g. postgresql://postgres:postgres@localhost:55432/uptime",
            file=sys.stderr,
        )
        return 2

    # 3. Create engine and seed
    engine_url = _engine_url(database_url)
    engine = sa.create_engine(engine_url, future=True)
    try:
        seed_topology(config, engine)
    except Exception as exc:
        print(f"Topology Seeding Failure: {exc}", file=sys.stderr)
        return 3
    finally:
        engine.dispose()

    # 4. Print summary
    num_apps = len(config.apps)
    num_components = sum(len(app.components) for app in config.apps)
    num_signals = sum(len(app.signals) for app in config.apps)
    print(
        f"Seeding completed successfully: {num_apps} app(s), "
        f"{num_components} component(s), {num_signals} signal(s) seeded."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
