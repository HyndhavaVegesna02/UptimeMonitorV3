"""Tests for the Component domain read type (dossier §9/§17)."""

import pytest
from pydantic import ValidationError
from src.core.domain.component import Component
from src.core.domain.status import ComponentStatus


def test_component_domain_type_construction():
    comp = Component(
        id="comp-1",
        name="Checkout Component",
        status=ComponentStatus.OPERATIONAL,
        app_id="app-1",
    )
    assert comp.id == "comp-1"
    assert comp.name == "Checkout Component"
    assert comp.status == ComponentStatus.OPERATIONAL
    assert comp.app_id == "app-1"


def test_component_domain_type_is_frozen():
    comp = Component(
        id="comp-1",
        name="Checkout Component",
        status=ComponentStatus.OPERATIONAL,
        app_id="app-1",
    )
    with pytest.raises(ValidationError):
        comp.id = "comp-2"  # type: ignore
