#!/usr/bin/env python
"""Shared throwaway-DynamoDB local harness.

Centralizes DynamoDB Local container lifecycle for test fixtures.
"""

from __future__ import annotations

import http.client
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


def start_container(name: str, host_port: int) -> None:
    """Start a throwaway `amazon/dynamodb-local` container."""
    subprocess.run(["docker", "rm", "-f", name], capture_output=True, text=True)
    result = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            name,
            "-p",
            f"{host_port}:8000",
            "amazon/dynamodb-local",
            "-jar",
            "DynamoDBLocal.jar",
            "-inMemory",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"docker run failed: {result.stdout}{result.stderr}")


def wait_for_dynamo(port: int, timeout_seconds: float = 30.0) -> None:
    """Poll the DynamoDB Local HTTP endpoint until ready or timeout."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=1.0)
            conn.request("GET", "/")
            res = conn.getresponse()
            res.read()
            return
        except Exception:
            time.sleep(0.1)
    raise TimeoutError(f"DynamoDB Local at port {port} did not become ready")


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
    port = _free_tcp_port()

    if spawn_container is None:
        try:
            start_container(name, port)
            wait_for_dynamo(port)
        except BaseException:
            stop_container(name)
            raise
    else:
        spawn_container(name, port)

    return DynamoPlan(
        source="container",
        endpoint_url=f"http://localhost:{port}",
        container_name=name,
    )
