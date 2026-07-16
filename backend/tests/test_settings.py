"""Tests for app runtime settings (composition zone)."""

from __future__ import annotations

import pytest
from src.composition.settings import Settings, load_settings


def test_app_settings_succeeds_without_database_url(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = load_settings()
    assert isinstance(settings, Settings)
    assert settings.aws_region == "us-east-1"


def test_app_settings_dynamodb_defaults(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("DYNAMO_OBSERVATIONS_TABLE", raising=False)
    monkeypatch.delenv("DYNAMO_CONTROL_TABLE", raising=False)
    monkeypatch.delenv("DYNAMO_ENDPOINT_URL", raising=False)

    settings = load_settings()
    assert settings.aws_region == "us-east-1"
    assert settings.dynamo_observations_table == "uptime-observations"
    assert settings.dynamo_control_table == "uptime-control"
    assert settings.dynamo_endpoint_url is None


def test_app_settings_dynamodb_overrides(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    monkeypatch.setenv("DYNAMO_OBSERVATIONS_TABLE", "custom-obs")
    monkeypatch.setenv("DYNAMO_CONTROL_TABLE", "custom-ctrl")
    monkeypatch.setenv("DYNAMO_ENDPOINT_URL", "http://localhost:8000")

    settings = load_settings()
    assert settings.aws_region == "us-west-2"
    assert settings.dynamo_observations_table == "custom-obs"
    assert settings.dynamo_control_table == "custom-ctrl"
    assert settings.dynamo_endpoint_url == "http://localhost:8000"
