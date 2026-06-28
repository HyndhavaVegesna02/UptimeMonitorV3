"""Tests for topology seeding (STORY-040 Phase B).

DB-gated. Exercises seed_topology(config, engine) and validates that apps,
components, and signals are created/updated idempotently and that component
runtime status is preserved.
"""

import json
from datetime import datetime, timezone
import psycopg
import pytest
import sqlalchemy as sa

from src.composition.config import AppConfig, ComponentConfig, Config, SignalConfig
from src.composition.seed import seed_topology
from src.core.domain.status import ComponentStatus
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
    
    # Capture state (created_at/updated_at/etc.)
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
            cur.execute("UPDATE components SET status = 'degraded' WHERE id = 'checkout';")
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
