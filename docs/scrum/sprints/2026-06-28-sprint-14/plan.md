# Sprint 14 — Plan

**Goal:** Stand up the Maintenance feature module — a `MaintenanceRepository` over the EXISTING
`maintenance_windows` table + a functional Maintenance tab (`GET` list + `POST` schedule at
`/api/v1/maintenance`) — and harden the import floor with the 5th `src→tests` linter contract.

**Branch:** `sprint-14` · **Start tag:** `sprint-14-start` · **Baseline:** `03a3931` (refinement on
branch; from main `0dc1d75`).

**Committed: 6 pts** — STORY-038 (1) → STORY-036 (5), in that order.

---

## How this sprint runs (external implementation — working-agreements.md 2026-06-26)
The **PO implements this plan externally** onto `sprint-14`; the orchestrator does NOT dispatch
implementers. This `plan.md` is the only contract — self-contained. When ready, say **"do your
review"**; the orchestrator diffs `sprint-14-start..HEAD`, runs the full DoD gate, runs the Opus
spec + quality reviewers on STORY-036 (3+ pts), resolves the wiki blast radius, then
review → verdict → merge → retro. **TDD + commit-after-green. Scoped staging only.**

### The DoD gate — exit 0 each
`pytest` · `lint-imports` (**4/0 until STORY-038 lands, then 5/0**) ·
`python scripts/check_fk_direction.py` · `alembic upgrade head` · `ruff check .` ·
`ruff format --check .`. DB-gated commands use `scripts/dev_db.py up` → run → `down`.
**No new migration this sprint** (the `maintenance_windows` table already exists).

### Established facts the implementer builds on
- `maintenance_windows` table (spine schema): `id BIGSERIAL PK`, `component_id TEXT FK→components`,
  `starts_at TIMESTAMPTZ`, `ends_at TIMESTAMPTZ`, `reason TEXT NULL`, `created_at TIMESTAMPTZ`.
- Five-file feature pattern + wiring: copy `api/v1/components` + `api/v1/approvals` (controller imports
  only its models+service; DI provider in the feature `service.py`; register the router in
  `src/api/v1/__init__.py`; add `get_*_repo(request)` to `src/api/dependencies.py`; add a
  `*_repo` param + `app.state` entry in `composition/app.py::create_app`).
- UTC-aware datetime validators + a `model_validator(mode="after")`: copy
  `core/domain/proposal.py::StatusProposal`.
- Read-adapter idiom: `PostgresProposalRepository` / `PostgresComponentRepository`. Fakes in
  `backend/tests/fakes.py`.
- import-linter contracts live in `pyproject.toml` `[tool.importlinter]`; the existing
  `core-independence` is a `forbidden` contract — mirror its shape for STORY-038.

---

## STORY-038 — 5th import-linter contract: src must not import tests (1 pt, gate only) — DO FIRST

