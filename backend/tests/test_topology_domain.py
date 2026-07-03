"""Tests for the topology domain types (dossier §7, §9, STORY-044 D2).

`Signal` is the seeded-topology read model — distinct from
`core/domain/signal.py::SignalObservation` (a runtime observation). Covers the
`interval_seconds > 0` coherence invariant (both shapes: `None` is allowed, a
non-positive int is rejected).
"""

import pytest
from pydantic import ValidationError
from src.core.domain.topology import (
    Signal,
    SignalIntervalUnconfiguredError,
    SignalNotFoundError,
)


def test_signal_allows_null_interval_seconds():
    """A signal predating D1's backfill (or a re-seed race) has interval_seconds=None."""
    signal = Signal(
        signal_key="checkout-http",
        name="Checkout HTTP",
        component_id="checkout",
        interval_seconds=None,
    )
    assert signal.interval_seconds is None


def test_signal_allows_positive_interval_seconds():
    signal = Signal(
        signal_key="checkout-http",
        name="Checkout HTTP",
        component_id="checkout",
        interval_seconds=120,
    )
    assert signal.interval_seconds == 120


def test_signal_allows_null_component_id_orphan():
    """An orphan signal (no component mapping) is a valid shape (AC1 nesting excludes it)."""
    signal = Signal(
        signal_key="orphan-sig",
        name="Orphan",
        component_id=None,
        interval_seconds=60,
    )
    assert signal.component_id is None


@pytest.mark.parametrize("bad_interval", [0, -1, -60])
def test_signal_rejects_non_positive_interval_seconds(bad_interval):
    with pytest.raises(ValidationError):
        Signal(
            signal_key="checkout-http",
            name="Checkout HTTP",
            component_id="checkout",
            interval_seconds=bad_interval,
        )


def test_signal_is_frozen():
    signal = Signal(
        signal_key="checkout-http",
        name="Checkout HTTP",
        component_id="checkout",
        interval_seconds=60,
    )
    with pytest.raises(ValidationError):
        signal.interval_seconds = 30


def test_domain_errors_are_exceptions_not_valueerror():
    """D2: SignalNotFoundError/SignalIntervalUnconfiguredError are plain Exception
    subclasses (unlike ComponentNotFoundError/ProposalNotFoundError, which are
    ValueError subclasses) — the edge service raises them, never the port.
    """
    assert issubclass(SignalNotFoundError, Exception)
    assert issubclass(SignalIntervalUnconfiguredError, Exception)
