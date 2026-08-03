---
id: STORY-215
title: Close the remaining env-var-NAME drift — the two DYNATRACE_* names, plus the file that guards the publish guard
type: defect
points: 3
status: ready
filed: 2026-08-03
refined: 2026-08-03
sprint: 68
---

## Context

STORY-202 (sprint 67) promoted five env-var names in `backend/src/composition/settings.py` to
`<NAME>_VAR` module constants so `tools/demo_loop_gate` could import them instead of re-typing the
strings — closing the rename-drift gap `ZR-3` flags across the `tools/` ↔ `backend/src/` boundary. It
bounded its own scope and left a remainder, gathered here so it is not rediscovered piecemeal.

**Four sites. Re-derived at refinement, 2026-08-03.**

| # | Site | What it re-types | Status |
| --- | --- | --- | --- |
| 1 | `tools/demo_loop_gate/env_matrix.py:81,83` | `DYNATRACE_ENV_URL`, `DYNATRACE_API_TOKEN` | left by 202 on purpose |
| 2 | `tools/demo_loop_gate/harness.py:614` | `DYNATRACE_ENV_URL` | same pair, same file family |
| 3 | `backend/tests/test_demo_fleet_config.py:164,200` | `CONFIG_DIR` | **the consequential one** |
| 4 | `scripts/seed_topology.py:25` | `CONFIG_DIR` **and** the `"config/apps"` default | found at this refinement |

The declaring side of the `DYNATRACE_*` pair is itself a raw literal — `settings.py:114,116,117,119`,
inside `load_live_secrets`'s function body — so there is no constant to import yet. That is exactly
why STORY-202 left them: fixing them means promoting two more constants, **which re-runs 202's own
trap** (newly-declared shape-i values turn existing `tools/` literals into fresh `ZR-3` collisions,
the sequence that took 202 from 1 point to 3). Expect the sweep count to move in both directions.

### Site 3 is the most consequential, and both sprint-67 reviewers flagged it independently

`backend/tests/test_demo_fleet_config.py:164,200` hardcode `"CONFIG_DIR"` against `settings.py`. This
is a **fourth file**, outside STORY-202's three-file scope, ruled correctly out of scope for 202 by
both reviewers *and* flagged by both as a real residual defect. It is STORY-176's file — the
`create_app` test asserting that `CONFIG_DIR` governs publisher safety.

**So the literal that re-creates the drift risk sits in the test that guards the publish guard.**
`CONFIG_DIR` selects `config/demo`, which empties `statuspage_mapping()`, which is what yields a
`LoggingPublisher`; and `decide` publishes recoveries with **no human gate**. A rename that silently
missed this test would leave it green while asserting nothing.

**Note the ZR-3 sweep is structurally blind to it** — the sweep compares `backend/src/`
declarations against `tools/` literals, and this file is under `backend/tests/`. That is why nobody
adjudicated it. Its fix therefore cannot be verified by the sweep and needs its own mutation (AC5).

### What is genuinely excluded, so the story does not churn tests

`backend/tests/test_settings.py:30` — `assert CONFIG_DIR_VAR == "CONFIG_DIR"` — is the **pin**, not a
duplication: it is the test that stops a rename silently changing the wire contract with the deployed
environment. It must survive untouched. The distinction from site 3 is the point: a test *asserting a
constant's value* is protection; a test *re-typing the name to consume it* is drift.

## Acceptance Criteria

- [ ] **AC1 — the two names get constants.** `DYNATRACE_ENV_URL_VAR` and `DYNATRACE_API_TOKEN_VAR`
      are declared in `settings.py` alongside the existing seven, same `<NAME>_VAR` convention, and
      `load_live_secrets` reads through them. Its "missing required secrets" message text must not
      change — `test_run_live_loop.py:332` asserts it verbatim.
- [ ] **AC2 — `tools/` imports rather than re-types.** Sites 1 and 2 use the imported constants.
      Afterwards `grep -rn '"DYNATRACE_ENV_URL"\|"DYNATRACE_API_TOKEN"' tools/` returns zero hits.
- [ ] **AC3 — site 3 consumes the constant.** `test_demo_fleet_config.py:164,200` set the env var
      through `CONFIG_DIR_VAR`, not a literal. `test_settings.py:30` is **unchanged** — confirm it,
      and state the pin-vs-drift distinction in the story's own diff so a later sweep does not
      "fix" the pin and delete the protection.
- [ ] **AC4 — site 4 stops resolving config on its own.** `scripts/seed_topology.py` obtains
      `config_dir` via `load_settings()` rather than its own `os.environ.get("CONFIG_DIR",
      "config/apps")`, killing an independent declaration of both the name **and** the default. If an
      import constraint makes that impossible, record the reason and adjudicate it rather than
      silently leaving it.
- [ ] **AC5 — mutation, two-sided, and it must cover site 3 specifically.** Rename an env var's VALUE
      in `settings.py` (not its symbol). Pre-fix the two sides **DISAGREE** — the literal keeps the
      old name, the consumer silently falls back to the default, and *the publish-guard test stays
      green while asserting nothing*. Post-fix they **AGREE**. Run the pre-fix half in an isolated
      `git worktree` with `PYTHONPATH=<worktree>/backend`, and **print `module.__file__`** to prove
      which tree ran (agreement A1-refinement: the editable install resolves `src.*` to the MAIN tree
      from inside a worktree). Restore; `git diff` empty.
- [ ] **AC6 — the sweep count is re-derived before and after, and expected to move BOTH ways.**
      Promoting two new shape-i constants may create fresh `ZR-3` collisions even as this story
      removes others — STORY-202's trap. Record both counts and adjudicate every new collision in
      `_ADJUDICATED` (`MUST-IMPORT-FROM-SRC` with a fix story, or `INDEPENDENT` with a reason). An
      unrecognised collision is a guard FAILURE, never a silent pass. Baseline to beat: **13**.
- [ ] **AC7 — `zone-rules.md`'s ZR-3 History records what closed and what did not**, including that
      the sweep cannot see site 3 at all. No claim that the name boundary is now fully closed unless
      a re-run measurement says so; record the command and its output. STORY-203 edits this same
      section earlier in the sprint — expect to touch it second.

## Not in scope

The VALUE duplications (STORY-203, same sprint). The `STATUSPAGE_*` names (already constants — verify,
then leave). Building the `ZR-5` parity guard itself (STORY-209, sprint 69). Widening the ZR-3 sweep
to cover `backend/tests/`.
