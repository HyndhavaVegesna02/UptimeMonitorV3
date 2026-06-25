"""DB-gated tests for the spine schema migration (STORY-006, dossier §9/§11).

These tests exercise the real Alembic migration against a live Postgres,
obtained via the shared `migrated_db` session fixture (STORY-019,
`backend/tests/conftest.py`): it reuses an externally-set DATABASE_URL/
DATABASE_URL_DIRECT, else spawns a throwaway `postgres:16` if Docker is
available, else skips cleanly — so a bare `pytest` run never errors, but
these tests MUST run and pass against a migrated Postgres as part of the DoD.

Each test owns one AC:
  - AC1: all eleven spine tables exist after `upgrade head`.
  - AC3: the three required indexes exist (unique source_event_id, composite
    signal_key/observed_at, partial-unique active-proposal-per-component).
  - AC4: every timestamp column is timestamptz; the three JSONB columns are
    jsonb; apps.config is NOT NULL.
  - AC6: every FK declares an explicit, non-default ON DELETE rule (RESTRICT
    into seeded topology).

AC2 (FK-direction) and AC5 (round-trip) are exercised by
`scripts/check_fk_direction.py` and by the manual upgrade/downgrade/upgrade
DoD sequence respectively (see story report); AC5 also gets a direct
round-trip test here so it runs under `pytest` too.
"""

import os

import psycopg
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


@pytest.fixture
def conn(migrated_db):
    with psycopg.connect(migrated_db.database_url) as connection:
        yield connection


def test_all_eleven_spine_tables_exist(conn):
    """AC1: every spine table exists in the public schema after upgrade head."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
        )
        existing = {row[0] for row in cur.fetchall()}
    missing = SPINE_TABLES - existing
    assert not missing, f"missing spine tables: {missing}"


def test_observations_source_event_id_has_unique_index(conn):
    """AC3: UNIQUE constraint/index on observations(source_event_id)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT indexdef FROM pg_indexes
            WHERE schemaname = 'public' AND tablename = 'observations'
            """
        )
        indexdefs = [row[0] for row in cur.fetchall()]
    matches = [
        d for d in indexdefs if "UNIQUE" in d.upper() and "source_event_id" in d
    ]
    assert matches, f"no unique index on observations(source_event_id); indexes: {indexdefs}"


def test_observations_has_composite_signal_key_observed_at_index(conn):
    """AC3: composite index on observations(signal_key, observed_at)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT indexdef FROM pg_indexes
            WHERE schemaname = 'public' AND tablename = 'observations'
            """
        )
        indexdefs = [row[0] for row in cur.fetchall()]
    matches = [
        d for d in indexdefs
        if "signal_key" in d and "observed_at" in d
        and d.index("signal_key") < d.index("observed_at")
    ]
    assert matches, f"no composite (signal_key, observed_at) index; indexes: {indexdefs}"


def test_status_proposals_has_partial_unique_active_index(conn):
    """AC3 (-> §11): partial UNIQUE index on status_proposals(component_id)
    filtered to active proposals (state = 'open'), enforcing at most one
    active proposal per component.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT indexdef FROM pg_indexes
            WHERE schemaname = 'public' AND tablename = 'status_proposals'
            """
        )
        indexdefs = [row[0] for row in cur.fetchall()]
    matches = [
        d for d in indexdefs
        if "UNIQUE" in d.upper() and "component_id" in d and "WHERE" in d.upper()
    ]
    assert matches, f"no partial unique index on status_proposals(component_id); indexes: {indexdefs}"


# AC4 — timestamptz, jsonb, NOT NULL.

TIMESTAMP_COLUMNS = [
    ("apps", "created_at"),
    ("apps", "updated_at"),
    ("signals", "created_at"),
    ("signals", "updated_at"),
    ("components", "created_at"),
    ("components", "updated_at"),
    ("observations", "observed_at"),
    ("observations", "created_at"),
    ("problem_signals", "started_at"),
    ("problem_signals", "ended_at"),
    ("problem_signals", "created_at"),
    ("watermarks", "watermark"),
    ("watermarks", "updated_at"),
    ("rejected_observations", "rejected_at"),
    ("status_proposals", "proposed_at"),
    ("status_proposals", "resolved_at"),
    ("status_proposals", "created_at"),
    ("approval_events", "occurred_at"),
    ("publications", "published_at"),
    ("maintenance_windows", "starts_at"),
    ("maintenance_windows", "ends_at"),
    ("maintenance_windows", "created_at"),
]


@pytest.mark.parametrize("table,column", TIMESTAMP_COLUMNS)
def test_timestamp_columns_are_timestamptz(conn, table, column):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT data_type FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s AND column_name = %s
            """,
            (table, column),
        )
        row = cur.fetchone()
    assert row is not None, f"{table}.{column} does not exist"
    assert row[0] == "timestamp with time zone", (
        f"{table}.{column} is {row[0]!r}, expected timestamptz"
    )


