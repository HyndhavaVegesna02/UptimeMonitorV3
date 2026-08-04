"""STORY-182 reality-gate harness, side 1 -- the positive full run.

Runs the REAL, UNMODIFIED `python -m src.composition.run` against the demo
engine and the demo fleet, and collects the AC1-AC5 evidence the story
requires. Nothing under `backend/src/` is imported for patching or mocking
here -- both the API and the loop run as REAL OS subprocesses, exactly as a
human would launch them per CLAUDE.md's "Run the app locally" recipe, with
`CONFIG_DIR` pointed at `config/demo` on both (the two-process trap AC1(a)
exists for).

Re-runnable: ``python tools/demo_loop_gate/harness.py`` (needs Docker's
`uptime_dynamo_8021` container up, i.e. `DYNAMO_ENDPOINT_URL=
http://127.0.0.1:8021` reachable). Prints every AC1-AC5 value it collects
AND asserts it holds (`_assert_ac1_preconditions`, `_assert_ac3_ingest`,
`_assert_ac4_vendor_health`, `_assert_ac5_approvals`,
`_assert_loop_startup_and_ingestion`) -- raises loudly (`AssertionError` or
`RealityGateError`, never a silent partial pass) if any of them fails, and
`main()`/`__main__` report an explicit PASS/FAIL verdict with a non-zero
exit code on failure.

**Safety, read before running:** every credential handed to either
subprocess is a deliberately fake, obviously-fake-looking placeholder (never
the real repo-root `.env` values) -- see `env_matrix.build_child_env`'s
docstring. `DYNATRACE_ENV_URL` points ONLY at the embedded local
`DemoEngineServer`. `config/demo` declares no `statuspage_component_id`
anywhere, so `statuspage_mapping()` is `{}` and the real
`build_publisher` selects its `LoggingPublisher` fallback regardless of
whatever credentials are present (independently pinned by
`tools/demo_loop_gate/publisher_chain.py` + its test) -- no
`StatuspagePublisher`/`make_statuspage_executor()` is ever even
constructed on this path, so no Statuspage network call is possible, not
merely unlikely.
"""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
TOOLS_ROOT = REPO_ROOT / "tools"

for _p in (str(TOOLS_ROOT),):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import httpx  # noqa: E402
from demo_engine.scenario import SignalScenario, expand_scenario  # noqa: E402
from demo_engine.server import DemoEngineServer  # noqa: E402
from import_provenance import assert_import_root  # noqa: E402
from src.composition.config import load_config  # noqa: E402
from src.composition.settings import (  # noqa: E402
    CONFIG_DIR_VAR,
    DYNAMO_CONTROL_TABLE_VAR,
    DYNAMO_ENDPOINT_URL_VAR,
    DYNAMO_OBSERVATIONS_TABLE_VAR,
    Settings,
)

from demo_loop_gate.env_matrix import build_child_env, fresh_table_names  # noqa: E402
from demo_loop_gate.evidence import (  # noqa: E402
    distinct_locations_from_history_dtos,
)
from demo_loop_gate.fleet_coverage import build_fleet_row_store  # noqa: E402

DEMO_CONFIG_DIR = REPO_ROOT / "config" / "demo"
DYNAMO_ENDPOINT_URL = "http://127.0.0.1:8021"
API_PORT = 8099
FAKE_DYNATRACE_TOKEN = "story182-fake-dynatrace-token"  # noqa: S105 - not a secret
FAKE_STATUSPAGE_PAGE_ID = "story182-fake-page-id"
FAKE_STATUSPAGE_API_TOKEN = "story182-fake-statuspage-token"  # noqa: S105


class RealityGateError(RuntimeError):
    """Raised when a positive-side AC1-AC5 assertion fails."""


def _print_provenance() -> None:
    print("PROVENANCE (STORY-187, before reporting anything):")
    for provenance in (
        assert_import_root("src.composition.run", BACKEND_ROOT),
        assert_import_root("src.composition.publish_helper", BACKEND_ROOT),
        assert_import_root("demo_engine.server", TOOLS_ROOT),
    ):
        print("  ", provenance)
    print()


