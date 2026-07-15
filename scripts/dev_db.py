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
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

CONTAINER_NAME = "uptime_pg_pytest"
HOST_PORT = 55432
POSTGRES_PASSWORD = "postgres"
POSTGRES_DB = "uptime"

_DEFAULT_READY_TIMEOUT_SECONDS = 60.0
READY_POLL_INTERVAL_SECONDS = 0.5


def _ready_timeout_seconds() -> float:
    """Read `DEV_DB_READY_TIMEOUT_SECONDS`; fall back to the default (60.0s) on
    a missing, empty, or non-numeric value.

    Called LAZILY (at `wait_for_postgres` call time, not at import time) so a
    bad env value can never crash test collection (`backend/tests/conftest.py`
    imports this module at collection time) — it degrades to the default
    instead (STORY-073 fix-forward)."""
    raw = os.environ.get("DEV_DB_READY_TIMEOUT_SECONDS")
    if not raw:
        return _DEFAULT_READY_TIMEOUT_SECONDS
    try:
        return float(raw)
    except ValueError:
        return _DEFAULT_READY_TIMEOUT_SECONDS


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


def _free_tcp_port() -> int:
    """Ask the OS for an ephemeral free TCP port (avoids collisions between
    concurrent/nested pytest runs that would otherwise fight over a fixed
    host port, e.g. a subprocess-driven test spawning a second throwaway DB
    while the outer session's container is still bound to the default port)."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def unique_container_name(prefix: str = "uptime_pg_pytest") -> str:
    """A container name unique to this process, to avoid collisions when a
    test spawns a nested pytest subprocess that also resolves a DB (e.g. the
    teardown-on-failure test) while this process's own container is alive."""
    return f"{prefix}_{os.getpid()}_{uuid.uuid4().hex[:8]}"


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
            "docker",
            "run",
            "-d",
            "--name",
            name,
            "-e",
            f"POSTGRES_PASSWORD={password}",
            "-e",
            f"POSTGRES_DB={db}",
            "-p",
            f"{host_port}:5432",
            "postgres:16",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"docker run failed: {result.stdout}{result.stderr}")


