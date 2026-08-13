---
id: STORY-224
title: An entire second test suite exists and the DoD gate does not run it — 7 skill-level modules, including the two guards that have already caught real defects
type: defect
points: 3
status: ready
refined: 2026-08-14   # sprint-72 planning; shape decided on measurement below. PENDING PO lock.
filed: 2026-08-13
sprint: null
---

## Context

Found 2026-08-13 by the sprint-71 pre-lock plan verifier, while checking a claim in STORY-192
about where a new encoding guard should live. The claim turned out to be false, and the reason it
was false is bigger than the story that raised it.

## The finding

**`.claude/skills/yourteam/scripts/tests/` holds 7 test modules that no DoD gate command executes.**

```
test_backlog_story_parity.py   test_scrum_encoding.py   test_template_parity.py
test_yt_board.py   test_yt_gate.py   test_yt_git_guard.py   test_yt_wiki.py
```

- `pyproject.toml:29` — `testpaths = ["backend/tests"]`
- `python -m pytest --collect-only -q` → **800 tests collected, zero from `.claude/`**
- The 8 DoD commands (`.scrum/definition-of-done.md`) are: pytest, import-linter, ruff check,
  ruff format, cfn-lint, npm test, npm build, npm lint. **`yt_selftest.py` is not among them.**

They are not dead — `yt_selftest.py:25-33` discovers and runs all of them via `unittest`
discovery. But **`yt_selftest` runs only when a human or an orchestrator remembers to invoke it.**
It is a habit, not a floor.

## Why this is not a filing-cabinet problem

Two of these modules have **already caught real defects, both times by luck of someone running the
script**:

1. **`test_template_parity.py`, sprint 70.** Amendment A19 was landed in the three
   `.claude/agents/*.md` instances but not in the skill templates they re-sync from. Left alone,
   A19 would have **silently reverted at the next standup re-sync** — a rule that appears to exist,
   does not fire, and nobody notices.
2. **`test_scrum_encoding.py`, STORY-188.** The guard for the `.scrum/` mojibake class. It is the
   thing standing between the repo and a recurrence — and no gate runs it.

A guard that runs only when someone remembers is judgement wearing a guard's clothes. **This is the
same defect class as STORY-178's `--only` false green** — the difference is that 178 ran and
reported the wrong answer, while these do not run at all.

## *** Shape DECIDED at sprint-72 refinement: (a), a 9th DoD command — on measurement ***

The filing listed three shapes. They were measured on 2026-08-14 and the answer is not close:

| Shape | Files it must edit | Wiki blast radius (measured) |
| --- | --- | --- |
| **(a) add `yt_selftest.py` as a 9th DoD command** | `.scrum/definition-of-done.md`, `CLAUDE.md` | **ZERO** — `.scrum/definition-of-done.md` and `.claude/skills/yourteam/scripts/yt_gate.py` are in **no** article's `code_refs` |
| (b) extend `testpaths` | `pyproject.toml` | **FOUR verified map articles** — `api-five-file-convention.md`, `architecture-boundary.md`, `config-layer.md`, `sample-mode.md`; A18 forces each re-verified in-story |
| (c) mirror repo-scope guards into `backend/tests/` | new/moved test files | splits the suite and leaves `test_template_parity` — the A19 catcher, the more valuable of the two — outside the gate |

**(b)'s hidden cost is larger than the fix**, exactly as the filing suspected; it is now measured
rather than suspected. **(c)** fixes the smaller half. **(a)** it is.

Supporting measurements at HEAD `fa5507d` (2026-08-14):

