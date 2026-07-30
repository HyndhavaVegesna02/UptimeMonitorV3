"""STORY-182 fix round -- MAJOR 3 (exception-safe loop teardown), MAJOR 4
(`_terminate_and_verify`'s returned field must describe what it actually
observed, not claim OS-level PID evidence it does not have), and the
API-port preflight minor (`API_PORT` is hardcoded and was never checked
before launch, though `_port_is_free` already existed and is used
post-teardown -- a busy port cost a silent 30s health-check timeout).

All drive REAL OS resources (`subprocess.Popen`, a real bound `socket`) --
no mocking of `subprocess`/`socket` itself, consistent with this sprint's
standing "no over-mocking" bar.
"""

from __future__ import annotations

import socket
import subprocess
import sys

import pytest
from demo_loop_gate.harness import (
    RealityGateError,
    _assert_api_port_free,
    _terminate_and_verify,
    _terminate_loop_after,
)


def _spawn_sleeper(seconds: float = 30.0) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-c", f"import time; time.sleep({seconds})"]
    )


def test_terminate_loop_after_terminates_the_process_even_when_body_raises():
    """MAJOR 3: before `_terminate_loop_after` existed, an exception raised
    while waiting on the loop subprocess (e.g. a `KeyboardInterrupt` during
    the up-to-270s poll, a `UnicodeDecodeError` from `read_text`, an
    `IndexError`) left it running with no `finally` to reap it. Here `body`
    raises deliberately; the real subprocess must still be dead afterwards."""
    proc = _spawn_sleeper()
    assert proc.poll() is None, "the sleeper should still be alive at the start"

    def _raising_body() -> None:
        raise ValueError("simulated failure between launch and teardown")

    with pytest.raises(ValueError, match="simulated failure"):
        _terminate_loop_after(proc, _raising_body)

    assert proc.poll() is not None, (
        "the loop subprocess must be terminated even though body() raised"
    )


def test_terminate_loop_after_returns_the_teardown_dict_on_success():
    proc = _spawn_sleeper()

    calls: list[str] = []

    def _body() -> None:
        calls.append("ran")

    teardown = _terminate_loop_after(proc, _body)

    assert calls == ["ran"]
    assert teardown["name"] == "loop"
    assert teardown["pid"] == proc.pid
    assert proc.poll() is not None


def test_terminate_and_verify_field_is_reaped_returncode_not_gone_by_pid():
    """MAJOR 4: `proc.poll()` called immediately after `proc.wait()` has
    already returned only reads Popen's cached `returncode` -- it never asks
    the OS again, so it can never be independent "gone BY PID" evidence.
    The field name must say what is actually true."""
    proc = _spawn_sleeper()

    result = _terminate_and_verify(proc, name="loop")

    assert "reaped_returncode_observed" in result
    assert "gone_by_pid" not in result
    assert result["reaped_returncode_observed"] is True
    assert result["returncode"] is not None


def test_assert_api_port_free_raises_on_a_genuinely_busy_port():
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    busy_port = listener.getsockname()[1]
    try:
        with pytest.raises(RealityGateError, match=str(busy_port)):
            _assert_api_port_free(busy_port)
    finally:
        listener.close()


def test_assert_api_port_free_passes_on_a_genuinely_free_port():
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    free_port = listener.getsockname()[1]
    listener.close()  # release it before asserting free

    _assert_api_port_free(free_port)  # must not raise
