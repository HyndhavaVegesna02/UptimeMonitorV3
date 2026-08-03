"""Tests for app runtime settings (composition zone)."""

from __future__ import annotations

import pytest
from src.composition.settings import (
    AWS_REGION_VAR,
    CONFIG_DIR_VAR,
    DYNAMO_CONTROL_TABLE_VAR,
    DYNAMO_ENDPOINT_URL_VAR,
    DYNAMO_OBSERVATIONS_TABLE_VAR,
    Settings,
    load_settings,
)


def test_env_var_name_constants_match_the_names_load_settings_historically_read(
    monkeypatch: pytest.MonkeyPatch,
):
    """STORY-202 AC1: the five names `load_settings()` used to read as
    function-body string literals are now module constants, pinned here to
    their known literal values -- the only assertion in this test that
    actually fires on a rename (quality-review mutation-verified). The
    round-trip below sets each env var under the SAME constant
    `load_settings()` reads and asserts the value comes back: by
    construction this cannot distinguish "reads through the constant" from
    "reads the literal" (setenv and load_settings reference the identical
    symbol, so the two strings can never differ) -- it demonstrates
    load_settings() still resolves correctly post-promotion, nothing more."""
    assert CONFIG_DIR_VAR == "CONFIG_DIR"
    assert AWS_REGION_VAR == "AWS_REGION"
    assert DYNAMO_OBSERVATIONS_TABLE_VAR == "DYNAMO_OBSERVATIONS_TABLE"
    assert DYNAMO_CONTROL_TABLE_VAR == "DYNAMO_CONTROL_TABLE"
    assert DYNAMO_ENDPOINT_URL_VAR == "DYNAMO_ENDPOINT_URL"

    monkeypatch.setenv(CONFIG_DIR_VAR, "config/via-constant")
    monkeypatch.setenv(AWS_REGION_VAR, "eu-west-1")
    monkeypatch.setenv(DYNAMO_OBSERVATIONS_TABLE_VAR, "via-constant-obs")
    monkeypatch.setenv(DYNAMO_CONTROL_TABLE_VAR, "via-constant-ctrl")
    monkeypatch.setenv(DYNAMO_ENDPOINT_URL_VAR, "http://via-constant:8000")

    settings = load_settings()
    assert settings.config_dir == "config/via-constant"
    assert settings.aws_region == "eu-west-1"
    assert settings.dynamo_observations_table == "via-constant-obs"
    assert settings.dynamo_control_table == "via-constant-ctrl"
    assert settings.dynamo_endpoint_url == "http://via-constant:8000"


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
