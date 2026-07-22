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

## History
- 2026-07-22: implemented on `sprint-60`. **Deleted** the `MaintenancePage` placeholder
  (`PlaceholderPage` mount from STORY-121) and replaced it with the real page — no other page still
  uses it (`PlaceholderPage` itself stays; Publications still mounts it). Tightened
  `MaintenanceWindowDTO.title` from `title?: string | null` to `title: string | null` and added
  `CreateMaintenanceRequest` (`frontend/src/api/types.ts`), fixing the one existing test literal
  this broke (`MaintenancePanel.test.tsx`'s null-title case). Extended the write path from STORY-131
  with a NEW private `deleteRequest(path): Promise<void>` helper (`frontend/src/api/client.ts`) —
  distinct from `postJson`/`getJson` because a 204 response has no body to parse (calling
  `.json()` on an empty 204 throws) — plus `postMaintenance` (201) and `deleteMaintenance` (204,
  not idempotent: a 404 on an already-deleted window is a real `ApiError.status === 404`, never a
  silent success). New `frontend/src/features/maintenance/` module, all pure/unit-tested first:
  `deriveWindowState.ts` (the half-open `[starts_at, ends_at)` upcoming/active/past rule, boundary
  instants pinned — `now === starts_at` is ACTIVE, `now === ends_at` is PAST), `mapMaintenanceError.ts`
  (the crux: order-sensitive 422 `detail`-string -> field mapping, "strictly greater than" checked
  BEFORE the plain "starts_at" check so the end-before-start message maps to `ends_at` and not the
  `starts_at` it also names), `localDateTimeToUtcIso.ts` (`datetime-local` -> tz-aware UTC ISO,
  round-trip tested), `formatWindowRange.ts`, `WindowStateBadge` (dot + text, never colour alone —
  a distinct vocabulary from `StatusBadge`'s `HealthStatus`, not an overload of it),
  `useScheduleMaintenance` (client-side guards `component_id` non-blank and `ends_at > starts_at`
  BEFORE calling the API; maps a server 422 through `mapMaintenanceError`; resets/refreshes on 201;
  never throws), `useMaintenanceDeletion` (the same confirm/submit shape as Approvals'
  `useApprovalsDecisions`, simplified to one action; a 404 sets a non-destructive notice AND still
  refreshes), `MaintenanceWindowCard` (title tidy-fallback, state badge, UTC range, reason `—` when
  null, inline delete confirm with Escape/focus management), and `ScheduleMaintenanceForm`
  (UNCONTROLLED inputs read via `FormData` on submit rather than per-keystroke controlled state —
  vercel-react-best-practices; its own `getComponents` fetch/loading/error, independent of the
  windows list's; field errors carry `aria-invalid`/`aria-describedby`/`role="alert"`; a detail
  naming no field renders a form-level banner). `MaintenancePage` composes the form (reconciles the
  list via `onScheduled`) and the list (`getMaintenance` + `useFetch` + `useMaintenanceDeletion`),
  each with independent loading/error/empty/success per AC5. Extended
  `frontend/src/mocks/handlers/maintenance.ts` with a populated upcoming/active/past fixture (year
  2000/2099 instants so the derived state is stable regardless of when the suite runs — the exact
  boundary math is unit-tested separately with pinned instants) and POST (201)/DELETE (204)
  handlers. Every AC has ≥1 test, including the required forced end-before-start 422 ->
  `ends_at`-field test (both at the pure-helper level and end-to-end through the real form, proving
  the crux ordering) and a delete-404 test (both as a hook test and a page-level integration test
  proving the non-destructive notice, the refresh, and zero `console.error` calls). All three
  frontend DoD gates (`npm test`: 643 passed / `npm run build` / `npm run lint`) green on a clean
  tree.
