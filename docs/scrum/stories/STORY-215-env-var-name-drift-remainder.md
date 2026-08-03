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

### Site 3 — real, but the mechanism is the OPPOSITE of what this story first claimed

`backend/tests/test_demo_fleet_config.py:164,200` hardcode `"CONFIG_DIR"` against `settings.py`. This
is a **fourth file**, outside STORY-202's three-file scope, ruled correctly out of scope for 202 by
both sprint-67 reviewers *and* flagged by both as a real residual defect. It is STORY-176's file —
the `create_app` test asserting that `CONFIG_DIR` governs publisher safety.

> ### ⚠ CORRECTED AT PLAN VERIFICATION (2026-08-03) — READ THIS BEFORE AC5
>
> The first version of this story said the rename would leave *the publish-guard test* "green while
> asserting nothing." **That is false, and it was refuted by running the mutation's observable state
> read-only, not by argument.** With `CONFIG_DIR_VAR`'s value renamed so `load_settings()` reads a
> name nothing set, while the test's own literal `setenv("CONFIG_DIR", …)` still "succeeds":
>
> ```
> statuspage_mapping() = {'http-check': 'xdnywbx77npw'}
> line 174  assert mapping == {}   -> FAIL   <-- the test goes RED
> delegate type = BestEffortPublisher
> ```
>
> **`test_demo_fleet_config.py:174` is a WORKING DETECTOR today.** It resolves to the live component
> id and the real Statuspage chain — exactly what it exists to catch — so the demo-side test fails
> loudly under the drift, as designed.
>
> **The test that genuinely goes silently green is the LIVE-side one**,
> `test_create_app_with_live_config_dir_and_real_looking_creds_selects_real_publisher_type`
> (`test_demo_fleet_config.py:179-212`): its literal sets `CONFIG_DIR=config/apps`, and the fallback
> default is **also** `"config/apps"` — so every assertion at `:206-212` passes *for the wrong
> reason*, whatever the env var is called.
>
> The residual defect is real either way (both tests re-type the name), but the severity argument
> now points at `:206-212`, not `:174`. AC5 below is written to the corrected mechanism.

**Note the ZR-3 sweep is structurally blind to it** — the sweep compares `backend/src/` declarations
against `tools/` literals only (`tools/zr3_duplicate_sweep.py:209-211`), and this file is under
`backend/tests/`. That is why nobody adjudicated it. **Site 4 is invisible for the same reason**
(`scripts/` is not scanned either). Neither fix can be verified by the sweep; both need AC5's
mutation.

### What is genuinely excluded, so the story does not churn tests

`backend/tests/test_settings.py:30` — `assert CONFIG_DIR_VAR == "CONFIG_DIR"` — is the **pin**, not a
duplication: it is the test that stops a rename silently changing the wire contract with the deployed
environment. It must survive untouched. The distinction from site 3 is the point: a test *asserting a
constant's value* is protection; a test *re-typing the name to consume it* is drift.

## Acceptance Criteria

- [ ] **AC1 — the two names get constants.** `DYNATRACE_ENV_URL_VAR` and `DYNATRACE_API_TOKEN_VAR`
      are declared in `settings.py` alongside the existing seven, same `<NAME>_VAR` convention, and
      `load_live_secrets` reads through them — i.e. `missing.append(DYNATRACE_ENV_URL_VAR)`, never a
      re-typed literal and never the *symbol* name. **The pin is
      `backend/tests/test_live_secrets.py:65-68`**, four substring assertions that the raised message
      contains both `DYNATRACE_*` names and neither `STATUSPAGE_*` name; it must stay green
      unmodified. *Corrected at plan verification: an earlier draft cited
      `test_run_live_loop.py:332` as asserting the message "verbatim". It is not an assertion at all
      — it is a fabricated `side_effect` payload on a **patched** `load_live_secrets`, so the
      production function never runs, and its string does not even match the real message, which
      reads `Missing required LIVE secrets:` (`settings.py:123`). Do not treat `:332` as a
      constraint.*
- [ ] **AC2 — `tools/` imports rather than re-types.** Sites 1 and 2 use the imported constants.
      Afterwards `grep -rn '"DYNATRACE_ENV_URL"\|"DYNATRACE_API_TOKEN"' tools/` returns zero hits.
- [ ] **AC3 — site 3 consumes the constant, and so do the six literals beside it.**
      `test_demo_fleet_config.py:164,200` set the env var through `CONFIG_DIR_VAR`, not a literal.
      **Widened at plan verification:** the same two tests re-type four more names that already HAVE
      constants — `"DYNAMO_ENDPOINT_URL"` (`:163`, `:199`) and `"STATUSPAGE_PAGE_ID"` /
      `"STATUSPAGE_API_KEY"` (`:168-169`, `:201-202`) — the last pair being the credential-name drift
      `ZR-3` originally adjudicated as its credential-safety risk. Fix them too, **or** record in the
      story why six literals in one file are excluded while a seventh is not. `test_settings.py:30`
      is **unchanged** — confirm it, and state the pin-vs-drift distinction in the story's own diff
      so a later sweep does not "fix" the pin and delete the protection.
