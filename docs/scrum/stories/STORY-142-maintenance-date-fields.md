# STORY-142 — Maintenance schedule date fields

- **Status:** ready
- **Points:** 3
- **Sprint:** 61
- **Type:** defect
- **Scope:** frontend only

## Context
From the 2026-07-22 design-QA review, verified. The schedule form's Start/End use raw
native `datetime-local` inputs (`ScheduleMaintenanceForm.tsx:115/131`) — unstyled, OS-locale
formatting, native pickers that clash with the form system. The UTC-conversion +
422-field-mapping behavior (STORY-132) must be preserved.

## Acceptance criteria
- **AC1** — Start/End are **styled to match the form system** (a consistent, legible
  date-time control) instead of bare native `datetime-local`. Styled wrapper vs custom field
  is the builder's call.
- **AC2** — The **UTC conversion is preserved** — local input → `…Z` stored (the STORY-132
  datetime-local→UTC-Z contract), proven by the existing conversion tests still passing
  (rewrite, don't delete, if the input mechanism changes).
- **AC3** — The **422 field-mapping** (server "ends_at must be strictly greater than
  starts_at" → `ends_at` aria-invalid, `starts_at` not) and the client-side end-before-start
  guard are preserved with their order-sensitive tests.
- **AC4** — A11y preserved: real `<label>` per field, `aria-invalid`/`aria-describedby`/
  `role=alert` on errors. Gates green.

## Design / skills
Honor the mandated skills. Do NOT regress the STORY-132 contracts — treat the conversion +
422 mapping tests as a safety net; rewrite them to the new input mechanism only if the
mechanism changes, never delete to a coverage gap.
