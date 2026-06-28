---
title: The architecture boundary — four zones + the two CI floors
code_refs: [pyproject.toml, scripts/check_fk_direction.py, backend/src/core/__init__.py, backend/src/adapters/__init__.py, backend/src/composition/__init__.py, backend/src/api/__init__.py]
verified_sha: e84ad46
verified_sprint: sprint-17
status: verified
# code_refs narrowed sprint-5 (retro): scoped to the boundary-DEFINING files — the import-linter
# contracts (pyproject.toml), the FK-direction script + SPINE allowlist, and the four zone package
# roots — NOT all of backend/src/. The article describes the BOUNDARY, which changes only when a
# contract or a zone is added/removed; in-zone code additions no longer falsely flag it stale (the
# detailed in-zone facts live in their own articles). See working-agreements.md (sprint-5 amendment).
---

## Facts (verified against code)
- The backend is four zones under `backend/src/`: `core/` (with `domain/`, `ports/`,
  `services/`), `adapters/` (with `inbound/`, `outbound/`, `persistence/`),
  `composition/`, `api/`. Each is an importable package (`__init__.py` present).
- `src` is the importable top-level package; it physically lives at `backend/src` and is
  exposed via `package-dir = {"" = "backend"}` (`pyproject.toml` ("tool.setuptools")). An editable
  install (`pip install -e ".[dev]"`) makes `import src.core` resolve.
- **Import boundary (dossier §4)** is enforced by import-linter, run as the bare command
  `lint-imports`, configured in `pyproject.toml` ("tool.importlinter") with five contracts:
  - `core-independence` (forbidden): `src.core` may not import `src.adapters`,
    `src.composition`, `src.api`, `sqlalchemy`, or `httpx` (`pyproject.toml` ("core-independence")).
  - `core-internal-layering` (layers): `src.core.services` → `src.core.ports` →
    `src.core.domain` (`pyproject.toml` ("core-internal-layering")).
  - `adapters-independence` (independence): `src.adapters.{inbound,outbound,persistence}`
    may not import one another (`pyproject.toml` ("adapters-independence")).
  - `api-feature-independence` (independence): `src.api.v1.decisions`, `src.api.v1.health`,
    `src.api.v1.components`, `src.api.v1.approvals`, `src.api.v1.maintenance`,
    `src.api.v1.availability`, and `src.api.v1.history` may not import one another
    (`pyproject.toml` ("api-feature-independence")).
  - `src-no-tests` (forbidden): `src` may not import `tests` (`pyproject.toml` ("src-no-tests")).
- `include_external_packages = true` (`pyproject.toml` ("tool.importlinter")) is REQUIRED because the
  forbidden set names external packages (`sqlalchemy`, `httpx`); without it import-linter
  errors out.
- The dossier §4 example names vendor subpackages (`inbound.dynatrace`, etc.) that do not
  exist yet; the contracts use the real `inbound/outbound/persistence` packages so they run
  against real modules, not phantoms (comment at `pyproject.toml` ("adapters-independence")).
- **Schema boundary (dossier §9)** is enforced by `scripts/check_fk_direction.py`, run as
  the bare command `python scripts/check_fk_direction.py`. It reads real FKs from
  `information_schema` over `DATABASE_URL` and exits nonzero if any spine table references a
  non-spine (feature) table. The decision logic is the pure function `find_violations`
  (`scripts/check_fk_direction.py::find_violations`); `main()` does the I/O (`scripts/check_fk_direction.py::main`).
- The SPINE allowlist (dossier §9) is the 11-table frozenset at
  `scripts/check_fk_direction.py::SPINE`: apps, signals, components, observations,
  watermarks, rejected_observations, problem_signals, status_proposals, approval_events,
  publications, maintenance_windows. Direction-only: feature→spine passes, spine→feature is
  the violation.
