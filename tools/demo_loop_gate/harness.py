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
http://127.0.0.1:8021` reachable). Prints every AC1-AC5 value it asserts,
inspectable in the console output; raises loudly (never a silent partial
pass) if any precondition fails.

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

import os
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
TOOLS_ROOT = REPO_ROOT / "tools"

for _p in (str(TOOLS_ROOT),):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import httpx  # noqa: E402
from demo_engine.server import DemoEngineServer  # noqa: E402
from import_provenance import assert_import_root  # noqa: E402
from src.composition.config import load_config  # noqa: E402

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
    from demo_loop_gate.evidence import distinct_locations_from_history_dtos

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
    """Terminate `proc`, confirm it is gone BY PID (not a wrapper-job kill),
    and record the (expected-nonzero-on-Windows) returncode."""
    proc.terminate()
    try:
        returncode = proc.wait(timeout=15)
        escalated_to_kill = False
    except subprocess.TimeoutExpired:
        proc.kill()
        returncode = proc.wait(timeout=15)
        escalated_to_kill = True

    gone_by_pid = proc.poll() is not None
    return {
        "name": name,
        "pid": proc.pid,
        "returncode": returncode,
        "escalated_to_kill": escalated_to_kill,
        "gone_by_pid": gone_by_pid,
    }


def run_positive_side(
    *,
    api_port: int = API_PORT,
    loop_wait_seconds: float = 90.0,
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
    """
    _print_provenance()

    cfg = load_config(DEMO_CONFIG_DIR)
    # `run.py:135-151` builds one `run_periodic` coroutine per signal in THIS
    # exact per-app/per-signal order, and `asyncio.gather` starts them in
    # that same order; since each `run_cycle` runs synchronously to
    # completion before its coroutine reaches its own first
    # `await asyncio.sleep`, the LAST entry in this list is the last signal
    # to complete its first cycle. Kept separate from the alphabetically
    # SORTED `all_signal_keys` used for reporting -- sorting here would
    # silently break the "wait for the last one" polling strategy below
    # (discovered live on this story's own second run: 6 trailing signals,
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

        api_env = build_child_env(
            base_env=dict(os.environ),
            config_dir=str(DEMO_CONFIG_DIR),
            dynamo_endpoint_url=DYNAMO_ENDPOINT_URL,
            observations_table=observations_table,
            control_table=control_table,
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
            f"env CONFIG_DIR={api_env['CONFIG_DIR']!r}"
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
                    f"CONFIG_DIR={loop_env['CONFIG_DIR']!r}"
                )

                print(
                    "Waiting for the loop to report 'Starting N periodic "
                    "monitoring loop(s)' (startup + the sequential 41-signal "
                    "vendor-health probe come first) -- polled, not a blind "
                    "fixed sleep, since the probe's real per-signal HTTP "
                    "round-trip cost is what this story's first run measured "
                    "directly."
                )
                startup_seen = _wait_for_marker_or_exit(
                    loop_proc,
                    loop_stdout_path,
                    loop_stderr_path,
                    marker="periodic monitoring loop",
                    timeout_seconds=180.0,
                )
                print(f"Startup marker observed: {startup_seen}")
                last_signal_ingested = False
                if startup_seen:
                    last_signal_key = iteration_order_signal_keys[-1]
                    print(
                        f"Polling for the LAST signal in build order "
                        f"({last_signal_key!r}) to ingest its first row -- "
                        "run_periodic's first pass runs every signal's "
                        "run_cycle sequentially before any coroutine reaches "
                        "its own first `await asyncio.sleep`, so this is the "
                        "adaptive replacement for a padded fixed sleep "
                        f"(up to {loop_wait_seconds}s)."
                    )
                    last_signal_ingested = _wait_for_last_signal_ingested(
                        api_base=api_base,
                        last_signal_key=last_signal_key,
                        since=(run_start - timedelta(minutes=5)).isoformat(),
                        timeout_seconds=loop_wait_seconds,
                    )
                    print(f"Last signal ingested: {last_signal_ingested}")
                    if last_signal_ingested:
                        # Small settle buffer: orchestrate_signal/decide still
                        # run (control-table reads/writes) after the LAST
                        # signal's observation batch is fully readable, before
                        # its coroutine reaches its own first
                        # `await asyncio.sleep`.
                        time.sleep(2.0)

                loop_teardown = _terminate_and_verify(loop_proc, name="loop")
                loop_teardown["startup_marker_observed"] = startup_seen
                loop_teardown["last_signal_ingested_before_terminate"] = (
                    last_signal_ingested
                )
            evidence["loop_teardown"] = loop_teardown
            print(f"Loop terminated: {loop_teardown}")

            loop_stdout_text = loop_stdout_path.read_text(encoding="utf-8")
            loop_stderr_text = loop_stderr_path.read_text(encoding="utf-8")
            evidence["ac4_vendor_health"] = _collect_ac4_evidence(
                loop_stdout_text + loop_stderr_text, all_signal_keys
            )

            run_end = datetime.now(timezone.utc)
            evidence["ac3_ingest"] = _collect_ac3_evidence(
                api_base=api_base,
                signal_keys=all_signal_keys,
                component_ids=all_component_ids,
                run_start=run_start,
                run_end=run_end,
            )
            evidence["ac5_approvals"] = _collect_ac5_evidence(api_base=api_base)

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
    # dict passed to Popen (the API resolved it via settings.py:32 with no
    # `config_dir` argument, exactly as `asgi.py` boots it).
    result["config_dir_api"] = api_env["CONFIG_DIR"]
    assert result["config_dir_api"].replace("\\", "/").endswith("config/demo"), (
        f"AC1(a) FAILED: API CONFIG_DIR={result['config_dir_api']!r}"
    )

    # AC1(b): DYNAMO_ENDPOINT_URL + table names, recorded from the same env.
    result["dynamo_endpoint_url"] = api_env["DYNAMO_ENDPOINT_URL"]
    result["observations_table"] = api_env["DYNAMO_OBSERVATIONS_TABLE"]
    result["control_table"] = api_env["DYNAMO_CONTROL_TABLE"]
    assert result["dynamo_endpoint_url"], "AC1(b) FAILED: DYNAMO_ENDPOINT_URL unset"
    assert result["observations_table"] not in (
        "uptime-observations",
        "uptime-monitor-observations",
    )
    assert result["control_table"] not in ("uptime-control", "uptime-monitor-control")

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
    guard_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "backend/tests/test_demo_fleet_config.py",
            "-q",
        ],
        cwd=str(REPO_ROOT),
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


if __name__ == "__main__":
    evidence = run_positive_side()
    print()
    print("=" * 78)
    print("REALITY GATE 182 SIDE 1 (positive) -- EVIDENCE SUMMARY")
    print("=" * 78)
    import json

    print(json.dumps(evidence, indent=2, default=str))
