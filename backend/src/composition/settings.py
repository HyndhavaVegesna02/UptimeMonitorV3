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
    """Immutable app settings resolved from the environment.

    Each field's dataclass default below is its ONE canonical declaration
    (STORY-218 AC1) -- `load_settings()`, the only construction site, reads
    it back via `Settings.<field>` instead of re-typing the literal, so
    renaming a default here is a rename everywhere, including
    `tools/demo_loop_gate/harness.py`'s table-name blocklist, which reads
    `Settings.dynamo_observations_table`/`dynamo_control_table` as class
    attributes -- the reason this shape is canonical and not the reverse
    (see `load_settings()`'s docstring for the two forbidden alternatives).
    `config_dir` alone has no default here: `CONFIG_DIR` is the entire
    demo/live publish guard (CLAUDE.md), and its own fallback literal,
    `"config/apps"`, must be visible at the one call site that resolves it
    rather than promoted to a class attribute nothing else reads.

    Falsiness (STORY-218 AC2), decided per field for an explicitly-set
    EMPTY env var -- `os.environ.get(VAR, default)` only substitutes
    `default` when the var is ABSENT, never when it is merely falsy, so
    this is the current behaviour for four of the five fields, kept
    deliberately rather than "fixed" to fall back on empty:
    - `config_dir`: preserved verbatim. This is the risky one -- if an
      explicitly-set empty `CONFIG_DIR=""` instead silently fell back to
      `"config/apps"`, an operator who emptied the guard var (e.g. clearing
      it in a script) would be silently redirected to `config/apps`'s REAL
      `statuspage_component_id` rather than failing loudly downstream on an
      empty path. Loud-and-empty is safer than silent-and-real.
    - `aws_region`, `dynamo_observations_table`, `dynamo_control_table`:
      preserved verbatim for the analogous reason -- an empty region or
      table name fails loudly against AWS/DynamoDB rather than silently
      substituting the production default.
    - `dynamo_endpoint_url` is the one deliberate exception, unchanged by
      this story: `load_settings()` folds BOTH "unset" and
      explicitly-set-empty to `None` (`or None`), because `None` means "no
      local override, talk to real AWS" for either case -- there is no
      "loud empty path" hazard here the way there is for a table name or
      `CONFIG_DIR`.
    """

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

    Reads config_dir from the ``CONFIG_DIR_VAR`` env var (currently
    ``"CONFIG_DIR"``), defaulting to ``"config/apps"``.

    STORY-218 AC1: every fallback below reads the field's OWN dataclass
    default off ``Settings`` rather than re-typing its literal a second
    time, so the value production resolves and the value
    ``Settings.<field>`` exposes as a class attribute can never drift
    apart -- the exact drift this story fixes (before it, renaming one side
    left the full suite green while `harness.py`'s blocklist guarded a dead
    name). Two shapes were considered and rejected for this reason (AC1):
    a module-level ``_DEFAULTS`` mapping, and converging ``config_dir``'s
    own no-class-default shape onto the other four fields -- both remove
    the class attribute `tools/demo_loop_gate/harness.py:763,770` depends
    on, which needs it to still exist AS A CLASS ATTRIBUTE.
    ``config_dir`` alone keeps its own literal fallback here: it has no
    class default to read (see the ``Settings`` docstring), by design.
    """
    return Settings(
        config_dir=os.environ.get(CONFIG_DIR_VAR, "config/apps"),
        aws_region=os.environ.get(AWS_REGION_VAR, Settings.aws_region),
        dynamo_observations_table=os.environ.get(
            DYNAMO_OBSERVATIONS_TABLE_VAR, Settings.dynamo_observations_table
        ),
        dynamo_control_table=os.environ.get(
            DYNAMO_CONTROL_TABLE_VAR, Settings.dynamo_control_table
        ),
        dynamo_endpoint_url=os.environ.get(DYNAMO_ENDPOINT_URL_VAR) or None,
    )


class MissingLiveSecretError(ValueError):
    """Raised when one or more required live loop secrets are missing from the environment (dossier §17)."""


# The env var names for the (optional) Statuspage credentials — the ONE naming
# convention `LiveSecrets` and `StatuspageSecrets` both read (STORY-045: the
# approve-trigger composition root must not invent a second convention).
STATUSPAGE_PAGE_ID_VAR = "STATUSPAGE_PAGE_ID"
STATUSPAGE_API_KEY_VAR = "STATUSPAGE_API_KEY"

# The required Dynatrace secret names `load_live_secrets()` reads (STORY-215
# AC1: promoted from function-body string literals to module constants, the
# same `<NAME>_VAR` convention as `CONFIG_DIR_VAR` etc. above -- left as
# literals by STORY-202 on purpose, because promoting them creates fresh
# ZR-3 collisions of its own; STORY-215 AC2/AC6 adjudicate those).
DYNATRACE_ENV_URL_VAR = "DYNATRACE_ENV_URL"
DYNATRACE_API_TOKEN_VAR = "DYNATRACE_API_TOKEN"


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
    env_url = os.environ.get(DYNATRACE_ENV_URL_VAR)
    if not env_url:
        missing.append(DYNATRACE_ENV_URL_VAR)
    dt_token = os.environ.get(DYNATRACE_API_TOKEN_VAR)
    if not dt_token:
        missing.append(DYNATRACE_API_TOKEN_VAR)

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
