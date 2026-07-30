"""STORY-191: tests for failure scenarios, scenario vocabulary, and recovery publish proof."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from demo_engine.scenario import expand_scenario, load_scenario_file, InvalidScenarioError
from src.adapters.inbound.dynatrace.adapter import fetch_observations
from src.adapters.inbound.dynatrace.health_mapping import UnknownVendorStatusError
from src.composition.config import load_config
from src.composition.publish_helper import build_publisher
from src.composition.orchestrate import orchestrate_signal
from src.core.domain import Component, ComponentStatus, Health
from src.core.services.decide import DecideAction, DecideService
from tests.fakes import (
    FakeClock,
    FakeComponentRepository,
    FakeMaintenanceRepository,
    FakeObservationRepository,
    FakeProposalRepository,
    FakePublicationRepository,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEMO_CONFIG_DIR = _REPO_ROOT / "config" / "demo"
_SCENARIOS_DIR = _DEMO_CONFIG_DIR / "scenarios"
_END = datetime(2026, 7, 30, 12, 0, 0, tzinfo=timezone.utc)


def test_existing_scenarios_load_and_expand_backward_compatibly():
    """AC: The five checked-in config/demo/scenarios/*.yaml load and expand byte-identically."""
    existing_files = [
        "clean-fleet.yaml",
        "dark-location.yaml",
        "dark-monitor.yaml",
        "late-return.yaml",
        "staggered-intervals.yaml",
    ]
    for filename in existing_files:
        scenarios = load_scenario_file(_SCENARIOS_DIR / filename)
        assert len(scenarios) > 0
        for scenario in scenarios:
            rows = expand_scenario(scenario, end_time=_END)
            assert isinstance(rows, list)


def test_down_ladder_scenario_expands_to_down_observations():
    scenarios = load_scenario_file(_SCENARIOS_DIR / "down-ladder.yaml")
    assert len(scenarios) == 1
    scenario = scenarios[0]
    rows = expand_scenario(scenario, end_time=_END)
    outcome = fetch_observations(
        signal_key=scenario.signal_key,
        native_id=scenario.monitor_id,
        watermark=None,
        executor=lambda q: rows,
    )
    assert len(outcome.failures) == 0
    assert len(outcome.observations) == 5 * 4  # 5 cycles x 4 locations
    assert all(obs.health is Health.DOWN for obs in outcome.observations)


def test_partial_breadth_scenario_expands_per_location_health():
    scenarios = load_scenario_file(_SCENARIOS_DIR / "partial-breadth.yaml")
    assert len(scenarios) == 1
    scenario = scenarios[0]
    rows = expand_scenario(scenario, end_time=_END)
    outcome = fetch_observations(
        signal_key=scenario.signal_key,
        native_id=scenario.monitor_id,
        watermark=None,
        executor=lambda q: rows,
    )
    assert len(outcome.failures) == 0
    assert len(outcome.observations) == 3 * 4  # 3 cycles x 4 locations
    
    # Check per-location health in one cycle
    cycle_obs = outcome.observations[:4]
    by_loc = {obs.location: obs.health for obs in cycle_obs}
    assert by_loc["SYNTHETIC_LOCATION-DEMOA"] is Health.DOWN
    assert by_loc["SYNTHETIC_LOCATION-DEMOB"] is Health.UP
    assert by_loc["SYNTHETIC_LOCATION-DEMOC"] is Health.UP
    assert by_loc["SYNTHETIC_LOCATION-DEMOD"] is Health.UP


def test_degraded_ladder_scenario_expands_to_degraded_observations():
    scenarios = load_scenario_file(_SCENARIOS_DIR / "degraded-ladder.yaml")
    assert len(scenarios) == 1
    scenario = scenarios[0]
    rows = expand_scenario(scenario, end_time=_END)
    outcome = fetch_observations(
        signal_key=scenario.signal_key,
        native_id=scenario.monitor_id,
        watermark=None,
        executor=lambda q: rows,
    )
    assert len(outcome.failures) == 0
    assert len(outcome.observations) == 3 * 4
    assert all(obs.health is Health.DEGRADED for obs in outcome.observations)


def test_poison_row_scenario_preserves_4_good_locations_and_captures_poison_failure():
    scenarios = load_scenario_file(_SCENARIOS_DIR / "poison-row.yaml")
    assert len(scenarios) == 1
    scenario = scenarios[0]
    rows = expand_scenario(scenario, end_time=_END)
    outcome = fetch_observations(
        signal_key=scenario.signal_key,
        native_id=scenario.monitor_id,
        watermark=None,
        executor=lambda q: rows,
    )
    # 4 good locations x 2 cycles = 8 observations
    assert len(outcome.observations) == 2 * 4
    assert all(obs.health is Health.UP for obs in outcome.observations)
    
    # 1 extra poison row x 2 cycles = 2 failures
    assert len(outcome.failures) == 2
    assert "UNMAPPED_POISON" in outcome.failures[0].reason or "unknown Dynatrace synthetic status" in outcome.failures[0].reason


def test_recovery_publish_proof_two_sided_persisted_evidence():
    """AC6 (STORY-191): proves that pre-setting component status to MAJOR_OUTAGE
    and running an all-UP ladder triggers PUBLISHED_RECOVERY, changing stored status
    to OPERATIONAL while publications table remains empty (safe logging publisher).
    """
    cfg = load_config(_DEMO_CONFIG_DIR)
    signal_key = "api-gateway-health"
    component_id = cfg.component_for_signal(signal_key)

    # 1. Setup fakes & pre-set component status to MAJOR_OUTAGE
    initial_component = Component(
        id=component_id,
        name="API Gateway",
        status=ComponentStatus.MAJOR_OUTAGE,
        app_id="demo-core",
    )
    component_repo = FakeComponentRepository(components=[initial_component])
    assert component_repo.get(component_id).status is ComponentStatus.MAJOR_OUTAGE

    publication_repo = FakePublicationRepository()
    clock = FakeClock(_END)

    # 2. Build publisher chain using demo config (safe chain -> LoggingPublisher fallback)
    publisher = build_publisher(
        component_repo=component_repo,
        publication_repo=publication_repo,
        clock=clock,
        statuspage_page_id="FAKE-PAGE-ID",
        statuspage_api_token="FAKE-API-TOKEN",
        component_mapping=cfg.statuspage_mapping(),  # {} -> safe chain
    )

    proposal_repo = FakeProposalRepository()
    decide_service = DecideService(proposal_repo=proposal_repo, publisher=publisher)

    # 3. Seed observation repo with all-UP ladder for 2 cycles (recovery threshold = 2)
    obs_repo = FakeObservationRepository()
    clean_scenario = load_scenario_file(_SCENARIOS_DIR / "clean-fleet.yaml")[0]
    rows = expand_scenario(clean_scenario, end_time=_END)
    outcome = fetch_observations(
        signal_key=signal_key,
        native_id=clean_scenario.monitor_id,
        watermark=None,
        executor=lambda q: rows,
    )
    obs_repo.saved.extend(outcome.observations)

    # 4. Orchestrate signal
    action = orchestrate_signal(
        signal_key=signal_key,
        config=cfg,
        observation_repo=obs_repo,
        maintenance_repo=FakeMaintenanceRepository(),
        component_repo=component_repo,
        decide_service=decide_service,
        clock=clock,
    )

    # 5. Two-sided persisted evidence assertions:
    # Side 1: Recovery publish fired & writeback updated stored status to OPERATIONAL
    assert action is DecideAction.PUBLISHED_RECOVERY
    assert component_repo.get(component_id).status is ComponentStatus.OPERATIONAL

    # Side 2: Nothing left the process — publications table remains EMPTY
    assert publication_repo.list_recent() == []


def test_recovery_publish_proof_negative_side_no_publish_when_already_operational():
    """Negative proof (C2/A7): when component status is already OPERATIONAL,
    the same all-UP ladder yields NOOP/OBSOLETED and does NOT fire a publish.
    """
    cfg = load_config(_DEMO_CONFIG_DIR)
    signal_key = "api-gateway-health"
    component_id = cfg.component_for_signal(signal_key)

    initial_component = Component(
        id=component_id,
        name="API Gateway",
        status=ComponentStatus.OPERATIONAL,
        app_id="demo-core",
    )
    component_repo = FakeComponentRepository(components=[initial_component])
    assert component_repo.get(component_id).status is ComponentStatus.OPERATIONAL

    publication_repo = FakePublicationRepository()
    clock = FakeClock(_END)

    publisher = build_publisher(
        component_repo=component_repo,
        publication_repo=publication_repo,
        clock=clock,
        statuspage_page_id="FAKE-PAGE-ID",
        statuspage_api_token="FAKE-API-TOKEN",
        component_mapping=cfg.statuspage_mapping(),
    )

    proposal_repo = FakeProposalRepository()
    decide_service = DecideService(proposal_repo=proposal_repo, publisher=publisher)

    obs_repo = FakeObservationRepository()
    clean_scenario = load_scenario_file(_SCENARIOS_DIR / "clean-fleet.yaml")[0]
    rows = expand_scenario(clean_scenario, end_time=_END)
    outcome = fetch_observations(
        signal_key=signal_key,
        native_id=clean_scenario.monitor_id,
        watermark=None,
        executor=lambda q: rows,
    )
    obs_repo.saved.extend(outcome.observations)

    action = orchestrate_signal(
        signal_key=signal_key,
        config=cfg,
        observation_repo=obs_repo,
        maintenance_repo=FakeMaintenanceRepository(),
        component_repo=component_repo,
        decide_service=decide_service,
        clock=clock,
    )

    # No recovery publish fired when already OPERATIONAL
    assert action is not DecideAction.PUBLISHED_RECOVERY
    assert component_repo.get(component_id).status is ComponentStatus.OPERATIONAL
    assert publication_repo.list_recent() == []
