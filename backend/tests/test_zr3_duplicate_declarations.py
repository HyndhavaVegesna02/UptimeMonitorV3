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
`harness.py:964`->`:971`) -- count after STORY-202: 13 (4 `MUST-IMPORT-FROM-SRC`, all
filed to STORY-203; 9 `INDEPENDENT`).

**STORY-203 fixed all four remaining `MUST-IMPORT-FROM-SRC` entries.** Two
(`env_matrix.py:49`, `failure_path_reality_gate.py:149`) each hardcoded
`Settings.aws_region`'s `"us-east-1"` default a second time; two
(`harness.py:754`/`:757`) hardcoded `Settings.dynamo_observations_table`/
`dynamo_control_table`'s defaults inside a defensive blocklist (fixed on its
RIGHT-hand side only -- the LEFT stays the real resolved `api_env` read, or the
blocklist becomes a tautology disconnected from the environment it exists to
check; see `backend/tests/demo_loop_gate/test_harness_assertions.py`'s
blocklist-discrimination tests). AC4's fifth, cross-representation case
(`store.py`'s `VENDOR_HEALTH_WINDOW`, invisible to this sweep's
literal-equality comparison) was a DECISION, not a fix: its existing
wire-contract justification is upheld and its entry below is `INDEPENDENT`,
not `MUST-IMPORT-FROM-SRC`. **Current count: 9, all `INDEPENDENT`, zero
`MUST-IMPORT-FROM-SRC` remain.**

Why an adjudicated-exemption list, not a hard zero-tolerance assertion (the
live-violation problem, STORY-197 AC5/C3): every entry below is `INDEPENDENT`
today, but the list stays an adjudication ledger, not a zero-tolerance
assertion -- a future genuine `MUST-IMPORT-FROM-SRC` finding is expected to be
filed here again, the same way STORY-203's four were. So this guard is green
today only because every current collision is named, with a reason, below --
and it fails loudly the moment a NEW, unadjudicated collision appears anywhere
under `tools/`, against anything `backend/src/` declares in either of ZR-3's
two pinned shapes.

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
    ("tools/demo_engine/store.py", 24): (
        "INDEPENDENT (this Constant node only): the bare `2` inside "
        "timedelta(hours=2)'s `hours=` keyword argument. The SEPARATE semantic "
        "finding on the whole VENDOR_HEALTH_WINDOW value (a str/timedelta "
        "cross-representation this sweep's literal-equality comparison cannot see "
        "at all) is ALSO adjudicated INDEPENDENT, not MUST-IMPORT-FROM-SRC "
        "(STORY-203 AC4, a decision rather than a fix): store.py:18-23's own "
        "docstring upholds the wire-contract justification -- the window is "
        "part of the vendor WIRE CONTRACT this engine answers, not an "
        "implementation detail borrowed from "
        "adapters/inbound/dynatrace/query.py's HEALTH_CHECK_WINDOW ('2h', "
        "line 136) -- and that agreement is mechanically pinned by "
        "backend/tests/demo_engine/test_vendor_health_query.py::"
        "test_vendor_health_window_matches_the_composition_health_check_window, "
        "so upholding the justification does not leave the two values "
        "unguarded against silent divergence. (Re-keyed from :22 by "
        "STORY-204's own store.py docstring edit repointing the "
        "_HEALTH_CHECK_WINDOW citation to its new home in "
        "adapters/inbound/dynatrace/query.py, which displaced this "
        "pre-existing collision without retiring it -- the collision is "
        "unchanged, only its line moved.)"
    ),
    ("tools/demo_loop_gate/backfill_reality_gate.py", 31): (
        "INDEPENDENT: Path(__file__).resolve().parents[2], a filesystem-ancestor "
        "index unrelated to FreshnessConfig.reentry_cycles. (Re-keyed from :30 "
        "by STORY-204's own module-docstring edit repointing its "
        "vendor-health-window citation to the relocated adapter builder, which "
        "displaced this pre-existing collision without retiring it.)"
    ),
    ("tools/demo_loop_gate/failure_path_reality_gate.py", 65): (
        "INDEPENDENT: Path(__file__).resolve().parents[2], same shape as :31 "
        "above, a different file."
    ),
    ("tools/demo_loop_gate/failure_path_reality_gate.py", 395): (
        "INDEPENDENT: a self-test fixture value "
        '("poison_signal_locations": 3), unrelated to '
        "FreshnessConfig.stale_after_cycles. (Re-keyed from :390 to :394 by "
        "STORY-205's own `_component_repo` docstring edit; re-keyed again "
        "from :394 to :395 by STORY-203's own failure_path_reality_gate.py "
        "import-block edit (adding `from src.composition.settings import "
        "Settings`), which displaced this pre-existing collision without "
        "retiring it -- the collision is unchanged, only its line moved.)"
    ),
    ("tools/demo_loop_gate/guard_reality_gate.py", 23): (
        "INDEPENDENT: Path(__file__).resolve().parents[2], same shape as above, a "
        "different file."
    ),
    ("tools/demo_loop_gate/harness.py", 49): (
        "INDEPENDENT: Path(__file__).resolve().parents[2], same shape as above, a "
        "different file."
    ),
    ("tools/demo_loop_gate/harness.py", 927): (
        "INDEPENDENT: dict(list(per_signal.items())[:3]), a slice bound unrelated "
        "to FreshnessConfig.stale_after_cycles. (Re-keyed from :903 to :910 by "
        "STORY-202's own harness.py edits, then :910 to :921 by STORY-203's own "
        "harness.py import-block edit (adding `Settings` to the existing "
        "`from src.composition.settings import (...)` block), then :921 to :927 "
        "by STORY-203's own fix-round edit adding failure messages to the "
        "AC1(b) blocklist asserts -- the collision is unchanged, only its line "
        "moved.)"
    ),
    ("tools/demo_loop_gate/harness.py", 988): (
        "INDEPENDENT: print(json.dumps(evidence, indent=2, default=str))'s "
        "indent=2 keyword argument, unrelated to FreshnessConfig.reentry_cycles. "
        "(Re-keyed from :964 to :971, same cause as :927 above, then :971 to "
        "982 by the same STORY-203 harness.py import-block edit, then :982 to "
        "988 by the same STORY-203 fix-round message edit that re-keyed :927.)"
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
        "original AC3 demonstration case, harness.py:754/757 vs settings.py:21/22, "
        "was fixed by STORY-203, but the remaining INDEPENDENT collisions -- e.g. "
        "harness.py:49 vs config.py's FreshnessConfig.reentry_cycles=2 -- should "
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
