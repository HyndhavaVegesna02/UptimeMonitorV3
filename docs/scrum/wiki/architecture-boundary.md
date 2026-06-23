---
title: The architecture boundary — four zones + the two CI floors
code_refs: [backend/src/, pyproject.toml, scripts/check_fk_direction.py]
verified_sha: 1a61002
verified_sprint: sprint-0
status: verified
---

## Facts (verified against code)
- The backend is four zones under `backend/src/`: `core/` (with `domain/`, `ports/`,
  `services/`), `adapters/` (with `inbound/`, `outbound/`, `persistence/`),
  `composition/`, `api/`. Each is an importable package (`__init__.py` present).
- `src` is the importable top-level package; it physically lives at `backend/src` and is
  exposed via `package-dir = {"" = "backend"}` (`pyproject.toml:21-22`). An editable
  install (`pip install -e ".[dev]"`) makes `import src.core` resolve.
- **Import boundary (dossier §4)** is enforced by import-linter, run as the bare command
  `lint-imports`, configured in `pyproject.toml:33-54` with three contracts:
  - `core-independence` (forbidden): `src.core` may not import `src.adapters`,
    `src.composition`, `src.api`, `sqlalchemy`, or `httpx` (`pyproject.toml:37-41`).
  - `core-internal-layering` (layers): `src.core.services` → `src.core.ports` →
    `src.core.domain` (`pyproject.toml:43-46`).
  - `adapters-independence` (independence): `src.adapters.{inbound,outbound,persistence}`
    may not import one another (`pyproject.toml:51-54`).
- `include_external_packages = true` (`pyproject.toml:35`) is REQUIRED because the
  forbidden set names external packages (`sqlalchemy`, `httpx`); without it import-linter
  errors out.
- The dossier §4 example names vendor subpackages (`inbound.dynatrace`, etc.) that do not
  exist yet; the contracts use the real `inbound/outbound/persistence` packages so they run
  against real modules, not phantoms (comment at `pyproject.toml:48-50`).
- **Schema boundary (dossier §9)** is enforced by `scripts/check_fk_direction.py`, run as
  the bare command `python scripts/check_fk_direction.py`. It reads real FKs from
  `information_schema` over `DATABASE_URL` and exits nonzero if any spine table references a
  non-spine (feature) table. The decision logic is the pure function `find_violations`
  (`scripts/check_fk_direction.py:55-71`); `main()` does the I/O (`:84-104`).
- The SPINE allowlist (dossier §9) is the 11-table frozenset at
  `scripts/check_fk_direction.py:27-39`: apps, signals, components, observations,
  watermarks, rejected_observations, problem_signals, status_proposals, approval_events,
  publications, maintenance_windows. Direction-only: feature→spine passes, spine→feature is
  the violation.
- As of sprint-0 the skeleton has no real imports and no tables, so the layering/independence
  contracts and the FK check are vacuously green; they begin to bite once real code/schema
  land in zones 1–4 / STORY-006.

## Inference (synthesis, not verified)
- The two mechanical checks (`lint-imports`, FK-direction) are the project's whole bet:
  enforce the replaceability boundary in CI so horizontal, zone-by-zone slicing is safe —
  the boundary is policed before the logic inside it is written.

## History
- sprint-0: created (STORY-001 scaffold + STORY-002 CI contracts).
