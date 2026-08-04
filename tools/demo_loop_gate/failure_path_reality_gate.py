"""STORY-191 reality gate — a REAL loop run that drives DOWN, DEGRADED, a
quarantined poison row, and a genuine recovery PUBLISH through the demo fleet.

This is the story's evidence of record. It is deliberately NOT a pytest
module: AC3 requires the *real, unmodified* ``python -m src.composition.run``
to ingest these scenarios as an OS subprocess, which is what
``harness.py::run_positive_side`` does. An in-process test that merely calls
``expand_scenario`` and asserts on the returned dicts proves the scenario
player works — it proves nothing about the loop, and would have passed even
while ``harness.py`` was un-runnable.

WHAT IT ASSERTS, all from PERSISTED STATE (never parsed log text):

  AC3  a DOWN verdict for the down-ladder signal
  AC4  DEGRADED, and a partial-breadth cycle distinguished by PER-LOCATION
       observation health -- NOT by the verdict, because ``_collapse_health``
       (``pipeline.py:85-98``) maps both "all degraded" and "a mix" to
       ``Health.DEGRADED``, so their verdicts are IDENTICAL and asserting on
       them would be a test that cannot fail for the right reason
  AC5  the poison row quarantined while its four good locations still ingest
  AC6  a recovery publish that FIRED, and nothing that LEFT the process

AC6 IS TWO-SIDED ON PURPOSE. Either half alone is worthless:

  * "publications table is empty" alone is satisfied by a run in which the
    publish path never executed at all -- which is exactly the state every
    previous sprint was in, and would let this gate pass while proving
    nothing about the guard.
  * "a recovery was decided" alone says nothing about whether a real
    Statuspage call went out.

Together they discriminate: the component's stored status changing
MAJOR_OUTAGE -> OPERATIONAL proves ``StatusWritebackPublisher.publish``
(``publish_helper.py:179``, the ONLY writer of component status) actually
ran, while an empty publications table proves the chain was the
``LoggingPublisher`` fallback -- because ``RecordingPublisher``
(``publish_helper.py:212-227``) writes a publications row on EVERY attempt
and exists ONLY in the credentialed+mapping chain.

SAFETY. The publish path genuinely fires here, for the first time in this
repo's history. Nothing reaches the live Statuspage because ``config/demo``
declares no ``statuspage_component_id``, so ``Config.statuspage_mapping()``
is ``{}`` and ``build_publisher`` (``publish_helper.py:211``) falls through to
``LoggingPublisher`` EVEN WITH REAL CREDENTIALS PRESENT. ``run_positive_side``
sets ``CONFIG_DIR=config/demo`` on BOTH subprocesses (the loop and the API),
which is the actual guard; the fake vendor credentials it also injects are
defence in depth, never the guard.

Usage:
    python tools/demo_loop_gate/failure_path_reality_gate.py
    python tools/demo_loop_gate/failure_path_reality_gate.py --self-test

``--self-test`` feeds every assertion deliberately BAD evidence and requires
each one to raise. A gate that has only ever been seen passing is not
evidence (working agreement A7, sprint-64 retro).

Exit codes: 0 PASS, 1 FAIL.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_ROOT = REPO_ROOT / "tools"
BACKEND_ROOT = REPO_ROOT / "backend"
for _p in (str(TOOLS_ROOT), str(BACKEND_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import boto3  # noqa: E402
from demo_engine.scenario import load_scenario_file  # noqa: E402
from src.adapters.persistence.dynamo_component_repository import (  # noqa: E402
    DynamoComponentRepository,
)
from src.composition.settings import Settings  # noqa: E402
from src.core.domain.status import ComponentStatus  # noqa: E402

from demo_loop_gate.harness import (  # noqa: E402
    DYNAMO_ENDPOINT_URL,
    RealityGateError,
    run_positive_side,
)

SCENARIO_DIR = REPO_ROOT / "config" / "demo" / "scenarios"

#: The component whose status is pre-set so the recovery branch is reachable.
#: Its signals report all-UP from the fleet-wide coverage store, so `anti_flap`
#: proposes OPERATIONAL (rank 0), which is BETTER than the pre-set MAJOR_OUTAGE
#: (rank 3) -> recovery publish.
#:
#: TWO constraints pin this choice, and both were learned the hard way.
#:
#: 1. It must be a component NO failure scenario touches. `api-gateway` is the
#:    obvious pick and is WRONG: `down-ladder.yaml` drives `api-gateway-health`
#:    DOWN, so its verdict would not be OPERATIONAL and the recovery could never
#:    fire -- AC6 would fail for a reason unrelated to the guard.
#:
#: 2. IT MUST ORCHESTRATE EARLY ENOUGH THAT ITS ROWS ARE STILL IN THE WINDOW.
#:    This one cost a full run. `orchestrate_signal` looks back
#:    `since = until - (max_threshold + 2) * interval` (`orchestrate.py:96-98`)
#:    where `until = clock.now()` AT ORCHESTRATE TIME, while the fleet store's
#:    rows are PAST-ANCHORED to `run_start` and span only `(cycles-1) * interval`
#:    backwards. So with `T = orchestrate_time - run_start`, keeping the >= 2
#:    cycles that `recovery: 2` needs requires:
#:
#:        T <= (max_threshold + 2 - (cycles - 1)) * interval  ==  6 * interval
#:
#:    for this fleet (max_threshold 5, cycles 5). The loop probes vendor health
#:    for all 41 signals and then runs each signal's cycle sequentially, so T
#:    grows with a signal's position in build order. `billing-service` sits at
#:    index 30/41 with 30s signals -> only 180s of tolerance, and its rows had
#:    aged out of the window by the time it orchestrated: streak < 2, anti_flap
#:    proposed nothing, decide NOOPed, and AC6(a) failed with the component
#:    still MAJOR_OUTAGE while every observation had ingested perfectly.
#:
#:    `cdn-edge` is the earliest untouched component (index 16) carrying a 60s
#:    signal -> 360s of tolerance, twice the margin of any 30s alternative.
#:
#: If AC6(a) ever fails again with all other assertions passing, SUSPECT THIS
#: ARITHMETIC FIRST -- the symptom (status unchanged) is identical whether the
#: guard is broken or the rows merely aged out.
RECOVERY_COMPONENT_ID = "cdn-edge"
PRE_SET_STATUS = "major_outage"
EXPECTED_RECOVERED_STATUS = "operational"

#: Scenario file -> the signal key it declares. Kept explicit so an assertion
#: failure names the scenario a human authored, not just a signal key.
FAILURE_SCENARIOS = {
    "down-ladder": ("down-ladder.yaml", "api-gateway-health"),
    "partial-breadth": ("partial-breadth.yaml", "auth-service-login"),
    "degraded-ladder": ("degraded-ladder.yaml", "payments-service-charge"),
    "poison-row": ("poison-row.yaml", "search-service-query"),
}
POISON_SIGNAL_KEY = "search-service-query"


#: MUST match `make_dynamo_resource` (`composition/dynamo.py:20-24`) exactly.
#:
#: DynamoDB Local namespaces tables by (access key, region) unless it was
#: started with `-sharedDb` -- and this project's container is not. So a client
#: using different dummy credentials than the app sees a DIFFERENT, EMPTY
#: namespace: `list_tables()` returns `[]` and every read raises
#: `ResourceNotFoundException: Cannot do operations on a non-existent table`,
#: even though the tables plainly exist and the harness just logged them ACTIVE.
#: Cost the first run of this gate; kept here so the next reader does not pay it
#: again.
_DUMMY_LOCAL_CREDENTIAL = "test"
_REGION = Settings.aws_region


def _dynamo():
    return boto3.resource(
        "dynamodb",
        endpoint_url=DYNAMO_ENDPOINT_URL,
        region_name=_REGION,
        aws_access_key_id=_DUMMY_LOCAL_CREDENTIAL,
        aws_secret_access_key=_DUMMY_LOCAL_CREDENTIAL,
    )


def _component_repo(control_table: str) -> DynamoComponentRepository:
    """Both the write and the read go through the REAL repository.

    This is not fastidiousness -- hand-rolled keys silently broke this gate.
    The first version used `pk=COMPONENT#<id>, sk=META`; the repository actually
    uses `pk=TOPOLOGY, sk=COMPONENT#<id>`
    (STORY-205: `adapters/persistence/topology_keys.py::component_item_key`, the
    single declaration `DynamoComponentRepository` and `seed_topology_dynamo` both
    import -- previously `dynamo_component_repository.py:36-41`, a citation
    STORY-199's pagination loops had already displaced by the time this was
    re-derived). So the write created a PHANTOM item nothing reads, and the
    read-back "verified" it against the SAME wrong key -- the AC6(a) precondition
    passed VACUOUSLY while the real component sat untouched at `operational`.
    `decide` then correctly declined to publish (there was nothing to recover
    from) and this gate reported the guard as broken. Two full runs were spent
    chasing a defect that did not exist.

    Going through the repository makes that class of drift impossible: if the
    schema changes, this gate follows it by construction.
    """
    return DynamoComponentRepository(_dynamo(), control_table)


def _set_component_status(
    *, control_table: str, component_id: str, status: str
) -> None:
    _component_repo(control_table).set_status(component_id, ComponentStatus(status))


def _get_component_status(*, control_table: str, component_id: str) -> str | None:
    component = _component_repo(control_table).get(component_id)
    return None if component is None else component.status.value


def _count_publications(*, control_table: str) -> int:
    """Count publication rows in the control table.

    A scan is acceptable here: these are throwaway per-run tables holding a
    few hundred items, and the count must be exact rather than paged-and-
    estimated -- an undercount would turn AC6's "nothing left the process"
    into a false pass.
    """
    table = _dynamo().Table(control_table)
    total, kwargs = 0, {}
    while True:
        resp = table.scan(**kwargs)
        total += sum(1 for it in resp.get("Items", []) if it.get("pk") == "PUBLICATION")
        if "LastEvaluatedKey" not in resp:
            return total
        kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]


def _observations_for(*, observations_table: str, signal_key: str) -> list[dict]:
    """All persisted observation rows for one signal (pk = SIG#<key>)."""
    from boto3.dynamodb.conditions import Key

    table = _dynamo().Table(observations_table)
    items, kwargs = [], {"KeyConditionExpression": Key("pk").eq(f"SIG#{signal_key}")}
    while True:
        resp = table.query(**kwargs)
        items.extend(resp.get("Items", []))
        if "LastEvaluatedKey" not in resp:
            return items
        kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]


