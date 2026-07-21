# STORY-132 — Maintenance page on real backend data (schedule + delete)

**Status:** ready · **Points:** 5 · **Sprint:** 60
**As** an operator, **I want** to see scheduled maintenance windows and schedule or delete them —
**so that** planned downtime is suppressed from availability/status and communicated.

## Context
New-frontend initiative (sprint 60, external mode), on the sprint-59 design system + shell.
Replaces the `MaintenancePage` placeholder. **Design fresh** with craft via the mandatory skills +
refimg language; do NOT reconstruct the old tab. Contracts in `plan.md` §Maintenance. Add to
`frontend/src/api/{client,types}.ts`: `postMaintenance(body)` (POST → 201) + `deleteMaintenance(id)`
(DELETE → 204) + the `CreateMaintenanceRequest` type (extend `MaintenanceWindowDTO` with `title`).
`getMaintenance()` already exists. Components for the form come from the existing `getComponents()`.

## Acceptance criteria
1. **Windows list:** render `GET /api/v1/maintenance` (`MaintenanceWindowDTO`) with title (or a tidy
   fallback when null), component, the start–end range, and reason. The DTO has **no state field** —
   derive **upcoming / active / past** client-side from `starts_at`/`ends_at` vs now using the
   half-open rule (`t < start` → upcoming; `t < end` → active; else past), shown as a badge
   (dot + text label, never colour alone). Boundary instants are pinned + tested.
2. **Schedule form:** fields for component (select from `GET /api/v1/components`), start, end,
   optional title, optional reason. `datetime-local` inputs are converted to **tz-aware UTC ISO**
   (`new Date(v).toISOString()`) on submit — the API rejects naive/non-UTC datetimes. POST returns
   **201** with the created window; on success the form resets and the list reconciles from the
   server.
3. **Validation + 422 field mapping:** guard `ends_at <= starts_at` client-side, and map the
   server's 422 `{detail}` string to the offending field **inline** (`aria-invalid`,
   `aria-describedby`, `role="alert"`). Match order matters: the "strictly greater than" message
   (end-before-start) maps to `ends_at` **first** (it also names `starts_at`), then `component_id`,
   `starts_at`, `ends_at`; a detail naming none of them falls back to a form-level banner.
4. **Delete with confirm:** each window has a delete action gated by an inline confirm; `DELETE`
   returns **204**. Delete is **not idempotent** — a **404** (already gone) surfaces as a
   non-destructive notice, then the list refreshes. Mutations never throw to the console.
5. States: loading / error (retry) / empty ("no maintenance scheduled") / success; the form and the
   list each manage their own loading/error.
6. Exactly one `<h1>`; every field has an associated `<label>`; visible focus; motion emil-guarded +
   `prefers-reduced-motion`; `tabular-nums` for times.
7. Gates: `npm test`, `npm run build`, `npm run lint` exit 0; every AC has ≥1 test — including a
   **forced end-before-start 422** (asserting it maps to the `ends_at` field) and a delete-404 test.

## Reality gate
Local stack up. Scripted Chromium: the empty state matches `GET /api/v1/maintenance` → `[]`; a
window is created against the **real** POST endpoint (UTC ISO bounds, 201) and appears with a
correctly derived state badge; an end-before-start submit shows the inline `ends_at` error from the
real 422; the created window is deleted (204) and the list reconciles; **then the reality-gate
window is deleted so live state is left clean.** 390px + 1440px, zero console errors.