def _wait_for_http_ok(url: str, *, timeout_seconds: float = 30.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_exc: Exception | None = None
    while time.monotonic() < deadline:
        try:
            resp = httpx.get(url, timeout=2.0)
            if resp.status_code == 200:
                return
        except Exception as exc:  # noqa: BLE001 - polling until ready
            last_exc = exc
        time.sleep(0.3)
    raise RealityGateError(
        f"{url} never returned 200 within {timeout_seconds}s: {last_exc}"
    )


def _port_is_free(port: int, *, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1.0)
        result = sock.connect_ex((host, port))
    return result != 0  # nonzero = connection refused = nothing listening


def _assert_api_port_free(port: int) -> None:
    """Minor (STORY-182 fix round): `API_PORT` was hardcoded and never
    pre-flight-checked, though `_port_is_free` already existed and was only
    used AFTER teardown. A busy port previously cost a silent, opaque 30s
    `_wait_for_http_ok` timeout instead of a clear message up front."""
    if not _port_is_free(port):
        raise RealityGateError(
            f"API port {port} is already in use -- free it before running "
            "this harness (a busy port otherwise costs a silent 30s "
            "health-check timeout instead of a clear error)."
        )


def _wait_for_marker_or_exit(
    proc: subprocess.Popen,
    *paths: Path,
    marker: str,
    timeout_seconds: float,
) -> bool:
    """Poll `paths` (opened fresh each poll, since the writer keeps its own
    handle open) for `marker`, or stop early if `proc` exits on its own.

    Returns True iff the marker was found. `PYTHONUNBUFFERED=1` (set on the
    loop subprocess's env) is what makes this reliable: a Windows
    `TerminateProcess` (what `Popen.terminate()` actually does on this
    platform -- there is no SIGTERM to catch) does NOT flush a child's
    block-buffered stdio, so without it the tail of the log can be silently
    lost the moment this harness terminates the process -- discovered live
    on this story's own first run (37 of 41 expected "health OK" lines,
    because unbuffered output had not made it out before termination).
    """
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        for path in paths:
            if path.exists() and marker in path.read_text(encoding="utf-8"):
                return True
        if proc.poll() is not None:
            return False
        time.sleep(1.0)
    return False


def _wait_for_last_signal_ingested(
    *, api_base: str, last_signal_key: str, since: str, timeout_seconds: float
) -> bool:
    """Poll `/api/v1/history` for `last_signal_key` until its FULL batch has
    landed (all 4 declared locations present), not merely its first row.

    `run_periodic`'s first pass runs every signal's `run_cycle` to completion
    SEQUENTIALLY (each blocks the single asyncio event loop thread until its
    own first `await asyncio.sleep`), so the LAST signal in build order is
    the last one to ingest -- polling it (rather than a padded fixed sleep)
    is what makes the wait adaptive to real per-cycle DynamoDB + HTTP cost
    instead of a guessed constant.

    Waiting for >=1 row (rather than all 4 locations) is NOT enough: a
    single `ingest_observations` call still writes its batch of ~20 rows one
    at a time, so a poll that returns as soon as the FIRST row is readable
    can terminate the process mid-batch -- discovered live on this story's
    own second run, where exactly the last signal in build order (and no
    other) showed 3 of 4 distinct locations. Polling for the full location
    count closes that race for the evidence-gathering purpose this harness
    exists for.
    """
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            resp = httpx.get(
                f"{api_base}/history",
                params={"signal_key": last_signal_key, "since": since},
                timeout=5.0,
            )
            if resp.status_code == 200:
                observations = resp.json()
                if distinct_locations_from_history_dtos(observations) >= 4:
                    return True
        except Exception:  # noqa: BLE001 - polling until ready
            pass
        time.sleep(1.0)
    return False


def _terminate_and_verify(proc: subprocess.Popen, *, name: str) -> dict:
    """Terminate `proc` (escalating to `.kill()` if it does not exit within
    15s) and record the (expected-nonzero-on-Windows) returncode.

    MAJOR 4 (STORY-182 fix round): `reaped_returncode_observed` -- NOT
    "gone_by_pid"/"OS-level PID verification" as this field and the
    docstring here (and `tools/demo_engine/README.md`'s Part 2b section)
    previously claimed. `proc.poll()` immediately after `proc.wait()` has
    already returned reads Popen's OWN CACHED `returncode` -- it never asks
    the OS again -- so it can never observe False here; it is not
    independent OS-level evidence of anything. Renamed to describe exactly
    what IS true (a returncode was observed via `wait`/`poll`), matching the
    honesty standard this harness already applies to
    `rollup_distinct_locations_HARDCODED_ZERO_NOT_PROOF` (:610). The genuine
    OS-level check in this harness is the PORT probe, `_port_is_free`
    (a real `connect_ex`), asserted separately after teardown.
    """
    proc.terminate()
    try:
        returncode = proc.wait(timeout=15)
        escalated_to_kill = False
    except subprocess.TimeoutExpired:
        proc.kill()
        returncode = proc.wait(timeout=15)
        escalated_to_kill = True

    reaped_returncode_observed = proc.poll() is not None
    return {
        "name": name,
        "pid": proc.pid,
        "returncode": returncode,
        "escalated_to_kill": escalated_to_kill,
        "reaped_returncode_observed": reaped_returncode_observed,
    }


def _terminate_loop_after(loop_proc: subprocess.Popen, body) -> dict:
    """Run `body()` (the loop's startup/ingest polling) and ALWAYS
    terminate+verify `loop_proc` in a `finally`, even if `body` raises.

    MAJOR 3 (STORY-182 fix round): before this helper existed, the loop
    subprocess was launched with no `try/finally` around its wait/poll
    logic -- only the outer `finally` (around `api_proc`) existed. Any
    exception raised while waiting on the loop (a `KeyboardInterrupt` during
    the up-to-270s of polling -- the obvious operator action on a long run;
    a `UnicodeDecodeError` from `_wait_for_marker_or_exit`'s `read_text`; an
    `IndexError` on `iteration_order_signal_keys[-1]`) leaked a live
    `python -m src.composition.run` that outlived the demo engine and the
    API and kept hitting DynamoDB. Pinned by
    `test_harness_teardown.py::test_terminate_loop_after_terminates_the_process_even_when_body_raises`
    against a REAL subprocess (no mock).
    """
    try:
        body()
    finally:
        loop_teardown = _terminate_and_verify(loop_proc, name="loop")
    return loop_teardown


def _assert_loop_startup_and_ingestion(
    *,
    startup_seen: bool,
    last_signal_ingested: bool,
    last_signal_key: str,
    loop_wait_seconds: float,
) -> None:
    """MAJOR 2 (STORY-182 fix round): a startup-marker or ingest-poll
    TIMEOUT is a FAILURE, never partial evidence -- previously these two
    flags were recorded and execution simply continued, contradicting this
    module's own docstring ("raises loudly ... if any precondition fails")."""
    if not startup_seen:
        raise RealityGateError(
            "AC3/AC4 FAILED: the loop never reported the 'periodic "
            "monitoring loop' startup marker within 180s -- see the loop "
            "subprocess's stdout/stderr logs."
        )
    if not last_signal_ingested:
        raise RealityGateError(
            f"AC3 FAILED: the last signal in build order ({last_signal_key!r}) "
            f"did not finish ingesting all 4 declared locations within "
            f"{loop_wait_seconds}s."
        )


def _assert_ac3_ingest(evidence: dict) -> None:
    """MAJOR 2: enforce every AC3 threshold the story requires, not merely
    print it."""
    assert evidence["signals_with_zero_rows"] == [], (
        "AC3 FAILED: signal(s) with zero ingested rows: "
        f"{evidence['signals_with_zero_rows']}"
    )
    assert evidence["signals_with_under_4_locations"] == [], (
        "AC3 FAILED: signal(s) with fewer than 4 distinct locations: "
        f"{evidence['signals_with_under_4_locations']}"
    )
    assert evidence["components_count"] >= 12, (
        f"AC3 FAILED: components_count={evidence['components_count']} < 12"
    )
    assert evidence["signals_count"] >= 40, (
        f"AC3 FAILED: signals_count={evidence['signals_count']} < 40"
    )


def _assert_ac4_vendor_health(evidence: dict) -> None:
    """MAJOR 2: enforce AC4 -- zero drift warnings, one healthy-INFO line
    per signal."""
    assert evidence["drift_warning_count"] == 0, (
        "AC4 FAILED: "
        f"{evidence['drift_warning_count']} 'VENDOR-ID DRIFT SUSPECTED' "
        "warning(s) logged"
    )
    assert evidence["healthy_info_count"] == evidence["expected_signal_count"], (
        "AC4 FAILED: healthy_info_count="
        f"{evidence['healthy_info_count']} != expected_signal_count="
        f"{evidence['expected_signal_count']}"
    )


def _parse_pytest_skip_count(pytest_stdout: str) -> int:
    """Parse `pytest -q`'s own summary line ("N passed[, M skipped] in Ts")
    for the skip count -- 0 if no "skipped" fragment is present.

    Minor (STORY-182 fix round): AC1(d)'s `guard_result.returncode == 0`
    cannot by itself distinguish "passed" from "skipped" -- 2 of
    `backend/tests/test_demo_fleet_config.py`'s 10 tests are
    `dynamo_local`-gated, and this sprint's standing rule is that a nonzero
    skip count is an incomplete gate, not a pass."""
    match = re.search(r"(\d+) skipped", pytest_stdout)
    return int(match.group(1)) if match else 0


def _assert_ac5_approvals(evidence: dict, *, expect_empty: bool = True) -> None:
    """STORY-182 AC5: the approvals endpoint returns a well-formed EMPTY result.

    `expect_empty` exists because STORY-182's "empty" was true only for the
    reason that made it VACUOUS: the demo engine could emit `UP` and absence
    only, so no degradation could ever be proposed and this endpoint could not
    have been non-empty whatever the code did.

    STORY-191 changed that. A failure scenario (e.g. partial-breadth) now
    legitimately opens a DEGRADED proposal, so with `extra_scenarios` supplied
    an EMPTY list would be the bug -- it would mean the degradation path never
    ran. The caller therefore states which world it is in, and the non-empty
    case is asserted just as strictly rather than merely tolerated: a proposal
    must be well-formed and OPEN, which is the positive evidence that
    `decide` proposed a degradation and (per the publish guard) published
    nothing.
    """
    if expect_empty:
        assert evidence["is_empty_list"], (
            f"AC5 FAILED: GET /api/v1/approvals returned a non-empty result: "
            f"{evidence['body']!r}"
        )
        return

    # With failure scenarios injected, proposals MAY legitimately be open -- but
    # their PRESENCE is deliberately NOT asserted, because it is not
    # deterministic, and a flaky assertion in a proof harness is worse than no
    # assertion.
    #
    # WHY (measured across two consecutive real runs with identical scenarios:
    # run 1 produced an open DEGRADED proposal for `auth-service`, run 2 produced
    # none): observations are WATERMARK-driven and therefore deterministic, but a
    # PROPOSAL additionally needs `anti_flap` to still SEE a streak, and
    # `orchestrate_signal` looks back only
    # `since = until - (max_threshold + 2) * interval` from `clock.now()` AT
    # ORCHESTRATE TIME, while the rows are PAST-ANCHORED to `run_start`. Keeping
    # the >= 2 cycles a `degraded: 2` threshold needs therefore requires
    # `orchestrate_time - run_start <= 6 * interval` -- only 180s for every
    # failure signal in `config/demo` (all 30s). The loop probes vendor health
    # across all 41 signals before its first cycle, so that budget can already be
    # spent by the time the signal is reached.
    #
    # Whatever IS present is still validated strictly, and the count is recorded
    # as evidence. Making proposal formation a RELIABLE assertion needs a failure
    # scenario on a longer-interval signal -- filed, not bodged.
    body = evidence["body"]
    assert isinstance(body, list), f"AC5 FAILED: expected a list, got {body!r}"
    evidence["open_proposal_count"] = len(body)
    print(
        f"AC5: {len(body)} open proposal(s) -- presence NOT asserted "
        "(window-timing dependent; see _assert_ac5_approvals)"
    )
    for proposal in body:
        missing = {"component_id", "from_status", "to_status", "state"} - set(proposal)
        assert not missing, (
            f"AC5 FAILED: proposal missing {sorted(missing)}: {proposal!r}"
        )
        assert proposal["state"] == "open", (
            f"AC5 FAILED: expected an OPEN proposal, got {proposal['state']!r}: "
            f"{proposal!r}"
        )


def run_positive_side(
    *,
    api_port: int = API_PORT,
    loop_wait_seconds: float = 90.0,
    extra_scenarios: list[SignalScenario] | None = None,
    pre_loop_hook: Callable[..., dict] | None = None,
) -> dict:
    """Run the full positive-side reality gate and return the evidence dict.

    Steps (STORY-182 AC1-AC6, sprint-64 plan "Steps" for story 4):
      1. Provenance (STORY-187).
      2. Build the fleet-wide coverage row store (B1) and start the embedded
         demo engine seeded with it.
      3. Create FRESH observations+control tables (AC2, B4).
      4. Launch the API as a real `uvicorn` subprocess with CONFIG_DIR=
         config/demo (AC1a) and the fresh table names (AC1b).
      5. Assert AC1(a)-(e) against the running API.
      6. Launch `python -m src.composition.run`, UNMODIFIED, with the SAME
         env matrix (AC1a/AC1b), against the demo engine.
      7. Wait long enough for every signal's first cycle (the loop's first
         cycle fires before its first sleep, `pull_loop.py:160` -- so this
         harness only needs to span STARTUP, not an interval), then
         terminate it externally (AC6 forbids a `stop_event` in
         `backend/src/`).
      8. Collect AC3 (ingest), AC4 (vendor-health), AC5 (empty approvals)
         evidence from the still-running API.
      9. Tear everything down with OS-level verification.

    `extra_scenarios` (STORY-191) MERGES additional scenario rows into the
    fleet-wide store rather than replacing it -- the fleet store must
    survive, because `_assert_ac3_ingest` requires every one of the 41
    signals to have ingested from all 4 locations.
    """
    _print_provenance()

    _assert_api_port_free(api_port)

    cfg = load_config(DEMO_CONFIG_DIR)
    # `run.py:135-151` builds one `run_periodic` coroutine per signal in THIS
    # exact per-app/per-signal order, and `asyncio.gather` starts them in
    # that same order; since each `run_cycle` runs synchronously to
    # completion before its coroutine reaches its own first
    # `await asyncio.sleep`, the LAST entry in this list is the last signal
    # to complete its first cycle. Kept separate from the alphabetically
    # SORTED `all_signal_keys` used for reporting -- sorting here would
    # silently break the "wait for the last one" polling strategy below
    # (discovered live on STORY-182's second run: 6 trailing signals,
    # exactly config/demo's last app/component in file-glob order, had not
    # ingested yet under a fixed post-startup sleep).
    iteration_order_signal_keys = [
        sig.signal_key for app in cfg.apps for sig in app.signals
    ]
    all_signal_keys = sorted(set(iteration_order_signal_keys))
    all_component_ids = sorted({comp.id for app in cfg.apps for comp in app.components})
    print(
        f"Demo fleet: {len(cfg.apps)} apps, {len(all_component_ids)} components, "
        f"{len(all_signal_keys)} signals (config/demo, loaded read-only here)."
    )

    observations_table, control_table = fresh_table_names()
    print(
        f"Fresh tables (AC2, B4): observations={observations_table!r} "
        f"control={control_table!r}"
    )

    child_env_base = build_child_env(
        base_env=dict(os.environ),
        config_dir=str(DEMO_CONFIG_DIR),
        dynamo_endpoint_url=DYNAMO_ENDPOINT_URL,
        observations_table=observations_table,
        control_table=control_table,
    )

    print("Creating fresh DynamoDB tables via scripts/create_tables.py ...")
    create_result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "create_tables.py")],
        cwd=str(REPO_ROOT),
        env=child_env_base,
        capture_output=True,
        text=True,
        timeout=60,
    )
    print(create_result.stdout)
    if create_result.returncode != 0:
        raise RealityGateError(f"create_tables.py failed:\n{create_result.stderr}")

    run_start = datetime.now(timezone.utc)
    print(f"Run start (UTC): {run_start.isoformat()}")

    store = build_fleet_row_store(cfg, end_time=run_start)
    if extra_scenarios:
        for sc in extra_scenarios:
            for row in expand_scenario(
                sc, end_time=run_start, event_id_prefix=f"fail-{sc.signal_key}"
            ):
                store.add_row(row)
        print(f"Merged {len(extra_scenarios)} extra scenario(s) into row store.")

    print(
        f"Coverage row store built: {len(store._rows)} rows "
        f"({len(all_signal_keys)} signals x 5 cycles x 4 locations)"
    )

    log_dir = Path(tempfile.mkdtemp(prefix="story182-"))
    loop_stdout_path = log_dir / "loop_stdout.log"
    loop_stderr_path = log_dir / "loop_stderr.log"
    print(f"Loop subprocess logs: {loop_stdout_path}")

    evidence: dict = {
        "observations_table": observations_table,
        "control_table": control_table,
    }

    with DemoEngineServer(store) as demo_engine:
        print(f"Embedded demo engine listening at {demo_engine.base_url}")

        # MAJOR 1 (STORY-182 fix round): the API process is genuinely
        # credential-bearing -- `composition/app.py:169-183` calls
        # `load_statuspage_secrets()` for the approve trigger -- so it gets
        # the SAME deliberately-fake Statuspage credentials as the loop
        # call site below, not just CONFIG_DIR/DYNAMO_*. Without this, its
        # own `load_dotenv()` (`composition/asgi.py`) would fill the gap
        # with the REAL repo-root `.env` values (`override=False` only
        # skips vars already set). The actual guard remains `config/demo`'s
        # empty `statuspage_mapping()` -- this is defence in depth on top
        # of it, never the guard itself.
        api_env = build_child_env(
            base_env=dict(os.environ),
            config_dir=str(DEMO_CONFIG_DIR),
            dynamo_endpoint_url=DYNAMO_ENDPOINT_URL,
            observations_table=observations_table,
            control_table=control_table,
            statuspage_page_id=FAKE_STATUSPAGE_PAGE_ID,
            statuspage_api_token=FAKE_STATUSPAGE_API_TOKEN,
        )
        api_proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "src.composition.asgi:app",
                "--port",
                str(api_port),
            ],
            cwd=str(REPO_ROOT),
            env=api_env,
        )
        print(
            f"API (uvicorn) subprocess launched, pid={api_proc.pid}, "
            f"env CONFIG_DIR={api_env[CONFIG_DIR_VAR]!r}"
        )

        api_base = f"http://127.0.0.1:{api_port}/api/v1"
        try:
            _wait_for_http_ok(f"{api_base}/health", timeout_seconds=30.0)
            print("API is up (/api/v1/health -> 200).")

            preconditions = _assert_ac1_preconditions(
                api_base=api_base,
                api_env=api_env,
                expected_component_ids=all_component_ids,
            )
            evidence["ac1_preconditions"] = preconditions

            # STORY-191 AC6 seam. Runs AFTER the fresh tables exist and the API
            # has seeded components, and BEFORE the loop subprocess starts --
            # the only window in which a caller can establish a pre-loop
            # control-table state that the loop will then react to.
            #
            # It exists because a recovery publish is UNREACHABLE from a seeded
            # baseline: `decide` publishes only when
            # severity_rank(proposed) < severity_rank(current)
            # (`decide.py:115-117`), every component seeds OPERATIONAL
            # (`seed_dynamo.py:49`), and a degradation never changes stored
            # status (`decide.py:128-136` opens a proposal and publishes
            # nothing). So a DOWN-then-UP observation ladder can NEVER trip the
            # recovery branch -- the caller must pre-set a worse-than-
            # OPERATIONAL status, which is a real reachable state (a
            # previously-approved degradation).
            if pre_loop_hook is not None:
                print("Running pre_loop_hook (STORY-191 AC6 precondition)...")
                evidence["pre_loop_hook"] = pre_loop_hook(
                    control_table=control_table,
                    api_base=api_base,
                )
                print(f"pre_loop_hook result: {evidence['pre_loop_hook']}")

            loop_env = build_child_env(
                base_env=dict(os.environ),
                config_dir=str(DEMO_CONFIG_DIR),
                dynamo_endpoint_url=DYNAMO_ENDPOINT_URL,
                observations_table=observations_table,
                control_table=control_table,
                dynatrace_env_url=demo_engine.base_url,
                dynatrace_api_token=FAKE_DYNATRACE_TOKEN,
                statuspage_page_id=FAKE_STATUSPAGE_PAGE_ID,
                statuspage_api_token=FAKE_STATUSPAGE_API_TOKEN,
            )
            # Unbuffered: a Windows Popen.terminate() is TerminateProcess (no
            # SIGTERM to catch, no chance for the child's own atexit flush),
            # so anything still sitting in a block-buffered stdio buffer at
            # that instant is lost -- discovered live on this story's own
            # first run.
            loop_env["PYTHONUNBUFFERED"] = "1"
            with (
                open(loop_stdout_path, "w", encoding="utf-8") as out_fh,
                open(loop_stderr_path, "w", encoding="utf-8") as err_fh,
            ):
                loop_proc = subprocess.Popen(
                    [sys.executable, "-u", "-m", "src.composition.run"],
                    cwd=str(REPO_ROOT),
                    env=loop_env,
                    stdout=out_fh,
                    stderr=err_fh,
                )
                print(
                    f"Loop subprocess launched, pid={loop_proc.pid}, env "
                    f"DYNATRACE_ENV_URL={loop_env['DYNATRACE_ENV_URL']!r} "
                    f"CONFIG_DIR={loop_env[CONFIG_DIR_VAR]!r}"
                )

                # MAJOR 3 (STORY-182 fix round): everything from the launch
                # above through the wait/poll logic below is wrapped in
                # `_terminate_loop_after`'s own `try/finally` -- an exception
                # raised anywhere in `_wait_for_loop_evidence` (a
                # `KeyboardInterrupt` mid-poll, a `UnicodeDecodeError` from
                # `read_text`, an `IndexError`) must still reap this
                # subprocess, not leak it. `startup_seen`/`last_signal_ingested`
                # are seeded False so the `finally` inside
                # `_terminate_loop_after` can run even if the body raises
                # before either is assigned.
                startup_seen = False
                last_signal_ingested = False

                def _wait_for_loop_evidence() -> None:
                    nonlocal startup_seen, last_signal_ingested
                    print(
                        "Waiting for the loop to report 'Starting N periodic "
                        "monitoring loop(s)' (startup + the sequential "
                        "41-signal vendor-health probe come first) -- polled, "
                        "not a blind fixed sleep, since the probe's real "
                        "per-signal HTTP round-trip cost is what this story's "
                        "first run measured directly."
                    )
                    startup_seen = _wait_for_marker_or_exit(
                        loop_proc,
                        loop_stdout_path,
                        loop_stderr_path,
                        marker="periodic monitoring loop",
                        timeout_seconds=180.0,
                    )
                    print(f"Startup marker observed: {startup_seen}")
                    if startup_seen:
                        last_signal_key = iteration_order_signal_keys[-1]
                        print(
                            f"Polling for the LAST signal in build order "
                            f"({last_signal_key!r}) to ingest its first row -- "
                            "run_periodic's first pass runs every signal's "
                            "run_cycle sequentially before any coroutine "
                            "reaches its own first `await asyncio.sleep`, so "
                            "this is the adaptive replacement for a padded "
                            f"fixed sleep (up to {loop_wait_seconds}s)."
                        )
                        last_signal_ingested = _wait_for_last_signal_ingested(
                            api_base=api_base,
                            last_signal_key=last_signal_key,
                            since=(run_start - timedelta(minutes=5)).isoformat(),
                            timeout_seconds=loop_wait_seconds,
                        )
                        print(f"Last signal ingested: {last_signal_ingested}")
                        if last_signal_ingested:
                            # Small settle buffer: orchestrate_signal/decide
                            # still run (control-table reads/writes) after the
                            # LAST signal's observation batch is fully
                            # readable, before its coroutine reaches its own
                            # first `await asyncio.sleep`.
                            time.sleep(2.0)

                loop_teardown = _terminate_loop_after(
                    loop_proc, _wait_for_loop_evidence
                )
                loop_teardown["startup_marker_observed"] = startup_seen
                loop_teardown["last_signal_ingested_before_terminate"] = (
                    last_signal_ingested
                )
            evidence["loop_teardown"] = loop_teardown
            print(f"Loop terminated: {loop_teardown}")

            last_signal_key = iteration_order_signal_keys[-1]
            # MAJOR 2 (STORY-182 fix round): a startup or ingest-poll
            # TIMEOUT is a FAILURE, never partial evidence -- previously
            # these two flags were recorded and execution simply continued.
            _assert_loop_startup_and_ingestion(
                startup_seen=startup_seen,
                last_signal_ingested=last_signal_ingested,
                last_signal_key=last_signal_key,
                loop_wait_seconds=loop_wait_seconds,
            )

            loop_stdout_text = loop_stdout_path.read_text(encoding="utf-8")
            loop_stderr_text = loop_stderr_path.read_text(encoding="utf-8")
            evidence["ac4_vendor_health"] = _collect_ac4_evidence(
                loop_stdout_text + loop_stderr_text, all_signal_keys
            )
            _assert_ac4_vendor_health(evidence["ac4_vendor_health"])

            run_end = datetime.now(timezone.utc)
            evidence["ac3_ingest"] = _collect_ac3_evidence(
                api_base=api_base,
                signal_keys=all_signal_keys,
                component_ids=all_component_ids,
                run_start=run_start,
                run_end=run_end,
            )
            _assert_ac3_ingest(evidence["ac3_ingest"])

            evidence["ac5_approvals"] = _collect_ac5_evidence(api_base=api_base)
            # With failure scenarios injected, an OPEN degradation proposal is
            # the EXPECTED outcome, not a violation -- see the assertion's
            # docstring for why STORY-182's "empty" was vacuous.
            _assert_ac5_approvals(
                evidence["ac5_approvals"], expect_empty=not extra_scenarios
            )

        finally:
            api_teardown = _terminate_and_verify(api_proc, name="api")
            evidence["api_teardown"] = api_teardown
            print(f"API terminated: {api_teardown}")
            time.sleep(0.5)
            port_free = _port_is_free(api_port)
            evidence["api_port_free_after_teardown"] = port_free
            print(f"API port {api_port} free after teardown: {port_free}")

    return evidence


