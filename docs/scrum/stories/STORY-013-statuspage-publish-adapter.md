---
id: STORY-013
title: Statuspage publish adapter + commit-first boundary
type: feature
---

## Context
Spec: dossier §12 + T1.1 (transaction boundary vs side effects). Zone 5. The publisher
port exists for testability (mock in tests, real in prod), not for a second real publisher.

## Description
Implement the real Statuspage publish behind `StatusPublisherPort` in
`adapters/outbound/statuspage/`. Commit the DB FIRST, then publish best-effort in a
try/except; a publish failure is logged and does NOT roll back the committed decision
(the human still finds out via the dashboard + an SLA re-notify safety net). The adapter
translates the canonical `component_id` → Statuspage object id.

## Acceptance Criteria (draft — confirm at refinement)
- [ ] AC1: An approved change publishes via the adapter (verified against a mock/recorded
      Statuspage in tests).
- [ ] AC2: A publish failure does NOT roll back the committed decision (commit-first
      proven by a test where publish raises).
- [ ] AC3: A mock publisher is used in tests; no live Statuspage required.
- [ ] AC4: The adapter lives in `adapters/outbound/`; the core sends only a canonical
      `StatusChange`/`component_id`; `lint-imports` green.

## Open Questions
- Confirm the Statuspage API surface (incidents vs component status) used for the demo.

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §12/§14(T1.1). Status: draft — refine before its sprint.
