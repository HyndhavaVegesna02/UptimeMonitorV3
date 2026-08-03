"""ZR-3 standing guard (STORY-197): promotes `tools/zr3_duplicate_sweep.py`
(STORY-196, `docs/scrum/wiki/zone-rules.md` ZR-3) from a report-only script to a
pytest test that fails the DoD gate on any NEW, unadjudicated `tools/`<->`backend/src/`
duplicated declaration.

Cites: `docs/scrum/wiki/zone-rules.md` ZR-3 (a value DECLARED in `backend/src/` -- a
module-level UPPER_CASE constant, or a settings/config field default -- must be
IMPORTED by `tools/`, never re-declared) and its Coverage verdict, which names this
exact promotion ("STORY-197 may promote it to a standing test"). Every adjudication
below originally reproduced `docs/scrum/sprints/2026-07-31-sprint-66/
audit-api-composition-tools.md` §3c's ledger (15 collisions at STORY-197's HEAD: 6
`MUST-IMPORT-FROM-SRC`, 9 `INDEPENDENT`/coincidental). **STORY-202 fixed its two
`MUST-IMPORT-FROM-SRC` entries** (`env_matrix.py:75`/`:77`, the Statuspage credential
key names) and re-keyed the three collisions its own edits displaced without
retiring (`env_matrix.py:39`->`:49`, `harness.py:747`->`:754`, `harness.py:750`->
`:757`) plus two `INDEPENDENT` entries similarly displaced (`harness.py:903`->`:910`,
`harness.py:964`->`:971`) -- current count: 13 (4 `MUST-IMPORT-FROM-SRC`, all filed to
STORY-203; 9 `INDEPENDENT`).

Why an adjudicated-exemption list, not a hard zero-tolerance assertion (the
live-violation problem, STORY-197 AC5/C3): the 4 remaining `MUST-IMPORT-FROM-SRC`
collisions are REAL, unfixed ZR-3 violations (STORY-203, filed, not fixed here per C1
-- this story guards, it does not fix). Landing this guard with zero exemptions would
fail the DoD gate on every future story until that fix story lands, which C4 forbids
as a side effect of a guard. So this guard is green today only because every current
collision is named, with a reason, below -- and it fails loudly the moment a NEW,
unadjudicated collision appears anywhere under `tools/`, against anything
`backend/src/` declares in either of ZR-3's two pinned shapes.

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
    ("tools/demo_loop_gate/env_matrix.py", 49): (
        "MUST-IMPORT-FROM-SRC (MINOR): build_child_env's aws_region parameter "
        "default re-declares Settings.aws_region's default a second time. "
        "Fix: STORY-203. (Re-keyed from :39 by STORY-202's own AC2 import "
        "block, which displaced this pre-existing collision without "
        "retiring it -- the collision is unchanged, only its line moved.)"
    ),
    ("tools/demo_loop_gate/failure_path_reality_gate.py", 65): (
        "INDEPENDENT: Path(__file__).resolve().parents[2], same shape as :30 "
        "above, a different file."
    ),
    ("tools/demo_loop_gate/failure_path_reality_gate.py", 149): (
        'MUST-IMPORT-FROM-SRC (MINOR): _REGION = "us-east-1" re-declares '
        "Settings.aws_region's default a second, independent time (a third "
        "hardcode counting env_matrix.py:49, re-keyed from :39 by STORY-202's "
        "own AC2 import block -- see the :49 entry above). Fix: STORY-203."
    ),
    ("tools/demo_loop_gate/failure_path_reality_gate.py", 394): (
        "INDEPENDENT: a self-test fixture value "
        '("poison_signal_locations": 3), unrelated to '
        "FreshnessConfig.stale_after_cycles. (Re-keyed from :390 by STORY-205's "
        "own `_component_repo` docstring edit, which displaced this "
        "pre-existing collision without retiring it -- the collision is "
        "unchanged, only its line moved.)"
    ),
    ("tools/demo_loop_gate/guard_reality_gate.py", 23): (
        "INDEPENDENT: Path(__file__).resolve().parents[2], same shape as above, a "
        "different file."
    ),
    ("tools/demo_loop_gate/harness.py", 49): (
        "INDEPENDENT: Path(__file__).resolve().parents[2], same shape as above, a "
        "different file."
    ),
    ("tools/demo_loop_gate/harness.py", 754): (
        "MUST-IMPORT-FROM-SRC (MINOR): the ZR-3 AC3 reference/demonstration case "
        "-- a defensive blocklist literal duplicating "
        "Settings.dynamo_observations_table's default. Fix: STORY-203. "
        "(Re-keyed from :747 by STORY-202's own harness.py edits, which "
        "displaced this pre-existing collision without retiring it.)"
    ),
    ("tools/demo_loop_gate/harness.py", 757): (
        "MUST-IMPORT-FROM-SRC (MINOR): paired with :754, duplicates "
        "Settings.dynamo_control_table's default. Fix: STORY-203. "
        "(Re-keyed from :750, same cause as :754 above.)"
    ),
    ("tools/demo_loop_gate/harness.py", 910): (
        "INDEPENDENT: dict(list(per_signal.items())[:3]), a slice bound unrelated "
        "to FreshnessConfig.stale_after_cycles. (Re-keyed from :903 by "
        "STORY-202's own harness.py edits, which displaced this pre-existing "
        "collision without retiring it.)"
    ),
    ("tools/demo_loop_gate/harness.py", 971): (
        "INDEPENDENT: print(json.dumps(evidence, indent=2, default=str))'s "
        "indent=2 keyword argument, unrelated to FreshnessConfig.reentry_cycles. "
        "(Re-keyed from :964, same cause as :910 above.)"
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
        "AC3 demonstration case, harness.py:754/757 vs settings.py:21/22, should "
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