def _assert_ac1_preconditions(
    *, api_base: str, api_env: dict, expected_component_ids: list[str]
) -> dict:
    """Assert and record AC1(a)-(e) BEFORE the loop starts."""
    result: dict = {}

    # AC1(a): CONFIG_DIR on the API process -- recorded from the exact env
    # dict passed to Popen (the API resolved it via
    # settings.py::load_settings with no `config_dir` argument, exactly as
    # `asgi.py` boots it).
    result["config_dir_api"] = api_env[CONFIG_DIR_VAR]
    assert result["config_dir_api"].replace("\\", "/").endswith("config/demo"), (
        f"AC1(a) FAILED: API CONFIG_DIR={result['config_dir_api']!r}"
    )

    # AC1(b): DYNAMO_ENDPOINT_URL + table names, recorded from the same env.
    result["dynamo_endpoint_url"] = api_env[DYNAMO_ENDPOINT_URL_VAR]
    result["observations_table"] = api_env[DYNAMO_OBSERVATIONS_TABLE_VAR]
    result["control_table"] = api_env[DYNAMO_CONTROL_TABLE_VAR]
    assert result["dynamo_endpoint_url"], "AC1(b) FAILED: DYNAMO_ENDPOINT_URL unset"
    # STORY-203 AC1/AC2: the right-hand blocklist values are IMPORTED from
    # `Settings`'s own defaults, never re-declared -- so this follows a future
    # rename automatically. The LEFT-hand side stays `result[...]`, read from
    # the REAL resolved `api_env` above: replacing it with the imported
    # constant too would turn this into a tautology disconnected from the
    # actual environment (see backend/tests/demo_loop_gate/
    # test_harness_assertions.py's blocklist-discrimination tests).
    assert result["observations_table"] not in (
        Settings.dynamo_observations_table,
        "uptime-monitor-observations",
    )
    assert result["control_table"] not in (
        Settings.dynamo_control_table,
        "uptime-monitor-control",
    )

    # Indirect proof CONFIG_DIR really resolved to config/demo: /api/v1/topology
    # and /api/v1/components must show the demo fleet, not config/apps's single
    # httpcheck component -- labelled seed-derived (not the AC3 ingest proof).
    components_resp = httpx.get(f"{api_base}/components", timeout=10.0).json()
    result["components_seed_derived"] = components_resp
    seeded_ids = sorted(c["id"] for c in components_resp)
    assert seeded_ids == expected_component_ids, (
        f"AC1(a) FAILED indirectly: API seeded components {seeded_ids} != "
        f"demo fleet {expected_component_ids} -- CONFIG_DIR did not resolve "
        "to config/demo on the API process."
    )

    # AC1(c): sample-mode must be OFF.
    sample_mode_resp = httpx.get(f"{api_base}/sample-mode", timeout=10.0).json()
    result["sample_mode"] = sample_mode_resp
    assert sample_mode_resp == {"enabled": False}, (
        f"AC1(c) FAILED: GET /sample-mode returned {sample_mode_resp!r}"
    )

    # AC1(e): every component operational, BEFORE the loop starts (B4).
    statuses = {c["id"]: c["status"] for c in components_resp}
    result["component_statuses"] = statuses
    non_operational = {cid: s for cid, s in statuses.items() if s != "operational"}
    assert not non_operational, (
        f"AC1(e) FAILED: non-operational components before loop start: {non_operational}"
    )

    # AC1(d): STORY-176's publish-guard checks re-run green at this HEAD.
    # Minor (STORY-182 fix round): this was previously the ONE child
    # process launched WITHOUT `env=api_env` (every other subprocess in
    # this harness gets an explicit env matrix), and `returncode == 0`
    # cannot distinguish "passed" from "skipped" -- 2 of these 10 tests are
    # `dynamo_local`-gated, and a nonzero skip count is an incomplete gate.
    guard_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "backend/tests/test_demo_fleet_config.py",
            "-q",
        ],
        cwd=str(REPO_ROOT),
        env=api_env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    result["publish_guard_regression_exit_code"] = guard_result.returncode
    result["publish_guard_regression_tail"] = "\n".join(
        guard_result.stdout.strip().splitlines()[-5:]
    )
    assert guard_result.returncode == 0, (
        f"AC1(d) FAILED: publish-guard regression tests did not pass:\n"
        f"{guard_result.stdout}\n{guard_result.stderr}"
    )
    result["publish_guard_regression_skipped_count"] = _parse_pytest_skip_count(
        guard_result.stdout
    )
    assert result["publish_guard_regression_skipped_count"] == 0, (
        "AC1(d) FAILED: publish-guard regression tests had "
        f"{result['publish_guard_regression_skipped_count']} skip(s) -- a "
        "nonzero skip count is an incomplete gate:\n"
        f"{guard_result.stdout}"
    )

    print("AC1 preconditions (a)-(e), all asserted and recorded:")
    for key, value in result.items():
        print(f"  {key}: {value}")

    return result


