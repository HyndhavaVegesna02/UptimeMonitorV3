# STORY-135 — Surface sample mode in the operator cockpit

**Status:** draft · **Points:** 2–3 (proposed) · **Sprint:** unscheduled (next planning)
**As** an operator, **I want** the cockpit to tell me when it is showing **sample (non-live) data**,
**so that** I don't mistake synthetic/sample observations for real production monitoring.

## Context
The greenfield frontend rebuild (sprint-59) **removed** the old sample-mode UI consumer and never
replaced it; the new cockpit (sprint-60, all six tabs) has **no sample-mode surface at all**
(confirmed 2026-07-22: zero references in `frontend/src/**`; documented in
`docs/scrum/wiki/frontend-zone.md` — "a new consumer is unscheduled"). The backend feature is intact:
`GET /api/v1/sample-mode` → `{ "enabled": bool }` and `PUT /api/v1/sample-mode` (`{ "enabled": bool }`),
DTO `SampleModeDTO`. The old frontend (on `main`) surfaced it as a TopBar toggle switch + a
dismissible `SampleModeBanner`, single-sourced via a `useSampleMode` hook in the shell.

**PO direction (2026-07-22):** surface it again, as a **new story for a future sprint** (not folded
into the locked sprint-60). Design **fresh** with the mandated skills — do NOT copy the old banner.

## ⚠ Open questions (resolve at refinement/planning — this is why status is `draft`)
1. **Read-only indicator vs. full toggle?** Minimum = a read-only "sample data" indicator (GET only).
   Fuller = add the on/off toggle (PUT). The toggle is a mutation and raises the estimate.
2. **The feature is flagged TEMPORARY for removal.** `backend/src/api/v1/sample_mode/models.py`:
   *"TEMPORARY feature (PO directive, 2026-07-03) — see `docs/scrum/wiki/sample-mode.md` for the
   REMOVAL inventory."* Confirm sample mode is still wanted before building new UI for it — otherwise
   the better path may be to proceed with the backend removal instead. **This story should not be
   scheduled until #2 is resolved.**

## Proposed acceptance criteria (draft — pending the above)
1. **Client + type:** add `getSampleMode()` → `SampleModeDTO` (`{ enabled: boolean }`) to
   `frontend/src/api/{client,types}.ts` (and `putSampleMode(enabled)` only if the toggle is in scope).
2. **Shell-level indicator (single source of truth):** read the flag once at the shell; when
   `enabled === true`, show a persistent, **shape+text (never colour-alone)** indicator that the
   cockpit is showing **sample / non-live data**, visible across all six tabs. When `enabled === false`
   (the current live state), no indicator shows.
3. **(If toggle in scope)** an operator control that PUTs the new value with a confirm step, disables
   while submitting, reconciles from the server on success (no optimistic-only), and never throws to
   the console; a forced-error test is required.
4. **States:** the flag GET has loading / error(retry) handling that never blocks the rest of the shell.
5. **a11y:** the indicator is a `role="status"`/region (announced), dismissible if a banner; any control
   is keyboard-operable with a visible focus state; motion emil-guarded + `prefers-reduced-motion`.
6. **Fresh design** on the sprint-59 design system + refimg language (mandated skills:
   ui-ux-pro-max, web-design-guidelines, emil-design-eng, vercel-react-best-practices, design-system);
   no raw hex; not a reconstruction of the old `SampleModeBanner`.
7. Gates: `npm test`, `npm run build`, `npm run lint` exit 0; every AC ≥1 test (enabled + disabled
   fixtures; forced PUT-error test if the toggle ships). MSW fixtures from the real captured sample.

## Reality gate (proposed)
Local stack up. Scripted Chromium: with live `GET /api/v1/sample-mode` → `{enabled:false}`, the
indicator is absent; with a fixture/flag flip to `enabled:true`, the indicator shows on every tab; if
the toggle ships, flipping it PUTs and reconciles, then is reset so live state is left clean. 390px +
1440px, zero console errors.

## Notes
Frontend only (the backend feature already exists). Estimate firms up once the read-only-vs-toggle
decision is made (~2 pts read-only indicator; ~3 pts with the toggle mutation).
