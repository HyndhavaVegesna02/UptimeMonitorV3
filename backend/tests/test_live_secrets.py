"""Tests for live secrets resolution (STORY-016 T3, dossier §17)."""

from __future__ import annotations

import pytest
from src.composition.settings import (
    LiveSecrets,
    MissingLiveSecretError,
    load_live_secrets,
)


def test_load_live_secrets_success(monkeypatch: pytest.MonkeyPatch):
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


def test_load_live_secrets_missing_all(monkeypatch: pytest.MonkeyPatch):
    """Verify that load_live_secrets raises MissingLiveSecretError naming all missing variables."""
    monkeypatch.delenv("DYNATRACE_ENV_URL", raising=False)
    monkeypatch.delenv("DYNATRACE_API_TOKEN", raising=False)
    monkeypatch.delenv("STATUSPAGE_PAGE_ID", raising=False)
    monkeypatch.delenv("STATUSPAGE_API_KEY", raising=False)

    with pytest.raises(MissingLiveSecretError) as exc_info:
        load_live_secrets()

    message = str(exc_info.value)
    assert "DYNATRACE_ENV_URL" in message
    assert "DYNATRACE_API_TOKEN" in message
    assert "STATUSPAGE_PAGE_ID" in message
    assert "STATUSPAGE_API_KEY" in message


def test_load_live_secrets_missing_some(monkeypatch: pytest.MonkeyPatch):
    """Verify that load_live_secrets raises MissingLiveSecretError naming only the missing variables."""
    monkeypatch.setenv("DYNATRACE_ENV_URL", "https://dt.example.com")
    monkeypatch.delenv("DYNATRACE_API_TOKEN", raising=False)
    monkeypatch.setenv("STATUSPAGE_PAGE_ID", "page123")
    monkeypatch.delenv("STATUSPAGE_API_KEY", raising=False)

    with pytest.raises(MissingLiveSecretError) as exc_info:
        load_live_secrets()

    message = str(exc_info.value)
    assert "DYNATRACE_ENV_URL" not in message
    assert "DYNATRACE_API_TOKEN" in message
    assert "STATUSPAGE_PAGE_ID" not in message
    assert "STATUSPAGE_API_KEY" in message
