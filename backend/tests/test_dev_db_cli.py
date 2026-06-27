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
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.skipif(
    subprocess.run(
        ["docker", "version"], capture_output=True, text=True
    ).returncode
    != 0,
    reason="requires Docker to exercise the dev_db.py CLI end-to-end",
)

_TEST_CONTAINER = "uptime_pg_pytest_cli_test"
_TEST_PORT = 55433


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "dev_db.py"), *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )


def test_up_then_check_fk_direction_then_down():
    # Ensure no leftover from a prior crashed run before we start.
    subprocess.run(["docker", "rm", "-f", _TEST_CONTAINER], capture_output=True, text=True)

    try:
        up_result = _run_cli("up", "--name", _TEST_CONTAINER, "--port", str(_TEST_PORT))
        assert up_result.returncode == 0, up_result.stdout + up_result.stderr

        url_match = re.search(r"export DATABASE_URL=(\S+)", up_result.stdout)
        direct_match = re.search(r"export DATABASE_URL_DIRECT=(\S+)", up_result.stdout)
        assert url_match, f"up did not print DATABASE_URL:\n{up_result.stdout}"
        assert direct_match, f"up did not print DATABASE_URL_DIRECT:\n{up_result.stdout}"

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
        down_result = _run_cli("down", "--name", _TEST_CONTAINER)
        assert down_result.returncode == 0, down_result.stdout + down_result.stderr

    leftover = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"name={_TEST_CONTAINER}", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
    )
    assert leftover.stdout.strip() == ""


def test_up_idempotent_against_leftover_container():
    # Ensure no leftover from a prior run
    subprocess.run(["docker", "rm", "-f", _TEST_CONTAINER], capture_output=True, text=True)

    # 1. Start a container manually with the target name
    result = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            _TEST_CONTAINER,
            "-p",
            f"{_TEST_PORT}:5432",
            "postgres:16",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    try:
        # 2. Run our CLI up command while the container is running.
        # It should force-remove it and recreate/migrate it without error.
        up_result = _run_cli("up", "--name", _TEST_CONTAINER, "--port", str(_TEST_PORT))
        assert up_result.returncode == 0, up_result.stdout + up_result.stderr
        assert "DB is up and migrated" in up_result.stdout
    finally:
        # Cleanup
        _run_cli("down", "--name", _TEST_CONTAINER)

