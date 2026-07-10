"""Unit tests for the dev_db readiness-timeout parsing and wait/backoff logic.

Filed against Sprint 43 quality-review MAJOR-1 (M1) + m5: `dev_db.py` parsed
`DEV_DB_READY_TIMEOUT_SECONDS` at MODULE scope with a bare `float(...)`, so an
empty/garbage value raised `ValueError` at import time — and
`backend/tests/conftest.py` imports `dev_db` at collection time, so that
crashed the ENTIRE pytest session instead of the graceful skip the harness is
built around. The fix made the parse lazy (`_ready_timeout_seconds()`, called
from `wait_for_postgres` at call time, not baked into a default arg). This
file is the regression coverage that was missing (m5) — the M1 bug slipped
through review with zero tests.

Hermetic: no Docker, no network, no real container. `subprocess.run` is
monkeypatched for the `wait_for_postgres` tests.
"""

from __future__ import annotations

import subprocess

import dev_db
import pytest

# --------------------------------------------------------------------------
# _ready_timeout_seconds()
# --------------------------------------------------------------------------


def test_ready_timeout_seconds_defaults_when_unset(monkeypatch):
    monkeypatch.delenv("DEV_DB_READY_TIMEOUT_SECONDS", raising=False)
    assert dev_db._ready_timeout_seconds() == 60.0


def test_ready_timeout_seconds_parses_valid_value(monkeypatch):
    monkeypatch.setenv("DEV_DB_READY_TIMEOUT_SECONDS", "12.5")
    assert dev_db._ready_timeout_seconds() == 12.5


def test_ready_timeout_seconds_defaults_on_empty_string(monkeypatch):
    """Regression guard for M1: `export DEV_DB_READY_TIMEOUT_SECONDS=` (empty)
    must NOT raise — it must fall back to the default."""
    monkeypatch.setenv("DEV_DB_READY_TIMEOUT_SECONDS", "")
    assert dev_db._ready_timeout_seconds() == 60.0


def test_ready_timeout_seconds_defaults_on_non_numeric_value(monkeypatch):
    monkeypatch.setenv("DEV_DB_READY_TIMEOUT_SECONDS", "not-a-number")
    assert dev_db._ready_timeout_seconds() == 60.0


def test_ready_timeout_seconds_reads_env_lazily_per_call(monkeypatch):
    """The read must happen at CALL time, not be frozen at import time."""
    monkeypatch.delenv("DEV_DB_READY_TIMEOUT_SECONDS", raising=False)
    assert dev_db._ready_timeout_seconds() == 60.0
    monkeypatch.setenv("DEV_DB_READY_TIMEOUT_SECONDS", "5")
    assert dev_db._ready_timeout_seconds() == 5.0


# --------------------------------------------------------------------------
# wait_for_postgres retry/backoff + timeout
# --------------------------------------------------------------------------


def test_wait_for_postgres_raises_timeout_error_without_spawning_a_container(
    monkeypatch,
):
    """`pg_isready` never reports ready -> TimeoutError after the budget, with
    NO real `docker`/subprocess call ever actually invoked (stubbed) and no
    container spawned. Uses a tiny explicit `timeout_seconds` to keep the test
    fast and to prove the seam works independent of the env knob."""
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="")

    monkeypatch.setattr(dev_db.subprocess, "run", fake_run)
    monkeypatch.setattr(dev_db.time, "sleep", lambda _seconds: None)

    with pytest.raises(TimeoutError):
        dev_db.wait_for_postgres(
            name="not-a-real-container",
            timeout_seconds=0.01,
            poll_interval_seconds=0.01,
        )

    assert calls, "expected pg_isready to have been attempted at least once"
    assert all(c[:2] == ["docker", "exec"] for c in calls)


def test_wait_for_postgres_defaults_timeout_from_env_when_not_passed(monkeypatch):
    """With `timeout_seconds` omitted, the budget comes from
    `_ready_timeout_seconds()` (the env knob), read at call time — the
    regression this whole story is about."""
    monkeypatch.setenv("DEV_DB_READY_TIMEOUT_SECONDS", "0.01")

    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="")

    monkeypatch.setattr(dev_db.subprocess, "run", fake_run)
    monkeypatch.setattr(dev_db.time, "sleep", lambda _seconds: None)

    with pytest.raises(TimeoutError):
        dev_db.wait_for_postgres(
            name="not-a-real-container", poll_interval_seconds=0.01
        )


def test_wait_for_postgres_returns_once_pg_isready_reports_ready(monkeypatch):
    """Sanity check on the happy path: a returncode-0 `pg_isready` attempt
    ends the poll loop without raising."""

    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(dev_db.subprocess, "run", fake_run)
    monkeypatch.setattr(dev_db.time, "sleep", lambda _seconds: None)

    dev_db.wait_for_postgres(
        name="not-a-real-container", timeout_seconds=1.0, poll_interval_seconds=0.01
    )
