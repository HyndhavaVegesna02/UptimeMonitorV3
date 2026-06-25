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

import pytest

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


def _docker_unavailable() -> bool:
    import subprocess as _sp

    return _sp.run(["docker", "version"], capture_output=True, text=True).returncode != 0


@pytest.mark.skipif(_docker_unavailable(), reason="requires Docker to spawn a real container")
def test_spawn_failure_does_not_leak_a_container(monkeypatch):
    """MAJOR regression: if readiness or migration raises AFTER start_container
    has created the container, resolve_db must tear that container down before
    re-raising — otherwise the PID+UUID-uniquely-named container leaks with
    nothing to ever reclaim it. The failure happens inside resolve_db, BEFORE
    the fixture's try/finally around `yield` is established, so the cleanup
    cannot live in the fixture; it must be in the spawn path itself.
    """
    import subprocess

    import dev_db

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL_DIRECT", raising=False)

    name = dev_db.unique_container_name(prefix="uptime_pg_pytest_leaktest")

    def failing_migrate(_direct_url):
        raise RuntimeError("simulated alembic upgrade head failure after container start")

    with pytest.raises(RuntimeError, match="simulated alembic"):
        dev_db.resolve_db(migrate=failing_migrate, container_name=name)

    # The container was created by start_container, then migrate raised — it
    # must NOT survive.
    leftover = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"name={name}", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
    )
    # Defensive cleanup so a regression doesn't leak across runs while red.
    if leftover.stdout.strip():
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, text=True)
    assert leftover.stdout.strip() == "", (
        f"spawn-time failure leaked container {name!r}"
    )


@pytest.mark.skipif(_docker_unavailable(), reason="requires Docker to spawn a real container")
def test_container_is_torn_down_even_when_a_test_using_the_fixture_fails(monkeypatch):
    """AC2: the finalizer runs on test FAILURE, not just happy-path cleanup.

    Drives `provide_migrated_db()` directly: advance it to get a live
    container-backed plan, then `.throw()` an exception into it at the
    `yield` point (simulating a test that uses the fixture and fails). The
    generator has no `except` around the yield, so its `finally` runs
    teardown and the exception propagates out of `.throw()` unchanged.

    This is deterministic and in-process: exactly one container is spawned
    (no nested pytest subprocess, no second concurrent container, no temp
    test file), unlike the previous version of this test.
    """
    import subprocess

    from conftest import provide_migrated_db

    # This outer test process may already have DATABASE_URL/DATABASE_URL_DIRECT
    # set (e.g. by the session-scoped `migrated_db` fixture having run earlier
    # in the suite). Clear them so resolve_db() takes the container-spawn
    # branch instead of the reuse branch — this test needs a REAL spawned
    # container to prove its teardown.
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL_DIRECT", raising=False)

    gen = provide_migrated_db()
    plan = next(gen)
    assert plan.source == "container"
    container_name = plan.container_name
    assert container_name

    running = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
    )
    assert running.stdout.strip() == container_name, (
        f"expected container {container_name!r} to exist after spawn:\n{running.stdout}{running.stderr}"
    )

    try:
        with pytest.raises(RuntimeError, match="simulated test failure"):
            gen.throw(RuntimeError("simulated test failure"))
    finally:
        # Defensive cleanup so a regression doesn't leak across runs while red.
        leftover = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
        )
        if leftover.stdout.strip():
            subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, text=True)

    assert leftover.stdout.strip() == "", (
        f"container {container_name!r} left behind after the fixture-using test failed"
    )
