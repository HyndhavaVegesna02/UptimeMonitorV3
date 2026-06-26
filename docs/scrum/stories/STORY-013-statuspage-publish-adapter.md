---
id: STORY-013
title: Statuspage publish adapter + commit-first boundary
type: feature
---

## Context
Spec: dossier §6 (StatusPublisherPort) + §12 + §14 T1.1 (transaction boundary vs side effects).
Zone 5. The publisher port exists for testability (recording fake in tests, real publisher in prod),
NOT for a second real publisher. The core sends a canonical `StatusChange{component_id, status:
ComponentStatus}` (frozen, `core/domain/status.py`); the adapter translates `component_id` → the
Statuspage object id and `ComponentStatus` → the vendor's status vocabulary. No live Statuspage in
any test — an injected HTTP executor seam + recorded fixtures, exactly like the Dynatrace adapter's
`Executor` pattern.

## Description
- **Adapter** (`adapters/outbound/statuspage/`): implements `StatusPublisherPort.publish(change:
  StatusChange) -> None`. Resolves `component_id` → vendor id via an INJECTED mapping (config loading
  is deferred — a passed-in dict/resolver, the established Zone 4/5 injection pattern). Maps
  `ComponentStatus` → the Statuspage component-status string (the demo uses the component-status
  update surface, NOT incidents — resolved below). Calls an injected `Executor`-style seam (no live
  HTTP in tests); recorded request/response fixtures.
- **Commit-first / best-effort publish** (T1.1): publishing is a SIDE EFFECT after the decision is
  committed. Provide a small composition-zone helper `publish_best_effort(publisher, change, *,
  logger)` that calls `publisher.publish(change)` inside a `try/except`, LOGS a failure, and does NOT
  re-raise — so a Statuspage outage can never roll back / crash the already-committed decision (the
  human still learns via the dashboard + the SLA re-notify safety net). The DB commit-before-publish
  ORDERING is the caller's contract (wired in `decide`, STORY-024); this story builds + proves the
  best-effort primitive with fakes.

## Acceptance Criteria (refined — PO-approved 2026-06-26)
- [ ] AC1: A `StatusChange` publishes via the adapter — `component_id` resolved to the vendor id
      (injected mapping), `ComponentStatus` mapped to the Statuspage component-status string, the
      built request asserted against a recorded fixture. Tested with the injected executor seam.
- [ ] AC2: `publish_best_effort` does NOT propagate a publish failure: when the injected publisher
      raises, it is caught + logged and the call returns normally (no exception escapes), proving a
      publish failure cannot roll back / crash the committed decision. Tested with a raising fake
      publisher.
- [ ] AC3: A recording/fake publisher is used in tests; NO live Statuspage and NO live HTTP — the
      executor seam is injected and faked.
- [ ] AC4: The adapter lives entirely under `adapters/outbound/statuspage/`; the core sends only a
      canonical `StatusChange`/`component_id` (no vendor id/type in core); `lint-imports` green (no
      adapter imports another adapter; the best-effort helper lives in `composition/`).

## Resolved Questions
- Statuspage API surface: the **component-status update** surface (set a component's status from the
  `ComponentStatus` mapping) for the demo — NOT incident objects. Simpler, maps 1:1 to the canonical
  status. PO-approved 2026-06-26.
- The DB commit-first ORDERING is the caller's contract (STORY-024 wires it); this story proves the
  best-effort no-rollback behavior with fakes. PO-approved 2026-06-26.

## History
- 2026-06-23: drafted from dossier §12/§14(T1.1). Status: draft.
- 2026-06-26 (sprint-9 refinement): API surface resolved (component-status update); scope = the
  outbound adapter (injected executor + mapping + recorded fixtures) + the best-effort publish helper
  proving no-rollback (commit-first DB ordering is STORY-024's wiring); AC1–AC4 finalized; estimate
  held at 3. Status: ready.
