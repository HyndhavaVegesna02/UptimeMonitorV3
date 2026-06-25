"""STORY-011: the availability engine — two-grain math + group rollup (dossier §11).

Zone 4 / pure core. `core/services/availability.py` computes availability%
(over collapsed verdicts) and completeness% (over raw observations) on
demand, plus a group rollup — derive-on-read, nothing persisted. Tested with
IN-MEMORY FAKE repositories only (no DB, no Dynatrace — working agreement).
Reuses `collapse` (STORY-010); never consults the streak (P4).
"""

from __future__ import annotations

from datetime import datetime, timezone

from src.core.services.availability import AvailabilityResult

_COMPUTED_AT = datetime(2026, 6, 25, 12, 0, 0, tzinfo=timezone.utc)


# --- AvailabilityResult: frozen result shape (dossier §11) -------------------


def test_availability_result_constructs_with_all_frozen_fields():
    result = AvailabilityResult(
        availability_pct=0.5,
        completeness_pct=0.75,
        total_verdicts=4,
        passing_verdicts=2,
        maintenance_verdicts=1,
        gap_verdicts=0,
        distinct_locations=3,
        window="24h",
        computed_at=_COMPUTED_AT,
    )

    assert result.availability_pct == 0.5
    assert result.completeness_pct == 0.75
    assert result.total_verdicts == 4
    assert result.passing_verdicts == 2
    assert result.maintenance_verdicts == 1
    assert result.gap_verdicts == 0
    assert result.distinct_locations == 3
    assert result.window == "24h"
    assert result.computed_at == _COMPUTED_AT


def test_availability_result_is_frozen():
    result = AvailabilityResult(
        availability_pct=1.0,
        completeness_pct=1.0,
        total_verdicts=1,
        passing_verdicts=1,
        maintenance_verdicts=0,
        gap_verdicts=0,
        distinct_locations=1,
        window="24h",
        computed_at=_COMPUTED_AT,
    )

    try:
        result.availability_pct = 0.0  # type: ignore[misc]
    except (TypeError, ValueError) as exc:
        # Pydantic v2 frozen models raise ValidationError (a ValueError
        # subclass); accept either to avoid coupling to the exact type.
        assert "frozen" in str(exc).lower()
    else:
        raise AssertionError("expected assignment to a frozen model to raise")


def test_availability_result_allows_none_percentages():
    # AC6: the empty/degenerate case carries None percentages, not a sentinel
    # like 0.0 or -1, so a caller cannot mistake "no data" for "0% available".
    result = AvailabilityResult(
        availability_pct=None,
        completeness_pct=None,
        total_verdicts=0,
        passing_verdicts=0,
        maintenance_verdicts=0,
        gap_verdicts=0,
        distinct_locations=0,
        window="24h",
        computed_at=_COMPUTED_AT,
    )

    assert result.availability_pct is None
    assert result.completeness_pct is None