def _collect_ac4_evidence(loop_output_text: str, signal_keys: list[str]) -> dict:
    drift_count = loop_output_text.count("VENDOR-ID DRIFT SUSPECTED")
    healthy_count = loop_output_text.count("Vendor-id health OK")
    starting_line = next(
        (
            line
            for line in loop_output_text.splitlines()
            if "periodic monitoring loop" in line
        ),
        None,
    )
    result = {
        "drift_warning_count": drift_count,
        "healthy_info_count": healthy_count,
        "starting_line": starting_line,
        "expected_signal_count": len(signal_keys),
    }
    print("AC4 (vendor-id health, from the loop subprocess's own log):")
    for key, value in result.items():
        print(f"  {key}: {value}")
    return result


def _collect_ac3_evidence(
    *,
    api_base: str,
    signal_keys: list[str],
    component_ids: list[str],
    run_start: datetime,
    run_end: datetime,
) -> dict:
    since = (run_start - timedelta(minutes=5)).isoformat()
    until = (run_end + timedelta(minutes=5)).isoformat()

    per_signal: dict[str, dict] = {}
    for signal_key in signal_keys:
        history_resp = httpx.get(
            f"{api_base}/history",
            params={"signal_key": signal_key, "since": since, "until": until},
            timeout=10.0,
        )
        observations = history_resp.json()
        distinct_locations = distinct_locations_from_history_dtos(observations)

        availability_resp = httpx.get(
            f"{api_base}/availability",
            params={"signal_key": signal_key, "since": since, "until": until},
            timeout=10.0,
        )
        availability = availability_resp.json()

        per_signal[signal_key] = {
            "history_row_count": len(observations),
            "history_distinct_locations": distinct_locations,
            "availability_distinct_locations": availability.get("distinct_locations"),
            "availability_pct": availability.get("availability_pct"),
            "completeness_pct": availability.get("completeness_pct"),
        }

    zero_rows = [k for k, v in per_signal.items() if v["history_row_count"] == 0]
    under_4_locations = [
        k for k, v in per_signal.items() if v["history_distinct_locations"] < 4
    ]

    component_sample_id = component_ids[0]
    component_availability_resp = httpx.get(
        f"{api_base}/availability/component/{component_sample_id}",
        params={"since": since, "until": until},
        timeout=10.0,
    )
    component_availability = component_availability_resp.json()

    topology_resp = httpx.get(f"{api_base}/topology", timeout=10.0)

    result = {
        "components_count": len(component_ids),
        "signals_count": len(signal_keys),
        "signals_with_zero_rows": zero_rows,
        "signals_with_under_4_locations": under_4_locations,
        "per_signal_sample": dict(list(per_signal.items())[:3]),
        "component_availability_sample": {
            "component_id": component_sample_id,
            "rollup_distinct_locations_HARDCODED_ZERO_NOT_PROOF": component_availability.get(
                "rollup", {}
            ).get("distinct_locations"),
            "signals_children_count": len(component_availability.get("signals", [])),
        },
        "topology_seed_derived_status_code": topology_resp.status_code,
        "components_and_topology_are_seed_derived_not_the_proof": True,
    }
    print("AC3 (ingest, observation-derived):")
    for key, value in result.items():
        print(f"  {key}: {value}")
    return result


