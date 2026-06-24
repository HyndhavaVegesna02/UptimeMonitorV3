"""STORY-004: the canonical SignalObservation spine (dossier §5, vocabulary rule P3).

Zone 1 / pure core. Tested with in-memory fixtures only — no Dynatrace, no DB,
no network. Every field must read vendor-neutrally; vendor identifiers live ONLY
inside `source` provenance.
"""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from src.core.domain import Health


# --- Step 1/2: Health closed enum (AC2 vocabulary; up/down/degraded) ------------


def test_health_has_exactly_up_down_degraded():
    assert {member.value for member in Health} == {"up", "down", "degraded"}
