"""STORY-182 reality gate side 3 -- discriminating on backfill, standalone.

Independently callable: ``python tools/demo_loop_gate/backfill_reality_gate.py``
(no pytest, no DynamoDB, no Docker, no network -- `check_vendor_id_health`
is driven through an in-memory `DemoRowStore`, exactly the injected
`Executor` seam `run_periodic` uses in production).

Restated per the sprint-64 plan (B7): the vendor-health probe needs >=1 row
INSIDE its trailing 2h window (`adapters/inbound/dynatrace/query.py:133,152`;
relocated there from `composition/vendor_health.py:37,50` at STORY-204), not
">=2h of coverage", and its healthy branch is NOT silent -- it logs one INFO
line per healthy signal (`composition/vendor_health.py:124-132`),
contradicting its own docstring at `:77` ("logs nothing"). Two sides over the
SAME demo fleet config, ONLY the row store differing:
  - EMPTY store  -> one `VENDOR-ID DRIFT SUSPECTED` warning PER SIGNAL,
    zero healthy-INFO lines;
  - the B1 fleet-wide COVERAGE store -> zero warnings, one healthy-INFO
    line per signal.

See `backend/tests/demo_loop_gate/test_backfill_discrimination.py` for the
same discrimination as a committed pytest regression.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
TOOLS_ROOT = REPO_ROOT / "tools"

if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from import_provenance import assert_import_root  # noqa: E402

print("PROVENANCE (STORY-187, before reporting anything):")
print("  ", assert_import_root("src.composition.vendor_health", BACKEND_ROOT))
print("  ", assert_import_root("demo_engine.store", TOOLS_ROOT))
print()

from demo_engine.store import DemoRowStore  # noqa: E402
from src.composition.config import load_config  # noqa: E402
from src.composition.vendor_health import check_vendor_id_health  # noqa: E402

from demo_loop_gate.fleet_coverage import build_fleet_row_store  # noqa: E402

_END = datetime(2026, 7, 30, 12, 0, 0, tzinfo=timezone.utc)


class _Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.drift = 0
        self.healthy = 0

    def emit(self, record: logging.LogRecord) -> None:
        msg = record.getMessage()
        if "VENDOR-ID DRIFT SUSPECTED" in msg:
            self.drift += 1
        elif "Vendor-id health OK" in msg:
            self.healthy += 1


def _run_side(label: str, store: DemoRowStore, config) -> _Capture:
    logger = logging.getLogger("src.composition.vendor_health")
    cap = _Capture()
    logger.addHandler(cap)
    logger.setLevel(logging.INFO)
    try:
        executor = lambda query: store.handle_query(query, request_instant=_END)  # noqa: E731
        check_vendor_id_health(config=config, executor=executor)
    finally:
        logger.removeHandler(cap)
    print(f"  {label}: drift_warnings={cap.drift}  healthy_info_lines={cap.healthy}")
    return cap


def main() -> bool:
    cfg = load_config(REPO_ROOT / "config" / "demo")
    signal_count = sum(len(app.signals) for app in cfg.apps)

    print("=" * 78)
    print("REALITY GATE 182 SIDE 3 -- backfill discrimination")
    print("=" * 78)
    print(f"  fleet signal count: {signal_count}")

    empty_cap = _run_side("EMPTY store   ", DemoRowStore(), cfg)
    coverage_store = build_fleet_row_store(cfg, end_time=_END)
    coverage_cap = _run_side("COVERAGE store", coverage_store, cfg)

    differ = (empty_cap.drift, empty_cap.healthy) != (
        coverage_cap.drift,
        coverage_cap.healthy,
    )
    matches_expected = (
        empty_cap.drift == signal_count
        and empty_cap.healthy == 0
        and coverage_cap.drift == 0
        and coverage_cap.healthy == signal_count
    )

    print(f"  sides DIFFER        : {differ}")
    print(f"  matches expectation : {matches_expected}")
    verdict = differ and matches_expected
    print()
    print(f"REALITY GATE 182 SIDE 3: {'PASS' if verdict else 'FAIL'}")
    return verdict


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
