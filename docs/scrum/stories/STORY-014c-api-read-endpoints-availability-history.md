---
id: STORY-014c
title: API read endpoints — Availability + Check History (per-signal)
type: feature
---

## Context
Spec: dossier §13 (five-file convention) + §11 (availability engine) + §10 (verdicts) + §17 (tabs).
Zone 6. Second half of the read-endpoint split (after STORY-014b's Dashboard + Approvals). These two
tabs REUSE existing backing — no new ports:
- **Availability** — `AvailabilityResult` (availability% + completeness%) from
  `core/services/availability.py::AvailabilityCalculator.compute`.
- **Check History** — recent observations from
  `core/ports/observation_repository.py::ObservationRepository.in_window`.

**Scope (refined 2026-06-28): PER-SIGNAL.** Both `AvailabilityCalculator.compute(signal_key, since,
until)` and `ObservationRepository.in_window(signal_key, ...)` key off **`signal_key`**, NOT
`component_id`. The signal→component mapping + group rollup do NOT exist yet (they belong to the
deferred §7/§17 config+topology layer — see STORY-040). So these endpoints expose **per-signal** data
now; per-component / group rollup (`availability.py::rollup_group`) is added once the topology layer
lands. This keeps STORY-014c unblocked and ready.

## Description
Two five-file read features under `api/v1/`, each thin (resolve the calculator / observation repo via
the container → shape DTOs), each added to the `api-feature-independence` contract, each with a
five-file-shape test (working-agreements.md 2026-06-28):
- `api/v1/availability/` — `GET /api/v1/availability?signal_key=...&since=...&until=...` →
  `AvailabilityResult` DTO. `since`/`until` optional (ISO-8601); default window = last 24h via the
  injected clock. Requires `signal_key`.
- `api/v1/history/` — `GET /api/v1/history?signal_key=...&since=...&until=...` → list of observation
  DTOs (recent first), reusing `in_window`. Same window defaulting.
Wire `observation_repo` into `create_app` + `app.state` + a `get_observation_repo` dependency
(mirror the components/maintenance wiring); the availability service constructs
`AvailabilityCalculator(observation_repo=...)`.

## Acceptance Criteria (refined — PO-approved 2026-06-28)
- [ ] AC1 (Availability): `GET /api/v1/availability?signal_key=X` → 200 with availability% +
      completeness% (an `AvailabilityResult` DTO, distinct from the domain result type), computed by
      `AvailabilityCalculator`. Tested (TestClient, fake observation repo) with data AND the
      **no-data window** case (0 observations → a coherent zero/empty result, not 500).
- [ ] AC2 (Check History): `GET /api/v1/history?signal_key=X` → 200 with the window's observations as
      DTOs; **empty** window → 200 + `[]`. A missing required `signal_key` → 422 before any core call.
- [ ] AC3 (window defaulting): with no `since`/`until`, the endpoints use a last-24h window derived
      from the injected clock; an explicit `since`/`until` is honored. Tested.
- [ ] AC4 (five-file shape + boundary): each feature has exactly the five files (§13 import rules);
      a five-file-shape test for each; `lint-imports` stays green (5/0) with `availability` + `history`
      added to the `api-feature-independence` module list.
- [ ] AC5 (full SIX-command DoD gate green); no new migration. Forward blast radius:
      `api-five-file-convention.md` (+ architecture-boundary independence list) updated + re-verified.

## Conventions checklist
- Docstrings cite the dossier §; DTOs distinct from domain types; DI provider in the feature
  `service.py`; controller imports only its models+service; five-file-shape test shipped; edge DTO
  maps ids directly (no sentinel — working-agreements.md 2026-06-28); empty/no-data tested; scoped
  staging; production `src/` never imports `tests` (contract-enforced). These are pure reads → the
  TOCTOU agreement does not apply.

## Resolved Questions
- **Per-signal scope** (not per-component) — the calculator + observation repo key off `signal_key`;
  the signal→component mapping is deferred to STORY-040. Group/component rollup added later. (2026-06-28.)
- **No new ports / no migration** — reuses `AvailabilityCalculator` + `ObservationRepository`.

## History
- 2026-06-28: created from the STORY-014b 4-tab split.
- 2026-06-28 (Sprint 15 refinement): scoped per-signal (the calculator/observation repo key off
  signal_key; component/group rollup needs the deferred topology layer). Estimate **3** (2 read
  features + observation_repo wiring + DTOs + tests; patterns established by STORY-014b). Status:
  draft → ready.
