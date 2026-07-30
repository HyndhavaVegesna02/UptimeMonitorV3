"""Tests for the STORY-182 two-process env matrix (AC1a/AC1b, B4).

`build_child_env` is the ONE place the harness computes the env dict handed
to BOTH the API (uvicorn) subprocess and the loop (`python -m
src.composition.run`) subprocess -- so they can never independently drift on
`CONFIG_DIR`/`DYNAMO_*` the way the two real composition roots
(`composition/run.py::main`, `composition/app.py::create_app`) could if a
human set the vars by hand on only one of them.

`fresh_table_names` generates table names that have never been used before
(AC2's "a newly-created observations table" route) -- a random suffix per
call, not a fixed pair a rerun could collide with.
"""

from __future__ import annotations

from demo_loop_gate.env_matrix import build_child_env, fresh_table_names


def test_fresh_table_names_are_disjoint_across_calls():
    first_obs, first_ctrl = fresh_table_names()
    second_obs, second_ctrl = fresh_table_names()

    assert first_obs != second_obs
    assert first_ctrl != second_ctrl
    assert first_obs != first_ctrl


def test_fresh_table_names_are_never_the_default_or_live_names():
    obs, ctrl = fresh_table_names()

    assert obs not in ("uptime-observations", "uptime-monitor-observations")
    assert ctrl not in ("uptime-control", "uptime-monitor-control")


def test_build_child_env_sets_config_dir_and_dynamo_vars_and_never_unsets_them():
    base_env = {"PATH": "/usr/bin", "CONFIG_DIR": "config/apps"}  # a stale value

    env = build_child_env(
        base_env=base_env,
        config_dir="config/demo",
        dynamo_endpoint_url="http://127.0.0.1:8021",
        observations_table="story182-obs-abc",
        control_table="story182-ctrl-abc",
        dynatrace_env_url="http://127.0.0.1:9",
        dynatrace_api_token="fake-token",
        statuspage_page_id="story182-fake-page",
        statuspage_api_token="story182-fake-token",
    )

    # Every one of the AC1(a)/AC1(b) preconditions is present and CORRECT --
    # the base env's stale CONFIG_DIR=config/apps is overridden, never left.
    assert env["CONFIG_DIR"] == "config/demo"
    assert env["DYNAMO_ENDPOINT_URL"] == "http://127.0.0.1:8021"
    assert env["DYNAMO_OBSERVATIONS_TABLE"] == "story182-obs-abc"
    assert env["DYNAMO_CONTROL_TABLE"] == "story182-ctrl-abc"
    assert env["DYNATRACE_ENV_URL"] == "http://127.0.0.1:9"
    assert env["DYNATRACE_API_TOKEN"] == "fake-token"
    assert env["STATUSPAGE_PAGE_ID"] == "story182-fake-page"
    assert env["STATUSPAGE_API_KEY"] == "story182-fake-token"
    # base env passthrough
    assert env["PATH"] == "/usr/bin"


def test_build_child_env_omits_optional_dynatrace_and_statuspage_vars_when_none():
    """Passing None for a field leaves it OUT of the child env entirely
    (never sets it to the literal string "None"). This says nothing about
    the API-process call site's actual exposure: `base_env={}` here cannot
    distinguish "omitted" from "stripped" -- see the two tests below, which
    exercise that with a REAL-LOOKING value already present in base_env.

    (STORY-182 fix round, MAJOR 1: this docstring previously claimed "the
    API-process call site never needs DYNATRACE_*/STATUSPAGE_* set by the
    harness at all -- create_app() never calls load_live_secrets()". That
    was false at the call-site level: `composition/app.py:169-183` DOES call
    `load_statuspage_secrets()` and wires both Statuspage vars into
    `build_publisher` whenever a component_repo/publication_repo are wired,
    which the API's approve trigger does. The harness's API call site must
    therefore pass explicit fakes too, exactly like the loop call site --
    the empty `config/demo` mapping is the guard, not the absence of
    credentials on that process.)"""
    env = build_child_env(
        base_env={},
        config_dir="config/demo",
        dynamo_endpoint_url="http://127.0.0.1:8021",
        observations_table="story182-obs-abc",
        control_table="story182-ctrl-abc",
    )

    assert "DYNATRACE_ENV_URL" not in env
    assert "DYNATRACE_API_TOKEN" not in env
    assert "STATUSPAGE_PAGE_ID" not in env
    assert "STATUSPAGE_API_KEY" not in env


def test_build_child_env_inherits_a_real_looking_statuspage_key_when_not_overridden():
    """`base_env={}` (the test above) cannot distinguish "omitted" from
    "stripped". Here base_env carries a REAL-LOOKING `STATUSPAGE_API_KEY`
    (standing in for what a child process's own `load_dotenv()` would load
    from the repo-root `.env` if the caller passes no override) -- and it
    passes straight through untouched. This is exactly why `harness.py`'s
    API-process call site must pass an explicit fake `statuspage_api_token`,
    the same as the loop call site: omitting the argument does not mean
    "absent" in the child process, it means "whatever is already there"."""
    base_env = {"STATUSPAGE_API_KEY": "real-looking-secret-do-not-leak"}

    env = build_child_env(
        base_env=base_env,
        config_dir="config/demo",
        dynamo_endpoint_url="http://127.0.0.1:8021",
        observations_table="story182-obs-abc",
        control_table="story182-ctrl-abc",
    )

    assert env["STATUSPAGE_API_KEY"] == "real-looking-secret-do-not-leak"


def test_build_child_env_overrides_a_real_looking_statuspage_key_when_given():
    """The counterpart to the inheritance test above: passing an explicit
    (fake) `statuspage_api_token` DOES override whatever base_env already
    carries -- the defence `harness.py`'s API call site now relies on."""
    base_env = {"STATUSPAGE_API_KEY": "real-looking-secret-do-not-leak"}

    env = build_child_env(
        base_env=base_env,
        config_dir="config/demo",
        dynamo_endpoint_url="http://127.0.0.1:8021",
        observations_table="story182-obs-abc",
        control_table="story182-ctrl-abc",
        statuspage_api_token="story182-fake-token",
    )

    assert env["STATUSPAGE_API_KEY"] == "story182-fake-token"
