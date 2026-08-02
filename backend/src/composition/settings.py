"""App runtime settings (composition zone).

The application runtime talks to DynamoDB (dossier §3, §17).

Reading env vars and owning configuration belongs in the composition zone, never
in ``core/`` (the import-linter boundary forbids core importing infrastructure).
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Immutable app settings resolved from the environment."""

    config_dir: str
    aws_region: str = "us-east-1"
    dynamo_observations_table: str = "uptime-observations"
    dynamo_control_table: str = "uptime-control"
    dynamo_endpoint_url: str | None = None


# The env var names `load_settings()` reads (STORY-202: promoted from
# function-body string literals to module constants, following the same
# `<NAME>_VAR` convention as `STATUSPAGE_PAGE_ID_VAR`/`STATUSPAGE_API_KEY_VAR`
# below) -- so `tools/demo_loop_gate`'s env matrix and harness can IMPORT the
# key names instead of re-declaring them, closing the rename-drift gap ZR-3
# flags between `backend/src/` and `tools/`.
CONFIG_DIR_VAR = "CONFIG_DIR"
AWS_REGION_VAR = "AWS_REGION"
DYNAMO_OBSERVATIONS_TABLE_VAR = "DYNAMO_OBSERVATIONS_TABLE"
DYNAMO_CONTROL_TABLE_VAR = "DYNAMO_CONTROL_TABLE"
DYNAMO_ENDPOINT_URL_VAR = "DYNAMO_ENDPOINT_URL"


def load_settings() -> Settings:
    """Load runtime settings from the environment.

    Reads config_dir from ``CONFIG_DIR`` env var, defaulting to ``"config/apps"``.
    """
    return Settings(
        config_dir=os.environ.get(CONFIG_DIR_VAR, "config/apps"),
        aws_region=os.environ.get(AWS_REGION_VAR, "us-east-1"),
        dynamo_observations_table=os.environ.get(
            DYNAMO_OBSERVATIONS_TABLE_VAR, "uptime-observations"
        ),
        dynamo_control_table=os.environ.get(DYNAMO_CONTROL_TABLE_VAR, "uptime-control"),
        dynamo_endpoint_url=os.environ.get(DYNAMO_ENDPOINT_URL_VAR) or None,
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
