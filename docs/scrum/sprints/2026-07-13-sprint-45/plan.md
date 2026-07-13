# Sprint 45 Plan — Redesign backend-gap follow-ups (Maintenance + Publications)

**Goal:** The Maintenance tab gains a real Title field and a per-window delete (STORY-065), and the
Publications timeline shows the real publish author (STORY-066) — closing two of the Sprint 38
redesign data gaps against real API data.

- **Date:** 2026-07-13 · **Mode:** `in-process` · **Stories:** 065 (3p) + 066 (3p) = 6p
- **Order:** 065 first (schema migration + the codebase's first DELETE verb → highest novelty/risk;
  settle the DB shape early), then 066 (no migration, pure derive-on-read → lower risk). Both are
  3-point full-pipeline stories (spec + quality reviewers, run concurrently).
- **Scope note:** STORY-066 narrowed at refinement to **author-only** — outcome was delivered by
  STORY-072 (sprint 40); the incident-id half split to STORY-081 (draft, deferred: the current
  Statuspage flow never creates incidents and discards the response). Both stories adapt to REAL
  data; MSW fixtures are captured from real wire responses, never invented.

## Preconditions (verified)
- Baseline nine-command `yt_gate.py` green on `main` at cut (throwaway DB up + migrated on the
  dev port; migration head `a2c1d89efcea`). Self-test green (28/28).
- Working tree clean apart from untracked PO artifacts (`.claude/skills/yourteam-main.zip`,
  `frontend/.vercel/`) and an uncommitted `.gitignore` tweak — none are sprint code.
- Mode declared; plan verified by `yt-plan-verifier` before lock (verdict recorded below).

## Verified API contracts

### STORY-065 — Maintenance title + DELETE
- **Current producer shape (no title, no delete):**
  - Domain `MaintenanceWindow` = `{component_id, starts_at, ends_at, reason: str|None, id: int|None}`
    with tz-aware UTC validators + `ends_at > starts_at` (`core/domain/maintenance.py:8-49`).
  - DTOs `MaintenanceWindowDTO` / `CreateMaintenanceRequest` mirror it, no title
    (`api/v1/maintenance/models.py:8-28`).
  - Schema `maintenance_windows` (id, component_id→components.id RESTRICT, starts_at, ends_at,
    reason nullable, created_at) from migration `3a8254bcfe59`; head is `a2c1d89efcea` → the title
    revision chains off `a2c1d89efcea`.
  - Port `MaintenanceRepository` = list_windows / create / is_under_maintenance only
    (`core/ports/maintenance_repository.py:9-47`); Postgres adapter implements only those
    (`adapters/persistence/maintenance_repository.py:23-97`); SQLAlchemy table def at `:13-20`
    (add a `title` column there).
  - Controller: GET + POST only (`api/v1/maintenance/controller.py:20-34`).
  - `_shared/errors.py:23-30` maps `ComponentNotFoundError`/`ProposalNotFoundError`/… → 404 via a
    single dict; add `MaintenanceWindowNotFoundError` there.
- **New work:** `title` nullable column + domain/DTO field; `delete(window_id)` on port + Postgres
  adapter + fake (raise `MaintenanceWindowNotFoundError` on unknown); `DELETE /v1/maintenance/{id}`
  → 204 / 404. First DELETE in the codebase (pattern is otherwise established).
- **Frontend:** form Title input separate from reason (`pages/MaintenancePage.tsx:86,99-109`
  currently maps Title→reason — split them); per-row delete with inline two-step confirm
  (`:249-285`); add `deleteMaintenance` to `api/client.ts:241-257`; delete mutation in
  `features/maintenance/useMaintenance.ts:47-80`. NO `window.confirm`/modal.

### STORY-066 — Publication author (author-only)
- **Author is DERIVED, not captured/persisted:** read the `actor` of the `approved`
  `approval_event` for `publications.proposal_id`.
  `approval_events.actor` is TEXT NOT NULL, written by `core/services/approval.py`; the table is
  from migration `3a8254bcfe59`; the `ck_approval_events_action` CHECK is `IN ('approved',
  'rejected')` (verified — `approval.py::_decide` writes `action=to_state.value` and
  `ProposalState.APPROVED.value == "approved"`, so the `action='approved'` filter is correct, not
  always-null). There is no user/identity concept — actor is an opaque string (frontend seam
  `api/actor.ts` supplies `"dashboard-operator"` today).
- **Derivation must not multiply rows (plan-verifier finding).** `list_recent` derives author via a
  **correlated scalar subquery** — `SELECT actor FROM approval_events WHERE proposal_id =
  publications.proposal_id AND action='approved' LIMIT 1` — NOT a `LEFT JOIN`, so the publication
  row count (and the `LIMIT 50`) is never inflated. This relies on the invariant of **≤1 `approved`
  event per proposal**: domain-guaranteed (`is_valid_transition` blocks re-approval; sole writer is
  `approval.py::_decide`) but NOT DB-enforced (no unique constraint on
  `approval_events(proposal_id, action)`). A defensive parity case pins it: two `approved` events
  for one proposal → still exactly one publication row.