@pytest.mark.parametrize(
    "table,column",
    [
        ("apps", "config"),
        ("observations", "source"),
        ("rejected_observations", "payload"),
    ],
)
def test_jsonb_columns_are_jsonb(conn, table, column):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT data_type FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s AND column_name = %s
            """,
            (table, column),
        )
        row = cur.fetchone()
    assert row is not None, f"{table}.{column} does not exist"
    assert row[0] == "jsonb", f"{table}.{column} is {row[0]!r}, expected jsonb"


def test_apps_config_is_not_null(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT is_nullable FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'apps' AND column_name = 'config'
            """
        )
        row = cur.fetchone()
    assert row is not None, "apps.config does not exist"
    assert row[0] == "NO", "apps.config must be NOT NULL"


# AC6 — every FK declares an explicit ON DELETE rule; topology references are RESTRICT.

TOPOLOGY_TABLES = {"apps", "signals", "components"}


def test_every_fk_has_explicit_on_delete_rule(conn):
    """No FK relies on the implicit default (NO ACTION is only acceptable when
    explicitly chosen for a non-topology target; references into seeded
    topology must be RESTRICT). We assert every FK's delete_rule is one of the
    explicit values Postgres reports, and that every FK targeting a topology
    table is specifically RESTRICT.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT tc.table_name AS source_table,
                   ccu.table_name AS target_table,
                   rc.delete_rule
            FROM information_schema.table_constraints tc
            JOIN information_schema.referential_constraints rc
              ON tc.constraint_name = rc.constraint_name
             AND tc.table_schema = rc.constraint_schema
            JOIN information_schema.constraint_column_usage ccu
              ON rc.unique_constraint_name = ccu.constraint_name
             AND rc.unique_constraint_schema = ccu.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
            """
        )
        rows = cur.fetchall()
    assert rows, "expected at least one FK in the spine schema"
    for source, target, delete_rule in rows:
        assert delete_rule in ("RESTRICT", "CASCADE", "SET NULL", "SET DEFAULT"), (
            f"{source} -> {target} has non-explicit delete_rule {delete_rule!r}"
        )
        if target in TOPOLOGY_TABLES:
            assert delete_rule == "RESTRICT", (
                f"{source} -> {target} (topology) must be ON DELETE RESTRICT, "
                f"got {delete_rule!r}"
            )


def test_migration_round_trips_upgrade_downgrade_upgrade(migrated_db):
    """AC5: upgrade head -> downgrade base -> upgrade head, each succeeding,
    and downgrade actually drops every spine table (round-trip is real, not
    a no-op).
    """
    import subprocess
    import sys

    # `migrated_db` has already set DATABASE_URL/DATABASE_URL_DIRECT in the
    # process env (reused-external or spawned-container, in the right
    # dialects) — read them from there rather than re-deriving from the
    # fixture object, since the alembic subprocess inherits os.environ.
    direct_url = os.environ["DATABASE_URL_DIRECT"]

    def run_alembic(*args):
        env = dict(os.environ)
        env["DATABASE_URL_DIRECT"] = direct_url
        return subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            cwd=os.environ.get("REPO_ROOT", os.getcwd()),
            env=env,
            capture_output=True,
            text=True,
        )

    # Ensure we start from head (idempotent if already there).
    result = run_alembic("upgrade", "head")
    assert result.returncode == 0, result.stdout + result.stderr

    result = run_alembic("downgrade", "base")
    assert result.returncode == 0, result.stdout + result.stderr

    with psycopg.connect(migrated_db.database_url) as connection:
        with connection.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
            )
            remaining = {row[0] for row in cur.fetchall()}
    assert not (remaining & SPINE_TABLES), (
        f"downgrade base left spine tables behind: {remaining & SPINE_TABLES}"
    )

    result = run_alembic("upgrade", "head")
    assert result.returncode == 0, result.stdout + result.stderr
