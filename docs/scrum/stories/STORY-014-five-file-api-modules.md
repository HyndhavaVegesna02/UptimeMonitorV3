---
id: STORY-014
title: Five-file API convention + the 4th linter contract + decision exemplar
type: feature
---

## Context
Spec: dossier §13 (five-file API convention) + §12 (proposal lifecycle, approve/reject)
+ T1.1 (commit-first, best-effort side effects). Zone 6 — the edge's *shape*; the
boundary governs where logic lives. This story OPENS Zone 6: it stands up the FastAPI
app + a composition provider/app-factory, establishes the five-file feature convention
for ONE exemplar feature, and adds the dossier-§13 "fourth linter contract" forbidding
horizontal feature imports.

**Exemplar-first scope (PO decision, 2026-06-28).** This story lands the *pattern + the
boundary + one full vertical slice*, not all six tabs. The exemplar is the **decision
(approve/reject) feature** — the highest-value endpoint (it mutates state via the proposal
lifecycle) and the one most stories depend on. The five read-only tab endpoints (Dashboard,
Availability, Check History, Maintenance, Publications) are deferred to **STORY-014b**.

The edge `service.py` stays THIN: it validates HTTP input, calls a CORE service via the
composition container, and shapes the HTTP result — it holds no business logic and imports
no other feature. The approve/reject orchestration (get the open proposal → validate the
transition → resolve + record the approval event → best-effort publish) is business logic,
so it lands as a new pure core service `ApprovalService` (`core/services/`), port-backed and
provider-blind. There is no approval *service* today — only `ProposalRepository.resolve` +
`record_approval_event` (`core/ports/proposal_repository.py`); this story adds the
orchestration that sits above them.

## Description
1. **Core** — add `core/services/approval.py::ApprovalService` (pure, port-backed):
   `approve(proposal_id, *, actor, notes, now)` and `reject(...)`. Each: load the proposal
   (via a port lookup by id — see Open-Q resolution below), guard that it is OPEN
   (`is_valid_transition`, `proposal.py::is_valid_transition`), `resolve(...)` to the terminal
   state, and `record_approval_event(...)`. Edge/error behavior is specified explicitly (see AC).
2. **Composition** — add a FastAPI **app factory** + a small **provider/container** that
   constructs the SQLAlchemy `Engine` from `Settings` (`composition/settings.py`), builds the
   `PostgresProposalRepository` + a `Clock`, wires `ApprovalService`, and mounts the v1 router.
   Composition is the only zone that may import both core and adapters (dossier §4).
3. **API** — `api/v1/decisions/` as the five-file module: `__init__.py` (router re-export) /
   `controller.py` (routes, status codes — NO logic) / `models.py` (pydantic HTTP request +
   response DTOs, NOT canonical domain types) / `validation.py` (syntactic input checks,
   stdlib only) / `service.py` (THIN: validate → call `ApprovalService` via the container →
   shape the HTTP result). Plus a tiny `api/v1/health/` feature so the independence contract
   is non-vacuous and the app has a liveness route.
4. **4th import-linter contract** — add an `independence` contract over the `api.v1.*` feature
   packages (`src.api.v1.decisions`, `src.api.v1.health`) to `[tool.importlinter]` in
   `pyproject.toml`, so `api.v1.<a>` may never import `api.v1.<b>`. **Command-sync agreement
   applies**: this changes the boundary the DoD floor enforces, so `.scrum/definition-of-done.md`
   note (the lint-imports line now covers 4 contracts) + CLAUDE.md (the §4 contract count) are
   updated in the SAME commit. (`lint-imports` is already a DoD command — no new command,
   so no new gate line, just the contract count.)

## Acceptance Criteria (refined — PO-approved 2026-06-28)
- [x] **AC1 (five-file shape, §13):** `api/v1/decisions/` contains exactly the five files with
      the dossier-§13 responsibilities and import rules: `controller.py` imports only
      models/validation/service; `models.py` pydantic DTOs only (no canonical domain types
      leak to the client); `validation.py` stdlib only (no services); `service.py` imports core
      + the container, never another feature. A test asserts the module shape + that DTOs are
      distinct from domain types.
- [x] **AC2 (4th contract — no horizontal feature imports):** a 4th `independence` import-linter
      contract over the `api.v1` feature packages is live and `lint-imports` reports **4 contracts
      kept, 0 broken**. A regression test (or a deliberately-reverted spike noted in the story)
      confirms the contract BREAKS if `decisions/service.py` imports `health` (proving it is not
      vacuous). `.scrum/definition-of-done.md` + CLAUDE.md updated in the same commit
      (command-sync agreement).
