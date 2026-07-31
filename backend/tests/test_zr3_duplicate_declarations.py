"""ZR-3 standing guard (STORY-197): promotes `tools/zr3_duplicate_sweep.py`
(STORY-196, `docs/scrum/wiki/zone-rules.md` ZR-3) from a report-only script to a
pytest test that fails the DoD gate on any NEW, unadjudicated `tools/`<->`backend/src/`
duplicated declaration.

Cites: `docs/scrum/wiki/zone-rules.md` ZR-3 (a value DECLARED in `backend/src/` -- a
module-level UPPER_CASE constant, or a settings/config field default -- must be
IMPORTED by `tools/`, never re-declared) and its Coverage verdict, which names this
exact promotion ("STORY-197 may promote it to a standing test"). Every adjudication
below reproduces `docs/scrum/sprints/2026-07-31-sprint-66/audit-api-composition-tools.md`
§3c's ledger (15 collisions at this story's HEAD: 6 `MUST-IMPORT-FROM-SRC`, 9
`INDEPENDENT`/coincidental), not re-derived from scratch.

Why an adjudicated-exemption list, not a hard zero-tolerance assertion (the
live-violation problem, STORY-197 AC5/C3): six of today's fifteen collisions are REAL,
unfixed ZR-3 violations (STORY-202, STORY-203, filed, not fixed here per C1 -- this
story guards, it does not fix). Landing this guard with zero exemptions would fail the
DoD gate on every future story until those fix stories land, which C4 forbids as a side
effect of a guard. So this guard is green today only because every current collision is
named, with a reason, below -- and it fails loudly the moment a NEW, unadjudicated
collision appears anywhere under `tools/`, against anything `backend/src/` declares in
either of ZR-3's two pinned shapes.

Maintenance note for a future author (AC3): a new `tools/` literal or `backend/src/`
declaration that does NOT collide with anything needs no entry at all -- the scan is
automatic. The ONLY manual step is `_ADJUDICATED` below: any NEW collision the sweep
reports must be read (not guessed) and added here as either `MUST-IMPORT-FROM-SRC` (a
real duplication -- fix it or file it, citing the fix story) or `INDEPENDENT`
(coincidental -- state why the two values matching is not a shared declaration). An
unrecognised collision is always a guard FAILURE, never silently accepted.
"""

from __future__ import annotations

from pathlib import Path

import zr3_duplicate_sweep as sweep  # tools/ is on sys.path via backend/tests/conftest.py

_REPO_ROOT = Path(__file__).resolve().parents[2]

# (tools_file, tools_line) -> adjudication. Every collision `sweep.find_collisions`
# reports today is listed here exactly once, reproducing STORY-196's audit ledger.
_ADJUDICATED: dict[tuple[str, int], str] = {
    ("tools/demo_engine/server.py", 244): (
        "INDEPENDENT: self._httpd.server_address[:2], a slice index unrelated to "
        "FreshnessConfig.reentry_cycles."
    ),
    ("tools/demo_engine/store.py", 22): (
        "INDEPENDENT (this Constant node only): the bare `2` inside "
        "timedelta(hours=2)'s `hours=` keyword argument. The SEPARATE semantic "
        "finding on the whole VENDOR_HEALTH_WINDOW value (a str/timedelta "
        "cross-representation this sweep's literal-equality comparison cannot see "
        "at all) is MUST-IMPORT-FROM-SRC, fix: STORY-203."
    ),
    ("tools/demo_loop_gate/backfill_reality_gate.py", 30): (
        "INDEPENDENT: Path(__file__).resolve().parents[2], a filesystem-ancestor "
        "index unrelated to FreshnessConfig.reentry_cycles."
    ),
    ("tools/demo_loop_gate/env_matrix.py", 39): (
        "MUST-IMPORT-FROM-SRC (MINOR): build_child_env's aws_region parameter "
        "default re-declares Settings.aws_region's default a second time. "
        "Fix: STORY-203."
    ),
    ("tools/demo_loop_gate/env_matrix.py", 75): (
        "MUST-IMPORT-FROM-SRC (MAJOR): re-declares STATUSPAGE_PAGE_ID_VAR's value "
        "as an env-dict key instead of importing the constant -- a rename in "
        "settings.py would silently defeat this harness's fake-credential "
        "injection. Fix: STORY-202."
    ),
    ("tools/demo_loop_gate/env_matrix.py", 77): (
        "MUST-IMPORT-FROM-SRC (MAJOR): re-declares STATUSPAGE_API_KEY_VAR's value, "
        "same mechanism and risk as :75. Fix: STORY-202."
    ),
    ("tools/demo_loop_gate/failure_path_reality_gate.py", 65): (
        "INDEPENDENT: Path(__file__).resolve().parents[2], same shape as :30 "
        "above, a different file."
    ),
    ("tools/demo_loop_gate/failure_path_reality_gate.py", 149): (
        'MUST-IMPORT-FROM-SRC (MINOR): _REGION = "us-east-1" re-declares '
        "Settings.aws_region's default a second, independent time (a third "
        "hardcode counting env_matrix.py:39). Fix: STORY-203."
    ),
    ("tools/demo_loop_gate/failure_path_reality_gate.py", 390): (
        "INDEPENDENT: a self-test fixture value "
        '("poison_signal_locations": 3), unrelated to '
        "FreshnessConfig.stale_after_cycles."
    ),
    ("tools/demo_loop_gate/guard_reality_gate.py", 23): (
        "INDEPENDENT: Path(__file__).resolve().parents[2], same shape as above, a "
        "different file."
    ),
    ("tools/demo_loop_gate/harness.py", 49): (
        "INDEPENDENT: Path(__file__).resolve().parents[2], same shape as above, a "
        "different file."
    ),
    ("tools/demo_loop_gate/harness.py", 747): (
        "MUST-IMPORT-FROM-SRC (MINOR): the ZR-3 AC3 reference/demonstration case "
        "-- a defensive blocklist literal duplicating "
        "Settings.dynamo_observations_table's default. Fix: STORY-203."
    ),
    ("tools/demo_loop_gate/harness.py", 750): (
        "MUST-IMPORT-FROM-SRC (MINOR): paired with :747, duplicates "
        "Settings.dynamo_control_table's default. Fix: STORY-203."
    ),
    ("tools/demo_loop_gate/harness.py", 903): (
        "INDEPENDENT: dict(list(per_signal.items())[:3]), a slice bound unrelated "
        "to FreshnessConfig.stale_after_cycles."
    ),
    ("tools/demo_loop_gate/harness.py", 964): (
        "INDEPENDENT: print(json.dumps(evidence, indent=2, default=str))'s "
        "indent=2 keyword argument, unrelated to FreshnessConfig.reentry_cycles."
    ),
}


