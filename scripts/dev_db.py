#!/usr/bin/env python
"""Shared throwaway-Postgres DB harness (STORY-019, dossier §3/§17/§9).

Centralizes the hand-rolled "start postgres:16 -> wait ready -> alembic upgrade
head -> two-URL dialect split" sequence that was previously re-implemented in
every DB-gated brief (Sprint 2 retro). Used two ways:

1. As a CLI: ``python scripts/dev_db.py up`` / ``python scripts/dev_db.py down``
   for manual/local runs of the DB-gated DoD commands
   (``scripts/check_fk_direction.py``, ``alembic upgrade head``).
2. As a library, imported by the pytest session fixture in
   ``backend/tests/conftest.py`` (``backend/tests`` puts this file's directory
   on ``sys.path``; see that conftest's docstring).

Two distinct connection env vars, never mixed (dossier §3, §17):
  - ``DATABASE_URL``        — plain libpq form, e.g. ``postgresql://...``.
    Used by the app runtime and by ``scripts/check_fk_direction.py`` (raw
    psycopg; the ``+psycopg`` prefix makes raw psycopg raise).
  - ``DATABASE_URL_DIRECT`` — psycopg3 dialect form, ``postgresql+psycopg://...``.
    Used by Alembic (``migrations/env.py``; SQLAlchemy 2 needs the psycopg3
    driver name).
Both point at the SAME database when using the throwaway container; only the
dialect prefix differs.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

CONTAINER_NAME = "uptime_pg_pytest"
HOST_PORT = 55432
POSTGRES_PASSWORD = "postgres"
POSTGRES_DB = "uptime"

DATABASE_URL_PLAIN = f"postgresql://postgres:{POSTGRES_PASSWORD}@localhost:{HOST_PORT}/{POSTGRES_DB}"
DATABASE_URL_DIRECT = f"postgresql+psycopg://postgres:{POSTGRES_PASSWORD}@localhost:{HOST_PORT}/{POSTGRES_DB}"

READY_TIMEOUT_SECONDS = 30
READY_POLL_INTERVAL_SECONDS = 0.5


# --------------------------------------------------------------------------
# Docker availability + container lifecycle
# --------------------------------------------------------------------------


def docker_available() -> bool:
    """True iff the `docker` CLI is callable on this machine."""
    try:
        result = subprocess.run(
            ["docker", "version", "--format", "{{.Server.Version}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def start_container(
    name: str = CONTAINER_NAME,
    host_port: int = HOST_PORT,
    password: str = POSTGRES_PASSWORD,
    db: str = POSTGRES_DB,
) -> None:
    """Start a throwaway `postgres:16` container. Idempotent: removes any
    same-named leftover first (e.g. from a prior crashed run)."""
    subprocess.run(["docker", "rm", "-f", name], capture_output=True, text=True)
    result = subprocess.run(
        [
            "docker", "run", "-d", "--name", name,
            "-e", f"POSTGRES_PASSWORD={password}",
            "-e", f"POSTGRES_DB={db}",
            "-p", f"{host_port}:5432",
            "postgres:16",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"docker run failed: {result.stdout}{result.stderr}")


def wait_for_postgres(
    name: str = CONTAINER_NAME,
    timeout_seconds: float = READY_TIMEOUT_SECONDS,
    poll_interval_seconds: float = READY_POLL_INTERVAL_SECONDS,
) -> None:
    """Poll `pg_isready` inside the container until ready or timeout."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        result = subprocess.run(
            ["docker", "exec", name, "pg_isready", "-U", "postgres"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return
        time.sleep(poll_interval_seconds)
    raise TimeoutError(f"Postgres in container {name!r} did not become ready within {timeout_seconds}s")


def stop_container(name: str = CONTAINER_NAME) -> None:
    """Remove the container. Idempotent — ignores "no such container"."""
    subprocess.run(["docker", "rm", "-f", name], capture_output=True, text=True)


# --------------------------------------------------------------------------
# Migration
# --------------------------------------------------------------------------


def run_migrations(database_url_direct: str) -> None:
    """Run `alembic upgrade head` against the given DIRECT URL via subprocess,
    so the real console entry point / env.py path is exercised (matches the
    bare DoD command exactly, just with the env var injected for this call)."""
    env = dict(os.environ)
    env["DATABASE_URL_DIRECT"] = database_url_direct
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"alembic upgrade head failed:\n{result.stdout}\n{result.stderr}")


