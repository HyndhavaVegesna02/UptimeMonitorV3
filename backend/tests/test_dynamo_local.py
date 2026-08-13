from __future__ import annotations

import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

# Add repo root and scripts to sys.path so we can import dynamo_local
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import dynamo_local  # noqa: E402


def test_import_exists():
    assert dynamo_local is not None


def test_candidate_port_for_test_injection_stays_outside_windows_dynamic_range():
    """STORY-179 AC1: the allocated port must never land in Windows' WinNAT
    dynamic range (>= 49152), where Docker's mapping is displayed by
    `docker ps` but never actually routes -- container `Up`, every request
    hangs forever.

    Sampled 5x rather than once: measured live on this machine, the OS
    hands out ports from that exact range on every call (e.g. 57634..57643),
    so a single sample already reds against the pre-fix `_free_tcp_port()`
    (renamed `_candidate_port_for_test_injection` in the fix round, MINOR 5),
    but 5 removes any doubt about a lucky draw.
    """
    for _ in range(5):
        port = dynamo_local._candidate_port_for_test_injection()
        assert port < 49152, (
            f"port {port} is inside Windows' WinNAT-reserved dynamic range "
            "(>= 49152); Docker's mapping for it may never route"
        )


def test_wait_for_dynamo_rejects_a_non_dynamo_answer():
    """STORY-179 AC4/AC5: `wait_for_dynamo` must prove the service ANSWERS a
    real DynamoDB call, not merely that something accepted the TCP connect
    and sent SOME bytes back.

    Stands up a plain TCP listener that accepts every connection and always
    replies with a generic, valid-looking HTTP 200 -- never a DynamoDB
    response. Measured live against the CURRENT (pre-fix) probe: it read
    that response's bytes and returned immediately -- green, in 0.02s --
    which is exactly defect 2 (`GET /`, "returns on ANY response"). The
    fixed probe must fail within its timeout and name the port in the
    message (AC5's diagnosis).
    """
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(5)
    port = listener.getsockname()[1]

    generic_response = (
        b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nOK"
    )

    def serve_forever():
        while True:
            try:
                conn, _ = listener.accept()
            except OSError:
                return
            try:
                conn.recv(4096)
                conn.sendall(generic_response)
            except OSError:
                pass
            finally:
                conn.close()

    server_thread = threading.Thread(target=serve_forever, daemon=True)
    server_thread.start()

    timeout_seconds = 3.0
    try:
        start = time.monotonic()
        with pytest.raises(TimeoutError, match=str(port)):
            dynamo_local.wait_for_dynamo(port, timeout_seconds=timeout_seconds)
        elapsed = time.monotonic() - start
        # STORY-179 fix round, CRITICAL 1: `elapsed < 10.0` pinned nothing --
        # it passed even at 9.5s against a 3.0s budget. Bound it proportional
        # to the budget actually requested instead.
        budget = timeout_seconds + 3.0
        assert elapsed < budget, (
            f"probe should fail fast, took {elapsed}s (budget {budget}s)"
        )
    finally:
        listener.close()


def test_wait_for_dynamo_does_not_claim_mapped_when_nothing_ever_listened():
    """STORY-179 fix round, MAJOR 1: the timeout message named "mapped but
    never answered -- the port is mapped, not dead-on-arrival" UNCONDITIONALLY,
    even when the probe never received so much as a TCP accept (measured: a
    closed port raises `ConnectTimeoutError`, never a connection). That
    over-claims a diagnosis the probe cannot support. Against a genuinely
    closed port, the message must NOT rule out "nothing is listening".
    """
    # A closed port: bind then immediately close, so nothing is listening.
    probe_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe_socket.bind(("127.0.0.1", 0))
    closed_port = probe_socket.getsockname()[1]
    probe_socket.close()

    with pytest.raises(TimeoutError, match=str(closed_port)) as excinfo:
        dynamo_local.wait_for_dynamo(closed_port, timeout_seconds=2.0)

    message = str(excinfo.value)
    assert "not dead-on-arrival" not in message, (
        f"message rules out dead-on-arrival against a port nothing was "
        f"listening on: {message!r}"
    )


def _fake_docker_run(cmd, **kwargs):
    return subprocess.CompletedProcess(cmd, 0, "container_id\n", "")


def test_docker_port_mapping_raises_runtime_error_on_malformed_output(
    monkeypatch: pytest.MonkeyPatch,
):
    """STORY-179 fix round, MINOR 1: a `docker port` output with no `:` (e.g.
    "no mapping found") made `int(port_str)` raise a bare `ValueError` --
    inconsistent with the contextual `RuntimeError`s raised beside it, and
    with none of their diagnostic naming.
    """

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["docker", "port"]:
            return subprocess.CompletedProcess(cmd, 0, "no mapping found\n", "")
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(dynamo_local.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="malformed_output_container"):
        dynamo_local._docker_port_mapping("malformed_output_container")


