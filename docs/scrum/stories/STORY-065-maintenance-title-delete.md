---
id: STORY-065
title: Maintenance title field + DELETE endpoint
type: feature
---

## Context
Filed 2026-07-07 from the Sprint 38 redesign data-gap analysis. The mock's Maintenance form has a
"Title" field and each window row has a delete button. Today `MaintenanceWindowDTO` has only
`reason` (no title) and the API exposes only `GET`/`POST /v1/maintenance` — no DELETE
(`api/v1/maintenance/controller.py:20-34`; the controller comment at `:222-223` explicitly defers
delete to this story). STORY-061 maps the form's Title↔`reason` and omits delete; this story adds
the real capability.

Refined 2026-07-13 (Sprint 45 planning) from a read-only scout probe. Findings:
- No `title` anywhere: domain `MaintenanceWindow` (`core/domain/maintenance.py:8-26`), the DTOs
  (`api/v1/maintenance/models.py:8-28`), and the schema (`maintenance_windows`, migration
  `3a8254bcfe59`) all lack it. Current migration head is `a2c1d89efcea`.
- No delete anywhere: the `MaintenanceRepository` port has only `list_windows`/`create`/
  `is_under_maintenance` (`core/ports/maintenance_repository.py:9-47`); the Postgres adapter
  implements only those (`adapters/persistence/maintenance_repository.py:23-97`). This would be the
  **first DELETE endpoint in the codebase** — but the five-file convention and the centralized
  `NotFoundError → 404` registry (`api/v1/_shared/errors.py:23-30`) are already in place.
- Frontend maps a "Title" input to `reason` on POST today (`pages/MaintenancePage.tsx:86,99-109`);
  the windows list (`:249-285`) has no delete control; `client.ts:241-257` has no
  `deleteMaintenance`; `useMaintenance.ts:47-80` has no delete mutation.

## Description
Add an optional `title` (distinct from `reason`) to the maintenance window model/DTO + a schema
column, and a `DELETE /v1/maintenance/{id}` endpoint (five-file conventions; repository `delete`
method on the port + Postgres adapter + fake; 404 on unknown id via the `_shared` registry). Then
the frontend adds a real Title field (separate from the reason/notes) and a per-row delete action
that honors the no-browser-dialog constraint.

## PO-approved design decisions (2026-07-13)
- `title` gets its own **nullable column**, distinct from `reason` (matches the mock; `reason`
  stays for the longer explanation). Not a rename of `reason`.
- Delete is a **hard delete** (no soft-delete / audit-retention requirement).
- The frontend delete control uses an **inline two-step confirm** (e.g. button → "Confirm?" inline
  state). NO `window.confirm`, no modal dialog — browser dialogs are banned (CLAUDE.md / Chrome
  automation constraint) and no modal primitive exists yet.

## Acceptance Criteria
- [ ] **AC1 (title — model + schema).** `MaintenanceWindow` (domain), `MaintenanceWindowDTO`, and
  `CreateMaintenanceRequest` gain an optional `title: str | None` (default `None`), distinct from
  `reason`. A new Alembic revision chained off `a2c1d89efcea` adds a **nullable** `title` column to
  `maintenance_windows`; `alembic upgrade head` and `alembic downgrade -1` both exit 0 on the
  throwaway DB. `check_fk_direction.py` still exits 0 (no new FK).
- [ ] **AC2 (title — persistence parity).** The SAME contract test against
  `PostgresMaintenanceRepository` AND the in-memory fake round-trips `title` through
  `create`/`list_windows`, including the `None` case. `POST /v1/maintenance` accepts and persists
  `title` when provided; omitted → `null`; existing `reason` behavior is unchanged.
- [ ] **AC3 (DELETE endpoint).** `DELETE /v1/maintenance/{window_id}` removes the window and
  returns **204** (no body) on success. Unknown id raises a new
  `MaintenanceWindowNotFoundError` (in `core/domain/maintenance.py`), registered in
  `_shared/errors.py` to map to **404** with `{"detail": ...}`. The `MaintenanceRepository` port
  gains `delete(window_id: int) -> None` (raising on unknown), implemented by the Postgres adapter
  and the fake, with parity tests: delete existing → absent from a subsequent `list_windows`;
  delete unknown → `MaintenanceWindowNotFoundError`.
- [ ] **AC4 (frontend — title).** The Maintenance form has a real **Title** input, separate from
  the reason/notes field, that posts as `title` and round-trips (the value shows on the created
  window row). MSW handlers reflect the `title` field.
- [ ] **AC5 (frontend — delete).** Each window row has a **Delete** control that calls
  `DELETE /v1/maintenance/{id}` and refreshes the list on success, using an **inline two-step
  confirm** (no `window.confirm`, no modal). A 404 from a concurrent delete surfaces a non-crashing
  error state. MSW handlers cover delete-success and delete-404.
- [ ] **Gates + wiki blast radius.** Full nine-command `yt_gate.py` green; `yt_wiki.py` sweep clean
  (any article whose `code_refs` this diff touches is updated/re-verified).

## History
- 2026-07-07: filed from the redesign data-gap analysis. Status: draft (needs refinement + estimate).
- 2026-07-13: refined at Sprint 45 planning (scout probe recorded above); estimate **3**; PO design
  decisions recorded; scheduled into Sprint 45 (with STORY-066 author-only). Status: ready.
