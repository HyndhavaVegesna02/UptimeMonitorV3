from __future__ import annotations

import sys
from pathlib import Path
import pytest

# Add repo root and scripts to sys.path so we can import dynamo_local
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import dynamo_local


def test_import_exists():
    assert dynamo_local is not None


def test_resolve_dynamo_uses_external_endpoint(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DYNAMO_ENDPOINT_URL", "http://aws-dynamo:8000")
    plan = dynamo_local.resolve_dynamo()
    assert plan.source == "env"
    assert plan.endpoint_url == "http://aws-dynamo:8000"


def test_resolve_dynamo_spawns_container_when_docker_available(monkeypatch: pytest.MonkeyPatch):
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


def test_resolve_dynamo_skips_when_no_external_and_no_docker(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("DYNAMO_ENDPOINT_URL", raising=False)
    monkeypatch.setattr(dynamo_local, "docker_available", lambda: False)

    plan = dynamo_local.resolve_dynamo()
    assert plan.source == "skip"
    assert plan.endpoint_url is None
    assert plan.container_name is None


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
        ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
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
            ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
        )
        if leftover.stdout.strip():
            subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, text=True)

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