- [ ] **AC4 — site 4 stops resolving config on its own.** `scripts/seed_topology.py` obtains
      `config_dir` via `load_settings()` rather than its own `os.environ.get("CONFIG_DIR",
      "config/apps")`, killing an independent declaration of both the name **and** the default. If an
      import constraint makes that impossible, record the reason and adjudicate it rather than
      silently leaving it.
- [ ] **AC5 — mutation, two-sided, written to the CORRECTED mechanism (see the box above).** Rename
      an env var's VALUE in `settings.py` (not its symbol). Pre-fix, demonstrate **both** halves,
      because they are different and only the second is the defect:
      **(a)** `test_demo_fleet_config.py:174` goes **RED** — the demo-side assertion is a working
      detector and must be shown working, so the fix is not credited with rescuing it; and
      **(b)** `test_demo_fleet_config.py:206-212` stays **GREEN while asserting nothing** — the
      live-side test sets `CONFIG_DIR=config/apps` and the fallback default is also `"config/apps"`,
      so it passes for the wrong reason. **(b) is the vacuity this story exists to close.**
      Post-fix, both sides read one symbol and agree. Run the pre-fix half in an isolated
      `git worktree` with `PYTHONPATH=<worktree>/backend`, and **print `module.__file__`** to prove
      which tree ran (agreement A1-refinement: the editable install resolves `src.*` to the MAIN tree
      from inside a worktree). Restore; `git diff` empty.
- [ ] **AC6 — the sweep count is re-derived at THIS story's start commit, and the forecast is
      specific.** *Corrected at plan verification, twice over.* First: **the baseline is 9, not 13** —
      STORY-203 runs earlier in this same sprint and takes 13 → 9; quoting 13 would be a number the
      sprint's own earlier story invalidates, which is precisely the sprint-67 defect class. Re-derive
      at the commit this story actually starts from (expect **9**; 13 only if STORY-203 was dropped).
      Second: declaring the two new constants creates **exactly three** candidate collisions, and
      they are precisely the three sites AC2 already fixes (`env_matrix.py:81`, `env_matrix.py:83`,
      `harness.py:614` — the nested dict-key `Constant`; the f-string's literal part is
      `"DYNATRACE_ENV_URL="` *with the `=`*, which does not match, and `harness.py:24`'s mention is
      inside the module docstring). **So if AC2 lands in the same commit the net is 9 → 9.** If a
      site is missed, that site alone surfaces as a new unadjudicated collision — the guard working.
      Adjudicate any new collision in `_ADJUDICATED`; an unrecognised one is a guard FAILURE, never a
      silent pass.
- [ ] **AC6b — re-key, do not merely remove.** Editing `harness.py:614` adds an import line, which
      shifts the surviving `INDEPENDENT` entries `("tools/demo_loop_gate/harness.py", 910)` and
      `("…harness.py", 971)`. Stale coordinates take `test_zr3_adjudications_are_still_current` RED.
      Re-key every surviving entry in any file this story touches, preserving its reason text —
      the convention already in `test_zr3_duplicate_declarations.py` (see its re-keyed entries).
      **STORY-203 will have re-keyed the same file earlier this sprint; re-derive, never carry
      forward its numbers.**
- [ ] **AC7 — `zone-rules.md`'s ZR-3 History records what closed and what did not**, including that
      the sweep cannot see site 3 **or site 4** (`backend/tests/` and `scripts/` are both outside the
      two trees `find_collisions` scans, `tools/zr3_duplicate_sweep.py:209-211`). No claim that the
      name boundary is now fully closed unless a re-run measurement says so; record the command and
      its output. STORY-203 edits this same section earlier in the sprint — expect to touch it
      second.
- [ ] **AC8 — `scripts/seed_topology.py` has no import obstacle; confirm rather than assume.**
      Verification found `load_settings` is **already imported** at `:20` and called at `:34`, so
      AC4 is a re-order, not a new dependency. If that is still true at execution, AC4's escape
      hatch ("if an import constraint makes it impossible") does not apply and must not be used.

## Not in scope

The VALUE duplications (STORY-203, same sprint). The `STATUSPAGE_*` names (already constants — verify,
then leave). Building the `ZR-5` parity guard itself (STORY-209, sprint 69). Widening the ZR-3 sweep
to cover `backend/tests/`.