def _rejected_count(*, control_table: str, signal_key: str) -> int:
    """Quarantined rows for one signal (pk = REJECTED#<key>, control table)."""
    from boto3.dynamodb.conditions import Key

    table = _dynamo().Table(control_table)
    resp = table.query(
        KeyConditionExpression=Key("pk").eq(f"REJECTED#{signal_key}"),
        Select="COUNT",
    )
    return int(resp.get("Count", 0))


# ---------------------------------------------------------------------------
# Assertions -- each raises RealityGateError with a message naming the evidence
# ---------------------------------------------------------------------------


def assert_recovery_published(evidence: dict) -> None:
    """AC6 side (a): the recovery publish FIRED, proven by persisted status."""
    hook = evidence.get("pre_loop_hook") or {}
    before = hook.get("status_after_preset")
    after = evidence.get("status_after_run")
    if before != PRE_SET_STATUS:
        raise RealityGateError(
            f"AC6(a) FAILED: precondition not established -- component "
            f"{RECOVERY_COMPONENT_ID!r} status was {before!r}, expected "
            f"{PRE_SET_STATUS!r}. Without it the recovery branch is "
            "unreachable and the rest of AC6 proves nothing."
        )
    if after != EXPECTED_RECOVERED_STATUS:
        raise RealityGateError(
            f"AC6(a) FAILED: component {RECOVERY_COMPONENT_ID!r} status is "
            f"{after!r}, expected {EXPECTED_RECOVERED_STATUS!r}. "
            "StatusWritebackPublisher.publish (publish_helper.py:179) is the "
            "ONLY writer of component status, so an unchanged status means the "
            "recovery publish never executed -- the guard was never under load. "
            "TWO CAUSES LOOK IDENTICAL HERE, so check the cheap one FIRST: if "
            "every other assertion passed, the likely cause is NOT a broken "
            "guard but the orchestrate WINDOW -- this component's past-anchored "
            "rows aged out before its signal orchestrated, so anti_flap saw a "
            "streak < recovery and proposed nothing. See RECOVERY_COMPONENT_ID's "
            "comment for the arithmetic."
        )


