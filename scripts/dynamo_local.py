#!/usr/bin/env python
"""Shared throwaway-DynamoDB local harness.

Centralizes DynamoDB Local container lifecycle for test fixtures.
"""

from __future__ import annotations

import http.client
import os
import subprocess
import time
import uuid
from collections.abc import Callable, Mapping
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


def _free_tcp_port() -> int:
    """Ask the OS for an ephemeral free TCP port."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


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
