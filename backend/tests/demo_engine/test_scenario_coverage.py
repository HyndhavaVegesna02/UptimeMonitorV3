"""STORY-176 AC5 — scenario coverage (`UP` and absence only; see the story's
scope note: a real failure code has never been observed, so no scenario here
drives a `DOWN`/`DEGRADED` observation).

Every case is driven through the REAL production ingest chain (`normalize_
rows` -> `IngestService`) with in-memory fakes (working agreement: pure core,
mockable edges, no live Dynatrace/DynamoDB needed) — never a live loop
(that is STORY-182). Each test asserts the REWORDED, real observable effect
(sprint-63 plan-verifier finding: `expected_locations`/`freshness_for`/
`stale_after_cycles`/`reentry_cycles` have zero consumers outside
`composition/config.py`), not a freshness-policy outcome nothing wires up.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from demo_engine.scenario import expand_scenario, load_scenario_file
from src.adapters.inbound.dynatrace.dispatch import normalize_rows
from src.composition.config import load_config
from src.composition.orchestrate import orchestrate_signal
from src.core.queries.availability import AvailabilityCalculator, bucket_into_cycles
from src.core.services.decide import DecideAction, DecideService
from src.core.services.ingest_service import IngestService
from tests.fakes import (
    FakeClock,
    FakeComponentRepository,
    FakeMaintenanceRepository,
    FakeObservationRepository,
    FakeProposalRepository,
    FakeWatermarkRepository,
    RecordingStatusPublisher,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEMO_CONFIG_DIR = _REPO_ROOT / "config" / "demo"
_SCENARIOS_DIR = _DEMO_CONFIG_DIR / "scenarios"

_END = datetime(2026, 7, 30, 12, 0, 0, tzinfo=timezone.utc)


def _ingest_scenario(
    scenario_file: str, signal_key: str, *, end_time: datetime = _END
):
    """Load one scenario file's named signal, expand + normalize + ingest it
    via the REAL production chain, and return (IngestResult, observation_repo,
    watermark_repo)."""
    scenarios = load_scenario_file(_SCENARIOS_DIR / scenario_file)
    by_key = {s.signal_key: s for s in scenarios}
    scenario = by_key[signal_key]

    rows = expand_scenario(scenario, end_time=end_time)
    observations = normalize_rows(rows, signal_key=signal_key)

    observation_repo = FakeObservationRepository()
    watermark_repo = FakeWatermarkRepository()
    rejected_repo_result = IngestService(
        observation_repo=observation_repo,
        watermark_repo=watermark_repo,
        rejected_repo=_FakeRejectedRepo(),
        clock=FakeClock(end_time),
    ).ingest_observations(observations)

    return rejected_repo_result, observation_repo, watermark_repo


class _FakeRejectedRepo:
    """A minimal `RejectedObservationRepository` fake — no scenario here is
    expected to be rejected (all timestamps are at or before `end_time`,
    AC2f), so this only needs to exist, not do anything interesting."""

    def __init__(self) -> None:
        self.saved: list[dict] = []

    def save(self, *, signal_key, reason, payload, rejected_at) -> None:
        self.saved.append(
            {
                "signal_key": signal_key,
                "reason": reason,
                "payload": payload,
                "rejected_at": rejected_at,
            }
        )


# --- AC5(a): a clean fleet across all locations -----------------------------


def test_clean_fleet_scenario_ingests_cleanly_and_reports_full_availability():
    signal_key = "api-gateway-health"
    result, observation_repo, _ = _ingest_scenario(
        "clean-fleet.yaml", signal_key, end_time=_END
    )

    assert result.accepted == 5 * 4  # 5 cycles x 4 locations
    assert result.rejected == 0

    since = _END - timedelta(seconds=30 * 7)
    calc = AvailabilityCalculator(observation_repo=observation_repo)
    availability = calc.compute(
        signal_key,
        since=since,
        until=_END,
        interval=timedelta(seconds=30),
        window="test",
        maintenance=lambda _cycle_start: False,
        computed_at=_END,
    )

    assert availability.distinct_locations == 4
    assert availability.availability_pct == 1.0


# --- AC5(b): a fully dark location -------------------------------------------


def test_dark_location_scenario_lowers_distinct_locations_but_stays_up():
    """AC5(b) reworded: a dark location does NOT exercise a freshness/
    completeness path (nothing consumes `expected_locations`) -- it lowers
    `distinct_locations` (3, not the 4 declared for this monitor) and
    `collapse` still sees `{UP}` from the surviving locations
    (`pipeline.py`'s `_collapse_health` has no location-count awareness)."""
    signal_key = "search-service-query"
    result, observation_repo, _ = _ingest_scenario(
        "dark-location.yaml", signal_key, end_time=_END
    )

    assert result.accepted == 3 * 3  # 3 cycles x 3 (of 4 declared) locations

    since = _END - timedelta(seconds=30 * 7)
    calc = AvailabilityCalculator(observation_repo=observation_repo)
    availability = calc.compute(
        signal_key,
        since=since,
        until=_END,
        interval=timedelta(seconds=30),
        window="test",
        maintenance=lambda _cycle_start: False,
        computed_at=_END,
    )

    assert availability.distinct_locations == 3  # not 4 -- loc-d never reported
    assert availability.availability_pct == 1.0  # still {UP} from survivors


# --- AC5(c): a fully dark monitor --------------------------------------------


def test_dark_monitor_scenario_yields_empty_window_and_orchestrate_noops():
    """AC5(c) reworded: no freshness path is consulted -- an empty window
    yields `streak(verdicts) is None`, and `orchestrate_signal` NOOPs
    (`orchestrate.py:113-121`)."""
    signal_key = "billing-service-invoice"
    result, observation_repo, _ = _ingest_scenario(
        "dark-monitor.yaml", signal_key, end_time=_END
    )

    assert result.accepted == 0
    assert result.rejected == 0

    since = _END - timedelta(seconds=30 * 7)
    buckets = bucket_into_cycles(
        list(observation_repo.in_window(signal_key, since, _END)),
        since=since,
        interval=timedelta(seconds=30),
    )
    assert buckets == {}

    cfg = load_config(_DEMO_CONFIG_DIR)
    action = orchestrate_signal(
        signal_key=signal_key,
        config=cfg,
        observation_repo=observation_repo,
        maintenance_repo=FakeMaintenanceRepository(),
        component_repo=FakeComponentRepository(),  # empty: never reached
        decide_service=DecideService(
            proposal_repo=FakeProposalRepository(),
            publisher=RecordingStatusPublisher(),
        ),
        clock=FakeClock(_END),
    )
    assert action == DecideAction.NOOP


# --- AC5(d): staggered intervals ---------------------------------------------


def test_staggered_intervals_scenario_produces_misaligned_cycle_boundaries():
    """AC5(d): two monitors on ONE component (`catalog-service`) at different
    `interval_seconds` (30 vs 45) -- their cycle-start boundaries, bucketed
    each at its OWN interval, do not line up."""
    cfg = load_config(_DEMO_CONFIG_DIR)
    list_interval = timedelta(
        seconds=cfg.signal("catalog-service-list").interval_seconds
    )
    detail_interval = timedelta(
        seconds=cfg.signal("catalog-service-detail").interval_seconds
    )
    assert list_interval != detail_interval

    list_result, list_repo, _ = _ingest_scenario(
        "staggered-intervals.yaml", "catalog-service-list", end_time=_END
    )
    detail_result, detail_repo, _ = _ingest_scenario(
        "staggered-intervals.yaml", "catalog-service-detail", end_time=_END
    )
    assert list_result.accepted == 2 * 2
    assert detail_result.accepted == 2 * 2

    list_since = _END - 7 * list_interval
    detail_since = _END - 7 * detail_interval

    list_buckets = bucket_into_cycles(
        list(list_repo.in_window("catalog-service-list", list_since, _END)),
        since=list_since,
        interval=list_interval,
    )
    detail_buckets = bucket_into_cycles(
        list(detail_repo.in_window("catalog-service-detail", detail_since, _END)),
        since=detail_since,
        interval=detail_interval,
    )

    # Cycle boundaries are keyed by their own start instant; the two
    # monitors' bucket keys must NOT be the same set -- the different
    # interval means they do not share cycle boundaries.
    assert set(list_buckets) != set(detail_buckets)


# --- AC5(e): a late-returning monitor -----------------------------------------


def test_late_return_scenario_resumes_ingest_after_the_gap():
    """AC5(e) reworded: `reentry_cycles` has zero consumers -- what this
    proves is that ingest simply RESUMES after a gap: rows land for the
    early AND the late cycle, and the watermark advances to the latest
    (post-gap) observation, not stuck at the pre-gap one."""
    signal_key = "notifications-service-email"
    result, observation_repo, watermark_repo = _ingest_scenario(
        "late-return.yaml", signal_key, end_time=_END
    )

    # 2 non-empty cycles (first and last) x 2 locations; the two middle
    # (dark) cycles contribute nothing.
    assert result.accepted == 2 * 2
    assert result.rejected == 0

    all_observed = [obs.observed_at for obs in observation_repo.saved]
    assert watermark_repo.get(signal_key) == max(all_observed)
    assert watermark_repo.get(signal_key) == _END  # the LAST cycle, post-gap