- As of sprint-1, Zone 1 code lives in `core/domain` and `core/ports`, so
  `core-internal-layering` now actually bites: `core/ports` imports `core/domain` (allowed)
  and not `core/services` — verified KEPT. The Zone 1 types/ports themselves are catalogued in
  [[canonical-types-and-ports]].
- As of sprint-5, `core/services` is populated for the first time (`IngestService`,
  STORY-009), so the FULL layering chain `core.services → core.ports → core.domain` is now
  exercised end-to-end and `core-internal-layering` stays KEPT against real service code.
  `composition/pull_loop.py` (STORY-009) is the first concrete module importing BOTH sides of
  the boundary (`src.core` + `src.adapters`) — the composition zone's defining privilege —
  and `core-independence` stays KEPT (the service imports no adapter/sqlalchemy/httpx). The
  ingest service + loop are catalogued in [[ingest-service-and-pull-loop]]. The FK check is
  live and green since STORY-006 (`10 checked, 0 violations`).

## Inference (synthesis, not verified)
- The two mechanical checks (`lint-imports`, FK-direction) are the project's whole bet:
  enforce the replaceability boundary in CI so horizontal, zone-by-zone slicing is safe —
  the boundary is policed before the logic inside it is written.

## History
- sprint-0: created (STORY-001 scaffold + STORY-002 CI contracts).
- sprint-1: re-verified after Zone 1 landed (STORY-004/005); layering contract now bites.
- sprint-4: re-verified after STORY-008 added the first real `adapters.inbound`
  package (`backend/src/adapters/inbound/dynatrace/`). The Facts above were checked
  against the new code and remain true unchanged: `adapters-independence` now bites for
  real (the dynatrace package imports `src.core.domain` only, no other adapter), and
  `lint-imports` stayed `3 kept, 0 broken`. No contract definition or zone-tree Fact
  changed — only the inference about phantom packages (dossier §4's
  `inbound.dynatrace` example) is no longer phantom on the inbound side.
- sprint-4 (fix loop 1): re-verified after extracting the shared
  `_assembly.assemble_observation` helper within `dynatrace/` (no new
  zone/package/contract — purely a within-package move). `lint-imports` stayed
  `3 kept, 0 broken`.
- sprint-5: re-verified after STORY-009 populated `core/services` (`IngestService`) + added
  `composition/pull_loop.py`, and STORY-020 added a named error in `dynatrace/`. No
  zone-tree / contract Fact changed; the full `core.services→ports→domain` layering chain is
  now exercised and `composition` gained its first both-sides importer. `lint-imports` stayed
  `3 kept, 0 broken`; FK-direction `10 checked, 0 violations`. verified_sha → cca043f.
- sprint-9: re-verified after STORY-013 added the FIRST `adapters/outbound/` impl
  (`outbound/statuspage/`) + a second `composition` both-sides importer
  (`composition/publish_helper.py`), and STORY-012 added `core/domain/proposal.py`,
  `core/ports/proposal_repository.py`, and `adapters/persistence/proposal_repository.py`. No
  zone-tree / contract Fact changed — `outbound` is a real package now, `core-independence` +
  `adapters-independence` stayed KEPT (`3 kept, 0 broken`), FK-direction `10 checked, 0 violations`.
  verified_sha → 2d42c60.
- sprint-14: re-verified after adding the 5th contract (`src-no-tests`, forbidden, `src` may not import `tests`) to prevent leaks of fakes/mocks into production. verified_sha → bbc324e.
- sprint-14: `src.api.v1.maintenance` added to the `api-feature-independence` contract (STORY-038) — the maintenance feature is now isolated from all other feature modules. verified_sha → 8e15534.
- sprint-15: `src.api.v1.availability` and `src.api.v1.history` added to the `api-feature-independence` contract (STORY-014c) — availability + history read features are now isolated from all other feature modules. `lint-imports`: 5 kept / 0 broken. verified_sha → 7efe64c.
