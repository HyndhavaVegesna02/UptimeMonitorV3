"""Tests for the STORY-182 reality-gate-side-2 publisher-chain discrimination.

`build_publisher` (`composition/publish_helper.py:183-234`) returns the SAME
top-level type, `StatusWritebackPublisher`, on BOTH the safe (empty mapping)
and unsafe (non-empty mapping) branch -- so asserting the top-level TYPE
proves nothing (sprint-64 plan finding B2). The only thing that actually
discriminates is the full `_delegate` chain of type names -- note `_delegate`,
not `delegate` (sprint-63's own trap, `implementer.md` A3).

No network call anywhere here: `build_publisher` only CONSTRUCTS the chain
(`StatuspagePublisher.__init__` and `make_statuspage_executor()` both just
build closures/store fields; nothing calls `.publish(...)`).
"""

from __future__ import annotations

from datetime import datetime, timezone

from demo_loop_gate.publisher_chain import describe_publisher_chain
from src.composition.publish_helper import build_publisher
from tests.fakes import FakeComponentRepository, FakePublicationRepository


def _build(component_mapping: dict[str, str]):
    return build_publisher(
        component_repo=FakeComponentRepository(),
        publication_repo=FakePublicationRepository(),
        clock=_FakeClock(),
        statuspage_page_id="REAL-LOOKING-PAGE-ID",
        statuspage_api_token="REAL-LOOKING-API-TOKEN",
        component_mapping=component_mapping,
    )


class _FakeClock:
    def now(self) -> datetime:
        return datetime(2026, 7, 30, tzinfo=timezone.utc)


def test_describe_publisher_chain_walks_delegate_not_delegate_attribute():
    safe_publisher = _build({})
    chain = describe_publisher_chain(safe_publisher)
    assert chain == ["StatusWritebackPublisher", "LoggingPublisher"]


def test_safe_and_unsafe_chains_differ_and_neither_is_length_one():
    safe_chain = describe_publisher_chain(_build({}))
    unsafe_chain = describe_publisher_chain(_build({"comp-1": "sp-1"}))

    assert len(safe_chain) > 1, (
        "a length-1 chain is a harness defect (wrong attribute walked)"
    )
    assert len(unsafe_chain) > 1, (
        "a length-1 chain is a harness defect (wrong attribute walked)"
    )
    assert safe_chain != unsafe_chain

    assert safe_chain == ["StatusWritebackPublisher", "LoggingPublisher"]
    assert unsafe_chain == [
        "StatusWritebackPublisher",
        "BestEffortPublisher",
        "RecordingPublisher",
        "StatuspagePublisher",
    ]
