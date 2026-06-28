"""Tests for topology seeding (STORY-040 Phase B).

DB-gated. Exercises seed_topology(config, engine) and validates that apps,
components, and signals are created/updated idempotently and that component
runtime status is preserved.
"""

import psycopg
import pytest
from src.composition.config import AppConfig, ComponentConfig, Config, SignalConfig
from src.composition.seed import seed_topology
from src.core.services.pipeline import AntiFlapThresholds


@pytest.fixture
def clean_topology(migrated_db):
    """Truncate topology tables before and after the test to keep database clean (STORY-039)."""
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE apps, components, signals CASCADE;")
        conn.commit()
    yield
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE apps, components, signals CASCADE;")
        conn.commit()


def _make_config() -> Config:
    thresholds = AntiFlapThresholds(major=3, partial=2, degraded=2, recovery=2)
    comp = ComponentConfig(id="checkout", name="Checkout Component")
    sig = SignalConfig(
        signal_key="checkout-http",
        native_id="SYNTHETIC_TEST-ABC",
        name="Checkout HTTP Signal",
        component_id="checkout",
        interval_seconds=60,
    )
    app = AppConfig(
        id="sockshop",
        name="Sock Shop App",
        monitor_provider="dynatrace",
        components=[comp],
        signals=[sig],
        thresholds=thresholds,
    )
    return Config([app])


def test_seed_topology_inserts_correctly(migrated_db, engine, clean_topology):
    """B1: seed_topology inserts correct topology in FK order: apps -> components -> signals.

    Signals carry their component_id.
    """
    config = _make_config()
    seed_topology(config, engine)

    # Verify rows in apps, components, signals using raw psycopg
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            # Check Apps
            cur.execute("SELECT id, name, config FROM apps;")
            apps = cur.fetchall()
            assert len(apps) == 1
            assert apps[0][0] == "sockshop"
            assert apps[0][1] == "Sock Shop App"
            cfg_dict = apps[0][2]
            assert cfg_dict["thresholds"]["major"] == 3

            # Check Components
            cur.execute("SELECT id, app_id, name, status FROM components;")
            components = cur.fetchall()
            assert len(components) == 1
            assert components[0][0] == "checkout"
            assert components[0][1] == "sockshop"
            assert components[0][2] == "Checkout Component"
            assert components[0][3] == "operational"  # default status

            # Check Signals
            cur.execute("SELECT signal_key, app_id, name, component_id FROM signals;")
            signals = cur.fetchall()
            assert len(signals) == 1
            assert signals[0][0] == "checkout-http"
            assert signals[0][1] == "sockshop"
            assert signals[0][2] == "Checkout HTTP Signal"
            assert signals[0][3] == "checkout"  # carries component_id (A1 FK)


def test_seed_topology_is_idempotent(migrated_db, engine, clean_topology):
    """B3: IDEMPOTENCY (AC2) — running seed_topology twice is a no-op (no duplicates or churn)."""
    config = _make_config()

    # First seed
    seed_topology(config, engine)

    # Capture state. We compare id/name/created_at (stable across an idempotent
    # re-seed) — NOT updated_at, which the ON CONFLICT DO UPDATE path legitimately
    # bumps to now() every run. Equality of these columns proves no row churn and
    # no value drift; do not "fix" this to also assert updated_at.
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, created_at FROM apps;")
            apps_before = cur.fetchall()
            cur.execute("SELECT id, name, created_at FROM components;")
            comps_before = cur.fetchall()
            cur.execute("SELECT signal_key, name, created_at FROM signals;")
            sigs_before = cur.fetchall()

    # Second seed with unchanged config
    seed_topology(config, engine)

    # Verify identical values and no new rows
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, created_at FROM apps;")
            apps_after = cur.fetchall()
            cur.execute("SELECT id, name, created_at FROM components;")
            comps_after = cur.fetchall()
            cur.execute("SELECT signal_key, name, created_at FROM signals;")
            sigs_after = cur.fetchall()

    assert apps_before == apps_after
    assert comps_before == comps_after
    assert sigs_before == sigs_after


def test_seed_topology_preserves_status(migrated_db, engine, clean_topology):
    """B4: STATUS PRESERVATION (AC3) — re-seeding never resets component's runtime status.

    Only name/app_id are updated on component, never status.
    """
    config = _make_config()
    seed_topology(config, engine)

    # Manually update component status to degraded (runtime change)
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE components SET status = 'degraded' WHERE id = 'checkout';"
            )
        conn.commit()

    # Seed again (perhaps name changed in config)
    changed_comp = ComponentConfig(id="checkout", name="New Checkout Component Name")
    changed_app = AppConfig(
        id="sockshop",
        name="Sock Shop App",
        monitor_provider="dynatrace",
        components=[changed_comp],
        signals=config.apps[0].signals,
        thresholds=config.apps[0].thresholds,
    )
    changed_config = Config([changed_app])

    seed_topology(changed_config, engine)

    # Verify status is still degraded, but name is updated
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name, status FROM components WHERE id = 'checkout';")
            row = cur.fetchone()
            assert row is not None
            assert row[0] == "New Checkout Component Name"
            assert row[1] == "degraded"  # preserved!


