# STORY-133 — Publications page on real backend data

**Status:** ready · **Points:** 2 · **Sprint:** 60
**As** an operator, **I want** a timeline of Statuspage publish attempts with their outcome —
**so that** I can confirm what was published to the public status page and whether it succeeded.

## Context
New-frontend initiative (sprint 60, external mode), on the sprint-59 design system + shell.
Replaces the `PublicationsPage` placeholder. **Design fresh** with craft via the mandatory skills +
refimg language; do NOT reconstruct the old tab. Contracts in `plan.md` §Publications. Add
`getPublications()` + the `PublicationDTO` type to `frontend/src/api/{client,types}.ts`.

## Acceptance criteria
1. **Publish timeline:** render `GET /api/v1/publications` (`PublicationDTO`), **most-recent-first**
   as returned (the endpoint caps at ~50 — note the cap in the UI; no pagination). Each entry shows
   the component, the published **status** (health badge), the **outcome** (`succeeded` / `failed`)
   as a distinct chip (never colour alone — outcome is separate from the health status), the
   published-at time, the triggering `proposal_id` (`null` → "—", never `0`), and `author`
   (`null` → "—").
2. **No fabricated fields:** the DTO has **no `incident_id`** — do not invent one; render only the
   real fields above.
3. States: loading / error (retry) / empty ("nothing published yet") / success.
4. Exactly one `<h1>`; `tabular-nums` for times/ids; ellipsis `…`; visible focus on any interactive
   elements; motion emil-guarded + `prefers-reduced-motion`.
5. Gates: `npm test`, `npm run build`, `npm run lint` exit 0; every AC has ≥1 test (MSW fixture from
   the `plan.md` sample shape, since the live list is currently empty).

## Reality gate
Local stack up. Scripted Chromium: the empty state renders (matches `GET /api/v1/publications` →
`[]`); component tests prove the populated timeline against the fixture shape. 390px + 1440px,
zero console errors, no horizontal scroll.
