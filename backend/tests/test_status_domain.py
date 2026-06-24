"""STORY-005: supporting canonical domain types for the core ports (dossier §6).

Zone 1 / pure core. `ComponentStatus`, `StatusChange`, and `IngestResult` are the
vendor-neutral types the ports speak in. `ComponentStatus` is a CLOSED enum; the
mapping to any Statuspage string lives in the Zone 5 adapter, never here.
"""

import pytest
from pydantic import ValidationError

from src.core.domain import ComponentStatus, IngestResult, StatusChange


# --- ComponentStatus: closed enum, canonical vocabulary only --------------------


def test_component_status_has_exactly_the_four_canonical_states():
    assert {member.value for member in ComponentStatus} == {
        "operational",
        "degraded",
        "partial_outage",
        "major_outage",
    }


def test_component_status_carries_no_vendor_vocabulary():
    # No member value leaks a Statuspage-specific word (e.g. major_outage is canonical
    # here; the adapter maps it to whatever the vendor calls it).
    for member in ComponentStatus:
        assert "statuspage" not in member.value.lower()


# --- StatusChange: frozen {component_id, status} --------------------------------


def test_status_change_constructs_from_component_id_and_status():
    change = StatusChange(component_id="checkout", status=ComponentStatus.OPERATIONAL)
    assert change.component_id == "checkout"
    assert change.status is ComponentStatus.OPERATIONAL


def test_status_change_is_frozen():
    change = StatusChange(component_id="checkout", status=ComponentStatus.OPERATIONAL)
    with pytest.raises(ValidationError):
        change.component_id = "other"


def test_status_change_rejects_unknown_status():
    with pytest.raises(ValidationError):
        StatusChange(component_id="checkout", status="on_fire")


# --- IngestResult: frozen {accepted, rejected} ----------------------------------


def test_ingest_result_constructs_from_accepted_and_rejected_counts():
    result = IngestResult(accepted=7, rejected=2)
    assert result.accepted == 7
    assert result.rejected == 2


def test_ingest_result_is_frozen():
    result = IngestResult(accepted=7, rejected=2)
    with pytest.raises(ValidationError):
        result.accepted = 0
