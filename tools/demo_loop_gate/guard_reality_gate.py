"""STORY-182 reality gate side 2 -- discriminating on the guard, standalone.

Independently callable: ``python tools/demo_loop_gate/guard_reality_gate.py``
(no pytest, no DynamoDB, no Docker). Builds the REAL `build_publisher` chain
twice -- once with `config/demo`'s own (empty) mapping, once with a
throwaway mapping that DOES declare a `statuspage_component_id` -- and
prints the full `_delegate` chain of type names for each side, asserting
they differ. Makes NO network call: `build_publisher` only constructs
objects (`StatuspagePublisher.__init__`, `make_statuspage_executor()`
build closures, nothing calls `.publish(...)`).

See `tools/demo_loop_gate/publisher_chain.py` for the (also independently
unit-tested, `backend/tests/demo_loop_gate/test_publisher_chain.py`) chain
walker this script uses.
"""

from __future__ import annotations

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
print("  ", assert_import_root("src.composition.publish_helper", BACKEND_ROOT))
print()

from src.composition.config import load_config  # noqa: E402
from src.composition.publish_helper import build_publisher  # noqa: E402
from src.core.domain.status import ComponentStatus  # noqa: E402
from src.core.ports.clock import ClockPort  # noqa: E402
from src.core.ports.component_repository import ComponentRepository  # noqa: E402
from src.core.ports.publication_repository import PublicationRepository  # noqa: E402

from demo_loop_gate.publisher_chain import describe_publisher_chain  # noqa: E402


class _NoopComponentRepository(ComponentRepository):
    def get(self, component_id):  # pragma: no cover - never called (no publish())
        raise NotImplementedError

    def list_components(self):  # pragma: no cover
        return []

    def set_status(
        self, component_id, status: ComponentStatus
    ) -> None:  # pragma: no cover
        raise NotImplementedError


class _NoopPublicationRepository(PublicationRepository):
    def record(self, publication):  # pragma: no cover - never called (no publish())
        raise NotImplementedError

    def list_recent(self, limit: int = 50):  # pragma: no cover
        return []


class _FixedClock(ClockPort):
    def now(self) -> datetime:
        return datetime(2026, 7, 30, tzinfo=timezone.utc)


def _build(component_mapping: dict[str, str]):
    return build_publisher(
        component_repo=_NoopComponentRepository(),
        publication_repo=_NoopPublicationRepository(),
        clock=_FixedClock(),
        statuspage_page_id="REAL-LOOKING-PAGE-ID",
        statuspage_api_token="REAL-LOOKING-API-TOKEN",
        component_mapping=component_mapping,
    )


def main() -> bool:
    demo_cfg = load_config(REPO_ROOT / "config" / "demo")
    demo_mapping = demo_cfg.statuspage_mapping()

    safe_publisher = _build(demo_mapping)
    unsafe_publisher = _build({"fake-component": "fake-statuspage-id"})

    safe_chain = describe_publisher_chain(safe_publisher)
    unsafe_chain = describe_publisher_chain(unsafe_publisher)

    print("=" * 78)
    print("REALITY GATE 182 SIDE 2 -- publisher-chain discrimination")
    print("=" * 78)
    print(f"  demo config statuspage_mapping() : {demo_mapping!r}  (expect {{}})")
    print(f"  SAFE   (_delegate chain) : {safe_chain}")
    print(f"  UNSAFE (_delegate chain) : {unsafe_chain}")

    length_one = [
        label
        for label, chain in (("SAFE", safe_chain), ("UNSAFE", unsafe_chain))
        if len(chain) <= 1
    ]
    if length_one:
        print(
            f"  HARNESS DEFECT: chain(s) {length_one} have length <= 1 -- "
            "the wrong attribute was walked (should be `_delegate`, not "
            "`delegate`). DISCARDING this result, not reporting it as a pass."
        )
        return False

    chains_differ = safe_chain != unsafe_chain
    print(f"  chains DIFFER             : {chains_differ}")
    expected_safe = ["StatusWritebackPublisher", "LoggingPublisher"]
    expected_unsafe = [
        "StatusWritebackPublisher",
        "BestEffortPublisher",
        "RecordingPublisher",
        "StatuspagePublisher",
    ]
    matches_expected = safe_chain == expected_safe and unsafe_chain == expected_unsafe
    print(f"  matches expected shapes    : {matches_expected}")

    verdict = chains_differ and matches_expected
    print()
    print(f"REALITY GATE 182 SIDE 2: {'PASS' if verdict else 'FAIL'}")
    return verdict


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
