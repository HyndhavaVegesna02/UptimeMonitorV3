"""STORY-004: the canonical SignalObservation spine (dossier §5, vocabulary rule P3).

Zone 1 / pure core. Tested with in-memory fixtures only — no Dynatrace, no DB,
no network. Every field must read vendor-neutrally; vendor identifiers live ONLY
inside `source` provenance.
"""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from src.core.domain import Health, Provenance


# --- Step 1/2: Health closed enum (AC2 vocabulary; up/down/degraded) ------------


def test_health_has_exactly_up_down_degraded():
    assert {member.value for member in Health} == {"up", "down", "degraded"}


# --- Step 3/4: Provenance frozen {system, native_id, native_kind} (AC1) ---------


def test_provenance_constructs_from_system_native_id_native_kind():
    prov = Provenance(system="dynatrace", native_id="HOST-ABC123", native_kind="http")
    assert prov.system == "dynatrace"
    assert prov.native_id == "HOST-ABC123"
    assert prov.native_kind == "http"


def test_provenance_is_frozen():
    prov = Provenance(system="dynatrace", native_id="HOST-ABC123", native_kind="http")
    with pytest.raises(ValidationError):
        prov.native_id = "HOST-OTHER"
