#!/usr/bin/env python
"""Shared throwaway-DynamoDB local harness.

Centralizes DynamoDB Local container lifecycle for test fixtures.
"""

from __future__ import annotations

import os
import random
import re
import subprocess
import sys
import time
import uuid
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class DynamoPlan:
    source: str
    endpoint_url: str | None
    container_name: str | None = None


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


# STORY-179 AC1: a fixed, non-ephemeral range, comfortably below Windows'
# WinNAT dynamic-port floor (49152). Drawing from here instead of asking the
# OS for an ephemeral port (the old `_free_tcp_port()`) removes the failure
# mode where the chosen port lands in WinNAT's reserved range: Docker still
# creates a mapping, `docker ps` still displays it as `Up`, but it never
# routes -- every request just hangs.
#
# Verified clear on this machine (fix round, 2026-08-13):
#   netsh interface ipv4 show excludedportrange protocol=tcp
# returned exclusions only in 50000-50059 and the 52680-53228 span -- nothing
# overlapping 18000-18099. WinNAT's exclusions are re-derived at boot from
# whatever is currently reserved, so this is a point-in-time observation, not
# a permanent guarantee; re-run the command above if this range ever needs
# re-justifying.
#
# STORY-173 (landed, sprint 72): a container leaked by a dead PID -- e.g. a
# killed pytest run that never reached its finalizer -- held its port slot
# in this fixed range indefinitely before 173's reaper existed.
# `resolve_dynamo` now calls `reap_dead_pytest_containers()` at the START of
# EVERY call (before the DYNAMO_ENDPOINT_URL short-circuit), so a container
# leaked by a previous killed run is removed at the start of the NEXT
# session that resolves a plan, before any new port is requested here. This
# substantially narrows the exposure this comment used to describe (any
# leaked slot could persist across arbitrarily many later runs); it does
# not eliminate it in a single pathological case the reaper's own
# conservative design (AC5) leaves alone on purpose: a PID that is dead but
# whose liveness cannot be confirmed as such (see `_pid_is_alive`'s
# "undetermined -> leave it alone" branch, and the still-open-handle trap
# documented there) still holds its slot.
_PORT_RANGE_START = 18000
_PORT_RANGE_END = 18100  # exclusive
# 20 of 100 slots: a compromise between tolerating a handful of
# undetermined-liveness/simultaneous in-use ports (STORY-173's reaper
# narrows, but does not zero out, the leaked-slot case described above) and
# not spending more than 20 subprocess round-trips retrying a range that is,
# in practice, almost always immediately available on a dev/CI box.
_MAX_BIND_ATTEMPTS = 20


def _candidate_ports() -> Iterator[int]:
    """Yield up to `_MAX_BIND_ATTEMPTS` distinct candidate ports, in random
    order, from the fixed range above. Each candidate is tried at most once
    per call so a bounded retry loop (AC3) can never spin on the same port.
    """
    ports = list(range(_PORT_RANGE_START, _PORT_RANGE_END))
    random.shuffle(ports)
    yield from ports[:_MAX_BIND_ATTEMPTS]


def _candidate_port_for_test_injection() -> int:
    """A single candidate host port drawn from the fixed range above.

    STORY-179 fix round, MINOR 5: this was named `_free_tcp_port()`, which
    overstates what it does -- it does not verify anything is free, it just
    draws one candidate from `_candidate_ports()`. `start_container()` (the
    real path) has never called this directly; it calls `_candidate_ports()`
    itself and lets Docker perform the actual bind, with `docker port`
    read-back as the verification (AC2/AC3). This function's only remaining
    caller is `resolve_dynamo`'s `spawn_container`-injected branch, which
    exists for test doubles that need a port number without spawning a real
    container -- hence the name.
    """
    return next(_candidate_ports())


def unique_container_name(prefix: str = "uptime_dynamo_pytest") -> str:
    """A container name unique to this process."""
    return f"{prefix}_{os.getpid()}_{uuid.uuid4().hex[:8]}"


