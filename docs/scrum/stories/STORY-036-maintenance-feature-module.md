---
id: STORY-036
title: Maintenance feature module — schedule + window state for the Maintenance tab
type: feature
---

## Context
Spec: dossier §9 (modularity model — a stateful feature module owning inward-FK'd tables) + §10
(maintenance short-circuits collapse). Surfaced by the Sprint 13 planning of STORY-014b: the
Maintenance tab has NO backing state. Today maintenance is only an INJECTED boolean into
`pipeline.py::collapse` (`under_maintenance`); there is no maintenance table, repository, or domain
type, and `MaintenanceSignal` is deferred in the dossier. Before a Maintenance read endpoint can
exist, the maintenance state must exist.

## Description
A stateful **feature module** (per the dossier §9 boundary rule): owns its own table(s) that
foreign-key INTO the spine (`components`), never the reverse. Stores scheduled/active maintenance
windows (component, start, end, reason, actor). Feeds: (a) the `under_maintenance` boolean the
pipeline already consumes (replacing the injected stub with a real lookup at the composition edge,
NOT inside pure core), and (b) the future Maintenance read endpoint. Includes the migration (new
table, inward FK, `check_fk_direction.py` stays green — spine never FKs into it).

## Acceptance Criteria (draft — refine before its sprint)
- [ ] AC1: a maintenance table + Alembic migration; FK into `components`; FK-direction check green.
- [ ] AC2: a domain type + repository port + Postgres adapter + fake for maintenance windows
      (create/list/active-at-time), with empty/edge tests.
- [ ] AC3: the pipeline's `under_maintenance` is resolved from real maintenance state at the
      composition layer (core stays pure — the boolean is still injected, just sourced for real).
- [ ] AC4: full SIX-command DoD gate green; blast radius resolved.

## Open Questions
- Is V3 scope "display + honor existing maintenance" only, or also create/edit windows via the API?
- Relationship to the deferred `MaintenanceSignal` (push-era) — confirm at refinement.
- Estimate at refinement (likely 5 — new table + migration + port + adapter + pipeline wiring).

## History
- 2026-06-28: created from Sprint 13 planning (STORY-014b found the Maintenance tab has no backing
  state). Status: draft.
