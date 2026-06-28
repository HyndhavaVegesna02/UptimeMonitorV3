"""Test config: make the repo-root `scripts/` dir importable, and provide the
shared throwaway-DB session fixture (STORY-019).

`scripts/` holds standalone CI scripts (e.g. check_fk_direction.py, dev_db.py)
that are not part of the `src` package but whose pure logic is unit-tested.
This repo-root is two levels up from this file (backend/tests/conftest.py ->
repo root).
"""

import os
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import dev_db  # noqa: E402  (after sys.path setup above)


def provide_migrated_db():
    """Generator implementing the `migrated_db` fixture's lifecycle.

    Extracted as a plain generator so the teardown-on-failure contract can be
    driven directly in a test (`.throw()` an exception in, assert the
    container is still torn down) — deterministically, without racing a nested
    pytest subprocess on Docker spin-up.

    Decision order (STORY-019, dossier §3/§17):
      1. If DATABASE_URL + DATABASE_URL_DIRECT are already set externally
         (CI, a developer's running DB), reuse them — re-running
         `alembic upgrade head` to ensure they're migrated — and spawn no
         container.
      2. Else if Docker is available, spawn a throwaway `postgres:16`
         (dev_db.start_container), wait for readiness, migrate, and yield.
         A finalizer tears the container down even if a test fails (it runs
         in a try/finally around the yield, not as happy-path-only cleanup).
      3. Else (no external DB, no Docker): skip cleanly — no error — so a
         bare `pytest` run on a machine without Docker/DB still passes.
    """
    plan = dev_db.resolve_db()

    if plan.source == "skip":
        pytest.skip(
            "no DATABASE_URL/DATABASE_URL_DIRECT set and Docker is unavailable; "
            "skipping DB-gated tests (see scripts/dev_db.py)"
        )

    # Reflect the resolved URLs into the process env so code paths that read
    # them directly from os.environ (e.g. scripts/check_fk_direction.py,
    # migrations/env.py via subprocess) see the same values.
    prev_url = os.environ.get("DATABASE_URL")
    prev_direct = os.environ.get("DATABASE_URL_DIRECT")
    os.environ["DATABASE_URL"] = plan.database_url
    os.environ["DATABASE_URL_DIRECT"] = plan.database_url_direct

    try:
        yield plan
    finally:
        if plan.source == "container":
            dev_db.stop_container(name=plan.container_name)
        if prev_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prev_url
        if prev_direct is None:
            os.environ.pop("DATABASE_URL_DIRECT", None)
        else:
            os.environ["DATABASE_URL_DIRECT"] = prev_direct


@pytest.fixture(scope="session")
def migrated_db():
    """Session-scoped throwaway-DB fixture; see provide_migrated_db()."""
    yield from provide_migrated_db()


@pytest.fixture
def clean_runtime_tables(migrated_db):
    """Function-scoped fixture: truncate runtime tables before each DB test.

    Ensures DB-gated tests are order/state-independent on a reused DB (STORY-039).
    Truncates the runtime tables that accumulate data across test runs:
      - rejected_observations (no FK, can be truncated directly)
      - observations (FK→signals; CASCADE to no dependents)
      - watermarks (FK→signals; CASCADE to no dependents)
      - problem_signals (FK→signals; CASCADE to no dependents)
    Leaves topology tables (apps, signals, components) intact so tests that
    call seed_signal/seed_component still work with ON CONFLICT DO NOTHING.
    Workflow tables (status_proposals etc.) are NOT truncated here — tests that
    need them clean already perform their own TRUNCATE components CASCADE.

    Any DB-gated test that makes count/existence assertions about rows IT created
    should request this fixture (or use the shared `engine` fixture which depends
    on it — defined in conftest so all persistence adapter tests get isolation
    without individual test edits).
    """
    import psycopg

    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "TRUNCATE TABLE rejected_observations, observations, watermarks, problem_signals"
            )
        conn.commit()
    yield


@pytest.fixture
def engine(migrated_db, clean_runtime_tables):  # noqa: F811
    """Function-scoped SQLAlchemy engine for DB-gated tests (STORY-039).

    Moved here from test_persistence_adapters.py so clean_runtime_tables runs
    before every test that requests `engine` — making the full suite
    order/state-independent on a reused DB without editing each test individually.
    """
    import sqlalchemy as sa
    from src.composition.settings import to_psycopg_url

    eng = sa.create_engine(to_psycopg_url(migrated_db.database_url), future=True)
    try:
        yield eng
    finally:
        eng.dispose()
