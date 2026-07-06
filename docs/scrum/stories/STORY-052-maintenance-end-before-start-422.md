---
id: STORY-052
title: Maintenance ordering 422 — clean edge message instead of a leaked Pydantic blob, + inline frontend mapping
type: defect
---

## Context (CORRECTED 2026-07-06 — the originally-claimed defect does not exist)
As first filed at sprint-34 planning, this story claimed `POST /api/v1/maintenance`
silently accepts `ends_at <= starts_at`. **That was wrong** — the planning check read
only the edge validator (`maintenance/validation.py`) and live-probed only the happy
path. The domain type (`core/domain` `MaintenanceWindow`, pinned by
`test_maintenance_domain.py::test_maintenance_window_ends_at_must_be_greater_than_starts_at`
and `test_maintenance_endpoint.py::test_post_maintenance_invalid_times`) enforces
`ends_at must be strictly greater than starts_at` — end-before-start AND equal
timestamps both return 422, live-confirmed 2026-07-06 during sprint 34.

What IS wrong (live wire sample, 2026-07-06): the ordering 422's `detail` leaks the raw
Pydantic internals —
`"1 validation error for MaintenanceWindow\n  Value error, ends_at must be strictly
greater than starts_at [type=value_error, input_value={...}] ... errors.pydantic.dev ..."`
— a multi-line blob exposing internal type names and input echo, inconsistent with the
edge validator's clean one-liners (`"starts_at must be timezone-aware."`). The
Maintenance tab (STORY-015f) maps 422 details to form fields by message substring, so
this blob renders poorly/unmapped, and 015f (built to the amended AC3) has no test for it.

## Description
Give the ordering violation the same clean edge treatment the other syntactic checks
have, and map it inline on the form.

## Acceptance Criteria (refined READY, sprint-37 planning 2026-07-06)
- [ ] AC1: `maintenance/validation.py::validate_maintenance_request` gains the ordering
      check (`ends_at <= starts_at` → `SyntacticValidationError` with a clean one-line
      message, e.g. "ends_at must be strictly greater than starts_at.") so the edge 422
      fires BEFORE domain construction; endpoint regression test asserts the clean
      detail for both end-before-start and equal timestamps. The domain validator stays
      (defense in depth) — this only changes which layer answers the API caller.
- [ ] AC2: The Maintenance tab's field-error mapping handles the ordering message
      (inline on `ends_at`), MSW-tested with the REAL new detail string. Includes the two
      sprint-34 quality-review minors in the same area (2026-07-06): rewrite
      `fieldError.ts`'s stale "two real backend 422 cases" doc comment, and add a test
      pinning the multi-field-detail behavior (a detail naming several fields resolves
      deterministically and never throws — today the raw ordering blob mis-maps to the
      COMPONENT field via the `component_id` token in the Pydantic repr).
- [ ] AC3: Six-gate backend DoD + three-gate frontend DoD green.

## Open Questions
None — the original "should equal timestamps 422?" question is answered by the existing
domain behavior: yes, "strictly greater" (live-confirmed).

## History
- 2026-07-06: filed as draft at sprint-34 planning claiming a missing end-before-start
  422 (consumer-DTO check finding; PO chose "trim AC3 + file draft").
- 2026-07-06 (later, sprint 34 in flight): CORRECTED after the STORY-015f implementer
  flagged `test_post_maintenance_invalid_times` — the 422 exists (domain layer); the
  planning check had probed only the happy path live. Re-scoped to the leaked-Pydantic
  detail + frontend inline mapping. Feeds the sprint-34 retro (probe failure paths, not
  just the happy path, when pinning consumer contracts).
- 2026-07-06 (sprint-37 planning): refined to READY, estimate 1 confirmed. Touches BOTH
  backend (`maintenance/validation.py` + endpoint test) and frontend (`fieldError.ts` +
  Maintenance tab MSW test) → runs the full six-gate + three-gate DoD. No open questions.