- **Fake seam (plan-verifier finding).** `FakePublicationRepository` (`backend/tests/fakes.py:236-262`)
  today takes no args and stores only publications — it has no author source. Give it an optional
  author-derivation seam: an injected `proposal_id → approved-actor` map (mirroring
  `FakeSampleModeRepository`'s optional shared `store` at `fakes.py:300`), OR a shared
  `FakeProposalRepository` whose `approval_events` it scans for `action=='approved'`. Its
  `list_recent` populates `author` from that seam; `record` must NOT persist an author (AC1:
  derive-on-read only). The contract test seeds each side equivalently — Postgres: insert a proposal
  + an `approved` approval_event; fake: the map/shared repo.
- **Null cases:** `publications.proposal_id` is nullable → author `null`; a proposal with no
  `approved` event → author `null`.
- **Current read path:** `PublicationsService.list_recent` maps domain→DTO directly
  (`api/v1/publications/service.py:21-34`); `Publication` frozen read model
  (`core/domain/publication.py`); `PostgresPublicationRepository.list_recent` selects six columns,
  no join today (`adapters/persistence/publication_repository.py:78-109`); port
  `list_recent(limit=50)` (`core/ports/publication_repository.py:37-46`).
- **No migration** — author adds no column. `check_fk_direction.py` stays 0.
- **Frontend:** `PublicationsPage.tsx:48-50` flags the gap; add `author` to `PublicationDTO` in
  `api/types.ts:159-166`; render in the timeline with graceful null handling.

## STORY-065 — Maintenance title + DELETE (3p, full pipeline)

TDD; commit after every green step. Migrations on the DIRECT URL; fake/adapter parity; tz-aware
validators untouched; five-file shape (feature already has controller/models/service/validation).

- [ ] 1. Failing domain/DTO test: `MaintenanceWindow` + `MaintenanceWindowDTO` +
  `CreateMaintenanceRequest` carry optional `title: str | None = None` distinct from `reason`. Add
  the field; green; commit.
- [ ] 2. Migration: new Alembic revision off `a2c1d89efcea` adds a **nullable** `title` column to
  `maintenance_windows`; `upgrade head` green on the throwaway DB (migrated_db fixture),
  `downgrade -1` drops it cleanly. Commit.
- [ ] 3. Persistence parity (title): SAME contract test vs `PostgresMaintenanceRepository` AND the
  in-memory fake — `create`/`list_windows` round-trip `title` incl. `None`. Add `title` to the
  adapter's SQLAlchemy table def + insert/select mappings. Green; commit.
- [ ] 4. Failing repo test for delete: add `delete(window_id: int) -> None` to the port; implement
  in the Postgres adapter (DELETE by id; raise `MaintenanceWindowNotFoundError` — new exception in
  `core/domain/maintenance.py` — when zero rows affected) and the fake. Parity: delete existing →
  absent from `list_windows`; delete unknown → raises. Green; commit.
- [ ] 5. API: failing endpoint tests — `POST` accepts/persists `title` (present + omitted→null);
  `DELETE /v1/maintenance/{id}` → 204 on success, 404 on unknown (register
  `MaintenanceWindowNotFoundError → 404` in `_shared/errors.py`). Add the service method + the
  `@router.delete` route; existing GET/POST + validation tests stay green. Commit.
- [ ] 6. Frontend (title): split the form's Title input from reason so it posts as `title`; mirror
  the DTO field in `api/types.ts`; **render `window.title` on the windows-list row**
  (`MaintenancePage.tsx:249-285` renders `reason` today — a posted title must actually appear).
  MSW handlers reflect `title`; the create-with-title test must **assert the title RENDERS on the
  created row** (not merely that it was sent in the POST body — otherwise AC4 ships
  green-but-unrendered). Commit.
- [ ] 7. Frontend (delete): `deleteMaintenance(id)` in `client.ts`; delete mutation in
  `useMaintenance`; per-row Delete control with **inline two-step confirm** (no dialog) that
  refreshes on success and shows a non-crashing error on 404; MSW covers delete + delete-404;
  tests. Commit.
- [ ] 8. Gates + wiki blast radius: `yt_wiki.py` sweep, update/re-verify each flagged article
  (commit per article); full `yt_gate.py` green; evidence recorded.

## STORY-066 — Publication author (3p, full pipeline)

- [ ] 1. Failing read-model test: `Publication` gains derive-on-read `author: str | None = None`
  (not persisted by `record`); `PublicationDTO` gains `author: str | None`;
  `PublicationsService.list_recent` threads it. Green on the mapping; commit.
- [ ] 2. Failing persistence-parity test (author derivation) vs Postgres repo AND fake:
  proposal approved by actor X → `author == "X"`; `proposal_id = None` → `None`; proposal with no
  `approved` event → `None`; **and the defensive case** — two `approved` events for one proposal →
  still exactly one publication row (no LIMIT-skewing multiplication). Implement author in
  `list_recent` as a **correlated scalar subquery** over `approval_events` (action='approved'),
  NOT a LEFT JOIN. Add the author-derivation seam to `FakePublicationRepository` (injected
  `proposal_id → approved-actor` map or shared `FakeProposalRepository`) so the fake derives author
  the same way — `record` persists NO author on either side. Seed each side equivalently (Postgres:
  proposal + approved approval_event row; fake: the map). Green; commit.
- [ ] 3. API: failing endpoint test — `GET /v1/publications` serializes `author` (string | null)
  for both an author-present and an author-null row; existing publication tests stay green. Commit.
- [ ] 4. Frontend: add `author` to `PublicationDTO` in `api/types.ts`; render author in the
  Publications timeline with graceful null handling; MSW fixtures (from a real
  `/api/v1/publications` wire capture) include author-present + author-null rows; tests. Commit.
- [ ] 5. Confirm **no migration** was added (story diff has none under `migrations/`);
  `check_fk_direction.py` = 0.
- [ ] 6. Gates + wiki blast radius: `yt_wiki.py` sweep, update/re-verify flagged articles; full
  `yt_gate.py` green; evidence recorded.

## Reality gate (per story, at DoD)
Both are consumer/rendering stories → live render-vs-wire spot check against the running local
stack (throwaway DB + uvicorn :8000 + live loop + vite :5173):
- **065:** create a window with a Title via the UI → confirm it renders on the row and the wire
  `/api/v1/maintenance` row carries `title`; delete it via the inline-confirm control → confirm it
  disappears and a re-fetch omits it.
- **066:** approve a proposal so a publication is recorded with a known actor → confirm the rendered
  Publications row's author matches the `approval_events.actor` for that proposal; confirm a
  null-proposal publication renders gracefully without an author.

## Conventions
In-process mode: `yt-implementer` loads `.scrum/checklists/implementer.md` (binding); reviewers load
theirs. Highlights: migration on the DIRECT URL; fake/adapter parity is mandatory; tz-aware
validation untouched; five-file API shape; no module-scope env side effects; frontend fixtures from
real wire samples; no `window.confirm`/browser dialogs.

## Plan verification
- **Round 1 (yt-plan-verifier, Opus): GAPS.** All contract/line-ref/migration-head checks passed
  — incl. confirming the STORY-071 `action='approve'`→`'approved'` trap resolves in our favor
  (`proposal.py:28` + `approval.py::_decide` + `ck_approval_events_action`), so the 066 author
  filter is correct, not always-null. Three gaps:
  1. (066, blocker) `FakePublicationRepository` (`fakes.py:236-262`) has no approval-event source →
     the "vs Postgres AND fake" test wasn't constructible; the fake must derive author (not
     round-trip a persisted one).
  2. (066, hardening) author join relied on the ≤1-`approved`-per-proposal invariant, which is
     domain-guaranteed but not DB-enforced → a naive LEFT JOIN would multiply rows / skew LIMIT 50.
  3. (065) form split posted `title` but the row still rendered `reason` → AC4 could pass green
     without the title ever rendering.
- **Amendments applied:** 066 contract section + step 2 now specify a correlated scalar subquery
  (not a LEFT JOIN), the ≤1-approved invariant reliance + a defensive two-approved-events parity
  case, and the `FakePublicationRepository` author-derivation seam (derive-on-read, `record`
  persists no author). 065 step 6 now requires rendering `window.title` on the row and asserting it
  renders (not just the POST body).
- **Round 2 (yt-plan-verifier, Opus): LOCK_READY** — zero lock-blocking gaps. All three round-1
  gaps confirmed closed; amendments introduce no new blocker. Re-confirmed: correlated scalar
  subquery adds a labeled column (not a row) against `publication_repository.py:78-109`; the fake
  seam is constructible from `fakes.py` patterns (`:300-307` shared store / `:121,174-191`
  FakeProposalRepository.approval_events); 065 step 6 traces fully to AC4 (title renders + asserted);
  two `approved` rows are insertable (`approval_events` has a CHECK + non-unique index only, no
  unique constraint). Non-blocking note: the two-approved defensive case is only meaningfully
  exercisable on the Postgres side under the map seam (the fake iterates a publications dict so it
  structurally cannot multiply rows) — a 2-minute implementer choice, not a plan defect.
