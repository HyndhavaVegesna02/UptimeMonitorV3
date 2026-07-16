#!/usr/bin/env python
"""Topology seeding CLI tool (dossier §7, §17).

Idempotently seeds the DynamoDB database from YAML configuration files under
config/apps/ (or CONFIG_DIR).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure we can import the `src` package (it lives at <repo>/backend).
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from src.composition.config import load_config
from src.composition.dynamo import make_dynamo_resource
from src.composition.seed_dynamo import seed_topology_dynamo
from src.composition.settings import load_settings


def main() -> int:
    # 1. Load config
    config_dir = os.environ.get("CONFIG_DIR", "config/apps")
    try:
        config = load_config(config_dir)
    except (ValueError, TypeError) as exc:
        print(f"Topology Config Load Failure: {exc}", file=sys.stderr)
        return 1

    # 2. Load settings and seed
    try:
        settings = load_settings()
        db_resource = make_dynamo_resource(settings)
        seed_topology_dynamo(config, db_resource, settings.dynamo_control_table)
    except Exception as exc:
        print(f"Topology Seeding Failure: {exc}", file=sys.stderr)
        return 3

    # 3. Print summary
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