def test_start_container_cleans_up_on_malformed_port_mapping(
    monkeypatch: pytest.MonkeyPatch,
):
    """STORY-179 fix round, MINOR 1: `start_container`'s mismatch branch
    (`:147`) calls `stop_container`, but a malformed `docker port` output
    propagated straight out of `_docker_port_mapping` without that cleanup,
    leaving the container running.
    """
    rm_calls = []

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["docker", "rm"]:
            rm_calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, "", "")
        if cmd[:2] == ["docker", "run"]:
            return _fake_docker_run(cmd, **kwargs)
        if cmd[:2] == ["docker", "port"]:
            return subprocess.CompletedProcess(cmd, 0, "no mapping found\n", "")
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(dynamo_local.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError):
        dynamo_local.start_container("fake_container_malformed_mapping")

    # One `docker rm` up front (the pre-emptive cleanup at the top of
    # start_container) plus one AFTER the malformed mapping is discovered.
    assert len(rm_calls) >= 2, f"expected a cleanup rm after failure, got {rm_calls}"


def test_start_container_raises_on_port_mapping_mismatch(
    monkeypatch: pytest.MonkeyPatch,
):
    """STORY-179 AC2: the mapping is verified via `docker port`, not assumed.
    A mismatch between the requested port and what Docker actually bound is
    an error naming both.
    """

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["docker", "rm"]:
            return subprocess.CompletedProcess(cmd, 0, "", "")
        if cmd[:2] == ["docker", "run"]:
            return _fake_docker_run(cmd, **kwargs)
        if cmd[:2] == ["docker", "port"]:
            # Docker reports a port that does NOT match what was requested.
            return subprocess.CompletedProcess(cmd, 0, "0.0.0.0:1\n", "")
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(dynamo_local.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="mismatch"):
        dynamo_local.start_container("fake_container_ac2")


def test_start_container_retries_on_bind_failure_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
):
    """STORY-179 AC3: a port already in use causes a retry within the range,
    not an immediate failure.
    """
    run_attempts = []

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["docker", "rm"]:
            return subprocess.CompletedProcess(cmd, 0, "", "")
        if cmd[:2] == ["docker", "run"]:
            run_attempts.append(cmd)
            if len(run_attempts) < 3:
                return subprocess.CompletedProcess(
                    cmd, 1, "", "Bind for 0.0.0.0:X failed: port is already allocated"
                )
            return _fake_docker_run(cmd, **kwargs)
        if cmd[:2] == ["docker", "port"]:
            # Report back whatever port the last successful `docker run` requested.
            requested = run_attempts[-1][run_attempts[-1].index("-p") + 1]
            requested_port = requested.split(":")[0]
            return subprocess.CompletedProcess(
                cmd, 0, f"0.0.0.0:{requested_port}\n", ""
            )
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(dynamo_local.subprocess, "run", fake_run)

    port = dynamo_local.start_container("fake_container_ac3_retry")
    # STORY-179 fix round, CRITICAL 2: `isinstance(port, int)` is vacuous --
    # `_docker_port_mapping` returns `int(port_str)` by construction, so this
    # can never be false. Pin the actual AC1 property instead: every port
    # `start_container` asked Docker to bind came from the fixed range, not
    # wherever Docker (or the OS) felt like putting it.
    for attempt in run_attempts:
        requested = attempt[attempt.index("-p") + 1]
        requested_port = int(requested.split(":")[0])
        assert (
            dynamo_local._PORT_RANGE_START
            <= requested_port
            < dynamo_local._PORT_RANGE_END
        ), (
            f"requested port {requested_port} outside the fixed range "
            f"{dynamo_local._PORT_RANGE_START}-{dynamo_local._PORT_RANGE_END - 1}"
        )
    assert dynamo_local._PORT_RANGE_START <= port < dynamo_local._PORT_RANGE_END
    assert len(run_attempts) == 3


def test_start_container_raises_after_exhausting_retry_budget(
    monkeypatch: pytest.MonkeyPatch,
):
    """STORY-179 AC3: bind failure that never clears is bounded, and
    exhaustion raises a message naming the range and the attempt count.
    """
    run_attempts = []

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["docker", "rm"]:
            return subprocess.CompletedProcess(cmd, 0, "", "")
        if cmd[:2] == ["docker", "run"]:
            run_attempts.append(cmd)
            return subprocess.CompletedProcess(
                cmd, 1, "", "Bind for 0.0.0.0:X failed: port is already allocated"
            )
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(dynamo_local.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="attempts"):
        dynamo_local.start_container("fake_container_ac3_exhaust")

    assert len(run_attempts) == dynamo_local._MAX_BIND_ATTEMPTS