def assert_nothing_published_outward(evidence: dict) -> None:
    """AC6 side (b): nothing LEFT the process, proven by an empty publications table."""
    count = evidence.get("publications_count")
    if count != 0:
        raise RealityGateError(
            f"AC6(b) FAILED: publications table holds {count!r} row(s), expected 0. "
            "RecordingPublisher (publish_helper.py:212-227) writes a row on EVERY "
            "attempt and exists ONLY in the credentialed+mapping chain -- so a "
            "non-zero count means the publisher was NOT the LoggingPublisher "
            "fallback and a real Statuspage call may have gone out."
        )


def assert_down_reached(evidence: dict) -> None:
    """AC3: a DOWN observation reached the domain through the real loop."""
    healths = evidence.get("observed_healths") or {}
    if "down" not in {h.lower() for h in healths.get("down-ladder", [])}:
        raise RealityGateError(
            f"AC3 FAILED: no DOWN observation persisted for the down-ladder "
            f"signal; observed {healths.get('down-ladder')!r}. The failure path "
            "did not reach the domain through the real ingest path."
        )


def assert_degraded_reached(evidence: dict) -> None:
    """AC4 part 1: DEGRADED travelled the real path."""
    healths = evidence.get("observed_healths") or {}
    if "degraded" not in {h.lower() for h in healths.get("degraded-ladder", [])}:
        raise RealityGateError(
            f"AC4 FAILED: no DEGRADED observation persisted; observed "
            f"{healths.get('degraded-ladder')!r}."
        )


