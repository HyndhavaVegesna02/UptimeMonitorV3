"""The STORY-182 two-process env matrix (AC1a, AC1b, B4).

Two composition roots read their OWN `load_settings()`/env at process start
(`composition/run.py::main`, `composition/app.py::create_app` via
`composition/asgi.py`) -- so a human setting `CONFIG_DIR`/`DYNAMO_*` on only
one of the loop/API processes leaves the other resolving its dangerous
default (`config/apps`, real Statuspage component ids). `build_child_env` is
the ONE place this harness computes that env dict, handed identically to
BOTH subprocesses, so they cannot independently drift the way a human-set
pair of terminals could.
"""

from __future__ import annotations

import uuid


def fresh_table_names() -> tuple[str, str]:
    """Return a (observations_table, control_table) pair that has never
    been used before (STORY-182 AC2's fresh-table route) -- a random suffix
    per call, so a rerun of this harness can never collide with a prior
    run's tables (and therefore never inherit their permanent `EVT#…/DEDUPE`
    markers or persisted component status, B4)."""
    suffix = uuid.uuid4().hex[:12]
    return f"story182-observations-{suffix}", f"story182-control-{suffix}"


def build_child_env(
    *,
    base_env: dict,
    config_dir: str,
    dynamo_endpoint_url: str,
    observations_table: str,
    control_table: str,
    dynatrace_env_url: str | None = None,
    dynatrace_api_token: str | None = None,
    statuspage_page_id: str | None = None,
    statuspage_api_token: str | None = None,
    aws_region: str = "us-east-1",
) -> dict[str, str]:
    """Build the env dict for one child process (STORY-182 AC1a/AC1b).

    Starts from `base_env` (normally `os.environ`) and OVERRIDES
    `CONFIG_DIR`/`AWS_REGION`/`DYNAMO_*` unconditionally -- never leaves a
    stale value in place. The optional Dynatrace/Statuspage fields are
    included ONLY when given (never set to the literal string `"None"`):
    the API-process call site does not need them at all
    (`create_app()` never calls `load_live_secrets()`), while the loop
    process needs `DYNATRACE_*` to reach the demo engine and gets
    deliberately fake-but-present `STATUSPAGE_*` values so the guard is
    demonstrated as config-driven (real-looking credentials present) without
    ever touching the actual repo-root `.env` secrets.
    """
    env: dict[str, str] = dict(base_env)
    env["CONFIG_DIR"] = config_dir
    env["AWS_REGION"] = aws_region
    env["DYNAMO_ENDPOINT_URL"] = dynamo_endpoint_url
    env["DYNAMO_OBSERVATIONS_TABLE"] = observations_table
    env["DYNAMO_CONTROL_TABLE"] = control_table

    if dynatrace_env_url is not None:
        env["DYNATRACE_ENV_URL"] = dynatrace_env_url
    if dynatrace_api_token is not None:
        env["DYNATRACE_API_TOKEN"] = dynatrace_api_token
    if statuspage_page_id is not None:
        env["STATUSPAGE_PAGE_ID"] = statuspage_page_id
    if statuspage_api_token is not None:
        env["STATUSPAGE_API_KEY"] = statuspage_api_token

    return env
