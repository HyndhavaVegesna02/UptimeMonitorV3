# Sprint 45 — Implementation Handoff Brief

Self-contained brief for an implementer agent. **Scope is frozen** (hard-locked sprint). Build to
the story ACs and the plan — not to any chat history. If an AC is genuinely ambiguous, STOP and ask;
do not guess.

## Where things are
- **Branch:** `sprint-45` (already cut; start tag `sprint-45-start` @ `bb0b4cd`). Work only here.
- **Board:** `.scrum/sprint-current.yaml` (both stories `board: todo`). The orchestrator is the sole
  writer of `.scrum/` state — an implementer must NOT edit it.
- **Canonical sources of truth (read these first):**
  - Plan (task breakdown + verified contracts + reality gate): `docs/scrum/sprints/2026-07-13-sprint-45/plan.md`
  - Story 065 (ACs verbatim): `docs/scrum/stories/STORY-065-maintenance-title-delete.md`
  - Story 066 (ACs verbatim): `docs/scrum/stories/STORY-066-publication-metadata.md`
  - Implementer checklist (binding): `.scrum/checklists/implementer.md`
  - Working agreements: `.scrum/working-agreements.md`
- **Order:** STORY-065 first (schema migration + first DELETE verb = highest novelty/risk), then
  STORY-066 (no migration).

## How to work (TDD + commit cadence)
- Strict TDD: write the failing test, see it fail, minimal code, see it pass, **commit after every
  green step**. That commit cadence is the crash-recovery mechanism — keep steps small.
- Do NOT bulk-stage. A PreToolUse git guard blocks `git add -A`/`.` and wrong-branch commits during
  an active sprint. Stage explicit paths.
- Do NOT touch `.scrum/` state, other stories, or anything outside these two stories' files.

## Definition of Done — the mechanical gate (all must exit 0)
Run from repo root with `.venv` (Windows: call `.venv/Scripts/*.exe` directly). The orchestrator
runs `python .claude/skills/yourteam/scripts/yt_gate.py` which executes all nine and records
evidence; you can run them individually while iterating:
1. `pytest`
2. `python -c "from importlinter.cli import lint_imports_command; lint_imports_command()"`  (the `lint-imports` exe is Device-Guard-blocked on this box — use the module path)
3. `python scripts/check_fk_direction.py`  (reads `DATABASE_URL`)
4. `alembic upgrade head`  (reads `DATABASE_URL_DIRECT`)
5. `ruff check .`
6. `ruff format --check .`
7. `npm test`  (from `frontend/`)
8. `npm run build`  (from `frontend/`)
9. `npm run lint`  (from `frontend/`)

DB-gated commands need a Postgres: `.venv/Scripts/python.exe scripts/dev_db.py up` prints both
URLs (pooled `DATABASE_URL` = plain libpq; direct `DATABASE_URL_DIRECT` = `+psycopg`). `down` when done.

