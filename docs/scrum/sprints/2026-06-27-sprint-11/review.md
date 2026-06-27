# Sprint 11 — Review (2026-06-27)

**Goal:** Tooling + cleanup consolidation — land the ruff DoD gate + clear the carried review chores.
**Committed 4 (deliberate under-commit), accepted 4/4.**

**Mechanical floor (orchestrator-verified at `c577330`, throwaway postgres:16) — now SIX commands:**
- `pytest` → **275 passed**
- `lint-imports` → **3 kept, 0 broken**
- `python scripts/check_fk_direction.py` → **0 violations**
- `alembic upgrade head` → **exit 0** (no new migration)
- `ruff check .` → **All checks passed!**
- `ruff format --check .` → **73 files already formatted**

All three stories are ≤ 2 pts → gate-only (no LLM reviewers).

## STORY-033 — ruff (format + import-sort) DoD gate (2 pts) → ACCEPT
Ruff added to dev extras + `[tool.ruff]` (py313, line-length 88, `select = [E,W,F,I]`, `E501` ignored).
One-pass `ruff format` + `ruff check --fix` over the tree — **verified formatting-only** (the 129-line
migration diff is exploded `sa.Column(...)` calls + single→double quotes + import reorder, zero DDL
change; `alembic upgrade head` + the schema/FK tests stay green). Both ruff commands wired into
`.scrum/definition-of-done.md` + documented in `CLAUDE.md` in one command-sync commit; the DoD is now
six commands. `dev-setup-and-dod.md` updated + verified.

## STORY-032 — decide.py quality minors (1 pt) → ACCEPT
`_open_proposal` helper factors the duplicated `StatusProposal` construction + `create_open` + None-check
out of the two degradation branches; `assert opened.id is not None` guards before `resolve`. The cosmetic
ACs (import style, trailing blanks) were subsumed by the ruff pass, as planned.

## STORY-031 — sprint-9 review cleanups (1 pt) → ACCEPT
Leftover `test_publisher_can_be_imported` smoke test removed; the unused `component_degraded.json`
fixture is now exercised by a new end-to-end `DEGRADED → degraded_performance` publish test; mid-module
imports hoisted (ruff).

## Compile pass — wiki (the one non-trivial outcome)
STORY-033's tree-wide reformat touched files referenced by **7 wiki articles**, drifting ~54 `file:line`
Fact citations (Facts still TRUE — only the line pointers moved; e.g. `proposal.py:10` → `:11` from a
ruff-inserted docstring blank line). **PO decision:** mark those 7 articles `status: stale`
(honest/quarantined — readable, not used in briefs) rather than hand-patch brittle line refs that would
re-drift; rehabilitate them via **STORY-034** under a **symbol-based citation** policy adopted at retro.
`core-pipeline-and-availability.md` + `dev-setup-and-dod.md` were re-pinned in-sprint (verified
`decide.py::DecideAction`/`DecideService` at 43/61) and stay `verified`.

Stale articles: architecture-boundary, canonical-types-and-ports, dynatrace-adapter,
ingest-service-and-pull-loop, migrations-and-db, persistence-adapters, statuspage-publish.

## Verdicts (PO, 2026-06-27)
- STORY-033 → **ACCEPT**
- STORY-032 → **ACCEPT**
- STORY-031 → **ACCEPT**

**Outcome:** 3/3 accepted, velocity 4/4. Whole `sprint-11` branch merges to main. Follow-up: STORY-034
(wiki rehab, draft, pending retro's symbol-citation syntax).