def test_seed_topology_cli_success(migrated_db, clean_topology, tmp_path):
    """C1: seed_topology.py CLI seeds correctly (exit 0) when valid env vars are present."""
    import os
    import subprocess
    import sys

    # Write a tiny valid yaml to a temp directory
    config_dir = tmp_path / "apps"
    config_dir.mkdir()
    yaml_content = """
app:
  id: cli-app
  name: CLI App
  monitor_provider: dynatrace
components:
  - { id: cli-comp, name: CLI Comp }
signals:
  - { signal_key: cli-sig, native_id: N-1, name: CLI Sig, component_id: cli-comp, interval_seconds: 30 }
"""
    (config_dir / "cli_app.yaml").write_text(yaml_content, encoding="utf-8")

    env = {
        **os.environ,
        "DATABASE_URL": migrated_db.database_url,
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

    # Verify directly from database
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM apps WHERE id = 'cli-app';")
            assert cur.fetchone() == ("CLI App",)


def test_seed_topology_cli_no_db_url_fails():
    """C1: CLI exits with code 2 when DATABASE_URL is missing."""
    import os
    import subprocess
    import sys

    env = {**os.environ}
    env.pop("DATABASE_URL", None)

    result = subprocess.run(
        [sys.executable, "scripts/seed_topology.py"],
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 2
    assert "ERROR: DATABASE_URL is not set" in result.stderr


def test_seed_topology_cli_invalid_config_fails(migrated_db, tmp_path):
    """C1: CLI exits with code 1 (AC5) when config validation fails."""
    import os
    import subprocess
    import sys

    # Write an invalid yaml (missing component name/id etc.)
    config_dir = tmp_path / "bad_apps"
    config_dir.mkdir()
    (config_dir / "bad.yaml").write_text("invalid_yaml: [unclosed", encoding="utf-8")

    env = {
        **os.environ,
        "DATABASE_URL": migrated_db.database_url,
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


def test_create_app_seeds_on_lifespan_startup(migrated_db, clean_topology, tmp_path):
    """D2: lifespan startup triggers seed_topology when seed_config and db_engine are present.

    And GET /api/v1/components returns the newly-seeded components.
    """
    from fastapi.testclient import TestClient
    from src.composition.app import create_app

    # Create a valid config in a temp dir
    config_dir = tmp_path / "apps"
    config_dir.mkdir()
    yaml_content = """
app:
  id: startup-app
  name: Startup App
  monitor_provider: dynatrace
components:
  - { id: startup-comp, name: Startup Comp }
signals:
  - { signal_key: startup-sig, native_id: N-2, name: Startup Sig, component_id: startup-comp, interval_seconds: 45 }
"""
    (config_dir / "startup_app.yaml").write_text(yaml_content, encoding="utf-8")

    app = create_app(
        database_url=migrated_db.database_url,
        config_dir=str(config_dir),
    )

    # Before lifespan, DB should not have the components
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM components WHERE id = 'startup-comp';")
            assert cur.fetchone()[0] == 0

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


def test_create_app_fails_fast_on_invalid_config(tmp_path):
    """D2: create_app fails fast (raises ValueError) if configuration load/validation fails."""
    from src.composition.app import create_app

    config_dir = tmp_path / "bad_apps"
    config_dir.mkdir()
    (config_dir / "bad.yaml").write_text("invalid_yaml: [unclosed", encoding="utf-8")

    with pytest.raises(ValueError):
        create_app(
            database_url="postgresql://postgres:postgres@localhost:55432/uptime",
            config_dir=str(config_dir),
        )


def test_create_app_injected_branch_skips_seeding():
    """D2: create_app in the injected branch (fakes passed in) sets seed_config to None and does not seed."""
    from fakes import FakeProposalRepository
    from fastapi.testclient import TestClient
    from src.composition.app import create_app

    fake_repo = FakeProposalRepository()
    app = create_app(proposal_repo=fake_repo)

    assert app.state.seed_config is None
    assert app.state.db_engine is None

    # lifespan should yield normally without attempting to seed or throwing errors
    with TestClient(app):
        pass
