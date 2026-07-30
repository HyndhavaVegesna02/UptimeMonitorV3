"""STORY-182 fix round, MAJOR 2 -- the positive side must ENFORCE its
AC3/AC4/AC5 evidence, not merely print it.

Before this fix, `harness.py::run_positive_side` collected
`_collect_ac3_evidence`/`_collect_ac4_evidence`/`_collect_ac5_evidence` and
`__main__` dumped the resulting dict as JSON unconditionally, exiting 0
regardless of the values inside it -- contradicting the module's own
docstring ("raises loudly ... if any precondition fails") and AC5's explicit
wording ("the endpoint is asserted to return a well-formed empty result").

These are pure functions over plain evidence dicts (the exact shape
`_collect_ac3_evidence`/`_collect_ac4_evidence`/`_collect_ac5_evidence`
already build) -- no subprocess, no network, no DynamoDB -- so the
enforcement logic itself is unit-tested directly, independent of the
integration-only full harness run.

`_assert_ac3_ingest`/`_assert_ac4_vendor_health`/`_assert_ac5_approvals` use
plain `assert` (matching the existing `_assert_ac1_preconditions` pattern),
so their failure mode is `AssertionError`. `_assert_loop_startup_and_ingestion`
raises `RealityGateError` explicitly for its two timeout conditions, per the
fix-round instruction to treat a timeout as a failure, never partial
evidence.
"""

from __future__ import annotations

import pytest
from demo_loop_gate.harness import (
    RealityGateError,
    _assert_ac3_ingest,
    _assert_ac4_vendor_health,
    _assert_ac5_approvals,
    _assert_loop_startup_and_ingestion,
    _parse_pytest_skip_count,
)

_GOOD_AC3 = {
    "components_count": 13,
    "signals_count": 41,
    "signals_with_zero_rows": [],
    "signals_with_under_4_locations": [],
}

_GOOD_AC4 = {
    "drift_warning_count": 0,
    "healthy_info_count": 41,
    "expected_signal_count": 41,
}

_GOOD_AC5 = {"is_empty_list": True, "body": []}


def test_assert_ac3_ingest_passes_on_good_evidence():
    _assert_ac3_ingest(_GOOD_AC3)  # must not raise


def test_assert_ac3_ingest_raises_on_a_zero_row_signal():
    bad = dict(_GOOD_AC3, signals_with_zero_rows=["sig-broken"])
    with pytest.raises(AssertionError, match="AC3"):
        _assert_ac3_ingest(bad)


def test_assert_ac3_ingest_raises_on_under_4_locations():
    bad = dict(_GOOD_AC3, signals_with_under_4_locations=["sig-partial"])
    with pytest.raises(AssertionError, match="AC3"):
        _assert_ac3_ingest(bad)


def test_assert_ac3_ingest_raises_on_too_few_components():
    bad = dict(_GOOD_AC3, components_count=5)
    with pytest.raises(AssertionError, match="AC3"):
        _assert_ac3_ingest(bad)


def test_assert_ac3_ingest_raises_on_too_few_signals():
    bad = dict(_GOOD_AC3, signals_count=10)
    with pytest.raises(AssertionError, match="AC3"):
        _assert_ac3_ingest(bad)


def test_assert_ac4_vendor_health_passes_on_good_evidence():
    _assert_ac4_vendor_health(_GOOD_AC4)  # must not raise


def test_assert_ac4_vendor_health_raises_on_nonzero_drift():
    bad = dict(_GOOD_AC4, drift_warning_count=3)
    with pytest.raises(AssertionError, match="AC4"):
        _assert_ac4_vendor_health(bad)


def test_assert_ac4_vendor_health_raises_on_healthy_count_mismatch():
    bad = dict(_GOOD_AC4, healthy_info_count=38)
    with pytest.raises(AssertionError, match="AC4"):
        _assert_ac4_vendor_health(bad)


def test_assert_ac5_approvals_passes_on_empty():
    _assert_ac5_approvals(_GOOD_AC5)  # must not raise


def test_assert_ac5_approvals_raises_on_nonempty():
    bad = {"is_empty_list": False, "body": [{"signal_key": "sig-1"}]}
    with pytest.raises(AssertionError, match="AC5"):
        _assert_ac5_approvals(bad)


def test_assert_loop_startup_and_ingestion_passes_when_both_true():
    _assert_loop_startup_and_ingestion(
        startup_seen=True,
        last_signal_ingested=True,
        last_signal_key="sig-last",
        loop_wait_seconds=90.0,
    )  # must not raise


def test_assert_loop_startup_and_ingestion_raises_when_startup_not_seen():
    """A startup-marker timeout is a FAILURE, never partial evidence --
    previously this only set a flag and execution continued regardless."""
    with pytest.raises(RealityGateError, match="startup"):
        _assert_loop_startup_and_ingestion(
            startup_seen=False,
            last_signal_ingested=False,
            last_signal_key="sig-last",
            loop_wait_seconds=90.0,
        )


def test_assert_loop_startup_and_ingestion_raises_when_last_signal_not_ingested():
    with pytest.raises(RealityGateError, match="sig-last"):
        _assert_loop_startup_and_ingestion(
            startup_seen=True,
            last_signal_ingested=False,
            last_signal_key="sig-last",
            loop_wait_seconds=90.0,
        )


# Minor (STORY-182 fix round): AC1(d)'s pytest subprocess exit code alone
# cannot distinguish "passed" from "skipped" -- 2 of
# backend/tests/test_demo_fleet_config.py's 10 tests are dynamo_local-gated,
# and a nonzero skip count is an incomplete gate (this sprint's standing
# rule). `_parse_pytest_skip_count` is the pure parser over `pytest -q`'s
# own summary line, unit-tested against real-shaped pytest output.


def test_parse_pytest_skip_count_reads_the_dash_q_summary_line():
    stdout = "..........                    [100%]\n10 passed in 0.42s\n"
    assert _parse_pytest_skip_count(stdout) == 0


def test_parse_pytest_skip_count_reads_a_nonzero_skip_count():
    stdout = "........ss                    [100%]\n8 passed, 2 skipped in 0.51s\n"
    assert _parse_pytest_skip_count(stdout) == 2