def assert_partial_breadth_is_mixed(evidence: dict) -> None:
    """AC4 part 2: partial breadth distinguished PER LOCATION, not by verdict.

    `_collapse_health` (pipeline.py:85-98) maps both "all degraded" and "a mix"
    to Health.DEGRADED, so the verdicts are identical and asserting on them
    would be a check that cannot fail for the right reason.
    """
    healths = {
        h.lower()
        for h in (evidence.get("observed_healths") or {}).get("partial-breadth", [])
    }
    if not ({"down", "up"} <= healths):
        raise RealityGateError(
            f"AC4 FAILED: partial-breadth signal did not persist BOTH a down and "
            f"an up location in the same window; observed {sorted(healths)!r}."
        )


def assert_poison_quarantined(evidence: dict) -> None:
    """AC5: the poison row was quarantined and its good locations still ingested."""
    locs = evidence.get("poison_signal_locations")
    if locs is None or locs < 4:
        raise RealityGateError(
            f"AC5 FAILED: poison-row signal ingested {locs!r} distinct locations, "
            "expected >= 4. A quarantined row must cost only itself -- fewer than "
            "4 means the poison took good rows with it, which is the STORY-190 "
            "defect resurfacing."
        )
    if not evidence.get("poison_row_rejected"):
        raise RealityGateError(
            "AC5 FAILED: no rejected-observation row recorded for the poison "
            "code. Quarantine must PERSIST the bad row, not silently drop it."
        )


ASSERTIONS = [
    assert_down_reached,
    assert_degraded_reached,
    assert_partial_breadth_is_mixed,
    assert_poison_quarantined,
    assert_recovery_published,
    assert_nothing_published_outward,
]


def self_test() -> bool:
    """Feed every assertion deliberately BAD evidence; each MUST raise (A7)."""
    good = {
        "pre_loop_hook": {"status_after_preset": PRE_SET_STATUS},
        "status_after_run": EXPECTED_RECOVERED_STATUS,
        "publications_count": 0,
        "observed_healths": {
            "down-ladder": ["down"],
            "degraded-ladder": ["degraded"],
            "partial-breadth": ["down", "up"],
        },
        "poison_signal_locations": 4,
        "poison_row_rejected": True,
    }
    bad_cases = [
        (
            "down never reached",
            {
                **good,
                "observed_healths": {**good["observed_healths"], "down-ladder": ["up"]},
            },
        ),
        (
            "degraded never reached",
            {
                **good,
                "observed_healths": {
                    **good["observed_healths"],
                    "degraded-ladder": ["up"],
                },
            },
        ),
        (
            "breadth not mixed",
            {
                **good,
                "observed_healths": {
                    **good["observed_healths"],
                    "partial-breadth": ["down"],
                },
            },
        ),
        ("poison took good rows", {**good, "poison_signal_locations": 3}),
        ("poison silently dropped", {**good, "poison_row_rejected": False}),
        (
            "precondition never established",
            {**good, "pre_loop_hook": {"status_after_preset": "operational"}},
        ),
        ("recovery never fired", {**good, "status_after_run": PRE_SET_STATUS}),
        ("something was published outward", {**good, "publications_count": 1}),
    ]

    print("=" * 78)
    print("STORY-191 REALITY GATE -- SELF-TEST (every assertion on BAD evidence)")
    print("=" * 78)

    ok = True
    for fn in ASSERTIONS:
        try:
            fn(good)
        except RealityGateError as exc:
            print(f"  [X] {fn.__name__} rejected GOOD evidence: {exc}")
            ok = False
        else:
            print(f"  [ok] {fn.__name__} accepts good evidence")

    for label, bad in bad_cases:
        raised = []
        for fn in ASSERTIONS:
            try:
                fn(bad)
            except RealityGateError:
                raised.append(fn.__name__)
        if raised:
            print(f"  [ok] {label!r} -> rejected by {', '.join(raised)}")
        else:
            print(f"  [X] {label!r} -> NO assertion raised; this gate cannot fail here")
            ok = False

    print()
    print(f"SELF-TEST: {'PASS' if ok else 'FAIL'}")
    return ok


