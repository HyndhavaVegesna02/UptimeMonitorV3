---
id: STORY-220
title: ZR-1's forbidden-module list is maintained by a prose note — make its completeness a test
type: chore
points: 2
status: done
filed: 2026-08-05
sprint: 70
---

## Context

**Split out of STORY-206 at sprint-69 plan verification**, where it was AC6. It is right, and it is
not dropped — carrying it inside STORY-206 made that story a 5 and sprint 69 a 13, against the PO
pacing directive to sit near 9–11. Proposed for sprint 70.

STORY-206 lands the `inbound-adapters-dont-persist` import-linter contract, whose `forbidden_modules`
enumerates the nine repository/watermark port modules by name. The contract ships with a prose
maintenance note, lifted verbatim from `docs/scrum/wiki/zone-rules.md` ZR-1 (`:130-134`):

> a newly added repository/persistence port module MUST be appended to this list in the SAME commit
> that adds it, or it is invisible to this guard.

**A mechanical guard whose completeness depends on a sentence nobody is required to read is the
defect class STORY-216 exists to catch** — and precisely sprint 67's MAJOR-1, where `ZR-6`'s row
claimed a guard that pinned a different property. Adding a tenth persistence port and forgetting the
list produces a green gate and an unguarded port, with nothing anywhere going red.

A14 says land an already-decided lesson at the mechanism rather than restating it in prose. This is
that landing.

## Verified at STORY-206's planning (2026-08-05)

`backend/src/core/ports/` holds exactly **12** modules. The proposed discovery rule reproduces the
contract's nine exactly:

- **Nine forbidden** — the eight matching `*_repository.py` (`component`, `maintenance`,
  `observation`, `proposal`, `publication`, `rejected_observation`, `sample_mode`, `signal`) plus
  the explicitly named `watermark.py`.