def wait_for_postgres(
    name: str = CONTAINER_NAME,
    host_port: int | None = None,
    timeout_seconds: float | None = None,
    poll_interval_seconds: float = READY_POLL_INTERVAL_SECONDS,
) -> None:
    """Poll `pg_isready` inside the container and verify connection readiness until ready or timeout.

    `timeout_seconds` defaults to `_ready_timeout_seconds()` (the current
    `DEV_DB_READY_TIMEOUT_SECONDS` env value, or 60.0s), read LAZILY here at
    call time rather than baked in at import time (STORY-073 fix-forward, M1).

    Cites: STORY-073, STORY-080
    """
    if timeout_seconds is None:
        timeout_seconds = _ready_timeout_seconds()
    deadline = time.monotonic() + timeout_seconds
    current_poll = poll_interval_seconds
    while time.monotonic() < deadline:
        try:
            # Bounded attempt with a 5-second timeout (STORY-073)
            result = subprocess.run(
                ["docker", "exec", name, "pg_isready", "-U", "postgres"],
                capture_output=True,
                text=True,
                timeout=5.0,
            )
            if result.returncode == 0:
                if host_port is not None:
                    try:
                        import psycopg

                        with psycopg.connect(
                            f"postgresql://postgres:{POSTGRES_PASSWORD}@localhost:{host_port}/{POSTGRES_DB}",
                            connect_timeout=2,
                        ):
                            pass
                        return
                    except (ImportError, Exception):
                        # Transient connection drops or psycopg import issue, treat as not ready and retry
                        pass
                else:
                    return
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
            # If docker exec times out or fails under Docker host contention,
            # we treat it as not ready and continue the loop.
            pass
        time.sleep(current_poll)
        current_poll = min(current_poll * 1.5, 5.0)
    raise TimeoutError(
        f"Postgres in container {name!r} did not become ready within {timeout_seconds}s"
    )


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
        raise RuntimeError(
            f"alembic upgrade head failed:\n{result.stdout}\n{result.stderr}"
        )


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
    env: Mapping[str, str] | None = None,
    docker_available: Callable[[], bool] = docker_available,
    spawn_container: Callable[[], None] | None = None,
    migrate: Callable[[str], None] = run_migrations,
    container_name: str | None = None,
) -> DbPlan:
    """Decide and execute how to obtain a migrated DB; returns a DbPlan.

    Order: (1) reuse external DATABASE_URL/DATABASE_URL_DIRECT if both are set
    in `env` — migrate to ensure they're up to date, no container spawned; (2)
    else if Docker is available, spawn the throwaway container (via
    `spawn_container`, which must start it, wait for readiness, and migrate);
    (3) else return a "skip" plan — the caller (fixture) turns this into a
    clean pytest.skip, never an error.

    The spawned container gets a PID+UUID-unique name and an OS-assigned free
    host port by default (not the fixed CONTAINER_NAME/HOST_PORT the CLI
    `up`/`down` use) — this avoids a nested/concurrent pytest run (e.g. a
    subprocess-driven test) colliding with this process's own still-alive
    session container on name or port.
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

    name = container_name or unique_container_name()
    if spawn_container is None:
        # Default path: pick a free host port (avoids collisions between
        # concurrent/nested runs) and report the URLs at that port.
        port_box: list[int] = []
        _spawn_default(name, migrate, port_box)
        port = port_box[0]
    else:
        # Injected spawner (tests): it owns the lifecycle and is assumed to
        # bind the fixed default port, so report URLs at HOST_PORT.
        spawn_container()
        port = HOST_PORT
    database_url = (
        f"postgresql://postgres:{POSTGRES_PASSWORD}@localhost:{port}/{POSTGRES_DB}"
    )
    database_url_direct = f"postgresql+psycopg://postgres:{POSTGRES_PASSWORD}@localhost:{port}/{POSTGRES_DB}"

    return DbPlan(
        source="container",
        database_url=database_url,
        database_url_direct=database_url_direct,
        container_name=name,
    )


def _spawn_default(container_name: str, migrate, port_box: list) -> None:
    """Start -> wait-ready -> migrate. If readiness or migration raises AFTER
    the container is created, tear it down before re-raising so a half-started
    container never leaks (the failure propagates out of resolve_db, before any
    caller finalizer is established, so cleanup must live here)."""
    port = _free_tcp_port()
    start_container(name=container_name, host_port=port)
    try:
        wait_for_postgres(name=container_name, host_port=port)
        direct_url = f"postgresql+psycopg://postgres:{POSTGRES_PASSWORD}@localhost:{port}/{POSTGRES_DB}"
        migrate(direct_url)
    except BaseException:
        stop_container(name=container_name)
        raise
    port_box.append(port)


# --------------------------------------------------------------------------
# CLI: up / down
# --------------------------------------------------------------------------


def cmd_up(args: argparse.Namespace) -> int:
    name = args.name
    print(f"Starting throwaway postgres:16 container {name!r} on port {args.port}...")
    start_container(name=name, host_port=args.port)
    database_url = (
        f"postgresql://postgres:{POSTGRES_PASSWORD}@localhost:{args.port}/{POSTGRES_DB}"
    )
    database_url_direct = f"postgresql+psycopg://postgres:{POSTGRES_PASSWORD}@localhost:{args.port}/{POSTGRES_DB}"
    try:
        print("Waiting for readiness...")
        wait_for_postgres(name=name, host_port=args.port)
        print("Running `alembic upgrade head`...")
        run_migrations(database_url_direct)
    except BaseException:
        # Don't leave a half-started container behind on readiness/migration
        # failure (same reasoning as _spawn_default).
        stop_container(name=name)
        raise

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