# STORY-173: anchored (`^...$`) to the EXACT shape `unique_container_name()`
# produces above -- prefix, pid, 8 lowercase hex chars -- so a name that
# merely starts with or contains "uptime_dynamo" (e.g. the gate's own
# long-lived `uptime_dynamo_8021`) never matches. AC2(b) depends on this
# being a full match, not a prefix/substring check.
_PYTEST_CONTAINER_NAME_RE = re.compile(r"^uptime_dynamo_pytest_(\d+)_[0-9a-f]{8}$")


def _list_pytest_containers() -> list[str]:
    """Names of all containers (running or stopped) whose name starts with
    the `unique_container_name()` prefix, via a single targeted
    `docker ps -a --filter name=...` -- never a broad listing (AC2c).
    """
    result = subprocess.run(
        [
            "docker",
            "ps",
            "-a",
            "--filter",
            "name=uptime_dynamo_pytest_",
            "--format",
            "{{.Names}}",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _pid_is_alive(pid: int) -> bool | None:
    """Best-effort liveness check for `pid`.

    Returns True if the process appears to be running, False if it is
    confirmed NOT running, and None if liveness could not be determined --
    the conservative case a caller must treat as "leave it alone" (AC5).

    STORY-173, measured on Windows at pre-lock verification (2026-08-14),
    do not re-derive: `os.kill(pid, 0)` does not terminate anything (that is
    signal 9's job) -- it is a liveness probe. On a dead or nonexistent pid
    it raises a bare `OSError` with `winerror == 87`, NOT
    `ProcessLookupError`. A reaper that only catches `ProcessLookupError`
    (the POSIX shape) lets that OSError propagate and violates AC4. A
    still-open process handle can also make a dead pid read as alive --
    which is exactly why the conservative branch below exists: anything
    that is not affirmatively "confirmed dead" is left alone.
    """
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError as exc:
        if getattr(exc, "winerror", None) == 87:
            return False
        # Some other OSError (e.g. a permission failure probing a process
        # owned by someone else) -- undetermined, not "dead".
        return None
    except Exception:
        return None
    else:
        return True


def reap_dead_pytest_containers(
    *,
    docker_available: Callable[[], bool] | None = None,
    list_containers: Callable[[], list[str]] | None = None,
    pid_is_alive: Callable[[int], bool | None] | None = None,
    remove_container: Callable[[str], None] | None = None,
) -> list[str]:
    """Remove `uptime_dynamo_pytest_*` containers whose embedded PID is
    confirmed dead -- the fix for STORY-173: a killed pytest run leaves its
    session-scoped container running, and the NEXT run's fixture then stalls
    against it with no diagnosis.

    Called from `resolve_dynamo` BEFORE the `DYNAMO_ENDPOINT_URL`
    short-circuit, so it runs whether or not that variable is set (a
    container leaked by a PREVIOUS run is leaked regardless of how THIS run
    obtains its endpoint; the gate itself sets that variable, so placing
    this after the short-circuit would make it dead code in exactly the
    configuration it exists for).

    Each collaborator is a keyword-only `Callable | None = None` that falls
    back to the real module-level implementation when omitted, following
    the same convention `resolve_dynamo` already uses for
    `docker_available`/`spawn_container` -- production callers are
    unaffected; only tests inject.

    AC2, the half that matters (a reaper that removes too much is worse than
    none):
    - only names matching `unique_container_name()`'s EXACT shape
      (`_PYTEST_CONTAINER_NAME_RE`, a full match) are ever considered --
      anything else, notably the gate's own long-lived
      `uptime_dynamo_8021`, is never touched no matter what
      `list_containers` returns.
    - a matching container is removed ONLY when `pid_is_alive` returns
      `False` -- confirmed dead. `True` (alive) or `None` (undetermined)
      leaves it alone (AC5's conservative branch).
    - removal is always a single targeted `stop_container(name)` call
      (`docker rm -f <name>`, one name) -- never a broad `docker rm -f`
      with no name and never a wildcard prune.

    AC4: degrades to a no-op, never a failure. Docker absent, slow,
    erroring, or a removal that itself raises is swallowed here and at most
    noted on stderr -- this must never fail the run that calls it.

    Returns the names actually removed.
    """
    if docker_available is None:
        docker_available = globals()["docker_available"]
    if list_containers is None:
        list_containers = _list_pytest_containers
    if pid_is_alive is None:
        pid_is_alive = _pid_is_alive
    if remove_container is None:
        remove_container = stop_container

    removed: list[str] = []
    try:
        if not docker_available():
            return removed
        for name in list_containers():
            match = _PYTEST_CONTAINER_NAME_RE.match(name)
            if match is None:
                continue
            pid = int(match.group(1))
            try:
                alive = pid_is_alive(pid)
            except Exception:
                alive = None
            if alive is not False:
                continue
            try:
                remove_container(name)
                removed.append(name)
            except Exception as exc:
                print(
                    f"dynamo_local: WARNING could not reap dead-PID "
                    f"container {name!r}: {exc!r}",
                    file=sys.stderr,
                )
    except Exception as exc:
        print(
            f"dynamo_local: WARNING reap_dead_pytest_containers failed, "
            f"continuing without reaping: {exc!r}",
            file=sys.stderr,
        )
    return removed


def _docker_port_mapping(name: str, container_port: int = 8000) -> int:
    """Read back the host port Docker actually bound for `container_port`."""
    result = subprocess.run(
        ["docker", "port", name, f"{container_port}/tcp"],
        capture_output=True,
        text=True,
    )
    output = result.stdout.strip()
    if result.returncode != 0 or not output:
        raise RuntimeError(
            f"docker port lookup failed for container {name!r}: "
            f"{result.stdout}{result.stderr}"
        )
    # One line per bound address family, e.g. "0.0.0.0:18007\n[::]:18007\n".
    first_line = output.splitlines()[0]
    _, _, port_str = first_line.rpartition(":")
    try:
        return int(port_str)
    except ValueError as exc:
        # STORY-179 fix round, MINOR 1: a bare `ValueError` here (measured:
        # "invalid literal for int() ... 'no mapping found'") was
        # inconsistent with the contextual `RuntimeError`s raised beside it
        # and named neither the container nor the raw output.
        raise RuntimeError(
            f"docker port lookup for container {name!r} returned "
            f"unparseable output: {output!r}"
        ) from exc


def _is_bind_failure(docker_output: str) -> bool:
    """True iff `docker run`'s failure output is shaped like a port-bind
    conflict, not some other reason `docker run` can exit non-zero (a dead
    daemon, a failed image pull, a disk error, ...).

    STORY-179 fix round, MAJOR 2: the retry loop previously caught EVERY
    non-zero exit and retried, so a daemon-down error was retried
    `_MAX_BIND_ATTEMPTS` times and then reported as "could not bind ... to
    any port in the fixed range" -- a false diagnosis for a failure that had
    nothing to do with the port range. Only the bind case should retry;
    everything else should surface immediately with Docker's own message.
    """
    lowered = docker_output.lower()
    return "already allocated" in lowered or "bind for" in lowered


def start_container(name: str) -> int:
    """Start a throwaway `amazon/dynamodb-local` container, verified bound.

    STORY-179 AC2/AC3, decision 1: request a port from the fixed range
    (`_candidate_ports`), let Docker perform the actual bind, then read the
    mapping back with `docker port` and confirm it matches what was
    requested -- Docker owns the bind, so there is no unowned gap between
    picking a port and handing it over the way the old `_free_tcp_port()`
    had. A port already in use causes a bounded retry within the range
    (`_MAX_BIND_ATTEMPTS`); a mismatched mapping is an error naming both
    ports; exhausting the range raises naming the range and the attempt
    count. Returns the actual, verified host port. A non-bind `docker run`
    failure (daemon down, image pull failure, ...) re-raises immediately
    with Docker's own output, rather than being retried and misreported as
    a bind-range exhaustion (fix round MAJOR 2).
    """
    subprocess.run(["docker", "rm", "-f", name], capture_output=True, text=True)

    attempts = 0
    last_error = "no attempts made"
    for candidate in _candidate_ports():
        attempts += 1
        result = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                name,
                "-p",
                f"{candidate}:8000",
                "amazon/dynamodb-local",
                "-jar",
                "DynamoDBLocal.jar",
                "-inMemory",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            last_error = (result.stdout + result.stderr).strip()
            subprocess.run(["docker", "rm", "-f", name], capture_output=True, text=True)
            if not _is_bind_failure(last_error):
                raise RuntimeError(
                    f"docker run failed for container {name!r} on attempt "
                    f"{attempts} for a reason unrelated to port binding: "
                    f"{last_error}"
                )
            continue

        try:
            actual_port = _docker_port_mapping(name)
        except RuntimeError:
            # STORY-179 fix round, MINOR 1: the mismatch branch below cleans
            # up via `stop_container`; a `_docker_port_mapping` failure
            # (e.g. malformed output) did not, leaving the container running.
            stop_container(name)
            raise
        if actual_port != candidate:
            stop_container(name)
            raise RuntimeError(
                f"docker port mapping mismatch for container {name!r}: "
                f"requested host port {candidate}, but docker reports "
                f"{actual_port} bound"
            )
        return actual_port

    raise RuntimeError(
        f"could not bind DynamoDB Local container {name!r} to any port in "
        f"the fixed range {_PORT_RANGE_START}-{_PORT_RANGE_END - 1} after "
        f"{attempts} attempts; last docker error: {last_error}"
    )


def wait_for_dynamo(port: int, timeout_seconds: float = 30.0) -> None:
    """Poll DynamoDB Local until it answers a real `ListTables` call.

    STORY-179 AC4: a bare `GET /` (the previous probe) returns on ANY
    response -- it proves the peer accepted a TCP connect and sent SOMETHING
    back, never that the peer is DynamoDB. Docker's own port-forwarding proxy
    can accept a connect for a mapping that never reaches the container, so
    that probe green-lights a dead container. This issues a real DynamoDB
    API call instead: only an actual DynamoDB Local response can satisfy it.

    STORY-179 AC5: on timeout the error names the port and states plainly
    that it was mapped but never answered -- the diagnosis that would have
    saved the hour this defect cost, not a bare `TimeoutError`.
    """
    import boto3
    from botocore.config import Config
    from botocore.exceptions import (
        BotoCoreError,
        ClientError,
        ConnectTimeoutError,
        EndpointConnectionError,
    )

    # STORY-179 fix round, CRITICAL 1: `deadline` below is only consulted
    # BETWEEN calls -- a single `list_tables()` call is otherwise bounded by
    # botocore's own defaults (60s connect, 60s read, up to 10 legacy
    # DynamoDB retries), so one call can overrun `timeout_seconds` by up to
    # two orders of magnitude (measured: a silent peer that accepts and never
    # answers made the unbounded client take 626.24s against a 3.0s budget).
    # Pinning connect/read to ~1s and disabling botocore's own retries (the
    # `while` loop below is this function's own bounded retry) keeps every
    # single call's worst case close to `timeout_seconds`, which is the
    # entire point of a caller-controlled timeout.
    client = boto3.client(
        "dynamodb",
        region_name="us-east-1",
        endpoint_url=f"http://127.0.0.1:{port}",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        config=Config(
            connect_timeout=1.0, read_timeout=1.0, retries={"max_attempts": 1}
        ),
    )

    # STORY-179 fix round, MAJOR 1: the probe cannot distinguish "connected
    # but got a non-DynamoDB response" from "connection refused" -- it only
    # sees whatever exception botocore raised on the last attempt. Track it
    # so the timeout message states what was actually observed instead of
    # asserting a diagnosis ("mapped, not dead-on-arrival") the check has no
    # basis for when nothing ever accepted a connection (measured: a closed
    # port raises `ConnectTimeoutError`/`EndpointConnectionError`, never
    # anything implying a live peer).
    last_exception: Exception | None = None
    connection_was_established = False

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            response = client.list_tables()
            connection_was_established = True
            # botocore's JSON-protocol parsing is lenient about a 200 whose
            # body isn't actually AWS JSON (measured live: it returns an
            # empty, exception-free result rather than raising) -- so a
            # non-DynamoDB peer that merely answers "200 OK" can otherwise
            # pass this call. Requiring the one key every real ListTables
            # response carries is what actually pins "the service answers".
            if "TableNames" in response:
                return
        except (BotoCoreError, ClientError, OSError) as exc:
            last_exception = exc
            # `ConnectionClosedError`/`ReadTimeoutError`/`ClientError` all
            # imply a TCP connection was actually accepted; a connect
            # failure (e.g. `ConnectTimeoutError`) never gets this far.
            if not isinstance(exc, ConnectTimeoutError | EndpointConnectionError):
                connection_was_established = True
        time.sleep(0.1)

    if connection_was_established:
        raise TimeoutError(
            f"DynamoDB Local port {port} was mapped and accepted a "
            f"connection, but never returned a valid ListTables response "
            f"within {timeout_seconds}s -- the port is mapped, not "
            "dead-on-arrival, but the service behind it never answered "
            f"(STORY-179). Last error: {last_exception!r}"
        )

    raise TimeoutError(
        f"DynamoDB Local port {port} never accepted a successful connection "
        f"within {timeout_seconds}s -- this observation cannot distinguish "
        "'nothing is listening' from 'something dropped the connection', so "
        f"no mapped-vs-dead-on-arrival diagnosis is claimed (STORY-179). "
        f"Last error: {last_exception!r}"
    )


def stop_container(name: str) -> None:
    """Remove the container."""
    subprocess.run(["docker", "rm", "-f", name], capture_output=True, text=True)


def resolve_dynamo(
    *,
    env: Mapping[str, str] | None = None,
    docker_available: Callable[[], bool] | None = None,
    spawn_container: Callable[[str, int], None] | None = None,
    reap: Callable[[], list[str]] | None = None,
) -> DynamoPlan:
    """Decide how to obtain a DynamoDB instance.

    Order:
    0. Reap dead-PID `uptime_dynamo_pytest_*` containers left by a killed
       PREVIOUS run (STORY-173) -- BEFORE step 1, deliberately. A leaked
       container is leaked regardless of how THIS run obtains its endpoint,
       and the gate's own configuration always sets DYNAMO_ENDPOINT_URL, so
       placing the reap after step 1 would make it dead code exactly where
       it is needed (STORY-179's AC8 trap, applied forward).
    1. DYNAMO_ENDPOINT_URL set -> reuse it (source="env")
    2. Docker available -> spawn container (source="container")
    3. Skip -> source="skip"

    `reap`: keyword-only, `Callable[[], list[str]] | None = None`. Falls
    back to the module-level `reap_dead_pytest_containers` when omitted, so
    production callers are unaffected; tests inject a stub to assert it was
    invoked (AC3) or to avoid touching Docker. `reap_dead_pytest_containers`
    itself never raises (AC4), so this call is unguarded here.
    """
    if reap is None:
        reap = reap_dead_pytest_containers
    reap()

    if env is None:
        env = os.environ

    env_endpoint = env.get("DYNAMO_ENDPOINT_URL")
    if env_endpoint:
        return DynamoPlan(source="env", endpoint_url=env_endpoint)

    if docker_available is None:
        docker_available = globals()["docker_available"]

    if not docker_available():
        return DynamoPlan(source="skip", endpoint_url=None)

    name = unique_container_name()

    if spawn_container is None:
        try:
            port = start_container(name)
            wait_for_dynamo(port)
        except BaseException:
            stop_container(name)
            raise
    else:
        port = _candidate_port_for_test_injection()
        spawn_container(name, port)

    return DynamoPlan(
        source="container",
        endpoint_url=f"http://localhost:{port}",
        container_name=name,
    )