# --------------------------------------------------------------------------
# Decision logic — reuse external / spawn container / skip
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class DbPlan:
    """The outcome of deciding how to obtain a migrated DB.

    `source` is one of "external" (reused already-set env URLs), "container"
    (spawned a throwaway postgres:16), or "skip" (neither available).
    """

    source: str
    database_url: str | None
    database_url_direct: str | None
    container_name: str | None = None


def resolve_db(
    *,
    env: "os._Environ[str] | dict[str, str] | None" = None,
    docker_available: "callable" = docker_available,
    spawn_container: "callable" = None,
    migrate: "callable" = run_migrations,
    container_name: str = CONTAINER_NAME,
) -> DbPlan:
    """Decide and execute how to obtain a migrated DB; returns a DbPlan.

    Order: (1) reuse external DATABASE_URL/DATABASE_URL_DIRECT if both are set
    in `env` — migrate to ensure they're up to date, no container spawned; (2)
    else if Docker is available, spawn the throwaway container (via
    `spawn_container`, which must start it, wait for readiness, and migrate);
    (3) else return a "skip" plan — the caller (fixture) turns this into a
    clean pytest.skip, never an error.
    """
    if env is None:
        env = os.environ

    external_url = env.get("DATABASE_URL")
    external_direct = env.get("DATABASE_URL_DIRECT")
    if external_url and external_direct:
        migrate(external_direct)
        return DbPlan(
            source="external",
            database_url=external_url,
            database_url_direct=external_direct,
        )

    if not docker_available():
        return DbPlan(source="skip", database_url=None, database_url_direct=None)

    if spawn_container is None:
        spawn_container = lambda: _spawn_default(container_name, migrate)
    spawn_container()
    return DbPlan(
        source="container",
        database_url=DATABASE_URL_PLAIN,
        database_url_direct=DATABASE_URL_DIRECT,
        container_name=container_name,
    )


def _spawn_default(container_name: str, migrate) -> None:
    start_container(name=container_name)
    wait_for_postgres(name=container_name)
    migrate(DATABASE_URL_DIRECT)


# --------------------------------------------------------------------------
# CLI: up / down
# --------------------------------------------------------------------------


def cmd_up(args: argparse.Namespace) -> int:
    name = args.name
    print(f"Starting throwaway postgres:16 container {name!r} on port {args.port}...")
    start_container(name=name, host_port=args.port)
    print("Waiting for readiness...")
    wait_for_postgres(name=name)
    database_url = (
        f"postgresql://postgres:{POSTGRES_PASSWORD}@localhost:{args.port}/{POSTGRES_DB}"
    )
    database_url_direct = (
        f"postgresql+psycopg://postgres:{POSTGRES_PASSWORD}@localhost:{args.port}/{POSTGRES_DB}"
    )
    print("Running `alembic upgrade head`...")
    run_migrations(database_url_direct)

    print("\nDB is up and migrated. Export these in your shell:\n")
    print(f"  export DATABASE_URL={database_url}")
    print(f"  export DATABASE_URL_DIRECT={database_url_direct}")

    if args.env_file:
        env_path = Path(args.env_file)
        env_path.write_text(
            f"DATABASE_URL={database_url}\nDATABASE_URL_DIRECT={database_url_direct}\n",
            encoding="utf-8",
        )
        print(f"\nAlso wrote {env_path} (dotenv form) for tools that source a file.")

    return 0


def cmd_down(args: argparse.Namespace) -> int:
    print(f"Removing container {args.name!r}...")
    stop_container(name=args.name)
    print("Done.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="dev_db.py",
        description="Start/stop the shared throwaway Postgres DB for local DoD gate runs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    up_parser = subparsers.add_parser("up", help="start + wait + migrate + emit URLs")
    up_parser.add_argument("--name", default=CONTAINER_NAME)
    up_parser.add_argument("--port", type=int, default=HOST_PORT)
    up_parser.add_argument(
        "--env-file",
        default=None,
        help="also write DATABASE_URL/DATABASE_URL_DIRECT to this dotenv-style file",
    )
    up_parser.set_defaults(func=cmd_up)

    down_parser = subparsers.add_parser("down", help="remove the container")
    down_parser.add_argument("--name", default=CONTAINER_NAME)
    down_parser.set_defaults(func=cmd_down)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
