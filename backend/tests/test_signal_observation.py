"""STORY-004: the canonical SignalObservation spine (dossier §5, vocabulary rule P3).

Zone 1 / pure core. Tested with in-memory fixtures only — no Dynatrace, no DB,
no network. Every field must read vendor-neutrally; vendor identifiers live ONLY
inside `source` provenance.
"""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError
from src.core.domain import Health, Provenance, SignalObservation


def _valid_observation(**overrides):
    """A construction-ready set of valid §5 fields; override one to probe a rule."""
    fields = dict(
        signal_key="checkout-http",
        observed_at=datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc),
        health=Health.UP,
        source_event_id="evt-0001",
        source=Provenance(
            system="dynatrace", native_id="HTTP_CHECK-9F2A", native_kind="http"
        ),
        location="us-east",
        latency_ms=142,
        raw_ref="s3://raw/evt-0001.json",
    )
    fields.update(overrides)
    return fields


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


# --- Step 5/6: SignalObservation constructs from valid §5 fields; frozen (AC1) --


def test_signal_observation_constructs_from_valid_fields():
    obs = SignalObservation(**_valid_observation())
    assert obs.signal_key == "checkout-http"
    assert obs.observed_at == datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc)
    assert obs.health is Health.UP
    assert obs.source_event_id == "evt-0001"
    assert obs.source.native_id == "HTTP_CHECK-9F2A"
    assert obs.location == "us-east"
    assert obs.latency_ms == 142
    assert obs.raw_ref == "s3://raw/evt-0001.json"


def test_signal_observation_optionals_default_to_none():
    fields = _valid_observation()
    del fields["latency_ms"]
    del fields["raw_ref"]
    obs = SignalObservation(**fields)
    assert obs.latency_ms is None
    assert obs.raw_ref is None


def test_signal_observation_is_frozen():
    obs = SignalObservation(**_valid_observation())
    with pytest.raises(ValidationError):
        obs.signal_key = "mutated"


# --- Step 7: invalid health raises ValidationError (AC2) ------------------------


def test_signal_observation_rejects_unknown_health():
    with pytest.raises(ValidationError):
        SignalObservation(**_valid_observation(health="flapping"))


# --- Step 8/9: observed_at must be tz-aware UTC; naive rejected (AC3) -----------


def test_signal_observation_rejects_naive_observed_at():
    naive = datetime(2026, 6, 24, 10, 0, 0)  # no tzinfo
    assert naive.tzinfo is None
    with pytest.raises(ValidationError):
        SignalObservation(**_valid_observation(observed_at=naive))


def test_signal_observation_accepts_tz_aware_utc_observed_at():
    aware = datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc)
    obs = SignalObservation(**_valid_observation(observed_at=aware))
    assert obs.observed_at == aware


def test_signal_observation_rejects_non_utc_offset_observed_at():
    plus_two = datetime(2026, 6, 24, 12, 0, 0, tzinfo=timezone(timedelta(hours=2)))
    with pytest.raises(ValidationError):
        SignalObservation(**_valid_observation(observed_at=plus_two))


# --- Step 10: vendor id lives ONLY in source; names read vendor-neutrally (AC4) -

# Field names that make sense to a reader who has never heard of Dynatrace.
_VENDOR_NEUTRAL_FIELDS = {
    "signal_key",
    "observed_at",
    "health",
    "source_event_id",
    "source",
    "location",
    "latency_ms",
    "raw_ref",
}


def test_signal_observation_field_names_are_vendor_neutral():
    assert set(SignalObservation.model_fields) == _VENDOR_NEUTRAL_FIELDS
    # No top-level field name leaks a vendor word.
    for name in SignalObservation.model_fields:
        lowered = name.lower()
        assert "dynatrace" not in lowered
        assert "native" not in lowered  # `native_*` belongs to Provenance, not here


def test_vendor_id_appears_only_inside_source():
    vendor_id = "HTTP_CHECK-9F2A"
    obs = SignalObservation(
        **_valid_observation(
            source=Provenance(
                system="dynatrace", native_id=vendor_id, native_kind="http"
            )
        )
    )

    # The vendor id is reachable only via source.native_id...
    assert obs.source.native_id == vendor_id
    # ...and appears in no field outside `source`.
    outside_source = obs.model_dump(exclude={"source"})
    assert vendor_id not in {str(v) for v in outside_source.values()}


# --- Step 11/12: round-trip equality + missing required field raises (AC5) ------


def test_signal_observation_round_trips_via_model_dump():
    obs = SignalObservation(**_valid_observation())
    reconstructed = SignalObservation(**obs.model_dump())
    assert reconstructed == obs


def test_signal_observation_round_trips_with_optionals_omitted():
    fields = _valid_observation()
    del fields["latency_ms"]
    del fields["raw_ref"]
    obs = SignalObservation(**fields)
    reconstructed = SignalObservation(**obs.model_dump())
    assert reconstructed == obs


def test_signal_observation_requires_signal_key():
    fields = _valid_observation()
    del fields["signal_key"]
    with pytest.raises(ValidationError):
        SignalObservation(**fields)


def test_signal_observation_requires_source():
    fields = _valid_observation()
    del fields["source"]
    with pytest.raises(ValidationError):
        SignalObservation(**fields)
