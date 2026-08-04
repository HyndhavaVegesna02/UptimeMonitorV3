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
      still fail when the resolved table name IS the production default. **Directly executable, no
      subprocess run needed** (confirmed at plan verification): those lines sit inside
      `_assert_ac1_preconditions` (`harness.py:733`), which takes `api_env` as a plain dict — call it
      with a fabricated env whose table names ARE the defaults and show the assertion fire.
      A "fix" that turns the blocklist into a tautology is a fail; note the risk bites only if the
      **left**-hand side (the resolved value) is replaced by the imported constant, not the right.
- [ ] **AC3 — the guard's ledger shrinks by four, and every SURVIVING entry in a touched file is
      RE-KEYED.** `_ADJUDICATED` loses those four entries; **zero `MUST-IMPORT-FROM-SRC` entries
      remain**; every survivor is `INDEPENDENT` (or AC4's new adjudication).
      *Corrected at plan verification — the original "loses **exactly** those four entries" was the
      wrong instruction and would have taken the DoD gate RED.* Line shifts here are near-certain,
      not speculative: `failure_path_reality_gate.py` imports nothing from `src.composition.settings`
      today, so fixing `:149` adds an import line and shifts the surviving entry
      `("…failure_path_reality_gate.py", 390)`; and `harness.py`'s settings import is a six-line
      parenthesised block that becomes seven, shifting `("…harness.py", 910)` and `("…harness.py",
      971)`. Stale coordinates fail `test_zr3_adjudications_are_still_current`, and the new
      coordinates fail `test_zr3_sweep_finds_no_unadjudicated_collision` — **both guards, not one.**
      Re-key each survivor with its reason text preserved, using the "re-keyed, not removed"
      convention already in `test_zr3_duplicate_declarations.py`. STORY-215 will re-key `harness.py`
      again later this sprint; that is expected, and it re-derives rather than trusting these
      numbers.
- [ ] **AC4 — `store.py` is adjudicated, not left dangling.** Either the value is obtained from
      `src`, **or** the existing wire-contract justification is upheld and the `_ADJUDICATED` entry
      is rewritten from `MUST-IMPORT-FROM-SRC … Fix: STORY-203` to a reasoned `INDEPENDENT` naming
      that argument. **Leaving an entry pointing at a closed story is a fail.** Whichever way it
      goes, the `file:line` cross-reference is repointed to wherever STORY-204 left the constant.
      **Found at plan verification, and it materially strengthens the "uphold it" outcome:** the
      wire-contract agreement is *already mechanically pinned* by
      `backend/tests/demo_engine/test_vendor_health_query.py:76-91`
      (`test_vendor_health_window_matches_the_composition_health_check_window`). So upholding the
      justification does not leave the two values un-guarded against silent divergence — cite that
      test in the adjudication rather than arguing from the docstring alone.
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

## History

- **2026-08-04, fix round — AC7 (constraint C3) NOT MET, and cannot be closed without rewriting
  history.** AC7 requires the catalogue to move with the code in the same commit. It didn't: the
  code fixes landed in `e9cb8c8`, `691227f`, `db949c8`, and `zone-rules.md`'s ZR-3 section wasn't
  updated to record the fix until `3ab9c9b` — after even `1c07def`'s own ledger rewrite. The
  spec reviewer proved the consequence rather than asserting it: checking out `zone-rules.md` at
  `1c07def` shows it still reading *"A genuine, adjudicated violation (not merely
  illustrative)... `tools/demo_loop_gate/harness.py:753-757`... hardcodes the literal table-name
  values... now filed solely to STORY-203 (not fixed here)"* — asserting a live violation that the
  very same tree had already fixed. At least two committed states, `92241bd` and `1c07def`, carried
  that false claim. **The final state at HEAD is correct** — this is a commit-sequencing defect,
  not a wrong end state. Per PO direction, this is recorded plainly rather than rewritten: no
  rebase, squash, amend, or reset was performed. AC7 is not claimed MET. STORY-204 carries an
  identical miss, recorded the same way; both are flagged for PO adjudication.
- **2026-08-04, fix round — a second, self-inflicted C3 miss inside this very fix round, caught
  and landed correctly.** The MINOR-1 fix (naming the AC1(b) blocklist asserts' failure messages,
  commit `b72750e`) added lines inside `harness.py`, displacing two `INDEPENDENT`
  `test_zr3_duplicate_declarations.py` ledger entries this story had already re-keyed
  (`:921`->`:927`, `:982`->`:988`) and the `zone-rules.md` line-span it cites (`:761-768` ->
  `:761-774`) — caught immediately by re-running the ZR-3 guards (both went RED), fixed and landed
  together with `zone-rules.md`'s own note in the SAME commit (`1d43b1b`), so C3 holds for this
  second instance even though it did not hold for the first.
