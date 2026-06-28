---
id: STORY-014b
title: API read endpoints — Dashboard (component statuses) + Approvals list
type: feature
---

## Context
Spec: dossier §13 (five-file convention) + §17 (six-tab IA) + P4 (availability vs status:
the Dashboard shows the *stable displayed status*, never the availability %). Zone 6.
Follow-up to STORY-014 (which established the five-file convention, the app factory + provider,
and the 4th import-linter contract via the decision/approve exemplar). This story adds the
**two headline read surfaces** the operator dashboard centers on:
- **Dashboard** — list each component with its current displayed status.
- **Approvals** — list the open status proposals awaiting a human decision (the read half;
  the approve/reject *write* already shipped in STORY-014 at `POST /api/v1/decisions/{id}`).

**Scope (PO decision, 2026-06-28).** The four-tab read surface is an 8 and must split. This
story takes **Dashboard + Approvals-list** (both need NEW read ports). The detail tabs
**Availability + Check History** (which reuse existing backing) move to **STORY-014c**.
**Maintenance + Publications** have NO backing state and become their own feature-module stories
(STORY-036, STORY-037) — they cannot be read endpoints until that state exists.

Both new endpoints are pure reads of the spine: the Dashboard reads `components.status` (the
human-approved displayed status, seeded/updated via the proposal lifecycle — NOT computed here),
and Approvals reads open `status_proposals`. No business logic at the edge.

## Description
1. **Core — two new read ports + one read domain type:**
   - `core/domain/component.py::Component` (frozen read model: `id`, `name`, `status:ComponentStatus`,
     and the spine fields the dashboard needs — pin exact columns against `components` in the plan).
   - `core/ports/component_repository.py::ComponentRepository` with
     `list_components() -> list[Component]` (reads the spine; returns `[]` when none).
   - Extend `core/ports/proposal_repository.py::ProposalRepository` with
     `list_open() -> list[StatusProposal]` (all open proposals across components; `[]` when none).
2. **Adapters — Postgres implementations** of `ComponentRepository.list_components` and
   `PostgresProposalRepository.list_open`, plus the in-memory fakes (`tests/fakes.py`) — fake and
   adapter must AGREE (empty -> `[]` for both).
3. **API — two five-file features:**
   - `api/v1/components/` — `GET /api/v1/components` -> list of component DTOs (id, name, status).
   - `api/v1/approvals/` — `GET /api/v1/approvals` -> list of open-proposal DTOs.
   Each: thin `service.py` (call the read port via the container -> shape DTOs), `models.py`
   (response DTOs, NOT domain types), `validation.py` (stdlib-only; near-empty for these GETs),
   `controller.py` (route only — imports ONLY this feature's models + service; the DI provider
   lives in the feature `service.py`, per `api-five-file-convention.md`), `__init__.py`.
4. **4th contract upkeep:** add `src.api.v1.components` and `src.api.v1.approvals` to the
   `api-feature-independence` independence contract's module list in `pyproject.toml`. (Contract
   COUNT is unchanged at 4 -> no DoD/CLAUDE command-sync needed; just keep the module list current.)

## Acceptance Criteria (refined — PO-approved 2026-06-28)
- [ ] **AC1 (Dashboard read):** `GET /api/v1/components` returns 200 with a list of components, each
      carrying its id, display name, and current `status` read from `components.status` (the displayed
      status, per P4 — NOT availability %). Tested (TestClient, repository faked) with: several
      components, and the **empty case** (no components -> 200 + `[]`, not 500).
- [ ] **AC2 (Approvals list read):** `GET /api/v1/approvals` returns 200 with the list of OPEN
      status proposals (id, component, from/to status, proposed_at). Tested with: multiple open
      proposals, a mix of open + terminal (only open returned), and the **empty case** (-> 200 + `[]`).
- [ ] **AC3 (new read ports + parity):** `ComponentRepository.list_components()` and
      `ProposalRepository.list_open()` exist on the ports with Postgres adapters + fakes; a DB-gated
      test exercises each adapter, and the fake and adapter AGREE on the empty case (both `[]`). DTOs
      are distinct from the `Component`/`StatusProposal` domain types (no domain leak to the client).
- [ ] **AC4 (five-file shape + boundary):** each new feature has exactly the five files with the §13
      import rules (controller imports only its models + service; service may import core + container;
      validation stdlib-only); `lint-imports` reports **4 kept / 0 broken** with
      `components` + `approvals` added to the `api-feature-independence` module list; a test asserts
      each feature's five-file shape.
- [ ] **AC5 (full DoD gate green):** all SIX commands exit 0. No new migration (reads existing spine
      tables). Forward blast radius: `canonical-types-and-ports.md` (new ports + `Component` type),
      `persistence-adapters.md` (new adapters), `api-five-file-convention.md` (new features) updated
      + re-verified.

## Conventions checklist (binds the external implementer — working-agreements.md 2026-06-27)
- Module + public class/function docstrings citing the relevant dossier § (mirror peers).
- Empty-input behavior tested for every new read method (no components / no open proposals -> `[]`).
- Fake and real adapter AGREE on edge cases (working-agreements.md 2026-06-26).
- DI provider in the feature `service.py`, controller import-clean (api-five-file-convention.md).
- Scoped staging; follow existing import/naming/structure patterns.
- (No check-then-act writes here — these are pure reads — so the 2026-06-28 TOCTOU agreement
  does not apply to this story.)

## Resolved Questions
- **Which two tabs → Dashboard + Approvals-list** (the new-read-port pair). Availability + Check
  History → STORY-014c. (PO, 2026-06-28.)
- **Maintenance + Publications → deferred** to feature-module stories STORY-036 / STORY-037 (no
  backing state exists; they own new inward-FK'd tables per the dossier §9 modularity model).
- **Dashboard shows displayed status, not availability** (P4) — a pure read of `components.status`.

## History
- 2026-06-28: created from the STORY-014 exemplar-first split; refined + re-scoped (PO) to
  Dashboard + Approvals-list with the two new read ports. Estimate **5** (2 read features + 2 new
  ports + adapters + a read domain type + tests; patterns established by STORY-014). Status: draft
  → ready.
