"""STORY-003 AC2: the migration path and the app runtime read DISTINCT env vars.

- App runtime settings (composition zone) read the POOLED ``DATABASE_URL``.
- The Alembic migration path reads the DIRECT ``DATABASE_URL_DIRECT``.

These tests assert the wiring honestly (by exercising the real code that reads
the env), not by restating a literal — and assert the two vars are not the same.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from src.composition.settings import (
    APP_DATABASE_URL_VAR,
    Settings,
    load_settings,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_app_settings_reads_pooled_database_url(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@pooled-host/db")
    settings = load_settings()
    assert isinstance(settings, Settings)
    assert settings.database_url == "postgresql+psycopg://u:p@pooled-host/db"
    assert APP_DATABASE_URL_VAR == "DATABASE_URL"


def test_app_settings_requires_database_url(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(KeyError):
        load_settings()


def _load_env_head() -> dict:
    """Exec migrations/env.py up to the alembic-context section, returning its namespace.

    We only want the top-of-file constants/helpers (the URL-source var and the
    normalize helper). Executing past the marker would touch ``alembic.context``
    and try to run migrations, so we stop there. The source is the honest source
    of truth — no restated literals.
    """
    env_path = _REPO_ROOT / "migrations" / "env.py"
    source = env_path.read_text(encoding="utf-8")
    marker = "# this is the Alembic Config object"
    head = source.split(marker, 1)[0]
    ns: dict = {}
    exec(compile(head, str(env_path), "exec"), ns)
    return ns


def test_migration_url_var_is_direct_and_distinct():
    """The Alembic env reads DATABASE_URL_DIRECT, distinct from the app var."""
    ns = _load_env_head()
    assert ns["MIGRATION_DATABASE_URL_VAR"] == "DATABASE_URL_DIRECT"
    # The migration var and the app var must be DISTINCT (the whole point).
    assert ns["MIGRATION_DATABASE_URL_VAR"] != APP_DATABASE_URL_VAR


def test_migration_url_normalizes_to_psycopg3():
    """A bare postgresql:// URL is normalized to the psycopg3 dialect."""
    normalize = _load_env_head()["_normalize_url"]

    assert normalize("postgresql://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert normalize("postgres://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    # already-qualified driver is left untouched
    assert normalize("postgresql+psycopg://u:p@h/db") == "postgresql+psycopg://u:p@h/db"


def test_app_settings_dynamodb_defaults(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@h/db")
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
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@h/db")
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    monkeypatch.setenv("DYNAMO_OBSERVATIONS_TABLE", "custom-obs")
    monkeypatch.setenv("DYNAMO_CONTROL_TABLE", "custom-ctrl")
    monkeypatch.setenv("DYNAMO_ENDPOINT_URL", "http://localhost:8000")

    settings = load_settings()
    assert settings.aws_region == "us-west-2"
    assert settings.dynamo_observations_table == "custom-obs"
    assert settings.dynamo_control_table == "custom-ctrl"
    assert settings.dynamo_endpoint_url == "http://localhost:8000"
