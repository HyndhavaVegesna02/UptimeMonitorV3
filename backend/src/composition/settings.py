"""App runtime settings (composition zone).

The application runtime talks to Neon through the POOLED PgBouncer connection,
read from the ``DATABASE_URL`` env var (dossier §3, §17). This is deliberately
distinct from the migration path, which uses the DIRECT connection
(``DATABASE_URL_DIRECT``) — DDL misbehaves through transaction pooling, so
migrations run as a separate release step on the direct connection
(see ``migrations/env.py``).

Reading env vars and owning configuration belongs in the composition zone, never
in ``core/`` (the import-linter boundary forbids core importing infrastructure).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# The env var the application runtime reads for its (pooled) database URL.
APP_DATABASE_URL_VAR = "DATABASE_URL"


def to_psycopg_url(database_url: str) -> str:
    """Normalize a plain libpq ``postgresql://`` URL to the psycopg3 dialect
    ``postgresql+psycopg://`` that SQLAlchemy 2 requires.

    A URL that already carries an explicit ``+driver`` (or any non-plain scheme)
    is returned unchanged. This is the ONE home for the dialect fix — the app
    factory, the seed CLI, and the test DB fixture all route through it rather
    than re-implementing the prefix swap (dossier §3 URL-dialect note).
    """
    prefix = "postgresql://"
    if database_url.startswith(prefix):
        return "postgresql+psycopg://" + database_url[len(prefix) :]
    return database_url


@dataclass(frozen=True)
class Settings:
    """Immutable app settings resolved from the environment."""

    database_url: str
    config_dir: str


def load_settings() -> Settings:
    """Load runtime settings from the environment.

    Reads the POOLED connection string from ``DATABASE_URL``. Raises
    ``KeyError`` if it is unset — the app must not start without a database URL.
    Also reads config_dir from ``CONFIG_DIR`` env var, defaulting to ``"config/apps"``.
    """
    return Settings(
        database_url=os.environ[APP_DATABASE_URL_VAR],
        config_dir=os.environ.get("CONFIG_DIR", "config/apps"),
    )


class MissingLiveSecretError(ValueError):
    """Raised when one or more required live loop secrets are missing from the environment (dossier §17)."""


@dataclass(frozen=True)
class LiveSecrets:
    """Immutable live secrets resolved from the environment (dossier §17)."""

    dynatrace_env_url: str
    dynatrace_api_token: str
    statuspage_page_id: str
    statuspage_api_token: str


def load_live_secrets() -> LiveSecrets:
    """Load live secrets from the environment (dossier §17).

    Reads DYNATRACE_ENV_URL, DYNATRACE_API_TOKEN, STATUSPAGE_PAGE_ID, STATUSPAGE_API_KEY.
    Raises MissingLiveSecretError if any are missing.
    """
    missing = []
    env_url = os.environ.get("DYNATRACE_ENV_URL")
    if not env_url:
        missing.append("DYNATRACE_ENV_URL")
    dt_token = os.environ.get("DYNATRACE_API_TOKEN")
    if not dt_token:
        missing.append("DYNATRACE_API_TOKEN")
    page_id = os.environ.get("STATUSPAGE_PAGE_ID")
    if not page_id:
        missing.append("STATUSPAGE_PAGE_ID")
    sp_token = os.environ.get("STATUSPAGE_API_KEY")
    if not sp_token:
        missing.append("STATUSPAGE_API_KEY")

    if missing:
        raise MissingLiveSecretError(
            f"Missing required live secrets: {', '.join(missing)}"
        )

    return LiveSecrets(
        dynatrace_env_url=env_url,
        dynatrace_api_token=dt_token,
        statuspage_page_id=page_id,
        statuspage_api_token=sp_token,
    )
