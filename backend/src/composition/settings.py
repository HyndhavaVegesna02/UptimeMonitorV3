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
    aws_region: str
    dynamo_observations_table: str
    dynamo_control_table: str
    dynamo_endpoint_url: str | None


def load_settings() -> Settings:
    """Load runtime settings from the environment.

    Reads the POOLED connection string from ``DATABASE_URL``. Raises
    ``KeyError`` if it is unset — the app must not start without a database URL.
    Also reads config_dir from ``CONFIG_DIR`` env var, defaulting to ``"config/apps"``.
    """
    return Settings(
        database_url=os.environ[APP_DATABASE_URL_VAR],
        config_dir=os.environ.get("CONFIG_DIR", "config/apps"),
        aws_region=os.environ.get("AWS_REGION", "us-east-1"),
        dynamo_observations_table=os.environ.get("DYNAMO_OBSERVATIONS_TABLE", "uptime-observations"),
        dynamo_control_table=os.environ.get("DYNAMO_CONTROL_TABLE", "uptime-control"),
        dynamo_endpoint_url=os.environ.get("DYNAMO_ENDPOINT_URL") or None,
    )


class MissingLiveSecretError(ValueError):
    """Raised when one or more required live loop secrets are missing from the environment (dossier §17)."""


# The env var names for the (optional) Statuspage credentials — the ONE naming
# convention `LiveSecrets` and `StatuspageSecrets` both read (STORY-045: the
# approve-trigger composition root must not invent a second convention).
STATUSPAGE_PAGE_ID_VAR = "STATUSPAGE_PAGE_ID"
STATUSPAGE_API_KEY_VAR = "STATUSPAGE_API_KEY"


@dataclass(frozen=True)
class LiveSecrets:
    """Immutable live secrets resolved from the environment (dossier §17)."""

    dynatrace_env_url: str
    dynatrace_api_token: str
    statuspage_page_id: str | None
    statuspage_api_token: str | None


@dataclass(frozen=True)
class StatuspageSecrets:
    """The Statuspage-only half of `LiveSecrets` (dossier §17, STORY-045).

    `composition/app.py::create_app` (the approve trigger's composition root)
    needs ONLY these two optional fields to build its publisher chain via
    `build_publisher` — it must NOT call `load_live_secrets`, which raises
    `MissingLiveSecretError` when the (irrelevant, here) DYNATRACE_* vars are
    absent. Both fields are `None` when unset; `build_publisher` falls back to
    a `LoggingPublisher` delegate in that case.
    """

    page_id: str | None
    api_token: str | None


def load_statuspage_secrets() -> StatuspageSecrets:
    """Load the optional Statuspage secrets from the environment (dossier §17, STORY-045).

    Reads the SAME env var names `load_live_secrets` uses for these two
    fields (`STATUSPAGE_PAGE_ID_VAR`/`STATUSPAGE_API_KEY_VAR`) — never a second
    naming convention. Tolerates total absence: both fields are `None`, no
    error raised (unlike `load_live_secrets`, nothing here is required).
    """
    return StatuspageSecrets(
        page_id=os.environ.get(STATUSPAGE_PAGE_ID_VAR),
        api_token=os.environ.get(STATUSPAGE_API_KEY_VAR),
    )


def load_live_secrets() -> LiveSecrets:
    """Load live secrets from the environment (dossier §17, STORY-016b).

    Requires DYNATRACE_ENV_URL and DYNATRACE_API_TOKEN. Statuspage secrets are optional.
    Raises MissingLiveSecretError if required Dynatrace secrets are missing.
    """
    missing = []
    env_url = os.environ.get("DYNATRACE_ENV_URL")
    if not env_url:
        missing.append("DYNATRACE_ENV_URL")
    dt_token = os.environ.get("DYNATRACE_API_TOKEN")
    if not dt_token:
        missing.append("DYNATRACE_API_TOKEN")

    if missing:
        raise MissingLiveSecretError(
            f"Missing required live secrets: {', '.join(missing)}"
        )

    statuspage_secrets = load_statuspage_secrets()

    return LiveSecrets(
        dynatrace_env_url=env_url,
        dynatrace_api_token=dt_token,
        statuspage_page_id=statuspage_secrets.page_id,
        statuspage_api_token=statuspage_secrets.api_token,
    )
