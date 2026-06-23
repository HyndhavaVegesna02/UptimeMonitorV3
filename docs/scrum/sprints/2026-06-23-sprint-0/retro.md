# Sprint 0 — Retrospective

**Outcome:** 8 pts committed, 8 pts accepted (3/3 stories). No blockers, no effort-cap trips,
no review ping-pong, no hotfixes. Estimates were exact (every story Done on the first attempt).

## What went well
- The horizontal-slicing bet paid off immediately: the two CI floors (`lint-imports`,
  `check_fk_direction.py`) exist and are proven to *bite* before any business logic — exactly
  the safety the design relies on. Both negative demonstrations (forbidden import → exit 1;
  spine→feature FK → exit 1) were reproduced by reviewers.
- Full pipeline on the 3-pt stories caught nothing critical because the work was clean, but
  the spec reviewer independently *reproduced* the AC2 boundary demonstration — evidence over
  claims worked as intended.
- The four-command DoD gate was independently re-run by the orchestrator against a fresh
  Postgres at each story close — no "trust the report" gaps.

## What dragged / friction
- **CLAUDE.md went stale mid-sprint (STORY-002).** The story made two new DoD commands real,
  but the implementer brief didn't include the doc sync the DoD standing rule requires, so
  CLAUDE.md still said they "arrive in later stories." Required a manual patch (and the
  implementer agent couldn't be resumed to do it). → Amendment 1.
- **Two Definition-of-Done files** (root companion + `.scrum/` operational) — a real drift
  risk flagged by the STORY-003 implementer. → Amendment 2.
- Cosmetic: Git emits `LF→CRLF` warnings on Windows. Harmless; a `.gitattributes` for
  deterministic EOLs is a candidate chore (not a process problem).

## Amendments adopted (PO-approved) → written to working-agreements.md
1. **Command-sync in the brief** — any story that adds/changes a DoD/build/test/run command
   must carry an explicit "update CLAUDE.md in the same commit" step, checked at the gate.
2. **Single canonical DoD** — `.scrum/definition-of-done.md` is the sole source of truth; the
   root `definition-of-done.md` is now a one-line pointer.

## Carried to the backlog (refine before a future sprint; not yet stories)
- `pythonpath = ["backend"]` in pyproject so bare `pytest` needs no editable install (CI portability).
- Composite-FK `SELECT DISTINCT` in `check_fk_direction.py` + comment the deliberate
  function-local `psycopg` import.
- `migrations/env.py` import-time URL resolution → optional `alembic revision` ergonomics.
- `.gitattributes` for EOL normalization.

## Wiki drift
- No stale articles (the wiki was seeded this sprint). Nothing stale ≥3 sprints.

## Tooling
- No tooling friction. Docker + Python toolchain sufficient for Sprint 0; no live
  Neon/Dynatrace/Statuspage credentials needed yet (first needed at the adapter/deploy zones).
- Frontend test runner (Vitest?) and E2E (Playwright?) remain open tooling gaps to raise when
  Zone 7 (STORY-015) is planned.
