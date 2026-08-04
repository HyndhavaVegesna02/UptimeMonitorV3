"""STORY-182 reality gate side 3 — discriminating on backfill.

Restated per the sprint-64 plan (B7): `check_vendor_id_health` needs >=1 row
INSIDE the trailing 2h window (`adapters/inbound/dynatrace/query.py:136,155`;
relocated there from `composition/vendor_health.py:37,50` at STORY-204), not
">=2h of coverage", and the healthy branch is NOT silent -- it logs one INFO
line per healthy signal (`composition/vendor_health.py:124-132`),
contradicting its own docstring at `:77` ("logs nothing"; the docstring is
wrong, this test is written against the CODE).

Two sides, over the SAME fleet config, differing ONLY in whether the engine
holds any rows in the window:
  - an empty `DemoRowStore` -> one `VENDOR-ID DRIFT SUSPECTED` warning PER
    SIGNAL (41), zero INFO lines;
  - the STORY-182 B1 fleet-wide coverage store -> zero warnings, one
    `Vendor-id health OK` INFO line per signal (41).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from demo_engine.store import DemoRowStore
from demo_loop_gate.fleet_coverage import build_fleet_row_store
from src.composition.config import load_config
from src.composition.vendor_health import check_vendor_id_health

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEMO_CONFIG_DIR = _REPO_ROOT / "config" / "demo"
_END = datetime(2026, 7, 30, 12, 0, 0, tzinfo=timezone.utc)


def _run_probe(store: DemoRowStore, caplog):
    cfg = load_config(_DEMO_CONFIG_DIR)
    executor = lambda query: store.handle_query(query, request_instant=_END)  # noqa: E731

    with caplog.at_level(logging.INFO, logger="src.composition.vendor_health"):
        check_vendor_id_health(config=cfg, executor=executor)

    drift = sum(
        1 for r in caplog.records if "VENDOR-ID DRIFT SUSPECTED" in r.getMessage()
    )
    healthy = sum(1 for r in caplog.records if "Vendor-id health OK" in r.getMessage())
    return drift, healthy, cfg


def test_backfill_discrimination_empty_store_warns_for_every_signal(caplog):
    empty_store = DemoRowStore()
    drift, healthy, cfg = _run_probe(empty_store, caplog)

    all_signal_keys = {sig.signal_key for app in cfg.apps for sig in app.signals}
    assert drift == len(all_signal_keys)
    assert healthy == 0


def test_backfill_discrimination_coverage_store_is_quiet_for_every_signal(caplog):
    cfg = load_config(_DEMO_CONFIG_DIR)
    coverage_store = build_fleet_row_store(cfg, end_time=_END)

    drift, healthy, cfg2 = _run_probe(coverage_store, caplog)

    all_signal_keys = {sig.signal_key for app in cfg2.apps for sig in app.signals}
    assert drift == 0
    assert healthy == len(all_signal_keys)


def test_backfill_discrimination_sides_actually_differ(caplog):
    """The two-sided proof itself (working agreement A3): both counts must
    DIFFER between sides, never come back identical."""
    empty_drift, empty_healthy, _ = _run_probe(DemoRowStore(), caplog)
    caplog.clear()
    cfg = load_config(_DEMO_CONFIG_DIR)
    coverage_drift, coverage_healthy, _ = _run_probe(
        build_fleet_row_store(cfg, end_time=_END), caplog
    )

    assert (empty_drift, empty_healthy) != (coverage_drift, coverage_healthy)
    assert empty_drift > 0 and coverage_drift == 0
    assert empty_healthy == 0 and coverage_healthy > 0
