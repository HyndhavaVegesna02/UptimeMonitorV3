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

## History
- 2026-07-22: implemented on `sprint-60`. Added `PublicationDTO` (`frontend/src/api/types.ts`) and
  `getPublications()` (`frontend/src/api/client.ts`, `GET /api/v1/publications`), fixture-backed by
  a new `frontend/src/mocks/handlers/publications.ts` (default `FIXTURE_PUBLICATIONS = []` — the
  live captured sample — plus `FIXTURE_PUBLICATIONS_TIMELINE`, a populated two-entry fixture derived
  from the plan appendix's sample and a second entry exercising the `proposal_id: null` /
  `author: null` / `outcome: 'failed'` edges). New `frontend/src/features/publications/` module:
  `OutcomeChip` (dot + text pill, `succeeded`→`--color-pos-*`/`failed`→`--color-neg-*` — a
  deliberately SEPARATE vocabulary from `StatusBadge`'s health tokens, so a `failed` outcome next to
  an `operational`/"Up" status never reads as the same kind of badge) and `PublicationsTimeline`
  (dense grid, same `overflow-x`-scrolled-table shape as `HistoryGrid`/`ComponentAvailabilityCard`;
  renders rows in the EXACT array order given — no re-sort — proven by a test that puts the
  chronologically-older entry first in the fixture array and asserts it renders first in the DOM).
  `PublicationsPage` composes `useFetch(getPublications)` with loading/error(retry)/empty("Nothing
  published yet")/success states and a description noting the ~50 server-side cap (no pagination).
  Reused `formatObservedAt` from `features/history/formatTimestamp.ts` for the published-at column
  rather than duplicating an identical UTC-formatting helper. **Deleted** the `PlaceholderPage`
  component (`frontend/src/components/PlaceholderPage/{PlaceholderPage.tsx,.css,.test.tsx}`) —
  `PublicationsPage` was its last mount (STORY-129–132 had already replaced the other four); a repo
  grep after the delete confirmed no remaining reference. This closes out the placeholder era:
  **all six nav routes are now real pages** — no route in `frontend/src/routes.tsx` renders a
  placeholder. Every AC has ≥1 test, including the required negative test for AC2 (searches the
  rendered DOM for `/incident/i` and asserts it is absent) and the `outcome`-vs-`status`
  non-conflation crux (a `failed` outcome paired with an `operational`/"Up" status, asserting both
  render distinctly). All three frontend DoD gates (`npm test` / `npm run build` / `npm run lint`)
  green on a clean tree.