## Project invariants you must not violate
- **Hexagonal zones:** every dependency points inward to `core`; adapters never import other
  adapters; only `composition` imports both sides. Boundary breaks are build failures (contract #2).
- **Migrations** live at repo top level (`migrations/`), run on the DIRECT URL; never `create_all`.
  New revisions chain off the current head `a2c1d89efcea`.
- **Fake ↔ adapter parity is mandatory:** every repository behavior is proven by the SAME contract
  test against both the Postgres adapter and the in-memory fake (`backend/tests/fakes.py`).
- **tz-aware UTC** datetimes throughout; existing validators untouched.
- **Frontend:** no `window.confirm`/browser modal dialogs (banned). Fixtures (MSW) come from REAL
  captured wire responses, never invented.
- **No CORS work** (deferred to STORY-017); the Vite dev proxy makes the frontend same-origin.

---

## STORY-065 — Maintenance title + DELETE (3p)
Full ACs: story file. Plan steps 1–8: `plan.md` §"STORY-065". Distilled must-hit contract:
- `title: str | None` is a NEW field distinct from `reason`, on domain `MaintenanceWindow`
  (`backend/src/core/domain/maintenance.py:8-49`), `MaintenanceWindowDTO` + `CreateMaintenanceRequest`
  (`backend/src/api/v1/maintenance/models.py:8-28`), and a **new nullable column** via an Alembic
  revision off `a2c1d89efcea` (add to the adapter's SQLAlchemy table def at
  `backend/src/adapters/persistence/maintenance_repository.py:13-20` + insert/select mappings).
- `DELETE /v1/maintenance/{window_id}` → **204** no body on success; **404** on unknown id. Add
  `delete(window_id: int) -> None` to the port (`backend/src/core/ports/maintenance_repository.py`),
  the Postgres adapter, and the fake (`FakeMaintenanceRepository`, `backend/tests/fakes.py:310-343`);
  raise a new `MaintenanceWindowNotFoundError` (define in `core/domain/maintenance.py`) on unknown,
  and register it `→ 404` in `backend/src/api/v1/_shared/errors.py:23-30`. This is the FIRST DELETE
  endpoint in the codebase — follow the five-file convention already used by the feature.
- **Frontend AC4 has a render requirement, not just a POST:** the windows-list row today renders
  `formatReason(window.reason)` (`frontend/src/pages/MaintenancePage.tsx:267-269`) and the form posts
  the Title input as `reason` (`:86`). You must (a) post the Title as `title`, (b) **render
  `window.title` on the row**, and (c) the create-with-title test must assert the title **renders on
  the created row** — not merely that it was in the POST body.
- **Frontend AC5 delete:** add `deleteMaintenance(id)` to `frontend/src/api/client.ts:241-257`, a
  delete mutation in `frontend/src/features/maintenance/useMaintenance.ts:47-80`, and a per-row
  Delete control using an **inline two-step confirm** (button → inline "Confirm?" state); refresh the
  list on success; a 404 surfaces a non-crashing error. MSW covers delete-success + delete-404.

## STORY-066 — Publication author, author-only (3p)
Full ACs: story file. Plan steps 1–6: `plan.md` §"STORY-066". Distilled must-hit contract:
- **No migration.** Author is DERIVED on read, not persisted. `PublicationDTO`
  (`backend/src/api/v1/publications/models.py:8-33`) gains `author: str | None`; the `Publication`
  read model (`backend/src/core/domain/publication.py`) gets an optional derive-on-read
  `author: str | None = None` that `record()` does NOT persist.
- **Derivation (the sharp edge — do it exactly this way):** in
  `PostgresPublicationRepository.list_recent` (`backend/src/adapters/persistence/publication_repository.py:78-109`)
  add author as a **correlated scalar subquery**, NOT a LEFT JOIN:
  `SELECT actor FROM approval_events WHERE proposal_id = publications.proposal_id AND action='approved' LIMIT 1`
  as a labeled column. A LEFT JOIN would multiply publication rows and skew the `LIMIT 50`. The
  `action` value is `'approved'` (verified: `ProposalState.APPROVED.value == "approved"`, written by
  `core/services/approval.py::_decide`). Null cases: `proposal_id IS NULL` → `author = null`; proposal
  with no `approved` event → `author = null`.
- **Fake parity:** `FakePublicationRepository` (`backend/tests/fakes.py:236-262`) has no author source
  today. Give it a derive-on-read seam — an injected `proposal_id → approved-actor` map (mirror
  `FakeSampleModeRepository`'s optional shared store at `fakes.py:300-307`) OR a shared
  `FakeProposalRepository` whose `.approval_events` (`fakes.py:121`, populated at `:174-191`) it scans
  for `action == "approved"`. `record` persists NO author on either side.
- **Tests (parity vs Postgres AND fake):** proposal approved by actor X → `author == "X"`;
  `proposal_id=None` → `None`; proposal with no approval event → `None`; **defensive case** — two
  `approved` events for one proposal → still exactly one publication row (proves no multiplication;
  two rows are insertable — `approval_events` has only a CHECK + non-unique index, no unique
  constraint).
- **Frontend AC4:** add `author` to `PublicationDTO` in `frontend/src/api/types.ts:159-166`; render it
  in the Publications timeline with graceful null handling; MSW fixtures (from a real
  `/api/v1/publications` capture) include an author-present and an author-null row.

---

## Wiki (reverse blast radius)
Sweep was **CLEAN at `6fa4305`** — all articles verified, none stale. Relevant verified articles to
consult (and to update/re-verify at DoD if your diff touches their `code_refs`):
- STORY-065: `api-five-file-convention.md`, `persistence-adapters.md`, `migrations-and-db.md`,
  `canonical-types-and-ports.md`, `frontend-zone.md`, `architecture-boundary.md`.
- STORY-066: `statuspage-publish.md`, `persistence-adapters.md`, `api-five-file-convention.md`,
  `frontend-zone.md`.
Run `python .claude/skills/yourteam/scripts/yt_wiki.py` after implementing; update any article whose
`code_refs` your diff touches and bump its `verified_sha`.

## Reality gate (required for Done — cannot ship on green tests alone)
Against the running local stack (throwaway DB + `uvicorn src.composition.asgi:app --port 8000` +
`python -m src.composition.run` + `cd frontend && npm run dev`):
- **065:** create a window with a Title in the UI → it renders on the row AND `/api/v1/maintenance`
  carries `title`; delete via the inline-confirm control → it disappears and a re-fetch omits it.
- **066:** approve a proposal so a publication is recorded with a known actor → the rendered
  Publications row's author matches `approval_events.actor` for that proposal; a null-proposal
  publication renders gracefully without an author.

## Closing a story (Done)
A story is Done only when: all its ACs met, the nine-command DoD gate is green with evidence, spec +
quality reviewers pass (both are 3-pointers → full pipeline), and the reality gate passed. The
**orchestrator** records DoD evidence + review verdicts into `.scrum/sprint-current.yaml` and runs
the spec/quality reviewers + reality gate — hand the branch back when the code is green and committed,
or tell the orchestrator to run the gates. Nothing merges to `main` until the PO accepts at review.