- `yt_selftest.py` exits **0**, **89 tests in 4.84s** — cheap enough to run on every gate.
- It is stdlib-only and needs no new dependency (no mid-sprint tooling-freeze problem).
- `yt_gate.py` parses DoD command lines with
  `CMD_RE = ^\s*-\s*\[[ xX]\]\s*(.+?):\s*`([^`]+)`` (`yt_gate.py:57`) and runs each with
  `cwd = root / entry["cwd"]`, where `cwd` comes from a `run from \`dir/\`` phrase on the section
  heading (`yt_gate.py:63, 298`). A backend-section line therefore runs from the repo root.

## *** The `.scrum/` edit belongs to the ORCHESTRATOR, not the implementer ***

`.scrum/definition-of-done.md` is orchestrator-owned; subagents never write `.scrum/` — including
via `git stash` (sprint-71 retro §3a). This is the STORY-222 AC7 precedent: that story's `.scrum/`
edit was reassigned to the orchestrator at pre-lock, and the implementer was told not to touch the
file. Same split here. AC1 is verified by the orchestrator's edit plus a gate run; everything else
is the implementer's.

## Acceptance Criteria

- [ ] **AC1 (the self-test is a gate command)** — after the orchestrator adds the DoD line,
      `yt_gate.py` discovers exactly **9** commands and the 9th invokes `yt_selftest.py`. Proven by
      a full gate run recording **9/9**. The implementer does **not** edit `.scrum/`.
- [ ] **AC2 (invocation survives this machine's policy)** — the command uses interpreter form
      (`python .claude/skills/yourteam/scripts/yt_selftest.py` or the venv interpreter), never a
      console-script shim: three shims are already blocked by Windows Device Guard and the policy
      has widened twice mid-sprint unannounced (`CLAUDE.md` Key commands, STORY-210). It runs from
      the **repo root**, matching how `yt_gate.py` invokes backend-section commands.
- [ ] **AC3 (*** the proof that matters ***: the GATE now catches what it could not)** — shown RED
      **at the gate, not at `yt_selftest`**. The defect is "the gate does not run it", so a proof
      that only shows `yt_selftest` failing proves nothing new. Break one guarded invariant — e.g.
      introduce a cp1252-mojibake sequence into a `.scrum/` file, or drop a rule from one
      `.claude/agents/*.md` instance so template parity breaks — and show **the full gate exits
      nonzero**, where the same mutation at the pre-story commit left the gate green. Do it in a
      scratch clone (A19: every scratch `cd` written `cd X || exit 1`), and revert.
- [ ] **AC4 (all 7 modules actually run, and a module silently dropping is caught)** — the report
      names each of the 7 modules with its test count, summing to the total (89 at refinement).
      Because `unittest` discovery fails **silently** when a module stops being discovered — an
      import error or a rename makes the count drop, not the run fail — `yt_selftest.py` gains an
      assertion that the discovered module count is **at least 7**. Shown RED by removing one
      module in a scratch clone.
- [ ] **AC5 (the gate does not red on bookkeeping)** — the skill suite asserts about *this repo's*
      content in places (`test_scrum_encoding`, `test_backlog_story_parity`), so it must not turn
      routine board state into a gate failure. `test_backlog_story_parity` currently emits its
      28-missing-story-file finding as an advisory **note** with exit 0; that stays advisory.
      Proven both ways in a scratch clone: adding a fresh draft entry with no story file leaves
      the gate **green**, while a genuine parity breach still fails it.
- [ ] **AC6 (runtime is recorded and bounded)** — measure the added wall-clock across ≥3 runs
      (4.84s at refinement). The gate runs many times per sprint, so if it exceeds ~15s the story
      **reports the number and flags it** rather than absorbing it.
- [ ] **AC7 (ride-along: the parity filter uses the full closed set)** —
      `test_backlog_story_parity.py:155` filters on `status != "done"` instead of the closed set,
      so 22 archived stories sit permanently in the "refinement should write one" advisory. Reuse
      `yt_board.py:68`'s `CLOSED_STATUSES` rather than declaring a second list. Shown RED: the
      advisory count drops by those entries.
- [ ] **AC8 (ride-along: `next_story_id` is asserted)** — add a `yt_selftest` assertion that
      `next_story_id > max(id)` across backlog stories. It has been stale three times.
- [ ] **AC9 (the count of record moves 8 → 9, everywhere it is stated)** — `CLAUDE.md:194`
      ("### The DoD gate — 8 commands") and its backend/frontend breakdown, plus
      `.scrum/definition-of-done.md` (orchestrator). **Grep for other copies before committing**
      (STORY-189's lesson, which found one). Known: `frontend-zone.md:21` and `:617` state the
      five/three/eight breakdown, and that article is `status: stale` and **not swept** — touching
      it would reset its staleness baseline without re-verifying 35 Facts, which the protocol
      forbids. Leave it, and say in the report that it was left and why.
- [ ] **AC10 (gate)** — the full **9-command** gate is green at the story's final HEAD, with pass
      counts recorded (a nonzero skip count is an incomplete gate, not a pass). Run the wiki sweep
      after the last commit and take what it returns.

## Open Questions

None. The filing's four refinement questions are settled: shape (a) on measured blast radius;
repo-scope vs skill-scope is moot under (a) since all 7 run; runtime measured at 4.84s; and the
modules pass standalone at HEAD (exit 0, 89 tests) — AC5 covers the clean-checkout concern that
remained.

## Not in scope

Writing new guards. STORY-192's mojibake repair (it depends on this story's answer for where its
new check lands, and that answer is now "inside the gate either way"). Changing what any existing
skill test asserts — AC7 changes a **filter** whose current value is a stated defect, not an
assertion.

## History

- 2026-08-13: filed by the sprint-71 pre-lock plan verifier.
- 2026-08-14: **refined at sprint-72 planning, estimated 3.** Shape (a) chosen on a measured
  blast-radius comparison (0 articles vs 4) rather than on the filing's bias. The code change is
  small; the estimate is carried by AC3 and AC5, which are proof work, not typing. Two owed
  one-liners were folded in as AC7/AC8 rather than becoming stories of their own — both live in
  the files this story already opens.