(First so the new contract immediately guards STORY-036's new code from a `src→tests` slip.)

- [ ] **038.1** Add to `pyproject.toml` `[tool.importlinter]`:
      ```toml
      [[tool.importlinter.contracts]]
      name = "src-no-tests"
      type = "forbidden"
      source_modules = ["src"]
      forbidden_modules = ["tests"]
      ```
      Run `lint-imports` → **5 contracts kept, 0 broken**.
- [ ] **038.2** Prove non-vacuous: temporarily add `from tests.fakes import FakeProposalRepository`
      to a `src/` module, confirm `lint-imports` reports `src-no-tests` **BROKEN**, then revert.
      Record the spike in the story History (AC2 evidence).
- [ ] **038.3** **Command-sync (same commit):** update `.scrum/definition-of-done.md` (the
      `lint-imports` line: now **five** contracts — add `src-no-tests`) AND `CLAUDE.md` (everywhere it
      says "4 contracts"/"four contracts"/the contract list for `lint-imports` → five + name the new
      one). No new gate COMMAND (lint-imports already runs).
- [ ] **038.4** Blast radius: `docs/scrum/wiki/architecture-boundary.md` enumerates the contracts —
      add the 5th (`src-no-tests`, forbidden, `src` may not import `tests`) and bump `verified_sha`.
- [ ] **038.5** Full DoD gate green (5/0).

**AC mapping:** AC1 ← 038.1; AC2 ← 038.2; AC3 ← 038.3 + 038.4; AC4 ← 038.5.

---

## STORY-036 — Maintenance feature module (5 pts) — DO SECOND

Pipeline: **gate + Opus spec & quality reviewers.** No migration. The POST create is an INSERT, not
a check-then-act write → the 2026-06-28 TOCTOU agreement does NOT apply.

### Phase A — `MaintenanceWindow` domain type (TDD)
- [ ] **A1** `backend/src/core/domain/maintenance.py::MaintenanceWindow` — frozen pydantic:
      `component_id: str`, `starts_at: datetime`, `ends_at: datetime`, `reason: str | None = None`,
      `id: int | None = None`. UTC-aware validators on `starts_at`/`ends_at` (reject naive/non-UTC,
      mirror `proposal.py`). `model_validator(mode="after")` raising `ValueError` if
      `ends_at <= starts_at`. Export from `core/domain/__init__.py`. Module + class docstrings cite
      dossier §9/§10/§17. Tests: valid constructs; `ends_at <= starts_at` raises; naive datetime raises.

### Phase B — `MaintenanceRepository` port + adapter + fake (TDD)
- [ ] **B1** Failing test (`test_core_ports.py`): `FakeMaintenanceRepository` — `list_windows()`
      returns injected windows ordered by `starts_at` and `[]` when empty; `create(window)` returns
      the window with an assigned `id`; `is_under_maintenance(component_id, at)` is True iff a window
      for that component covers `at` with **inclusive start / exclusive end** (`starts_at <= at <
      ends_at`).
- [ ] **B2** `backend/src/core/ports/maintenance_repository.py::MaintenanceRepository` (abstract
      `list_windows() -> list[MaintenanceWindow]`, `create(window: MaintenanceWindow) ->
      MaintenanceWindow`, `is_under_maintenance(component_id: str, at: datetime) -> bool`; docstrings
      state the empty/boundary contracts); export from `core/ports/__init__.py`; implement
      `FakeMaintenanceRepository` in `backend/tests/fakes.py`. Green.
- [ ] **B3** Failing **DB-gated** test (`test_persistence_adapters.py`, `migrated_db`):
      `PostgresMaintenanceRepository` against `maintenance_windows` — `create` inserts + returns the
      row with `id`; `list_windows` maps rows → `MaintenanceWindow` ordered by `starts_at`, `[]` when
      empty; `is_under_maintenance` boundary (test exactly `at == starts_at` → True,
      `at == ends_at` → False, a covered time → True, an uncovered time → False). Parity with the fake.
- [ ] **B4** Implement `backend/src/adapters/persistence/maintenance_repository.py::PostgresMaintenanceRepository(engine)`.
      Green.

### Phase C — `api/v1/maintenance/` five-file feature + wiring (TDD)
- [ ] **C1** `models.py`: `MaintenanceWindowDTO {id: int, component_id: str, starts_at: datetime,
      ends_at: datetime, reason: str | None}` and `CreateMaintenanceRequest {component_id: str,
      starts_at: datetime, ends_at: datetime, reason: str | None = None}` (DTOs, NOT the domain type).
      `validation.py` (stdlib-only): required-field / parseable-timestamp checks raising a structured
      error → 422. Failing TestClient tests (`backend/tests/test_maintenance_endpoint.py`):
      `GET /api/v1/maintenance` empty → 200 + `[]`; with windows → 200 + list; `POST` valid →
      **201** + created DTO (with id); `POST` with `ends_at <= starts_at` → **422**; `POST` malformed
      (missing field) → **422** before any core/DB call.
- [ ] **C2** `service.py`: thin — `list_windows()` → DTOs; for create, construct a `MaintenanceWindow`
      from the request (catch the domain `ValueError` from the `ends_at>starts_at` invariant → raise
      `HTTPException(422)` `from e`), call `repo.create`, return the DTO; plus the DI provider
      `get_maintenance_service` (uses `get_maintenance_repo` from `src.api.dependencies`).
      `controller.py`: `GET /maintenance` + `POST /maintenance` (status_code=201). `__init__.py`:
      router re-export. Wire: add `maintenance_repo: MaintenanceRepository | None = None` param to
      `create_app` (default `PostgresMaintenanceRepository(engine)` in the DB branch; left as-passed
      in the injected branch — do NOT import tests), store `app.state.maintenance_repo`; add
      `get_maintenance_repo(request)` to `dependencies.py`; register the maintenance router. Green.
      Docstrings cite §13/§10/§17.
- [ ] **C3** **Five-file-shape test** (working-agreements.md 2026-06-28): assert
      `src.api.v1.maintenance` contains exactly `{__init__, controller, models, validation,
      service}.py` (mirror `test_components_endpoint.py::test_components_module_five_file_shape`).

### Phase D — contract module list
- [ ] **D1** Add `"src.api.v1.maintenance"` to the `api-feature-independence` contract's `modules`
      list in `pyproject.toml`. `lint-imports` → **5 kept / 0 broken** (the count is 5 after
      STORY-038; this only extends a module list). No command-sync.

### Phase E — wiki forward-blast-radius (DoD)
- [ ] **E1** `canonical-types-and-ports.md`: add `MaintenanceWindow` + `MaintenanceRepository` Facts;
      bump `verified_sha`. `persistence-adapters.md`: add `PostgresMaintenanceRepository`; bump.
      `api-five-file-convention.md`: add the `maintenance` feature; bump. `architecture-boundary.md`:
      add `maintenance` to the `api-feature-independence` module list (the 5th contract itself is
      added by STORY-038); bump. Use symbol citations (`file.py::Symbol`).

### Phase F — full gate
- [ ] **F** All SIX commands exit 0 (throwaway DB up for FK/alembic/DB-gated pytest). No migration.

**AC mapping:** AC1 ← A; AC2 ← B; AC3 ← C1/C2 (GET); AC4 ← C1/C2 (POST + 422s); AC5 ← C3 + D;
AC6 ← F + E.

---

## Standing conventions checklist (binds all new code)
- [ ] Module + public class/function docstrings citing the dossier §.
- [ ] `MaintenanceWindow` enforces `ends_at > starts_at` via `model_validator(mode="after")` + test
      (2026-06-26).
- [ ] Empty-input tested for `list_windows`; boundary tested for `is_under_maintenance` (2026-06-25).
- [ ] Port fake and real adapter AGREE on edges; same contract run against both (2026-06-26).
- [ ] Five-file-shape test shipped with the feature (2026-06-28).
- [ ] DI provider in the feature `service.py`; controller imports only its models+service.
- [ ] Production `src/` never imports `tests` (now mechanically enforced by STORY-038's contract).
- [ ] Scoped staging; mirror the components/approvals feature structure.

## Notes / risks
- STORY-036 spans core (type+port) + adapters + api + composition; if a phase balloons past its
  share, mark Blocked with the specific obstacle rather than guessing.
- No tooling/MCP change. No migration.
