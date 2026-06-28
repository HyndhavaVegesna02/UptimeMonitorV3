# Sprint 13 — Plan

**Goal:** Extend Zone 6 with the two headline read surfaces — `GET /api/v1/components` (dashboard
component statuses, the *displayed* status per P4) and `GET /api/v1/approvals` (open proposals
awaiting a decision) — adding the two new read ports they need, and clear the two STORY-014 API
minors.

**Branch:** `sprint-13` · **Start tag:** `sprint-13-start` · **Baseline:** `31d6e57` (refinement on
branch; from main `c0ad76c`).

**Committed: 7 pts** — STORY-014b (5) → STORY-035 (2), in that order.

---

## How this sprint runs (external implementation — working-agreements.md 2026-06-26)
The **PO implements this plan externally** onto `sprint-13`; the orchestrator does NOT dispatch
implementers. This `plan.md` is the only contract — self-contained. When ready, say **"do your
review"**; the orchestrator diffs `sprint-13-start..HEAD`, runs the full six-command DoD gate, runs
the Opus spec + quality reviewers on STORY-014b (3+ pts), resolves the wiki blast radius, then
review → verdict → merge → retro.

**TDD + commit-after-every-green-step. Scoped staging only (never `git add -A`).**

### The six-command DoD gate (every story)
1. `pytest` 2. `lint-imports` (**4 kept / 0 broken** — `components`+`approvals` added to the
existing `api-feature-independence` contract; count stays 4) 3. `python scripts/check_fk_direction.py`
4. `alembic upgrade head` 5. `ruff check .` 6. `ruff format --check .` — all exit 0.
DB-gated commands use `scripts/dev_db.py up` → run → `down` (see CLAUDE.md). **No new migration this
sprint** (014b reads existing spine tables; 035 is composition/test cleanup).

### Established facts the implementer builds on
- `create_app(*, database_url=None, proposal_repo=None, clock=None)` (`composition/app.py`) wires
  repos into `app.state` and mounts `src.api.v1.router` under `/api/v1`. Test injection is via the
  `*_repo`/`clock` params (fakes) — see `backend/tests/test_decisions.py`.
- DI dependencies live in `src/api/dependencies.py` (`get_approval_service(request)` →
  `request.app.state.approval_service`). Each feature's DI provider lives in **its own `service.py`**
  so the controller imports only its `models`+`service` (api-five-file-convention.md / STORY-014 fix).
- `components` table columns: `id:text PK`, `app_id:text FK→apps`, `name:text`, `status:text`
  (CHECK in `operational|degraded|partial_outage|major_outage`, default `operational`),
  `created_at`, `updated_at`. `status` maps to `core/domain/status.py::ComponentStatus`.
- Read-adapter idiom: see `PostgresProposalRepository.get_open` (a `WHERE`-filtered SELECT mapped to
  a domain type) and `PostgresWatermarkRepository`. Fakes live in `backend/tests/fakes.py`.

---

## STORY-014b — Dashboard + Approvals read endpoints (5 pts) — DO FIRST

Pipeline: **gate + Opus spec & quality reviewers.** Spans core (new read type + 2 ports),
adapters (2 Postgres impls + fakes), api (2 five-file features), composition (wiring). All PURE
READS — no writes, so the 2026-06-28 TOCTOU agreement does not apply here.

### Phase A — `Component` domain read type (TDD)
- [x] **A1** Add `backend/src/core/domain/component.py::Component` — frozen pydantic read model:
      `id: str`, `name: str`, `status: ComponentStatus`, `app_id: str`. Module + class docstring cite
      dossier §9 (spine topology) / §17. Export it from `core/domain/__init__.py` if peers are
      exported there. Test: constructs from valid fields; `status` accepts a `ComponentStatus`.

### Phase B — `ComponentRepository` port + adapter + fake (TDD)
- [x] **B1** Failing test (`backend/tests/test_core_ports.py`): `FakeComponentRepository.list_components()`
      returns the injected components, and returns `[]` when empty.
