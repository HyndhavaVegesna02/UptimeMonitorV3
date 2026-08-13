---
id: STORY-224
title: An entire second test suite exists and the DoD gate does not run it — 7 skill-level modules, including the two guards that have already caught real defects
type: defect
points: null
status: draft
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
   does not fire, and nobody notices. It was caught because `yt_selftest` happened to be run at
   sprint close.
2. **`test_scrum_encoding.py`, STORY-188.** The guard for the `.scrum/` mojibake class. It is the
   thing standing between the repo and a recurrence — and no gate runs it.

The project's stated invariant is that the mechanical floor is what makes judgement non-load-bearing.
A guard that runs only when someone remembers is judgement wearing a guard's clothes. **This is the
same defect class as STORY-178's `--only` false green** — the difference is that 178 ran and
reported the wrong answer, while these do not run at all.

It is also why STORY-192's stated choice ("does the new guard live in `test_scrum_encoding.py` or
in `yt_wiki.py`?") is a false choice: **both options are outside the gate.**

## Fix direction — decide at refinement, do not assume

Three shapes, with the trade-off that decides it:

**(a) Add `yt_selftest.py` as a 9th DoD command.** Cleanest conceptually — it already runs
everything and exits nonzero on failure. Cost: the DoD list is a deliberately small, stable
contract; adding to it is a real change and `yt_gate.py` parses that file.

**(b) Extend `testpaths` to include the skill tests dir.** One line — but ⚑ **`pyproject.toml` is
an amplifier `code_ref` in FOUR wiki articles** (`api-five-file-convention.md`,
`architecture-boundary.md`, `config-layer.md`, `sample-mode.md`), so touching it stales all four
in-story under A18. That is a hidden cost larger than the fix. Verify with `yt_wiki.py refs`
before choosing it.

**(c) Mirror only the repo-scope guards into `backend/tests/`.** `test_scrum_encoding.py` checks
*repo* content (`.scrum/`), not skill behaviour, so it arguably belongs there anyway. Narrow, no
amplifier cost — but it splits the suite and leaves `test_template_parity` (the A19 catcher)
outside the gate, which is the more valuable of the two.

**A refinement bias, not a decision:** (c) fixes the smaller half of the problem and leaves the
half that already bit us. Prefer (a) or (b) unless something rules them out.

## Refinement should settle

1. **Which shape** — and if (b), measure the four-article blast radius first and price it in.
2. **Which of the 7 modules are repo-scope vs. skill-scope.** They are not homogeneous:
   `test_scrum_encoding` and `test_backlog_story_parity` assert about *this repo's* content;
   `test_yt_wiki`/`test_yt_gate`/`test_yt_board` assert about *skill code*. That distinction may
   split the answer across (a) and (c).
3. **Runtime cost.** Measure it. If the skill suite is slow, adding it to every gate run is a real
   tax on a command already run many times per sprint.
4. **Whether the skill tests can even pass from a clean checkout** — they may assume state this
   repo happens to have. Run them standalone before committing to gating on them.

## Not in scope

Writing new guards. STORY-192's mojibake repair (it *depends* on this story's answer for where its
new check lands, but does not block on it — 192 can state its placement conditionally).
Changing what any existing skill test asserts.
