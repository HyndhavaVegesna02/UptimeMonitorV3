---
id: STORY-014b
title: API read endpoints for the six dashboard tabs
type: feature
---

## Context
Spec: dossier §13 (five-file convention) + §11 (availability engine) + §10 (pipeline /
status). Zone 6. Follow-up to STORY-014, which established the five-file convention, the
FastAPI app factory + composition provider, and the 4th import-linter contract (no
horizontal feature imports) via the decision (approve/reject) exemplar. This story fills in
the **read-only** endpoints that feed the six dashboard tabs (STORY-015 consumes them).

## Description
Add the read-only feature modules under `api/v1/` (each the five-file shape, each a thin
edge `service.py` delegating to a core service via the container, none importing another
feature) serving the data for: **Dashboard** (current component statuses), **Availability**
(availability% + completeness% over a window, from `core/services/availability.py`),
**Check History** (recent collapsed verdicts / observations per component), **Maintenance**
(active/scheduled maintenance windows), **Publications** (recent Statuspage publish results).
The Approvals tab's list of OPEN proposals also lands here (the mutate endpoint is already in
STORY-014). The 4th linter contract's `independence` module list extends to every new feature.

## Acceptance Criteria (draft — refine before its sprint)
- [ ] AC1: Each new feature follows the five-file shape (§13); `lint-imports` stays 4/0 with
      every new `api.v1.<feature>` added to the independence contract.
- [ ] AC2: Read endpoints for Dashboard, Availability, Check History, Maintenance, Publications,
      and the Approvals list — each tested (TestClient, repositories faked), each returning DTOs
      (not canonical domain types).
- [ ] AC3: Each endpoint delegates to a core service/calculator via the container; no business
      logic at the edge; core-independence stays KEPT.
- [ ] AC4: Empty-state tested for every list endpoint (no components / no proposals / no
      publications → 200 + empty payload, not 500).
- [ ] AC5: Full SIX-command DoD gate green.

## Open Questions
- Exact response DTO shape per tab (confirm against STORY-015's needs at refinement — these
  two stories should be refined together so the contract matches what the UI renders).
- Whether Maintenance/Publications have backing core services/repositories yet, or whether a
  thin read port must be added first (audit at refinement; may carve out a prerequisite chore).
- Estimate at refinement (likely 3–5 depending on how many tabs have ready backing services).

## History
- 2026-06-28: created from the STORY-014 exemplar-first split (PO decision). Holds the five
  read-only tab endpoints deferred from STORY-014. Status: draft — refine (with STORY-015)
  before its sprint.