- [x] **B2** Add `backend/src/core/ports/component_repository.py::ComponentRepository` (abstract
      `list_components(self) -> list[Component]`, docstring: "all components from the spine; `[]` if
      none"); export from `core/ports/__init__.py`; implement `FakeComponentRepository` in
      `backend/tests/fakes.py`. Green. Commit.
- [x] **B3** Failing **DB-gated** test (`backend/tests/test_persistence_adapters.py`, `migrated_db`
      fixture): `PostgresComponentRepository.list_components` returns mapped `Component`s for seeded
      rows and `[]` for an empty table. Fake/adapter parity (empty → `[]` for both).
- [x] **B4** Implement `backend/src/adapters/persistence/component_repository.py::PostgresComponentRepository(engine)`
      — `SELECT id, name, status, app_id FROM components`, mapping `status` text →
      `ComponentStatus(...)`. Green. Commit.

### Phase C — `ProposalRepository.list_open` (TDD)
- [x] **C1** Failing test: `FakeProposalRepository.list_open()` returns all OPEN proposals; `[]` when
      none.
- [x] **C2** Add abstract `list_open(self) -> list[StatusProposal]` to
      `core/ports/proposal_repository.py::ProposalRepository` (docstring states the empty contract);
      implement on `FakeProposalRepository`. Green. Commit.
- [x] **C3** Failing DB-gated test: `PostgresProposalRepository.list_open` SELECTs
      `WHERE state = 'open'`, returns mapped proposals; `[]` when none. Parity with fake.
- [x] **C4** Implement on `PostgresProposalRepository`. Green. Commit.

### Phase D — `api/v1/components/` five-file feature + wiring (TDD)
- [x] **D1** `models.py`: `ComponentDTO {id: str, name: str, status: str}` (DTO, NOT the `Component`
      domain type). `validation.py`: present per the five-file convention; for a no-input GET it
      carries only a module docstring (no validators). Failing TestClient test
      (`backend/tests/test_components_endpoint.py`): `GET /api/v1/components` → 200 + list of DTOs;
      **empty case** → 200 + `[]`.
- [x] **D2** `service.py`: thin — resolve `ComponentRepository` via the container, `list_components()`,
      map → `ComponentDTO`s; plus the DI provider `get_components_service` (lives here, imports
      `get_component_repo` from `src.api.dependencies`). `controller.py`: `GET /components` route,
      imports only this feature's `models`+`service`. `__init__.py`: router re-export.
      Wire it: add `component_repo: ComponentRepository | None = None` param to `create_app`, default
      to `PostgresComponentRepository(engine)`, store `app.state.component_repo`; add
      `get_component_repo(request)` to `src/api/dependencies.py`; register the components router in
      `src/api/v1/__init__.py` (same as `decisions`/`health`). Green. Commit. Docstrings cite §13/§17.

### Phase E — `api/v1/approvals/` five-file feature + wiring (TDD)
- [x] **E1** `models.py`: `ProposalDTO {id: int, component_id: str, from_status: str | None,
      to_status: str, state: str, proposed_at: datetime}`. Failing TestClient test
      (`backend/tests/test_approvals_endpoint.py`): `GET /api/v1/approvals` → 200 + open proposals;
      a **mix of open + terminal** → only the open ones; **empty** → `[]`.
- [x] **E2** `service.py`: thin — resolve the proposal repo via the container, `list_open()`, map →
      `ProposalDTO`s; DI provider `get_approvals_service` (uses `get_proposal_repo` from
      `src.api.dependencies`). `controller.py`: `GET /approvals`. Wire: add `get_proposal_repo(request)`
      → `request.app.state.proposal_repo` to `dependencies.py` (the repo is already in `app.state`
      from STORY-014); register the approvals router. Green. Commit.

### Phase F — 4th-contract module list
- [x] **F1** Add `"src.api.v1.components"` and `"src.api.v1.approvals"` to the
      `api-feature-independence` contract's `modules` list in `pyproject.toml`. Run `lint-imports` →
      **4 kept / 0 broken**. (Contract COUNT unchanged → no DoD/CLAUDE command-sync needed.)

### Phase G — wiki forward-blast-radius (DoD)
- [x] **G1** `canonical-types-and-ports.md`: add Facts for the `Component` read type, the
      `ComponentRepository` port, and `ProposalRepository.list_open`; bump `verified_sha`.
- [x] **G2** `persistence-adapters.md`: add Facts for `PostgresComponentRepository.list_components`
      and `PostgresProposalRepository.list_open`; bump `verified_sha`.
- [x] **G3** `api-five-file-convention.md`: note `components`+`approvals` as the read-feature
      instances in the independence list; bump `verified_sha`. (Use symbol citations
      `file.py::Symbol` — working-agreements.md 2026-06-27.)

### Phase H — full gate
- [x] **H** All SIX commands exit 0 (throwaway DB up for FK/alembic/DB-gated pytest). No migration.

**AC mapping:** AC1 ← D; AC2 ← E; AC3 ← B+C (+ DTO distinctness tests); AC4 ← D/E shape + F;
AC5 ← H + G.

---

## STORY-035 — API minors (2 pts, gate only) — DO SECOND

(After 014b, so engine-disposal is added to the final `app.py` that already wires the new repos.)

- [x] **035.1 — dispose the engine on shutdown.** Give `create_app` a FastAPI `lifespan` (or shutdown
      handler) that calls `app.state.db_engine.dispose()` on shutdown when `db_engine` is not `None`
      (it is `None` when repos were injected for tests). Test: drive the app through its lifespan
      (e.g. `with TestClient(app):` triggers startup/shutdown) and assert `dispose` is invoked
      (spy/patch on a fake engine, or assert no connection leak across instances). Commit.
- [x] **035.2 — clear the TestClient/httpx deprecation.** Resolve
      `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install
      httpx2 instead`. Pick the mechanism against current Starlette/FastAPI guidance — pin/upgrade
      `httpx` in `pyproject.toml`, adopt the recommended successor, or (last resort, with a written
      justification in the story History) a targeted `filterwarnings` for exactly that warning.
      **AC bar:** the warning no longer appears in the `pytest` run AND the endpoint tests still pass
      (e.g. confirm with a focused `pytest -W error::DeprecationWarning backend/tests/test_decisions.py`
      or a clean warnings summary). A dependency change here is sanctioned (planning-time tooling
      decision). If it changes install/run commands, command-sync applies (it should not). Commit.
- [x] **035.3** Full SIX-command gate green.

---

## Standing conventions checklist (binds all new code — working-agreements.md 2026-06-27)
- [x] Module + public class/function docstrings citing the relevant dossier §.
- [x] Empty-input behavior tested for every new read method (`list_components`/`list_open` → `[]`).
- [x] Port fake and real adapter AGREE on edge cases (run the empty-case contract against both).
- [x] DTOs distinct from domain types; DI provider in the feature `service.py`; controller imports
      only its models+service.
- [x] Scoped staging; follow existing import/naming/structure patterns.


## Notes / risks
- 014b's two new read ports + two features are the bulk; if a phase balloons past its share, mark the
  story Blocked with the specific obstacle rather than guessing.
- No MCP/CLI tooling change beyond the possible `httpx` pin in 035.