- **Three excluded** — `signal_ingest.py` (the core's documented front door, dossier §6/§8),
  `clock.py`, `status_publisher.py`. None matches the discovery rule, so the exclusion set is
  *dead code* under it: worth a comment explaining why they are named at all (they document intent),
  not an exercisable branch.

## Proposed Acceptance Criteria

- [x] **AC1** — a test parses `pyproject.toml`, finds the `inbound-adapters-dont-persist` contract,
      and asserts its `forbidden_modules` equals the set of persistence port modules discovered on
      disk under `backend/src/core/ports/`, by a stated decidable rule: filename matching
      `*_repository.py`, plus the explicitly named `watermark.py`.
- [x] **AC2 — non-vacuity floor.** The test asserts the contract was found by name and that
      discovery returned a plausibly-populated set. **The floor is DIRECTION-FREE (≥ 5), not
      "≥ 9 at time of writing"** — corrected 2026-08-13 at plan verification: nine is today's count,
      and a floor of 9 breaks on the LEGITIMATE removal of a port. STORY-155 (remove `sample_mode`,
      named in CLAUDE.md) deletes `sample_mode_repository.py`, taking the correct count to 8; a
      ≥ 9 floor would go red on a correctly-updated contract. AC1's set EQUALITY is the real guard;
      this floor exists only so a parse that finds nothing goes red instead of green.
- [x] **AC3 — shown RED (A9).** Add an empty `backend/src/core/ports/zzz_repository.py` without
      touching `pyproject.toml`; the test fails **naming that module**, **and no other test changes
      state** — so a collateral failure cannot be read as the proof; revert; green; `git diff`
      empty. Recorded verbatim in the board's `reality_gate` block.
- [x] **AC4 — shown RED in the other direction.** Remove one module from the contract's
      `forbidden_modules`; the test fails naming it; revert. This proves set equality rather than a
      "contract ⊆ disk" subset check.
- [x] **AC5 — the residue is in the test's docstring.** A persistence port following neither naming
      rule (`*_repository.py`, `watermark.py`) is invisible to this test, as is a port that is
      persistence-shaped but named otherwise. The guard does not make the list self-maintaining; it
      makes forgetting it loud.
- [x] **AC6** — runs inside the existing `python -m pytest`. No ninth DoD command.
- [x] **AC7** — `zone-rules.md`'s ZR-1 row gains this test path alongside the contract name, and the
      sentence STORY-206 AC6 put there ("completeness is maintained by hand until STORY-220 lands")
      is removed in the same commit. **The `verified_sha` clause is DELETED** (2026-08-13, plan
      verification): the field was dropped from every wiki article on 2026-08-12 (`d9319d8`,
      yourteam 2.3.0) and `grep -l "^verified_sha" docs/scrum/wiki/*.md` now matches nothing. Under
      the redrafted A18 the baseline is derived from the article's own last commit, so **touching the
      article IS re-verifying it** — there is nothing to bump. Re-read ZR-1's Facts before editing
      the row, per A18 clause 2.

## Depends on

**STORY-206** — the contract must exist before its completeness can be asserted. This story cannot
start first.

## Not in scope

The contract itself, its exclusions, and the 8 → 9 count-of-record sweep (all STORY-206). Any other
import-linter contract's completeness — if the pattern is wanted more widely, that is a separate
story sized against how many contracts enumerate modules by hand.

---

## History — 2026-08-13 (STORY-220 execution, sprint-70)

New test module: `backend/tests/test_zr1_forbidden_list_completeness.py`. No production code
changed.

### AC1 — discovery rule reproduced entry-for-entry

`_discover_persistence_port_modules` walks `backend/src/core/ports/` for `*_repository.py` files
plus the explicitly named `watermark.py`, returning `src.core.ports.<stem>` dotted names.
Reproduced directly at HEAD:

```
component_repository, maintenance_repository, observation_repository, proposal_repository,
publication_repository, rejected_observation_repository, sample_mode_repository,
signal_repository, watermark
```

— 9 modules, matching `pyproject.toml`'s `inbound-adapters-dont-persist.forbidden_modules` entry
for entry.
`test_forbidden_modules_matches_discovered_persistence_ports_exactly` asserts this set equality
against the real files, not a synthetic fixture.

### AC2 — non-vacuity floor, direction-free

`_NON_VACUITY_FLOOR = 5` (not 9) — see the module docstring's own reasoning. Unit-level coverage:
`test_load_contract_forbidden_modules_raises_when_contract_not_found` proves the loader itself
raises, naming the contract, rather than silently returning `[]`, closing the vacuous-pass path
the floor alone cannot close.

### AC3 — shown RED (new module on disk, contract untouched)

```
> "backend/src/core/ports/zzz_repository.py"          # empty file, pyproject.toml untouched
python -m pytest -q   (DYNAMO_ENDPOINT_URL=http://127.0.0.1:8021, REQUIRE_DYNAMO=1)
```
Result: `1 failed, 748 passed` (baseline was `749 passed, 0 skipped` immediately before this
mutation) — 748 + 1 = 749, so **no other test changed state**. The one failure named
`src.core.ports.zzz_repository` under "On disk but not in the contract" in the assertion message.
Reverted (`rm backend/src/core/ports/zzz_repository.py`); `git status --short` and
`git diff --stat` both empty; full suite back to `749 passed, 0 skipped`.

### AC4 — shown RED in the other direction (contract entry removed, disk untouched)

Temporarily removed `"src.core.ports.watermark"` from `inbound-adapters-dont-persist`'s
`forbidden_modules` in `pyproject.toml`. Same command, same test failed, naming
`src.core.ports.watermark` (this time under "On disk but not in the contract" too, since the module
still exists on disk once it is dropped from `declared` — the identical failure shape as AC3,
which is the point: **only checking both directions catches a removal**; a "contract ⊆ disk" check
alone would have stayed green, because disk was still a superset either way). `1 failed, 748
passed`. Reverted; `git diff pyproject.toml` empty; full suite `749 passed, 0 skipped`.

### AC5 — residue in the module docstring

Stated in the new module's own docstring (see "AC5 -- the residue, stated rather than hidden"):
a persistence port named following neither pattern is invisible to discovery, symmetric with a
persistence-shaped-but-not-actually-persistence name — both accepted limits of a decidable,
filename-only rule.

### AC6 — no ninth DoD command

The new module lives under `backend/tests/` (`testpaths = ["backend/tests"]` in `pyproject.toml`)
and is collected by the existing `python -m pytest` command. `CLAUDE.md` / `.scrum/definition-of-
done.md` unchanged.

### AC7 — `zone-rules.md` ZR-1 row edited

Two edits to the same table row (both land as one line-diff since the whole row is one physical
line):
1. Verdict cell: `` `ENFORCED-BY inbound-adapters-dont-persist` `` gained
   `` + `backend/tests/test_zr1_forbidden_list_completeness.py::test_forbidden_modules_matches_discovered_persistence_ports_exactly` ``
   alongside the contract name.
2. Detail cell: the "**Residue, stated rather than hidden (two, not one):** (1) ... is maintained
   BY HAND until STORY-220 (sprint 70) lands the completeness test ..." sentence is removed,
   replaced with a statement that the completeness residue is now itself guarded by this test,
   leaving only the pre-existing front-door-exclusion residue (unchanged).
No `verified_sha` bump — that field does not exist. Re-read ZR-1's Facts/Coverage verdict before
editing, per A18 clause 2; the edit does not touch any Fact, only the Adjudication row.

`test_zone_rules_enforced_by_claims.py` (STORY-216's parser) re-run after the edit: 21/21 passed —
both new references (`inbound-adapters-dont-persist`, and the new test's
`path::test_name`) resolve; the per-row floor and global non-vacuity floor both still hold.
Confirmed directly with `resolve_reference` against the real file: both references
`exists=True`.

### AC6/gate — 8/8 DoD, fresh run after the last commit

`DYNAMO_ENDPOINT_URL=http://127.0.0.1:8021`, `REQUIRE_DYNAMO=1` for every pytest invocation;
module-form entry points per CLAUDE.md's Device Guard note.

| # | Command | Exit | Tail |
| - | --- | --- | --- |
| 1 | `python -m pytest` | 0 | `749 passed in 40.51s` (0 skipped — up from the sprint-70 plan's 743, by exactly this story's 6 new tests) |
| 2 | `python -c "from importlinter.cli import lint_imports_command; lint_imports_command()"` | 0 | `Contracts: 9 kept, 0 broken.` |
| 3 | `python -m ruff check .` | 0 | `All checks passed!` |
| 4 | `python -m ruff format --check .` | 0 | `255 files already formatted` |
| 5 | `python -c "from cfnlint.runner import main; main()" infra/stack.yaml` | 0 | (no findings; exit 0) |
| 6 | `npm test` (from `frontend/`) | 0 | `Test Files  51 passed (51)` / `Tests  363 passed (363)` |
| 7 | `npm run build` (from `frontend/`) | 0 | `built in 308ms` |
| 8 | `npm run lint` (from `frontend/`) | 0 | (no findings; exit 0) |

8/8 green. Wiki sweep (`python .claude/skills/yourteam/scripts/yt_wiki.py sweep`), run after the
last commit: `== sweep: CLEAN ==`. Pre-existing `not swept (status=stale)` notes on
`core-pipeline-and-availability.md`, `deployment-and-infra.md`, `frontend-zone.md` predate this
story and are unrelated to its diff (this story's diff touches only `backend/tests/` and
`zone-rules.md`'s ZR-1 row) — flagged for the orchestrator, not fixed here (out of scope).
