# Sprint 10 — Review (2026-06-27)

**Goal:** Close out Zone 4 — the pipeline's final stage `decide` (§10 + §12) — plus three carried
cleanups. **Committed 6 pts, all 4 stories Done.**

**Mechanical floor (orchestrator-verified at `ed87055`, throwaway postgres:16):**
- `pytest` → **275 passed**
- `lint-imports` → **3 kept, 0 broken**
- `python scripts/check_fk_direction.py` → **0 violations (10 FKs)**
- `alembic upgrade head` → **exit 0** (no new migration this sprint)

Implementation was external (PO / Gemini) per the workflow agreement; the orchestrator ran the full
DoD gate, the Opus reviewers (STORY-024), the wiki compile pass, and one inline fix loop.

---

## STORY-024 — Core pipeline stage 4: decide (3 pts)
**Spec review (Opus): PASS** — all 3 AC MET. **Quality review (Opus): APPROVE** after fix loop 1.

- **AC1 (§10 direction vs published)** — MET. `decide.py` compares proposed vs `current_status` via
  `severity_rank`/`is_worse` (`status.py`): worse → `create_open` degradation, no publish; better →
  `StatusPublisherPort.publish`; same → nothing. Tests: `test_decide_*` cover each.
- **AC2 (§12 reconciliation)** — MET. supersede-vs-leave (differing vs identical open proposal),
  recovered → `resolve(OBSOLETED)` with **nothing published** (distinct from the auto-publish recovery),
  one-open invariant honored, commit-first (repo write committed before publish; verified with a
  `FailingStatusPublisher`).
- **AC3 (pure/provider-blind)** — MET. `core/services/decide.py` imports only `src.core.*`; a core
  service with injected `ProposalRepository` + `StatusPublisherPort`; tests use existing fakes, no DB.
- **Fix loop 1 (orchestrator, inline at PO request):** quality MAJOR — the new service had no
  docstrings (violating the core-service convention). Added module + class/method docstrings citing
  §10/§12; logic untouched (`ed87055`); gates re-verified green.
- **Non-blocking minors** (recorded): trailing blank lines, mixed import style, a DRY nit across the
  two degradation branches, an `opened.id` typing hole. Candidate follow-up chore if wanted.

## STORY-029 — Audit frozen value/result types for unenforced coherence invariants (1 pt)
**Gate-only (1 pt): all four gates green.** Audited all 12 frozen Pydantic types under `core/` (+ the
new `DecideAction` enum), recorded findings in the story file. Found one real gap — `AvailabilityResult`
percentages weren't validated against degenerate denominators — and closed it with a
`model_validator(mode="after")` (availability None-iff-zero-denominator; completeness None rules,
including the group-rollup case) + tests for valid and invalid shapes.

## STORY-027 — Hoist the lazy AvailabilityCalculator import (1 pt)
**Gate-only: green.** Lazy in-function import moved to module top in `test_availability.py` alongside
`AvailabilityResult`/`rollup_group`. Test-only; availability tests pass unchanged.

## STORY-030 — Make dev_db.py up idempotent against a leftover container (1 pt)
**Gate-only: green.** `dev_db.py up` now force-removes its own leftover/stuck container before
`docker run` (only its own named container; a real foreign port conflict still surfaces). Integration
test `test_up_idempotent_against_leftover_container` added; `dev-setup-and-dod.md` re-verified.

---

## Verdicts (PO, 2026-06-27)
- STORY-024 → **ACCEPT** (minors → follow-up STORY-032)
- STORY-029 → **ACCEPT**
- STORY-027 → **ACCEPT**
- STORY-030 → **ACCEPT**

**Outcome:** 4/4 accepted, velocity 6/6. Whole `sprint-10` branch merges to main. Follow-up chore
STORY-032 filed (1 pt) for the STORY-024 quality minors. Velocity recorded in `velocity.json`.
