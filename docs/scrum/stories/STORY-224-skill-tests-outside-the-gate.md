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

- [ ] **AC1 (the self-test is a gate command, at a NAMED placement)** — the orchestrator appends a
      **third section, `## Commands (skill self-test)`, AFTER the frontend section**, carrying one
      command line in `yt_gate.py`'s parse shape (`- [ ] <label>: \`<command>\` -> exit 0`) and
      **no `run from \`dir/\`` phrase**, so `section_cwd` stays empty and the command runs from the
      repo root. `yt_gate.py` then discovers exactly **9** commands and the **9th** invokes
      `yt_selftest.py`. Proven by a full gate run recording **9/9**. The implementer does **not**
      edit `.scrum/`.
      **The placement is named because it is the only one that satisfies both this AC and AC2**:
      appending to `## Commands (backend)` makes the self-test command **6 of 9**, not the 9th, and
      silently turns `CLAUDE.md`'s "Backend (5)" into six (pre-lock verification, 2026-08-14, run
      through the real `yt_gate.parse_dod`).
- [ ] **AC2 (invocation survives this machine's policy)** — the command uses interpreter form
      (`python .claude/skills/yourteam/scripts/yt_selftest.py` or the venv interpreter), never a
      console-script shim: three shims are already blocked by Windows Device Guard and the policy
      has widened twice mid-sprint unannounced (`CLAUDE.md` Key commands, STORY-210). It runs from
      the **repo root** — which under AC1's placement is what an absent `run from` phrase gives
      (`yt_gate.py:63, 298`).
- [ ] **AC3 (*** the proof that matters ***: the GATE now catches what it could not)** — shown RED
      **at the gate, not at `yt_selftest`**. The defect is "the gate does not run it", so a proof
      that only shows `yt_selftest` failing proves nothing new. In a scratch clone (A19: every
      scratch `cd` written `cd X || exit 1`), break one guarded invariant — a cp1252-mojibake
      sequence in a `.scrum/` file, or a rule dropped from one `.claude/agents/*.md` instance so
      template parity breaks — and show the full gate exits nonzero, where the same mutation at the
      pre-story commit left it green.
      ***The mutation MUST BE COMMITTED in the scratch clone, and the evidence MUST name the
      failing command's label and its exit code.*** `yt_gate.py` **exits 3 on a dirty tree before
      running any command** (`yt_gate.py:427-437`), and A20 exempts only `.scrum/`
      (`_ORCHESTRATOR_OWNED_PREFIXES`, `yt_gate.py:125`) — so an *uncommitted* mutation outside
      `.scrum/` produces a nonzero exit that proves nothing about the ninth command. An exit 3 is
      not this AC's RED; only a **command failure (exit 1) naming the self-test** is.
- [ ] **AC4 (all 7 modules actually run, and a module silently dropping is caught)** — the report
      names each of the 7 modules with its test count, summing to the total (89 at refinement).
      Because `unittest` discovery fails **silently** when a module stops being discovered — an
      import error or a rename makes the count drop, not the run fail — `yt_selftest.py` gains an
      assertion that the discovered module count is **at least 7**. Shown RED by removing one
      module in a scratch clone.
- [ ] **AC5 (the gate does not red on bookkeeping — and the HARD assertions are the real exposure)**
      — the skill suite asserts about *this repo's* content in places (`test_scrum_encoding`,
      `test_backlog_story_parity`), so it must not turn routine board state into a gate failure.
      Three proofs, in a scratch clone:
      (a) the advisory stays advisory — `test_backlog_story_parity.py:144`'s missing-story-file
          finding is a **note** with exit 0, and adding a fresh draft entry with no story file
          leaves the gate **green**;
      (b) a genuine parity breach still **fails** it;
      (c) *** the two HARD assertions are exercised ***: `test_every_file_pointer_resolves`
          (`test_backlog_story_parity.py:101`) and `test_no_orphan_story_files` (`:119`) are not
          advisory — they fail. So a story file committed before its backlog entry, or a `file:`
          pointer committed before the file it names, **reds the gate for an unrelated story**.
          Prove both directions and state the working rule that follows: **a mid-sprint filing
          lands its backlog entry and its story file in ONE commit.** Sprint 71 filed STORY-224
          itself mid-sprint, so this is a live path, not a hypothetical.
- [ ] **AC6 (runtime is recorded and bounded)** — measure the added wall-clock across ≥3 runs
      (4.84s at refinement). The gate runs many times per sprint, so if it exceeds ~15s the story
      **reports the number and flags it** rather than absorbing it.
- [ ] **AC7 (ride-along: the parity filter uses the full closed set)** —
      `test_backlog_story_parity.py:155` filters on `status != "done"` instead of the closed set,
      so 22 archived stories sit permanently in the "refinement should write one" advisory. Reuse
      `yt_board.py:68`'s `CLOSED_STATUSES` rather than declaring a second list. Shown RED: the
      advisory count drops by those entries.
- [ ] **AC8 (ride-along: `next_story_id` is asserted — and it is RED at HEAD)** — add a
      `yt_selftest` assertion that `next_story_id > max(id)` across backlog stories. It has been
      stale three times, **and it is stale right now**: measured 2026-08-14, `next_story_id: 225`
      against a maximum id of `STORY-225`, so `225 > 225` is **False**.
      ***Precondition, and it is the orchestrator's:*** because AC1 makes `yt_selftest` a gate
      command, writing this assertion without fixing the data would red the gate for every story
      after this one — and the only fix lives in `.scrum/backlog.yaml`, which the implementer may
      not touch. **The orchestrator bumps `next_story_id` to 226 in the same commit as the DoD
      line.** AC8's shown-RED is taken against the **pre-bump** state and recorded as such.
- [ ] **AC9 (the count of record moves 8 → 9, everywhere it is stated — and NOT where it is
      history)** — `CLAUDE.md:194` ("### The DoD gate — 8 commands") and its backend/frontend
      breakdown, plus `.scrum/definition-of-done.md` (orchestrator). **Grep for other copies before
      committing** (STORY-189's lesson, which found one). Three specific hazards, all measured at
      pre-lock verification:
      - ⛔ **`docs/scrum/wiki/demo-engine.md:617` and `:636` record historical "DoD gate 8/8"
        evidence from past sprints. Those are FACTS ABOUT THE PAST and must NOT become 9/9.** A
        literal grep-and-replace corrupts sprint history.
      - `frontend-zone.md:21` and `:617` state the five/three/eight breakdown. That article is
        `status: stale` and **not swept**; touching it would reset its staleness baseline without
        re-verifying its Facts (14 top-level bullets in `## Facts`), which the protocol forbids.
        **Leave it, and say in the report that it was left and why.**
      - `CLAUDE.md:78` ("the five backend DoD commands never touch it") stays **correct** under
        AC1's placement, because the self-test goes in its own section rather than the backend one.
        Verify that is still true of whatever the DoD ends up saying; if the placement ever moves,
        this line moves with it.
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