def _pre_loop_hook(*, control_table: str, api_base: str) -> dict:
    """Establish AC6's precondition and report what was actually persisted."""
    _set_component_status(
        control_table=control_table,
        component_id=RECOVERY_COMPONENT_ID,
        status=PRE_SET_STATUS,
    )
    # Read it BACK rather than trusting the write -- the whole point of AC6(a)
    # is that the "before" state is real, and an unverified write would make a
    # later unchanged-status failure indistinguishable from a never-set one.
    return {
        "component_id": RECOVERY_COMPONENT_ID,
        "status_after_preset": _get_component_status(
            control_table=control_table, component_id=RECOVERY_COMPONENT_ID
        ),
        "control_table": control_table,
    }


def main(argv: list[str] | None = None) -> bool:
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return self_test()

    scenarios = []
    for label, (filename, expected_signal_key) in FAILURE_SCENARIOS.items():
        loaded = load_scenario_file(SCENARIO_DIR / filename)
        keys = {s.signal_key for s in loaded}
        if expected_signal_key not in keys:
            # Fail here rather than 40 minutes later with a confusing empty
            # result: if a scenario file is re-pointed at a different signal,
            # every assertion below would query a signal the run never touched
            # and report "no DOWN observation" as though the LOOP were broken.
            print(
                f"FAIL: {filename} declares {sorted(keys)!r}, but this gate "
                f"expects {expected_signal_key!r} for {label!r}. Update "
                "FAILURE_SCENARIOS."
            )
            return False
        scenarios.extend(loaded)
    print(
        f"Loaded {len(scenarios)} failure scenario(s) from "
        f"{len(FAILURE_SCENARIOS)} file(s)."
    )

    try:
        evidence = run_positive_side(
            extra_scenarios=scenarios,
            pre_loop_hook=_pre_loop_hook,
        )
    except Exception as exc:  # noqa: BLE001
        # Deliberately broad. A7 requires this artifact to end with an explicit
        # verdict and a non-zero exit -- an unhandled traceback is neither. The
        # first run of this gate died on a botocore ResourceNotFoundException
        # (not a RealityGateError), printed a stack trace, and reported no
        # verdict at all; catching only the "expected" types is precisely how a
        # proof harness ends up with no answer.
        print()
        print("=" * 78)
        print("STORY-191 REALITY GATE -- FAIL (harness raised)")
        print("=" * 78)
        print(f"  {type(exc).__name__}: {exc}")
        return False

    control_table = evidence["control_table"]
    observations_table = evidence["observations_table"]

    evidence["status_after_run"] = _get_component_status(
        control_table=control_table, component_id=RECOVERY_COMPONENT_ID
    )
    evidence["publications_count"] = _count_publications(control_table=control_table)

    # Read every assertion's evidence straight out of the tables the loop
    # wrote, AFTER the subprocesses are gone. The throwaway tables outlive the
    # run, so this is persisted state by construction -- there is no log
    # parsing anywhere in this gate (working agreement A7).
    observed: dict[str, list[str]] = {}
    for label, (_file, signal_key) in FAILURE_SCENARIOS.items():
        rows = _observations_for(
            observations_table=observations_table, signal_key=signal_key
        )
        observed[label] = sorted({str(r.get("health")) for r in rows})
        print(f"  {label} ({signal_key}): healths={observed[label]} rows={len(rows)}")
    evidence["observed_healths"] = observed

    poison_rows = _observations_for(
        observations_table=observations_table, signal_key=POISON_SIGNAL_KEY
    )
    evidence["poison_signal_locations"] = len(
        {str(r.get("location")) for r in poison_rows}
    )
    evidence["poison_row_rejected"] = (
        _rejected_count(control_table=control_table, signal_key=POISON_SIGNAL_KEY) > 0
    )
    print(
        f"  poison signal: {evidence['poison_signal_locations']} distinct locations "
        f"ingested, rejected_rows={evidence['poison_row_rejected']}"
    )

    failures = []
    for fn in ASSERTIONS:
        try:
            fn(evidence)
        except RealityGateError as exc:
            failures.append(str(exc))

    print()
    print("=" * 78)
    print("STORY-191 REALITY GATE -- " + ("FAIL" if failures else "PASS"))
    print("=" * 78)
    for f in failures:
        print(f"  {f}")
    if not failures:
        print(
            f"  component {RECOVERY_COMPONENT_ID!r}: "
            f"{PRE_SET_STATUS} -> {evidence['status_after_run']} (recovery publish FIRED)"
        )
        print(
            f"  publications rows: {evidence['publications_count']} (nothing left the process)"
        )
    return not failures


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
