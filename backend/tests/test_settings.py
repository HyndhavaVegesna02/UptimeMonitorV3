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


# STORY-218 AC2/AC3: the falsiness decision, made PER FIELD in
# `load_settings()`'s own docstring, pinned here one case per field. An
# explicitly-set EMPTY env var is NOT the same as an unset one --
# `os.environ.get(VAR, default)` only substitutes `default` when the key is
# ABSENT, never when it is falsy. Four of the five fields (`config_dir`,
# `aws_region`, `dynamo_observations_table`, `dynamo_control_table`)
# preserve the empty string verbatim rather than silently falling back to
# their default -- deliberately, because for `config_dir` in particular
# (CLAUDE.md's publish-guard section) silently promoting an emptied
# `CONFIG_DIR` to `config/apps`'s REAL `statuspage_component_id` would be
# far more dangerous than a loud downstream failure on an empty path. The
# fifth, `dynamo_endpoint_url`, is the deliberate exception (`:52`'s `or
# None`, unchanged by this story): empty is folded to `None`, the same as
# unset, because `None` means "no local override, talk to real AWS" for
# BOTH cases.


def test_load_settings_empty_config_dir_is_preserved_verbatim(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("CONFIG_DIR", "")
    settings = load_settings()
    assert settings.config_dir == ""


def test_load_settings_empty_aws_region_is_preserved_verbatim(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("AWS_REGION", "")
    settings = load_settings()
    assert settings.aws_region == ""


def test_load_settings_empty_observations_table_is_preserved_verbatim(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("DYNAMO_OBSERVATIONS_TABLE", "")
    settings = load_settings()
    assert settings.dynamo_observations_table == ""


def test_load_settings_empty_control_table_is_preserved_verbatim(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("DYNAMO_CONTROL_TABLE", "")
    settings = load_settings()
    assert settings.dynamo_control_table == ""


def test_load_settings_empty_dynamo_endpoint_url_resolves_to_none(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("DYNAMO_ENDPOINT_URL", "")
    settings = load_settings()
    assert settings.dynamo_endpoint_url is None


def test_load_settings_resolves_defaults_from_the_class_attributes_themselves(
    monkeypatch: pytest.MonkeyPatch,
):
    """STORY-218 AC1's invariant, pinned directly -- added 2026-08-13 after
    quality review (m3) found nothing asserted it.

    The story removed a DUPLICATION: each default literal used to be typed
    twice, once as a dataclass field default and once as an
    ``os.environ.get(VAR, "<literal>")`` fallback here. Every other test in
    this file would stay GREEN if someone re-typed the literal back into
    ``load_settings()`` with the same value -- the duplication would return
    silently and only the NEXT rename would surface it, which is exactly the
    drift this story exists to close.

    This test fails on that re-introduction the moment the two copies differ,
    because it asserts the resolved value IS the class attribute rather than
    asserting it equals a literal spelled out a second time here (which would
    make this test the third copy, and vacuous).
    """
    for var in (
        AWS_REGION_VAR,
        DYNAMO_OBSERVATIONS_TABLE_VAR,
        DYNAMO_CONTROL_TABLE_VAR,
    ):
        monkeypatch.delenv(var, raising=False)

    settings = load_settings()

    assert settings.aws_region == Settings.aws_region
    assert settings.dynamo_observations_table == Settings.dynamo_observations_table
    assert settings.dynamo_control_table == Settings.dynamo_control_table
