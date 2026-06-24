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
from pathlib import Path

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


def test_container_is_torn_down_even_when_a_test_using_the_fixture_fails():
    """AC2: the finalizer runs on test FAILURE, not just happy-path cleanup.

    Drives a deliberately-failing test that depends on `migrated_db` in a
    fresh pytest subprocess (so this outer test's own use of the fixture
    doesn't interfere), then asserts: (a) the subprocess reports the
    deliberate failure (proving teardown didn't swallow/mask it), and (b) no
    `uptime_pg_pytest` container is left running afterward (proving the
    finalizer fired despite the failure).

    The temp test file is placed inside `backend/tests/` (not an arbitrary
    tmp_path) so pytest's conftest discovery picks up the `migrated_db`
    fixture from this directory's conftest.py; it is removed in a finally
    block regardless of outcome.
    """
    import subprocess
    import sys
    import uuid

    repo_root = Path(__file__).resolve().parents[2]
    tests_dir = Path(__file__).resolve().parent
    failing_test = tests_dir / f"test_zz_deliberately_failing_{uuid.uuid4().hex[:8]}.py"
    # The test prints the container name it was given so this outer test can
    # check specifically for THAT container (not any container matching a
    # shared prefix) — the fixture mints a PID+UUID-unique name per process
    # specifically so a nested/concurrent run never collides with this outer
    # test's own still-alive session container.
    failing_test.write_text(
        "def test_deliberately_fails(migrated_db):\n"
        "    print('CONTAINER_NAME=' + (migrated_db.container_name or ''))\n"
        "    assert False, 'deliberate failure to prove teardown-on-failure'\n",
        encoding="utf-8",
    )

    # Force the subprocess down the container-spawn branch: this outer test's
    # own session fixture may have already set these in os.environ (inherited
    # by subprocesses by default), which would make the inner run reuse the
    # OUTER container instead of spawning its own.
    subprocess_env = dict(os.environ)
    subprocess_env.pop("DATABASE_URL", None)
    subprocess_env.pop("DATABASE_URL_DIRECT", None)

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(failing_test), "-p", "no:cacheprovider", "-q", "-s"],
            cwd=str(repo_root),
            env=subprocess_env,
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0, (
            "expected the deliberately-failing test to fail the subprocess run:\n"
            + result.stdout + result.stderr
        )
        combined_output = result.stdout + result.stderr
        assert "deliberate failure" in combined_output

        container_name = None
        for line in combined_output.splitlines():
            if line.startswith("CONTAINER_NAME="):
                container_name = line.split("=", 1)[1].strip()
        assert container_name, (
            f"could not find the spawned container's name in subprocess output:\n{combined_output}"
        )

        # `docker rm -f` can return slightly before `docker ps -a` reflects the
        # removal; poll briefly rather than racing a single snapshot.
        import time

        deadline = time.monotonic() + 10
        leftover_names = container_name
        while time.monotonic() < deadline:
            leftover = subprocess.run(
                ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
            )
            leftover_names = leftover.stdout.strip()
            if leftover_names == "":
                break
            time.sleep(0.5)
        assert leftover_names == "", (
            f"container {container_name!r} left behind after a failing test"
        )
    finally:
        failing_test.unlink(missing_ok=True)
