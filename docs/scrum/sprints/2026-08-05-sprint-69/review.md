# Sprint 69 — Review

**Branch:** `sprint-69` (UNMERGED, per the standing directive — sprints 66, 67, 68 and 69 all stay off main)
**Start:** `29eb824` (tag `sprint-69-start`) · **Head at review:** `cf80f33` · **73 commits**
**Goal:** guard what is already clean. ZR-1, ZR-2, ZR-4 and ZR-5 had ZERO live violations — which is
why nothing would have stopped tomorrow's first one. Each gets a standing guard, each shown RED by a
mutation before it counts, and STORY-216 makes the catalogue unable to claim a guard that does not exist.

**Delivered: 11 of 11 points. All five stories code-complete, gated, and reality-gated.**

---

## The goal's mechanical measure

The sprint goal was falsifiable in one command: at close, no ZR rule may remain in
`GUARDABLE-DEFERRED`.

| Claim | Command | Result |
| --- | --- | --- |
| No rule left deferred | `grep '^\| ZR-[0-9] ' zone-rules.md \| grep -c GUARDABLE-DEFERRED` | **0** (the 3 remaining hits are the legend's own definition and two dated History entries) |
| Every ZR has a terminal verdict | read the adjudication table | **8 of 8** — 6 `ENFORCED-BY`, ZR-5 additionally `UNGUARDABLE` for its operational half, ZR-6 `FIXED — NO STANDING GUARD` |
| Guards actually resolve | `test_zone_rules_enforced_by_claims.py` | **10 references across 7 of 8 rows**, all resolving |
| Full DoD gate | `yt_gate.py` | **8/8 PASS** — 743 passed / 0 skipped, 9 contracts kept, ruff + cfn-lint clean, frontend 363 passed + build + lint |
| Wiki | `yt_wiki.py` | sweep / facts / links **all CLEAN** |

Test count **714 → 743 (+29)**, and the arithmetic reconciles exactly: STORY-207 +3, STORY-209 +5,
STORY-208 **+0** (it extended an existing test, by design), STORY-216 +21.

Import-linter contracts **8 → 9**.

---

## Story-by-story

### STORY-206 — ZR-1's guard: an import-linter contract (3 pts)

A ninth contract forbidding `src.adapters.inbound` from importing any of nine repository ports.
Three quality rounds.

- **Reality gate:** an unused `ObservationRepository` import in the real inbound adapter → exit 1,
  `inbound-adapters-dont-persist` BROKEN naming the exact edge and line; reverted → 9 kept, 0 broken.
  Shown RED by **three** parties over the story's life.
- **The substantive finding, which outlived the story:** `core/ports/__init__.py` re-exports all nine
  repositories and import-linter follows indirect chains, so the *package* import form trips the
  contract even for the front door. Decision taken and documented: **fix the documents, not the
  contract** — `allow_indirect_imports` stays unset, because setting it would legalise the
  package-level import of a repository port and blind the guard to the likeliest violation shape.
- **Cost of getting there, stated plainly:** the row's residue sentence was written **wrong twice**,
  both times carrying an unverified causal inference under a "verified by mutation" stamp. The third
  version was mutation-verified before being written and then independently reproduced clause-by-clause
  by a reviewer. The genuinely unguarded shape is now stated: a PEP 562 `__getattr__`/`importlib`
  dynamic re-export resolves a repository port at runtime while the contract reports 9 kept / 0 broken.

### STORY-207 — ZR-2's guard: vendor vocabulary never becomes an identifier in `core/` (2 pts)

A six-rule AST walk over all 31 `core/` modules.

- **Reality gate:** `dynatrace_code: str` added to `Component` → `component.py:32 [Name]
  'dynatrace_code'`, naming file, line, node class **and** token; reverted → clean.
- **The check that mattered most, and was not faked:** AC2 proves the *compliant* direction. With
  rule (6)'s `Expr`-sole exclusion off, the walk really does flag `signal.py`'s docstring and
  `publication.py:66`'s attribute docstring — both already adjudicated COMPLIANT. An over-triggering
  guard gets reverted, never obeyed by editing compliant code.
- **Residue shipped rather than hidden:** the walk sees string annotations only as opaque constants,
  and an identifier assembled from fragments is invisible. ZR-2 is **not** described as fully enforced
  anywhere. The `Provenance` carve-out is explicitly unimplemented, with the correct future fix named.
- One AC miss caught at verification: the row landed as a bare path where AC8 specified
  `path::test_name`. Returned and fixed — it matters because STORY-216's mutation (b) is exactly
  "existing path + nonexistent `::test_name`".

### STORY-209 — ZR-5's guard: composition-root `CONFIG_DIR` parity (2 pts)

Resolution parity plus an AST assertion that neither root reads the env var itself. Clean run — one
dispatch, no rework, no AC returned.

- **Reality gate, both roots:** `app.py::create_app` → RED naming that root at line 137; `run.py::main`
  → RED at line 186. Both reverted to empty diffs.
- **The asymmetry proof is the point of doing both:** the `run.py` mutation fails *only* the `run.py`
  test. Neither root can be left unwatched — the exact asymmetry ZR-5 exists to prevent. Both mutations
  leave runtime behaviour identical today, which is precisely why prose never caught this shape.
- **Publish safety held.** Source-level mutations only; `python -m src.composition.run` was never
  invoked and no `create_app()` was constructed.
- **Half the story is its scope limit,** and it is in the guard's own docstring: the two-process
  failure that caused the sprint-64 incident is UNGUARDABLE here, and a green run "must not be read as
  'the sprint-64 incident cannot recur'". The code-level residue is stated too — a root that hardcodes
  `load_config("config/apps")` passes the whole walk undetected.

### STORY-208 — ZR-4's guard: the five-file feature shape (1 pt)

- **Reality gate, both directions:** renaming `approvals/validation.py` → RED naming the feature and
  missing file; adding a sixth file → RED naming the extra. The second proves **set equality**, not a
  subset check.
- **The retargeting earned its keep:** "1 failed, 5 passed **with no collection error**". Renaming
  `models.py` — the obvious target — would have raised `ModuleNotFoundError` across much of the suite,
  and the recorded "red" would not have been the guard firing at all.
- **AC2 verified as exercised, not asserted:** `approvals/__pycache__` exists in this tree and the
  guard passes anyway. Without the `*.py`-only rule this guard would be red on every developer machine
  and green in CI — colour depending on whether tests had been run before.

### STORY-216 — mechanise the `ENFORCED-BY` claim (3 pts)

The capstone: a test that fails when a row claims a guard that does not exist. Two review rounds, two
fix rounds, 21 tests.

- **Anti-vacuity evidence:** 10 references across 7 of 8 rows — ZR-8 carrying four, ZR-6 correctly
  zero — spanning both reference kinds, bare paths, `::test_name` rows, the two-verdict cell and the
  four-reference cell. Re-derived independently by **three** parties. One reviewer went further and ran
  `pytest --collect-only` on all seven node ids: 10 collected, so the claims hold against real
  collection, not only the AST.
- **AC6 held end to end:** `git diff c14ea29..HEAD -- zone-rules.md` is **empty**. No adjudication row
  was ever edited to make the parser pass — the specific damage the original AC would have caused, and
  the reason plan verification rewrote it.
- **Two MAJORs, both the same shape at different scopes** — a floor whose slack varies by input:
  round 1, a *global* floor let any single row silently drop to zero coverage; round 2, the *per-row*
  floor was absorbed on ZR-8, the one multi-reference cell (40% of coverage). Both were reproduced by
  the orchestrator before being actioned. The final floor uses
  `max(marker_count, py_count)` and the residual limit is stated rather than papered over.
- **AC3 is the honesty AC and it holds:** the check verifies a row *records* a shown-RED demonstration;
  it cannot verify the demonstration happened. That limit is in the docstring **and** the failure
  message, so no future reader can treat a green run as proof the mutations were real.

---

## Verification posture — what was re-performed rather than believed

Every reality-gate mutation in this sprint was **re-performed by the orchestrator**, not transcribed
from an agent's report. That is a direct consequence of sprint-67's MAJOR-1 and of this sprint's own
RC-1: a shown-RED proof living only in an agent's final report is deleted when a session limit kills
the agent, which happened **three times** here.

Independent verification also caught things reports did not:
- the ZR-4 mutation naming, the `__pycache__` condition, the seed-declared-once check;
- the ZR-8 evasion, reproduced before dispatching its fix;
- a scope control that caught **the orchestrator's own probe error** — the same `::test_name` edit
  applied to Coverage-verdict *prose* leaves the guard green, which is correct, because that prose is
  out of AC1's scope. It briefly looked like a regression and was not.

---

## Defects and corrections found during the sprint

- **STORY-221 (`npm test`) is not a rare flake.** Measured FAIL/PASS/FAIL/PASS at one commit with zero
  frontend diff — 2 red in 4, one failing when run alone. It then did **not** fire in six consecutive
  gates, which does **not** retire it: that is what a load-sensitive failure looks like when the load
  is absent. Re-price at sprint-70 planning against the measurement, never the streak.
- **STORY-179 is mis-scoped.** Its documented workaround (point `DYNAMO_ENDPOINT_URL` at a fixed-port
  container) **cannot** help `test_provide_dynamo_local_teardown_on_failure`, which deliberately unsets
  that variable to force a container spawn. Both halves of the filing are too narrow.
- **A red gate was refused rather than discounted.** For about an hour, newly published Docker ports
  were intermittently unroutable and `python -m pytest` exited 1. The two-limb contention discount did
  **not** apply (it failed in isolation), so it was recorded RED and the story was held out of `done`
  until a genuine green existed. It self-healed with no restart.
- **The orchestrator's own diagnosis of that fault was overstated** and is corrected in the board:
  "broken machine-wide for new containers", called *decisive*, claimed a permanence the evidence did
  not support. Filed as RC-12.
- **RC-11:** ZR-7's row cites its guard file, but that path is not in `zone-rules.md`'s `code_refs`,
  while ZR-2/ZR-3/ZR-5's are. STORY-216 does not close this — it checks a guard *exists*, not that the
  article is quarantined when the guard changes. Needs a ruling, not a silent fix.

---

## What this sprint does NOT deliver

Stated because the sprint's own thesis is that guards must not overclaim:

- **ZR-1's forbidden-module list is still maintained by hand** until STORY-220 lands. The PO accepted
  this consequence explicitly at approval when choosing the 11-point shape.
- **ZR-5's operational half is permanently unguardable** by a unit test.
- **ZR-6 has no standing guard** — fixed, but nothing prevents recurrence.
- **ZR-1, ZR-2 and ZR-5 each ship a stated residue**, and STORY-216 ships one too.

The audit's catalogue is complete. The architecture is not "guarded", and no artifact in this sprint
says it is.

---

## Blocked stories

None. No story was blocked at any point.

## Recommendation to the PO

Accept all five. Sprint 70's strongest candidates, in order: **STORY-220** (converts ZR-1's
hand-maintained promise back into a mechanism — the residue you knowingly took for one sprint),
**STORY-212** (lands the evidence-artifact rule at the script rung; three agent deaths this sprint say
it has earned its place), and **STORY-221 + STORY-179** re-priced against what was measured here.
