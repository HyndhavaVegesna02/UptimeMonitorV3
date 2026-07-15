"""STORY-019 AC1: `scripts/dev_db.py up`/`down` as a CLI.

Proves the documented manual workflow mechanically rather than only by hand:
`up` starts a throwaway postgres:16, waits for readiness, runs
`alembic upgrade head`, and prints both URLs in their correct dialects; with
those exported, `scripts/check_fk_direction.py` exits 0 with no further URL
juggling; `down` removes the container.

This is the one piece of the harness that's awkward to unit-test in isolation
(it really does spin up Docker + a real DB), so this is an integration check
against the real CLI subprocess and a real container, skipped if Docker is
unavailable.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.skipif(
    subprocess.run(["docker", "version"], capture_output=True, text=True).returncode
    != 0,
    reason="requires Docker to exercise the dev_db.py CLI end-to-end",
)


@pytest.fixture(scope="module", autouse=True)
def run_with_blocker():
    """Spin up an unrelated container on the old fixed port and name to prove the CLI tests don't collide with it (STORY-080).

    Name: "uptime_pg_pytest_cli_test", port: 55433
    """
    blocker_name = "uptime_pg_pytest_cli_test"
    blocker_port = 55433
    # Remove any existing blocker container
    subprocess.run(["docker", "rm", "-f", blocker_name], capture_output=True, text=True)
    # Start the blocker
    subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            blocker_name,
            "-p",
            f"{blocker_port}:5432",
            "postgres:16",
        ],
        capture_output=True,
        text=True,
    )
    # Give Docker a brief moment
    time.sleep(1)
    yield
    # Clean up the blocker
    subprocess.run(["docker", "rm", "-f", blocker_name], capture_output=True, text=True)


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "dev_db.py"), *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )


def test_up_then_check_fk_direction_then_down():
    from dev_db import _free_tcp_port, unique_container_name

    container_name = unique_container_name(prefix="uptime_pg_pytest_cli_test")
    port = _free_tcp_port()

    # Ensure no leftover from a prior crashed run before we start.
    subprocess.run(
        ["docker", "rm", "-f", container_name], capture_output=True, text=True
    )

    try:
        up_result = _run_cli("up", "--name", container_name, "--port", str(port))
        assert up_result.returncode == 0, up_result.stdout + up_result.stderr

        url_match = re.search(r"export DATABASE_URL=(\S+)", up_result.stdout)
        direct_match = re.search(r"export DATABASE_URL_DIRECT=(\S+)", up_result.stdout)
        assert url_match, f"up did not print DATABASE_URL:\n{up_result.stdout}"
        assert direct_match, (
            f"up did not print DATABASE_URL_DIRECT:\n{up_result.stdout}"
        )

        database_url = url_match.group(1)
        database_url_direct = direct_match.group(1)
        assert not database_url.startswith("postgresql+psycopg://")
        assert database_url_direct.startswith("postgresql+psycopg://")

        # "no manual URL juggling" -> exactly what `up` printed, exported as-is.
        env = dict(os.environ)
        env["DATABASE_URL"] = database_url
        env["DATABASE_URL_DIRECT"] = database_url_direct

        fk_result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "check_fk_direction.py")],
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
        )
        assert fk_result.returncode == 0, fk_result.stdout + fk_result.stderr
    finally:
        down_result = _run_cli("down", "--name", container_name)
        assert down_result.returncode == 0, down_result.stdout + down_result.stderr

    leftover = subprocess.run(
        [
            "docker",
            "ps",
            "-a",
            "--filter",
            f"name={container_name}",
            "--format",
            "{{.Names}}",
        ],
        capture_output=True,
        text=True,
    )
    assert leftover.stdout.strip() == ""


def test_up_idempotent_against_leftover_container():
    from dev_db import _free_tcp_port, unique_container_name

    container_name = unique_container_name(prefix="uptime_pg_pytest_cli_idemp")
    port = _free_tcp_port()

    # Ensure no leftover from a prior run
    subprocess.run(
        ["docker", "rm", "-f", container_name], capture_output=True, text=True
    )

    # 1. Start a container manually with the target name
    result = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            container_name,
            "-p",
            f"{port}:5432",
            "postgres:16",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    try:
        # 2. Run our CLI up command while the container is running.
        # It should force-remove it and recreate/migrate it without error.
        up_result = _run_cli("up", "--name", container_name, "--port", str(port))
        assert up_result.returncode == 0, up_result.stdout + up_result.stderr
        assert "DB is up and migrated" in up_result.stdout
    finally:
        # Cleanup
        _run_cli("down", "--name", container_name)