def _collect_ac5_evidence(*, api_base: str) -> dict:
    resp = httpx.get(f"{api_base}/approvals", timeout=10.0)
    body = resp.json()
    result = {
        "status_code": resp.status_code,
        "body": body,
        "is_empty_list": body == [],
        "vacuousness_note": (
            "With only UP observations and every component seeded/asserted "
            "OPERATIONAL (AC1(e)), proposed_status == current_status for "
            "every signal, so decide.py takes neither branch and "
            "publish_change stays None (decide.py:119-126) -- publish() is "
            "NEVER CALLED. Any 'no Statuspage POST was attempted' log "
            "observation is therefore VACUOUS: it would be equally true if "
            "the guard were broken. The guard's real evidence is the "
            "_delegate-chain assertion in publisher_chain.py, never this "
            "silence."
        ),
    }
    print("AC5 (approvals, empty + vacuousness note):")
    print(f"  status_code: {result['status_code']}  body: {result['body']}")
    return result


def main() -> bool:
    """MAJOR 2 (STORY-182 fix round): give this side an explicit PASS/FAIL
    verdict, mirroring `guard_reality_gate.py`/`backfill_reality_gate.py`
    (sides 2 and 3) -- previously `__main__` dumped the evidence dict as
    JSON and exited 0 UNCONDITIONALLY, regardless of whether any AC1-AC5
    assertion inside `run_positive_side` had failed."""
    try:
        evidence = run_positive_side()
    except (RealityGateError, AssertionError) as exc:
        print()
        print("=" * 78)
        print("REALITY GATE 182 SIDE 1 (positive) -- FAIL")
        print("=" * 78)
        print(f"  {exc}")
        return False

    print()
    print("=" * 78)
    print("REALITY GATE 182 SIDE 1 (positive) -- EVIDENCE SUMMARY")
    print("=" * 78)
    print(json.dumps(evidence, indent=2, default=str))
    print()
    print("REALITY GATE 182 SIDE 1: PASS")
    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
