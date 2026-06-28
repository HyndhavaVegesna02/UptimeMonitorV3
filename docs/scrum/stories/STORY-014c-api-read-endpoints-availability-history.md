---
id: STORY-014c
title: API read endpoints — Availability + Check History
type: feature
---

## Context
Spec: dossier §13 (five-file convention) + §11 (availability engine) + §10 (pipeline/verdicts).
Zone 6. Second half of the read-endpoint split (after STORY-014b's Dashboard + Approvals-list).
These two tabs reuse EXISTING backing — no new read ports for the core computation:
- **Availability** — availability% + completeness% over a window, from
  `core/services/availability.py`.
- **Check History** — recent collapsed verdicts / observations per component, from
  `core/ports/observation_repository.py::ObservationRepository.in_window`.

## Description
Two five-file features under `api/v1/` (Availability, Check History), each a thin edge service
delegating to the existing availability calculator / observation repository via the container,
each added to the `api-feature-independence` contract module list. May need a small read helper to
enumerate components/signals for the availability rollup (assess at refinement — STORY-014b adds
`ComponentRepository.list_components`, which this story can reuse).

## Acceptance Criteria (draft — refine before its sprint)
- [ ] AC1: `GET /api/v1/availability` (per component and/or group, over a window param) returns
      availability% + completeness% computed by `availability.py`; tested incl. the empty / no-data
      window case.
- [ ] AC2: `GET /api/v1/history` (recent verdicts/observations for a component) returns the series;
      tested incl. empty.
- [ ] AC3: five-file shape + §13 import rules; `lint-imports` 4/0 with both features added to the
      independence list.
- [ ] AC4: full SIX-command DoD gate green; forward blast radius resolved.

## Open Questions
- Window/param shape for the availability endpoint (default window, per-component vs group rollup).
- Whether Check History returns raw observations, collapsed verdicts, or both (confirm against
  STORY-015's needs — refine with the frontend).
- Estimate at refinement (likely 3).

## History
- 2026-06-28: created from the STORY-014b 4-tab split (PO). Holds the two reuse-existing-backing
  detail tabs. Status: draft — refine (with STORY-015) before its sprint.