def test_start_container_reraises_non_bind_docker_failure_immediately(
    monkeypatch: pytest.MonkeyPatch,
):
    """STORY-179 fix round, MAJOR 2: the retry loop caught EVERY non-zero
    `docker run` exit and retried, so a daemon-down/image-pull/disk error
    was retried `_MAX_BIND_ATTEMPTS` times and then reported as a false
    "could not bind ... to any port in the fixed range" diagnosis. A
    non-bind failure must re-raise immediately, on the FIRST attempt, with
    the docker output -- never the bind-exhaustion message.
    """
    run_attempts = []

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["docker", "rm"]:
            return subprocess.CompletedProcess(cmd, 0, "", "")
        if cmd[:2] == ["docker", "run"]:
            run_attempts.append(cmd)
            return subprocess.CompletedProcess(
                cmd,
                1,
                "",
                "Cannot connect to the Docker daemon at unix:///var/run/docker.sock",
            )
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(dynamo_local.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="daemon") as excinfo:
        dynamo_local.start_container("fake_container_non_bind_failure")

    assert "any port in the fixed range" not in str(excinfo.value)
    assert len(run_attempts) == 1


def test_resolve_dynamo_uses_external_endpoint(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DYNAMO_ENDPOINT_URL", "http://aws-dynamo:8000")
    plan = dynamo_local.resolve_dynamo()
    assert plan.source == "env"
    assert plan.endpoint_url == "http://aws-dynamo:8000"


def test_resolve_dynamo_spawns_container_when_docker_available(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv("DYNAMO_ENDPOINT_URL", raising=False)

    # Mock docker_available to return True
    monkeypatch.setattr(dynamo_local, "docker_available", lambda: True)

    spawned = []

    def mock_spawn(name, port):
        spawned.append((name, port))

    plan = dynamo_local.resolve_dynamo(spawn_container=mock_spawn)
    assert plan.source == "container"
    assert plan.endpoint_url.startswith("http://localhost:")
    assert plan.container_name is not None
    assert len(spawned) == 1
    assert spawned[0][0] == plan.container_name


def test_resolve_dynamo_skips_when_no_external_and_no_docker(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv("DYNAMO_ENDPOINT_URL", raising=False)
    monkeypatch.setattr(dynamo_local, "docker_available", lambda: False)

    plan = dynamo_local.resolve_dynamo()
    assert plan.source == "skip"
    assert plan.endpoint_url is None
    assert plan.container_name is None


@pytest.mark.skipif(
    not dynamo_local.docker_available(),
    reason="requires Docker to spawn a real container",
)
def test_provide_dynamo_local_teardown_on_failure(monkeypatch: pytest.MonkeyPatch):
    import subprocess

    from conftest import provide_dynamo_local

    # Clear external endpoint to force container spawn
    monkeypatch.delenv("DYNAMO_ENDPOINT_URL", raising=False)
    monkeypatch.setattr(dynamo_local, "docker_available", lambda: True)

    gen = provide_dynamo_local()
    plan = next(gen)
    assert plan.source == "container"
    container_name = plan.container_name
    assert container_name

    # Verify container exists
    running = subprocess.run(
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
    assert running.stdout.strip() == container_name

    try:
        with pytest.raises(RuntimeError, match="simulated test failure"):
            gen.throw(RuntimeError("simulated test failure"))
    finally:
        # Check if container is stopped/deleted
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
        if leftover.stdout.strip():
            subprocess.run(
                ["docker", "rm", "-f", container_name], capture_output=True, text=True
            )

    assert leftover.stdout.strip() == ""


def test_dynamo_resource_fixture_isolation_part_1(dynamo_resource):
    # Retrieve the control table (using default name)
    table = dynamo_resource.Table("uptime-control")

    # Put a dummy item
    table.put_item(Item={"pk": "TEST#1", "sk": "META", "val": "hello"})

    # Verify it exists
    res = table.get_item(Key={"pk": "TEST#1", "sk": "META"})
    assert "Item" in res
    assert res["Item"]["val"] == "hello"


def test_dynamo_resource_fixture_isolation_part_2(dynamo_resource):
    # This test runs after part_1, and clean_dynamo_tables should have run,
    # so the table must be empty!
    table = dynamo_resource.Table("uptime-control")
    res = table.get_item(Key={"pk": "TEST#1", "sk": "META"})
    assert "Item" not in res
