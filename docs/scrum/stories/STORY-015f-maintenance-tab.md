---
id: STORY-015f
title: Maintenance tab — windows list + schedule form
type: feature
---

## Context
Spec: dossier §17. Zone 7. Split-child of STORY-015; depends on STORY-015a. API:
`GET /api/v1/maintenance` + `POST /api/v1/maintenance` (STORY-036). The second mutating tab.

## Description
Lists maintenance windows with their state (upcoming / active / past — active windows suppress
degradation proposals, so state must be unmistakable) and provides a form to schedule a new
window: component, start, end, reason. Datetimes are entered in local time and submitted
tz-aware; the API's 422 validation errors surface inline on the form fields.

## Acceptance Criteria
- [ ] AC1: Windows render from `GET /api/v1/maintenance` with component, start/end (mono),
      reason, and a state badge (upcoming/active/past) derived per the API/window-state
      contract — icon/dot + label, tokens only.
- [ ] AC2: The schedule form POSTs `/api/v1/maintenance` with tz-aware datetimes; a successful
      create refreshes the list. MSW test asserts the submitted payload is tz-aware and
      well-formed.
- [ ] AC3: API 422 validation errors (naive datetime, empty component_id — the two real
      backend cases; see History 2026-07-06) render inline on the relevant fields — not a
      toast-only or console-only failure. Tested.
- [ ] AC4: Form inputs use shell primitives (text-input spec, focus ring), are keyboard
      operable and labeled; loading/empty/error+retry states tested.

## Open Questions
None.

## History
- 2026-06-29: first version refined; reverted with `521764c`.
- 2026-07-02: re-refined for the Linear-guided direction. Status: ready. Estimate 3.
- 2026-07-06 (sprint-34 planning, PO-approved): AC3's "end before start" example TRIMMED —
  the consumer-DTO check (2026-07-02 agreement) found `maintenance/validation.py` rejects
  only naive datetimes and an empty component_id; `ends_at <= starts_at` is accepted
  silently (live-probed). The producer gap is filed as STORY-052 (draft). AC3 now names
  only the two real 422 cases. Pulled into sprint 34.
