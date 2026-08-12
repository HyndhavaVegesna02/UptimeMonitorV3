---
id: STORY-220
title: ZR-1's forbidden-module list is maintained by a prose note — make its completeness a test
type: chore
points: 2
status: draft
filed: 2026-08-05
sprint: null
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

- [ ] **AC1** — a test parses `pyproject.toml`, finds the `inbound-adapters-dont-persist` contract,
      and asserts its `forbidden_modules` equals the set of persistence port modules discovered on
      disk under `backend/src/core/ports/`, by a stated decidable rule: filename matching
      `*_repository.py`, plus the explicitly named `watermark.py`.
- [ ] **AC2 — non-vacuity floor.** The test asserts the contract was found by name and that
      discovery returned a plausibly-populated set. **The floor is DIRECTION-FREE (≥ 5), not
      "≥ 9 at time of writing"** — corrected 2026-08-13 at plan verification: nine is today's count,
      and a floor of 9 breaks on the LEGITIMATE removal of a port. STORY-155 (remove `sample_mode`,
      named in CLAUDE.md) deletes `sample_mode_repository.py`, taking the correct count to 8; a
      ≥ 9 floor would go red on a correctly-updated contract. AC1's set EQUALITY is the real guard;
      this floor exists only so a parse that finds nothing goes red instead of green.
- [ ] **AC3 — shown RED (A9).** Add an empty `backend/src/core/ports/zzz_repository.py` without
      touching `pyproject.toml`; the test fails **naming that module**, **and no other test changes
      state** — so a collateral failure cannot be read as the proof; revert; green; `git diff`
      empty. Recorded verbatim in the board's `reality_gate` block.
- [ ] **AC4 — shown RED in the other direction.** Remove one module from the contract's
      `forbidden_modules`; the test fails naming it; revert. This proves set equality rather than a
      "contract ⊆ disk" subset check.
- [ ] **AC5 — the residue is in the test's docstring.** A persistence port following neither naming
      rule (`*_repository.py`, `watermark.py`) is invisible to this test, as is a port that is
      persistence-shaped but named otherwise. The guard does not make the list self-maintaining; it
      makes forgetting it loud.
- [ ] **AC6** — runs inside the existing `python -m pytest`. No ninth DoD command.
- [ ] **AC7** — `zone-rules.md`'s ZR-1 row gains this test path alongside the contract name, and the
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
