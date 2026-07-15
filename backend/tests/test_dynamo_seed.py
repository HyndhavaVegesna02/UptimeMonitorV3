from __future__ import annotations

from src.adapters.persistence.dynamo_component_repository import (
    DynamoComponentRepository,
)
from src.adapters.persistence.dynamo_signal_repository import DynamoSignalRepository
from src.composition.config import AppConfig, ComponentConfig, Config, SignalConfig
from src.composition.seed_dynamo import seed_topology_dynamo
from src.composition.settings import load_settings
from src.core.domain.status import ComponentStatus
from src.core.services.pipeline import AntiFlapThresholds


def test_seed_topology_dynamo(dynamo_resource):
    settings = load_settings()
    comp_repo = DynamoComponentRepository(
        dynamo_resource, settings.dynamo_control_table
    )
    sig_repo = DynamoSignalRepository(dynamo_resource, settings.dynamo_control_table)

    app_cfg = AppConfig(
        id="app-1",
        name="Test App",
        monitor_provider="dynatrace",
        components=[
            ComponentConfig(id="comp-a", name="Component A"),
            ComponentConfig(id="comp-b", name="Component B"),
        ],
        signals=[
            SignalConfig(
                signal_key="sig-x",
                native_id="NATIVE-X",
                name="Signal X",
                component_id="comp-a",
                interval_seconds=60,
            ),
            SignalConfig(
                signal_key="sig-y",
                native_id="NATIVE-Y",
                name="Signal Y",
                component_id="comp-b",
                interval_seconds=120,
            ),
        ],
        thresholds=AntiFlapThresholds(major=3, partial=2, degraded=1, recovery=1),
    )
    config = Config([app_cfg])

    # 1. Seed once -> verify items created
    seed_topology_dynamo(config, dynamo_resource, settings.dynamo_control_table)

    # Verify component mapping
    comp_a = comp_repo.get("comp-a")
    assert comp_a is not None
    assert comp_a.name == "Component A"
    assert comp_a.app_id == "app-1"
    assert comp_a.status == ComponentStatus.OPERATIONAL

    comp_b = comp_repo.get("comp-b")
    assert comp_b is not None
    assert comp_b.name == "Component B"
    assert comp_b.app_id == "app-1"
    assert comp_b.status == ComponentStatus.OPERATIONAL

    # Verify signals
    signals = sig_repo.list_signals()
    assert len(signals) == 2
    assert signals[0].signal_key == "sig-x"
    assert signals[0].name == "Signal X"
    assert signals[0].component_id == "comp-a"
    assert signals[0].interval_seconds == 60

    assert signals[1].signal_key == "sig-y"
    assert signals[1].name == "Signal Y"
    assert signals[1].component_id == "comp-b"
    assert signals[1].interval_seconds == 120

    # 2. Seed twice (idempotence) -> verify state unchanged
    seed_topology_dynamo(config, dynamo_resource, settings.dynamo_control_table)
    assert len(comp_repo.list_components()) == 2
    assert len(sig_repo.list_signals()) == 2

    # 3. Modify signal config and re-seed -> verify update reflected
    app_cfg_mod = AppConfig(
        id="app-1",
        name="Test App",
        monitor_provider="dynatrace",
        components=[
            ComponentConfig(id="comp-a", name="Component A Modified"),
            ComponentConfig(id="comp-b", name="Component B"),
        ],
        signals=[
            SignalConfig(
                signal_key="sig-x",
                native_id="NATIVE-X",
                name="Signal X Modified",
                component_id="comp-a",
                interval_seconds=90,
            ),
        ],
        thresholds=AntiFlapThresholds(major=3, partial=2, degraded=1, recovery=1),
    )
    config_mod = Config([app_cfg_mod])
    seed_topology_dynamo(config_mod, dynamo_resource, settings.dynamo_control_table)

    comp_a_mod = comp_repo.get("comp-a")
    assert comp_a_mod.name == "Component A Modified"

    sig_x_mod = sig_repo.get("sig-x")
    assert sig_x_mod.name == "Signal X Modified"
    assert sig_x_mod.interval_seconds == 90

    # 4. Status preservation check (crux)
    # Set status of comp-a to DEGRADED
    comp_repo.set_status("comp-a", ComponentStatus.DEGRADED)
    assert comp_repo.get("comp-a").status == ComponentStatus.DEGRADED

    # Re-seed with config_mod -> status should STILL be DEGRADED
    seed_topology_dynamo(config_mod, dynamo_resource, settings.dynamo_control_table)
    assert comp_repo.get("comp-a").status == ComponentStatus.DEGRADED
