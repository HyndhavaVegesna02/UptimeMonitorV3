---
id: STORY-203
title: Batch the four MINOR ZR-3 duplications — tools/ should import shared literals from backend/src/
type: chore
points: 2
status: ready
filed: 2026-07-31
refined: 2026-08-03
sprint: 68
---

## Context

`ZR-3`'s remaining VALUE duplications. STORY-202 (sprint 67) closed the seven env-var-**NAME**
collisions in the same files and deliberately left these — they are duplicated *values*, which was
outside its scope. Authoritative detail:
`docs/scrum/sprints/2026-07-31-sprint-66/audit-api-composition-tools.md` §6.

**None is a live defect today** — every value currently agrees. Each is a drift risk the next person
editing the `backend/src/` side has no way to learn about from `tools/`'s own code. The audit graded
all four MINOR, and that grading stands.

**Re-measured at refinement, 2026-08-03** (`python tools/zr3_duplicate_sweep.py`, exit 0):
**13 colliding pairs**, of which exactly **four** are adjudicated `MUST-IMPORT-FROM-SRC` in
`backend/tests/test_zr3_duplicate_declarations.py::_ADJUDICATED`, each naming this story as its fix:

| `tools/` site (HEAD) | duplicates | value |
| --- | --- | --- |
| `demo_loop_gate/env_matrix.py:49` | `settings.py:20` `Settings.aws_region` | `"us-east-1"` |
| `demo_loop_gate/failure_path_reality_gate.py:149` | `settings.py:20` (same default, a third hardcode) | `"us-east-1"` |
| `demo_loop_gate/harness.py:754` | `settings.py:21` `Settings.dynamo_observations_table` | `"uptime-observations"` |
| `demo_loop_gate/harness.py:757` | `settings.py:22` `Settings.dynamo_control_table` | `"uptime-control"` |

The other nine are adjudicated `INDEPENDENT` (bare `2`/`3` integers coinciding with
`FreshnessConfig` defaults — slice indices, `parents[2]`, fixture values) and must stay.

`harness.py:754,757` are the **ZR-3 AC3 reference case** the sweep had to prove it could find before
any empty result elsewhere was trusted. Both sit inside a *defensive blocklist* asserting the
resolved table name is NOT the production default — so importing the declared default and asserting
inequality does not merely remove a literal, it makes the blocklist follow a future rename
automatically. That is the fix's real value.

## The fifth case — `store.py`, which the sweep structurally cannot see

`tools/demo_engine/store.py:22` declares `VENDOR_HEALTH_WINDOW = timedelta(hours=2)` against
`composition/vendor_health.py`'s `_HEALTH_CHECK_WINDOW = "2h"` — the **cross-representation** case,
invisible to any literal-equality comparison, found only by direct reading. It is the standing limit
of value-comparison sweeps and worth remembering before trusting an empty ZR-3 result.

**Refinement's finding: this one may not be a violation at all.** `store.py:17-19` already carries a
written justification — the window is *"part of the WIRE CONTRACT this engine answers, not an
implementation detail borrowed from composition."* That argument is sound: the demo engine emulates a
vendor, and a vendor's wire behaviour is not supposed to track our config. AC4 therefore requires a
*decision*, not a reflexive fix.

**Dependency:** STORY-204 relocates `_HEALTH_CHECK_WINDOW` into the adapter, moving the `file:line`
`store.py` cites. **This story runs AFTER STORY-204.**

## Acceptance Criteria

- [ ] **AC1 — the four are fixed.** Each of the four sites above obtains its value from
      `backend/src/` (importing the declaring symbol, or reading the settings object) rather than
      re-declaring the literal. Re-derive each `file:line` against HEAD before editing — STORY-202's
      own edits re-keyed three of these once already.
- [ ] **AC2 — `harness.py`'s blocklist still blocks.** The defensive assertions at `:754`/`:757`
      still fail when the resolved table name IS the production default. Prove it: set the child env
      to the default and show the assertion fire. A "fix" that turns a blocklist into a tautology
      (`x not in (x,)` → always false, or an import that makes both sides trivially equal) is a fail.
- [ ] **AC3 — the guard's ledger shrinks.** `_ADJUDICATED` loses exactly those four entries.
      **Zero `MUST-IMPORT-FROM-SRC` entries remain**; every surviving entry is `INDEPENDENT` (or
      AC4's new adjudication). The guard's stale-entry check goes RED if a fix lands without its
      entry being removed — that is this story's mechanical success measure, the same shape sprint 67
      used for ZR-7.
- [ ] **AC4 — `store.py` is adjudicated, not left dangling.** Either the value is obtained from
      `src`, **or** the existing wire-contract justification is upheld and the `_ADJUDICATED` entry
      is rewritten from `MUST-IMPORT-FROM-SRC … Fix: STORY-203` to a reasoned `INDEPENDENT` naming
      that argument. **Leaving an entry pointing at a closed story is a fail.** Whichever way it
      goes, the `file:line` cross-reference is repointed to wherever STORY-204 left the constant.
- [ ] **AC5 — sweep count, re-derived not predicted.** Run `python tools/zr3_duplicate_sweep.py`
      before and after and record both counts. Arithmetic says 13 → 9. **If it is not 9, say so and
      explain rather than editing the number** (sprint 67 twice found a quoted count that did not
      reproduce).
- [ ] **AC6 — mutation proof.** Re-introduce one removed duplicate; the guard fails naming that
      `file:line`; restore; `git diff` empty.
- [ ] **AC7 — `zone-rules.md`'s ZR-3 History records what closed and what did not.** No claim that
      ZR-3 is now clean unless the sweep says so, and the `harness.py`/`settings.py` adjudicated-
      violation Fact — which this story retires — is updated rather than left asserting a live
      violation. (STORY-215, later this sprint, adds its own entry; expect to touch this section
      twice.)

## Not in scope

The env-var-**NAME** remainder (STORY-215, same sprint). The nine `INDEPENDENT` collisions. Widening
the sweep to see cross-representation duplicates — that limit is documented, and chasing it is a
different, much larger story.
