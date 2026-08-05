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

from src.composition.settings import (
    AWS_REGION_VAR,
    CONFIG_DIR_VAR,
    DYNAMO_CONTROL_TABLE_VAR,
    DYNAMO_ENDPOINT_URL_VAR,
    DYNAMO_OBSERVATIONS_TABLE_VAR,
    DYNATRACE_API_TOKEN_VAR,
    DYNATRACE_ENV_URL_VAR,
    STATUSPAGE_API_KEY_VAR,
    STATUSPAGE_PAGE_ID_VAR,
    Settings,
)


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
    aws_region: str = Settings.aws_region,
) -> dict[str, str]:
    """Build the env dict for one child process (STORY-182 AC1a/AC1b).

    Starts from `base_env` (normally `os.environ`) and OVERRIDES
    `CONFIG_DIR`/`AWS_REGION`/`DYNAMO_*` unconditionally -- never leaves a
    stale value in place. The optional Dynatrace/Statuspage fields are
    included ONLY when given (never set to the literal string `"None"`).

    Both call sites in `harness.py` now pass deliberately fake-but-present
    `STATUSPAGE_*` values: the loop process needs `DYNATRACE_*` to reach the
    demo engine, and -- corrected in the STORY-182 fix round, MAJOR 1 -- the
    API process is ALSO credential-bearing. `composition/app.py:169-183`
    calls `load_statuspage_secrets()` and wires both Statuspage vars into
    `build_publisher()` whenever the API's approve trigger has a
    component_repo/publication_repo, which it does. Omitting the fakes at
    that call site does not mean "no credentials" -- the subprocess's own
    `load_dotenv()` (`composition/asgi.py`) would supply the REAL
    repo-root `.env` values instead (`load_dotenv()`'s default
    `override=False` only fills vars not already set). The empty
    `config/demo` `statuspage_mapping()` is the actual guard (verified by
    `tools/demo_loop_gate/guard_reality_gate.py`); passing fakes here is
    defence in depth on top of it, not the guard itself.
    """
    env: dict[str, str] = dict(base_env)
    env[CONFIG_DIR_VAR] = config_dir
    env[AWS_REGION_VAR] = aws_region
    env[DYNAMO_ENDPOINT_URL_VAR] = dynamo_endpoint_url
    env[DYNAMO_OBSERVATIONS_TABLE_VAR] = observations_table
    env[DYNAMO_CONTROL_TABLE_VAR] = control_table

    if dynatrace_env_url is not None:
        env[DYNATRACE_ENV_URL_VAR] = dynatrace_env_url
    if dynatrace_api_token is not None:
        env[DYNATRACE_API_TOKEN_VAR] = dynatrace_api_token
    if statuspage_page_id is not None:
        env[STATUSPAGE_PAGE_ID_VAR] = statuspage_page_id
    if statuspage_api_token is not None:
        env[STATUSPAGE_API_KEY_VAR] = statuspage_api_token

    return env
