#!/usr/bin/env python
"""Shared throwaway-DynamoDB local harness.

Centralizes DynamoDB Local container lifecycle for test fixtures.
"""

from __future__ import annotations

import os
import random
import subprocess
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
# STORY-173 (separate story, NOT in this sprint): a container leaked by a
# dead PID -- e.g. a killed pytest run that never reached its finalizer --
# holds its port slot in this fixed range until 173's reaper lands. That is
# a known, accepted limitation of shipping 179 without 173: the range is
# small enough that a handful of leaks could exhaust it.
_PORT_RANGE_START = 18000
_PORT_RANGE_END = 18100  # exclusive
_MAX_BIND_ATTEMPTS = 20


def _candidate_ports() -> Iterator[int]:
    """Yield up to `_MAX_BIND_ATTEMPTS` distinct candidate ports, in random
    order, from the fixed range above. Each candidate is tried at most once
    per call so a bounded retry loop (AC3) can never spin on the same port.
    """
    ports = list(range(_PORT_RANGE_START, _PORT_RANGE_END))
    random.shuffle(ports)
    yield from ports[:_MAX_BIND_ATTEMPTS]


def _free_tcp_port() -> int:
    """A single candidate host port drawn from the fixed range above.

    Previously bound `("127.0.0.1", 0)` to ask the OS for an ephemeral port,
    then closed the socket and handed the bare number to `docker run` -- the
    port was unowned in the gap between close and bind (a race), AND on
    Windows it landed in WinNAT's reserved dynamic range (see `_PORT_RANGE_START`
    above). `start_container()`'s bind-retry loop plus its `docker port`
    read-back (AC2/AC3) is the backstop for whatever race still slips through
    a single candidate picked here.
    """
    return next(_candidate_ports())


def unique_container_name(prefix: str = "uptime_dynamo_pytest") -> str:
    """A container name unique to this process."""
    return f"{prefix}_{os.getpid()}_{uuid.uuid4().hex[:8]}"


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
    return int(port_str)


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
    count. Returns the actual, verified host port.
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
            continue

        actual_port = _docker_port_mapping(name)
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
) -> DynamoPlan:
    """Decide how to obtain a DynamoDB instance.

    Order:
    1. DYNAMO_ENDPOINT_URL set -> reuse it (source="env")
    2. Docker available -> spawn container (source="container")
    3. Skip -> source="skip"
    """
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
        port = _free_tcp_port()
        spawn_container(name, port)

    return DynamoPlan(
        source="container",
        endpoint_url=f"http://localhost:{port}",
        container_name=name,
    )
