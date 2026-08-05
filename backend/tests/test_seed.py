"""Tests for topology seeding (STORY-040 Phase B).

DynamoDB-gated. Exercises seed_topology_dynamo and validates that apps,
components, and signals are created/updated idempotently and that component
runtime status is preserved.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from src.adapters.persistence.dynamo_component_repository import (
    DynamoComponentRepository,
)
from src.composition.app import create_app
from src.composition.settings import load_settings


def test_seed_topology_cli_success(dynamo_local, dynamo_resource, tmp_path):
    """C1: seed_topology.py CLI seeds correctly (exit 0) when valid config is present."""
    # Write a tiny valid yaml to a temp directory
    config_dir = tmp_path / "apps"
    config_dir.mkdir()
    yaml_content = """
app:
  id: cli-app
  name: CLI App
  monitor_provider: dynatrace
components:
  - id: cli-comp
    name: CLI Comp
    monitors:
      - { signal_key: cli-sig, native_id: N-1, name: CLI Sig, interval_seconds: 30 }
"""
    (config_dir / "cli_app.yaml").write_text(yaml_content, encoding="utf-8")

    # These two names are re-typed literals, not CONFIG_DIR_VAR/DYNAMO_ENDPOINT_URL_VAR
    # imports, on purpose: this dict is a subprocess env, a real process boundary the
    # CLI under test reads via os.environ, so there is nothing importable to cross it
    # with -- the literal string IS the wire contract. Left deliberately, unlike
    # test_demo_fleet_config.py's in-process setenv sites, which import the constants
    # because they cross no such boundary; see that file's module docstring for the
    # pin-vs-drift distinction this mirrors.
    env = {
        **os.environ,
        "DYNAMO_ENDPOINT_URL": dynamo_local.endpoint_url,
        "CONFIG_DIR": str(config_dir),
    }

    result = subprocess.run(
        [sys.executable, "scripts/seed_topology.py"],
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    assert "Seeding completed successfully" in result.stdout
    assert "1 app(s)" in result.stdout

    # Verify directly from DynamoDB
    settings = load_settings()
    comp_repo = DynamoComponentRepository(
        dynamo_resource, settings.dynamo_control_table
    )
    comp = comp_repo.get("cli-comp")
    assert comp is not None
    assert comp.name == "CLI Comp"


def test_seed_topology_cli_invalid_config_fails(dynamo_local, tmp_path):
    """C1: CLI exits with code 1 when config validation fails."""
    # Write an invalid yaml (missing component name/id etc.)
    config_dir = tmp_path / "bad_apps"
    config_dir.mkdir()
    (config_dir / "bad.yaml").write_text("invalid_yaml: [unclosed", encoding="utf-8")

    # Same subprocess-env-boundary rationale as the success test above: the two
    # names are deliberately re-typed literals, not constant imports.
    env = {
        **os.environ,
        "DYNAMO_ENDPOINT_URL": dynamo_local.endpoint_url,
        "CONFIG_DIR": str(config_dir),
    }

    result = subprocess.run(
        [sys.executable, "scripts/seed_topology.py"],
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 1
    assert (
        "Topology Config Load Failure" in result.stdout
        or "Topology Config Load Failure" in result.stderr
    )


def test_create_app_seeds_on_lifespan_startup(dynamo_local, dynamo_resource, tmp_path):
    """D2: lifespan startup triggers seed_topology_dynamo when seed_config and dynamo_resource are present.

    And GET /api/v1/components returns the newly-seeded components.
    """
    # Create a valid config in a temp dir
    config_dir = tmp_path / "apps"
    config_dir.mkdir()
    yaml_content = """
app:
  id: startup-app
  name: Startup App
  monitor_provider: dynatrace
components:
  - id: startup-comp
    name: Startup Comp
    monitors:
      - { signal_key: startup-sig, native_id: N-2, name: Startup Sig, interval_seconds: 45 }
"""
    (config_dir / "startup_app.yaml").write_text(yaml_content, encoding="utf-8")

    # Temporarily set env CONFIG_DIR for create_app settings load
    os.environ["CONFIG_DIR"] = str(config_dir)
    try:
        app = create_app(
            config_dir=str(config_dir),
        )

        settings = load_settings()
        comp_repo = DynamoComponentRepository(
            dynamo_resource, settings.dynamo_control_table
        )

        # Before lifespan, DB should not have the components
        assert comp_repo.get("startup-comp") is None

        # Entering TestClient context manager triggers lifespan events
        with TestClient(app) as client:
            # After lifespan startup, DB should have the components seeded
            response = client.get("/api/v1/components")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == "startup-comp"
            assert data[0]["name"] == "Startup Comp"
            assert data[0]["status"] == "operational"
    finally:
        os.environ.pop("CONFIG_DIR", None)


def test_create_app_fails_fast_on_invalid_config(tmp_path):
    """D2: create_app fails fast (raises ValueError) if configuration load/validation fails."""
    config_dir = tmp_path / "bad_apps"
    config_dir.mkdir()
    (config_dir / "bad.yaml").write_text("invalid_yaml: [unclosed", encoding="utf-8")

    with pytest.raises(ValueError):
        create_app(
            config_dir=str(config_dir),
        )


def test_create_app_injected_branch_skips_seeding():
    """D2: create_app in the injected branch (fakes passed in) sets seed_config to None and does not seed."""
    from fakes import FakeProposalRepository

    fake_repo = FakeProposalRepository()
    app = create_app(proposal_repo=fake_repo)

    assert app.state.seed_config is None
    assert getattr(app.state, "dynamo_resource", None) is None

    # lifespan should yield normally without attempting to seed or throwing errors
    with TestClient(app):
        pass