- [x] **AC3 (thin edge, logic in core):** the approve/reject business logic lives in
      `core/services/approval.py::ApprovalService`; `decisions/service.py` holds only
      validate→delegate→shape. `lint-imports` core-independence stays KEPT (core imports no
      FastAPI/adapter). A unit test exercises `ApprovalService` directly with a fake
      `ProposalRepository` + a fixed `Clock` — no HTTP, no DB.
- [x] **AC4 (decision endpoint — happy + edge paths):** the approve/reject endpoint(s) under
      `/api/v1/decisions/...` are served by the app factory and tested (FastAPI `TestClient`,
      repository faked):
      - approve an OPEN proposal → 200, proposal resolves to `APPROVED`, an approval event is
        recorded with the supplied `actor`/`notes`;
      - reject an OPEN proposal → 200, resolves to `REJECTED`, event recorded;
      - the proposal does not exist → **404**;
      - the proposal is already terminal (not OPEN) → **409** (the `is_valid_transition` guard),
        no event recorded;
      - malformed body (missing `actor`, unknown `action`) → **422** from `validation.py`
        BEFORE any core/DB call.
- [x] **AC5 (best-effort side effects, T1.1):** the approval path commits the DB resolution
      FIRST; any post-commit publish/notify is best-effort (a failure there is logged, not
      raised — the proposal is already resolved). Tested: a failing publisher does not 500 the
      approve call nor un-resolve the proposal. *(If publish-on-approve is out of this exemplar's
      wiring, AC5 reduces to "the endpoint commits via the repository before returning"; the plan
      states which.)*
- [x] **AC6 (full DoD gate green):** all SIX DoD commands exit 0 (`pytest`, `lint-imports` [now
      4/0], `check_fk_direction.py`, `alembic upgrade head`, `ruff check`, `ruff format --check`).
      No new migration unless a schema gap is found (none expected — proposals/approval-events
      tables exist from STORY-012). Forward blast radius: `architecture-boundary.md` (the import
      contracts) is updated for the 4th contract and re-verified.

## Conventions checklist (binds the external implementer — working-agreements.md 2026-06-27)
- Module + public class/function **docstrings citing the relevant dossier §** (mirror peers:
  `ingest_service.py`, `pipeline.py`, `decide.py`, `status.py`).
- New frozen value/result DTOs enforce any cross-field coherence invariant with a
  `model_validator(mode="after")` + test.
- Empty-input / edge behavior tested for every new port-touching method (the 404/409/422 paths
  ARE these for the decision endpoint).
- Scoped staging (never `git add -A`); follow existing import/naming/structure patterns.
- The fake `ProposalRepository` used in tests and the real `PostgresProposalRepository` must
  AGREE on edge behavior (working-agreements.md 2026-06-26) — the not-found / already-terminal
  cases run against BOTH where DB-gated.

## Resolved Questions
- **Endpoint list (§13 AC4) → exemplar only.** This story serves the decision (approve/reject)
  feature; the six tabs' read endpoints move to STORY-014b. (PO, 2026-06-28.)
- **4th linter contract → YES, now.** An `independence` contract over the `api.v1` feature
  packages, added in this story with the command-sync doc update. (PO, 2026-06-28.)
- **Proposal lookup by id.** `ApprovalService.approve/reject` need to load a proposal by its
  `proposal_id` (the endpoint's path param), but `ProposalRepository` today exposes only
  `get_open(component_id)`. **The plan adds a `get(proposal_id) -> StatusProposal | None`
  method to the port + both implementations (fake + Postgres) with the not-found contract,
  per the "plan states edge behavior + fake/adapter parity" agreements.** (Surfaced at
  refinement 2026-06-28; folded into scope — small, port-backed.)

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §13. Status: draft.
- 2026-06-28 (refinement): re-scoped exemplar-first (PO); open questions resolved; AC rewritten
  to the decision-feature vertical slice + the 4th linter contract; surfaced the `get(proposal_id)`
  port gap and folded it in. Estimate held at **5** (meaty: app factory + provider + new core
  service + one five-file feature + 4th contract + tests; patterns are well-established). Read
  endpoints split out to STORY-014b. Status: draft → ready.
- 2026-06-28 (implementation): completed by Antigravity under sprint-12. Verified that the fourth contract breaks when `decisions/service.py` imports `health` (reverted). All six DoD gate checks pass. Status: ready → done.
