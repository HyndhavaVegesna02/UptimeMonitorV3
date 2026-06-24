"""STORY-019: tests for the shared throwaway-DB session fixture (`migrated_db`).

These tests exercise the fixture's *contract*, independent of `test_spine_schema.py`
(which is the "real consumer" refactor target). Each AC owns a test:

  - AC2/step1: depending on `migrated_db` yields a live, migrated connection —
    the eleven spine tables exist — proving the fixture actually migrates.
  - AC3: with `DATABASE_URL`/`DATABASE_URL_DIRECT` already set externally, the
    fixture reuses them and does not spawn a container.
  - AC3: with neither an external DB nor Docker available, DB-gated tests skip
    cleanly (no error). Exercised by directly calling the fixture's decision
    helper rather than monkeypatching the session-scoped fixture itself.
"""

from __future__ import annotations

import os

SPINE_TABLES = {
    "apps",
    "signals",
    "components",
    "observations",
    "problem_signals",
    "watermarks",
    "rejected_observations",
    "status_proposals",
    "approval_events",
    "publications",
    "maintenance_windows",
}


def test_migrated_db_fixture_yields_live_migrated_connection(migrated_db):
    """The session fixture provides URLs to a migrated DB with the spine tables."""
    import psycopg

    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
            )
            existing = {row[0] for row in cur.fetchall()}
    missing = SPINE_TABLES - existing
    assert not missing, f"missing spine tables: {missing}"


def test_migrated_db_fixture_sets_both_url_env_vars(migrated_db):
    """The fixture's URLs are reflected into the process env in the right dialects."""
    assert os.environ.get("DATABASE_URL") == migrated_db.database_url
    assert os.environ.get("DATABASE_URL_DIRECT") == migrated_db.database_url_direct
    assert not migrated_db.database_url.startswith("postgresql+psycopg://")
    assert migrated_db.database_url_direct.startswith("postgresql+psycopg://")


def test_resolve_db_reuses_external_urls_without_spawning(monkeypatch):
    """AC3: external DATABASE_URL/DATABASE_URL_DIRECT -> reuse, no container spawned."""
    from dev_db import resolve_db

    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@external-host/db")
    monkeypatch.setenv("DATABASE_URL_DIRECT", "postgresql+psycopg://u:p@external-host/db")

    spawned = []

    def fake_spawn():
        spawned.append(True)
        raise AssertionError("should not spawn a container when external URLs are set")

    plan = resolve_db(spawn_container=fake_spawn, migrate=lambda *_a, **_k: None)
    assert plan.source == "external"
    assert plan.database_url == "postgresql://u:p@external-host/db"
    assert plan.database_url_direct == "postgresql+psycopg://u:p@external-host/db"
    assert not spawned


def test_resolve_db_skips_cleanly_when_no_external_db_and_no_docker(monkeypatch):
    """AC3: no external URLs + Docker unavailable -> a clean skip signal, no error."""
    from dev_db import resolve_db

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL_DIRECT", raising=False)

    plan = resolve_db(
        docker_available=lambda: False,
        spawn_container=lambda: (_ for _ in ()).throw(AssertionError("no docker")),
        migrate=lambda *_a, **_k: None,
    )
    assert plan.source == "skip"
    assert plan.database_url is None
    assert plan.database_url_direct is None
