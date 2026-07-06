---
id: STORY-052
title: Maintenance API rejects end-before-start windows with a 422
type: defect
---

## Context
Found by the sprint-34 planning consumer-DTO check (2026-07-06), while pinning the wire
contract for STORY-015f: `POST /api/v1/maintenance` accepts `ends_at <= starts_at` and
persists a zero/negative-length window (live-probed against the running local stack).
`maintenance/validation.py::validate_maintenance_request` checks only empty
`component_id` and tz-naive datetimes. A zero/negative window is nonsense data: it can
never be "active" under the half-open `starts_at <= at < ends_at` rule
(`core/ports/maintenance_repository.py::MaintenanceRepository.is_under_maintenance`),
so it silently does nothing while looking scheduled. STORY-015f's AC3 originally named
this as a 422 example; it was trimmed at planning (PO-approved) and the gap filed here.

## Description
Reject `ends_at <= starts_at` at the API edge with a `SyntacticValidationError` → HTTP
422, mirroring the existing naive-datetime checks in the same validator.

## Acceptance Criteria (draft — refine before scheduling)
- [ ] AC1: `POST /api/v1/maintenance` with `ends_at <= starts_at` (both tz-aware) returns
      422 with a message naming the ordering problem; equal timestamps are rejected too
      (a zero-length window can never be active). Regression-tested at the endpoint level.
- [ ] AC2: `validate_maintenance_request` gains the check + unit tests (reject
      end-before-start and end-equals-start; accept a valid ordering).
- [ ] AC3: Once landed, STORY-015f's Maintenance tab (if already merged) needs no change —
      its inline-422 rendering is field-generic; verify the new 422 surfaces inline. If
      015f grew a client-side ordering guard meanwhile, the two must not disagree.

## Open Questions
None known; confirm at refinement whether equal-timestamps should really 422 (recommended)
or be allowed as a no-op.

## History
- 2026-07-06: filed as draft at sprint-34 planning (consumer-DTO check finding; PO chose
  "trim AC3 + file draft").