def test_zr3_sweep_finds_no_unadjudicated_collision() -> None:
    """Guard (STORY-197, ZR-3): every backend/src<->tools/ duplicated-declaration
    collision the sweep finds is adjudicated in `_ADJUDICATED` above (either a real,
    filed finding or a reasoned `INDEPENDENT`/coincidental clearance). A NEW,
    unadjudicated collision -- anywhere under `tools/`, against anything declared
    under `backend/src/` in either of ZR-3's two pinned shapes -- fails this test.
    """
    deduped = sweep.find_collisions(_REPO_ROOT)
    assert deduped, (
        "The sweep found zero collisions -- that would be surprising (STORY-196's "
        "AC3 demonstration case, harness.py:747/750 vs settings.py:21/22, should "
        "still be present) and is more likely a broken scan than a clean tree; "
        "re-check collect_src_declarations/collect_tools_literals before trusting "
        "an empty result."
    )

    unadjudicated = [
        f"value={val!r} SRC: {src_file}:{src_line} [{kind} {name}] "
        f"TOOLS: {tools_file}:{tools_line}"
        for val, src_file, src_line, kind, name, tools_file, tools_line in deduped
        if (tools_file, tools_line) not in _ADJUDICATED
    ]

    assert not unadjudicated, (
        "ZR-3 collision(s) found with no adjudication on record -- a tools/ "
        "literal matches a backend/src/ declared constant/settings default. "
        "Either fix the duplication (import the src symbol) or, if genuinely "
        "coincidental, add a reasoned INDEPENDENT entry to _ADJUDICATED:\n"
        + "\n".join(unadjudicated)
    )


def test_zr3_adjudications_are_still_current() -> None:
    """Every `_ADJUDICATED` entry must still correspond to a real collision the
    sweep finds today. An entry whose collision has vanished means either its fix
    story landed (a `MUST-IMPORT-FROM-SRC` entry -- remove it) or the coincidental
    literal moved/was deleted (an `INDEPENDENT` entry -- also remove it) -- either
    way it should not sit unnoticed and imply a duplication that no longer exists.
    """
    deduped = sweep.find_collisions(_REPO_ROOT)
    found_coords = {(h[5], h[6]) for h in deduped}

    stale = [
        f"{tools_file}:{tools_line} -- adjudication on record but no longer found "
        f"by the sweep"
        for tools_file, tools_line in _ADJUDICATED
        if (tools_file, tools_line) not in found_coords
    ]

    assert not stale, "Stale ZR-3 adjudication(s) -- update _ADJUDICATED:\n" + (
        "\n".join(stale)
    )
