---
id: STORY-036
title: Maintenance feature module — repository + Maintenance tab (list + schedule)
type: feature
---

## Context
Spec: dossier §9 (modularity model — a stateful feature attaching to the spine) + §10 (maintenance
short-circuits collapse, excluded from availability both sides) + §17 (Maintenance tab) + the
deferred-auth agreement (2026-06-23; actor self-declared until auth lands). Zone 6 (+ a thin core
read seam). Surfaced by Sprint 13 planning: the Maintenance tab had no backing repository/endpoint.

**Corrected at Sprint 14 refinement (investigation):**
- The **`maintenance_windows` table ALREADY EXISTS** (spine schema, STORY-006):
  `id BIGSERIAL PK`, `component_id TEXT FK→components (RESTRICT)`, `starts_at TIMESTAMPTZ`,
  `ends_at TIMESTAMPTZ`, `reason TEXT NULL`, `created_at TIMESTAMPTZ`. **No migration needed.**
- There is **no pipeline orchestration** running collapse→…→decide per cycle yet (the pull loop only
  ingests). `under_maintenance` is an INJECTED seam in `pipeline.py::collapse` and the
  `availability.py` calculator's `maintenance(at)` callable. So this story does NOT wire maintenance
  into a live pipeline (nothing to wire into); it PROVIDES the repository query
  (`is_under_maintenance(component_id, at)`) that a future orchestration + the availability callable
  will consume. (Pipeline wiring tracked separately when an orchestration story exists.)

## Description
1. **Core — domain type + read seam:**
   - `core/domain/maintenance.py::MaintenanceWindow` (frozen pydantic: `component_id:str`,
     `starts_at:datetime`, `ends_at:datetime`, `reason:str|None=None`, `id:int|None=None`).
     UTC-aware validation on `starts_at`/`ends_at` (mirror `proposal.py::StatusProposal`), AND a
     `model_validator(mode="after")` enforcing the coherence invariant `ends_at > starts_at`
     (frozen-type agreement, 2026-06-26) + test of both rejected and valid shapes.
   - `core/ports/maintenance_repository.py::MaintenanceRepository`:
     `list_windows() -> list[MaintenanceWindow]` (all, ordered by `starts_at`; `[]` if none),
     `create(window) -> MaintenanceWindow` (INSERT; returns persisted with assigned `id`),
     `is_under_maintenance(component_id, at) -> bool` (True iff a window covers `at`:
     `starts_at <= at < ends_at`). Export from `core/ports/__init__.py`.
2. **Adapters — Postgres impl + fake** against the existing `maintenance_windows` table, with
   fake/adapter parity (empty→`[]`; `is_under_maintenance` agrees; `create` returns id). DB-gated
   adapter tests.
3. **API — `api/v1/maintenance/` five-file feature:**
   - `GET /api/v1/maintenance` → list windows (DTOs).
   - `POST /api/v1/maintenance` → schedule a window (body: component_id, starts_at, ends_at, reason;
     `actor` self-declared per deferred-auth) → 201/200 with the created window DTO.
   - `validation.py` (stdlib-only) does syntactic checks (required fields, parseable timestamps);
     the `ends_at > starts_at` SEMANTIC invariant is enforced by the domain type (a 422 if violated).
   - Thin `service.py` (DI provider lives here); `controller.py` imports only models+service; DTOs
     distinct from `MaintenanceWindow`. Add `src.api.v1.maintenance` to the `api-feature-independence`
     contract module list (count stays — well, see note; contract COUNT unchanged at the value it is
     after STORY-038; just extend the module list → no command-sync).

## Acceptance Criteria (refined — PO-approved 2026-06-28)
- [ ] **AC1 (domain type + invariant):** `MaintenanceWindow` is frozen, validates UTC-aware
      `starts_at`/`ends_at`, and a `model_validator(mode="after")` rejects `ends_at <= starts_at`.
      Tested: valid shape constructs; `ends_at <= starts_at` and naive datetimes raise.
- [ ] **AC2 (repository + parity):** `MaintenanceRepository` exists with `list_windows`, `create`,
      `is_under_maintenance`; Postgres adapter (against the existing table) + fake both implemented;
      DB-gated tests exercise the adapter; fake and adapter AGREE on: empty→`[]`, `create` returns a
      persisted window with `id`, and `is_under_maintenance` boundary (`starts_at <= at < ends_at`,
      i.e. inclusive start / exclusive end — test the exact boundaries and a non-covered time).
- [ ] **AC3 (GET list):** `GET /api/v1/maintenance` → 200 with the windows as DTOs (distinct from the
      domain type); empty case → 200 + `[]`.
- [ ] **AC4 (POST create):** `POST /api/v1/maintenance` with a valid body creates a window
      (persisted, returned with `id`); a body with `ends_at <= starts_at` → **422** (the domain
      invariant, surfaced before/at persistence); a malformed body (missing field / unparseable
      timestamp) → **422** from validation BEFORE the core/DB call.
- [ ] **AC5 (five-file shape + boundary):** the feature has exactly the five files (§13 import
      rules); a test asserts the five-file shape (working-agreements.md 2026-06-28); `lint-imports`
      stays green with `maintenance` added to `api-feature-independence`.
- [ ] **AC6 (full DoD gate green + blast radius):** all SIX commands exit 0; no new migration.
      `canonical-types-and-ports.md` (MaintenanceWindow + MaintenanceRepository),
      `persistence-adapters.md` (PostgresMaintenanceRepository), `api-five-file-convention.md`
      (maintenance feature), `architecture-boundary.md` (independence module list) updated + re-verified.

## Conventions checklist (binds the external implementer)
- Module + public class/function docstrings citing the relevant dossier § (mirror peers).
- Frozen `MaintenanceWindow` enforces `ends_at > starts_at` with a `model_validator` + test (2026-06-26).
- Empty-input tested for `list_windows`; boundary tested for `is_under_maintenance` (2026-06-25).
- Fake and real adapter AGREE on edges (2026-06-26).
- Five-file-shape test shipped with the feature (2026-06-28).
- DI provider in the feature `service.py`; controller import-clean. Scoped staging.
- `create`/`POST` is an INSERT, not a check-then-act read-modify-write → the 2026-06-28 TOCTOU
  agreement does NOT apply (no guarded conditional write here).

## Resolved Questions
- **Scope → read + create** (GET list + POST schedule). (PO, 2026-06-28.)
- **Table exists → no migration.** (Investigation, 2026-06-28.)
- **No pipeline wiring this story** (no orchestration exists); the repo provides
  `is_under_maintenance` for a future consumer. (Investigation, 2026-06-28.)
- **Auth deferred** — `actor` on POST is self-declared, consistent with the 2026-06-23 agreement.

## History
- 2026-06-28: created from Sprint 13 planning (Maintenance tab had no backing repository/endpoint).
- 2026-06-28 (Sprint 14 refinement): corrected — table already exists (no migration); no pipeline to
  wire (provides the query instead); scoped to read+create (PO). Estimate **5** (domain type +
  invariant + 3-method repo port/adapter/fake + two-endpoint five-file feature + contract + wiki).
  Status: draft → ready.
