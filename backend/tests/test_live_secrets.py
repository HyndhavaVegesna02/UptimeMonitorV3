"""Tests for live secrets resolution (STORY-016b, dossier §17).

STORY-045 adds `load_statuspage_secrets` — the Statuspage-only half of
`LiveSecrets`, usable by `composition/app.py::create_app` (the approve trigger's
composition root) WITHOUT requiring the DYNATRACE_* vars `load_live_secrets`
demands (create_app must not call load_live_secrets just to get two optional
fields — plan.md "Key facts").
"""

from __future__ import annotations

import pytest
from src.composition.settings import (
    DYNATRACE_API_TOKEN_VAR,
    DYNATRACE_ENV_URL_VAR,
    LiveSecrets,
    MissingLiveSecretError,
    StatuspageSecrets,
    load_live_secrets,
    load_statuspage_secrets,
)


def test_dynatrace_env_var_name_constants_match_the_names_load_live_secrets_historically_read(
    monkeypatch: pytest.MonkeyPatch,
):
    """STORY-215 AC1: the two `DYNATRACE_*` names `load_live_secrets()` used to
    read as function-body string literals are now module constants (same
    `<NAME>_VAR` convention `CONFIG_DIR_VAR` etc. already use), pinned here to
    their known literal values. As with `test_settings.py`'s equivalent pin,
    the round-trip below cannot by itself distinguish "reads through the
    constant" from "reads the literal" (setenv and load_live_secrets
    reference the identical symbol) -- it demonstrates load_live_secrets()
    still resolves correctly post-promotion."""
    assert DYNATRACE_ENV_URL_VAR == "DYNATRACE_ENV_URL"
    assert DYNATRACE_API_TOKEN_VAR == "DYNATRACE_API_TOKEN"

    monkeypatch.setenv(DYNATRACE_ENV_URL_VAR, "https://dt.example.com")
    monkeypatch.setenv(DYNATRACE_API_TOKEN_VAR, "dt.token.123")
    monkeypatch.delenv("STATUSPAGE_PAGE_ID", raising=False)
    monkeypatch.delenv("STATUSPAGE_API_KEY", raising=False)

    secrets = load_live_secrets()
    assert secrets.dynatrace_env_url == "https://dt.example.com"
    assert secrets.dynatrace_api_token == "dt.token.123"


def test_load_live_secrets_success_all_set(monkeypatch: pytest.MonkeyPatch):
    """Verify that load_live_secrets works when all 4 secrets are set."""
    monkeypatch.setenv("DYNATRACE_ENV_URL", "https://dt.example.com")
    monkeypatch.setenv("DYNATRACE_API_TOKEN", "dt.token.123")
    monkeypatch.setenv("STATUSPAGE_PAGE_ID", "page123")
    monkeypatch.setenv("STATUSPAGE_API_KEY", "spkey123")

    secrets = load_live_secrets()
    assert isinstance(secrets, LiveSecrets)
    assert secrets.dynatrace_env_url == "https://dt.example.com"
    assert secrets.dynatrace_api_token == "dt.token.123"
    assert secrets.statuspage_page_id == "page123"
    assert secrets.statuspage_api_token == "spkey123"


def test_load_live_secrets_success_only_dynatrace_set(
    monkeypatch: pytest.MonkeyPatch,
):
    """Verify that load_live_secrets succeeds when only the required Dynatrace secrets are set."""
    monkeypatch.setenv("DYNATRACE_ENV_URL", "https://dt.example.com")
    monkeypatch.setenv("DYNATRACE_API_TOKEN", "dt.token.123")
    monkeypatch.delenv("STATUSPAGE_PAGE_ID", raising=False)
    monkeypatch.delenv("STATUSPAGE_API_KEY", raising=False)

    secrets = load_live_secrets()
    assert isinstance(secrets, LiveSecrets)
    assert secrets.dynatrace_env_url == "https://dt.example.com"
    assert secrets.dynatrace_api_token == "dt.token.123"
    assert secrets.statuspage_page_id is None
    assert secrets.statuspage_api_token is None


def test_load_live_secrets_missing_required(monkeypatch: pytest.MonkeyPatch):
    """Verify that load_live_secrets raises MissingLiveSecretError only when required secrets are missing."""
    monkeypatch.delenv("DYNATRACE_ENV_URL", raising=False)
    monkeypatch.delenv("DYNATRACE_API_TOKEN", raising=False)
    monkeypatch.setenv("STATUSPAGE_PAGE_ID", "page123")
    monkeypatch.setenv("STATUSPAGE_API_KEY", "spkey123")

    with pytest.raises(MissingLiveSecretError) as exc_info:
        load_live_secrets()

    message = str(exc_info.value)
    assert "DYNATRACE_ENV_URL" in message
    assert "DYNATRACE_API_TOKEN" in message
    assert "STATUSPAGE_PAGE_ID" not in message
    assert "STATUSPAGE_API_KEY" not in message


# --- load_statuspage_secrets (STORY-045) -----------------------------------


def test_load_statuspage_secrets_present(monkeypatch: pytest.MonkeyPatch):
    """Both Statuspage vars set -> both fields populated, no DYNATRACE_* needed."""
    monkeypatch.delenv("DYNATRACE_ENV_URL", raising=False)
    monkeypatch.delenv("DYNATRACE_API_TOKEN", raising=False)
    monkeypatch.setenv("STATUSPAGE_PAGE_ID", "page123")
    monkeypatch.setenv("STATUSPAGE_API_KEY", "spkey123")

    secrets = load_statuspage_secrets()

    assert isinstance(secrets, StatuspageSecrets)
    assert secrets.page_id == "page123"
    assert secrets.api_token == "spkey123"


def test_load_statuspage_secrets_absent_tolerated(monkeypatch: pytest.MonkeyPatch):
    """Neither var set -> both fields None, no error raised (tolerates absence)."""
    monkeypatch.delenv("STATUSPAGE_PAGE_ID", raising=False)
    monkeypatch.delenv("STATUSPAGE_API_KEY", raising=False)

    secrets = load_statuspage_secrets()

    assert secrets.page_id is None
    assert secrets.api_token is None


def test_load_statuspage_secrets_uses_same_env_var_names_as_live_secrets(
    monkeypatch: pytest.MonkeyPatch,
):
    """Same env var NAMES as LiveSecrets — one convention, not a second one."""
    monkeypatch.setenv("DYNATRACE_ENV_URL", "https://dt.example.com")
    monkeypatch.setenv("DYNATRACE_API_TOKEN", "dt.token.123")
    monkeypatch.setenv("STATUSPAGE_PAGE_ID", "page123")
    monkeypatch.setenv("STATUSPAGE_API_KEY", "spkey123")

    live = load_live_secrets()
    standalone = load_statuspage_secrets()

    assert standalone.page_id == live.statuspage_page_id
    assert standalone.api_token == live.statuspage_api_token
