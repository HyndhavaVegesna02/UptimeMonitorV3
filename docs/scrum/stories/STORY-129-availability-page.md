# STORY-129 — Availability page on real backend data

**Status:** ready · **Points:** 5 · **Sprint:** 60
**As** an operator, **I want** a two-grain Availability page — component-rollup availability plus
per-signal drill-down, over a selectable window — **so that** I can see how available each
monitored component and its signals have been, on real data.

## Context
New-frontend initiative (sprint 60, external mode), built on the sprint-59 design system + shell.
Replaces the `AvailabilityPage` placeholder. **Design this page fresh** with craft using the
mandatory skills + the refimg visual language — do NOT reconstruct the old tab's layout. Data
comes from the live `/api/v1` contracts (see `plan.md` §Availability for exact shapes + the live
sample). The typed API client (sprint-59) is GET-only and lacks the methods this page needs —
add `getTopology()` + `getComponentAvailability(componentId, {since, until})` (+ the DTO types
`ComponentTopologyDTO`, `TopologySignalDTO`, `ComponentAvailabilityDTO`, `SignalAvailabilityDTO`)
to `frontend/src/api/{client,types}.ts`, following the existing patterns.

## Acceptance criteria
1. **Component-rollup grain:** for every component (from `GET /api/v1/topology`), fetch and show
   its rollup availability via `GET /api/v1/availability/component/{component_id}` — availability %
   and data-completeness %, plus the real verdict counts (total / passing / maintenance / gap) and
   distinct-locations.
2. **Per-signal drill-down:** each component can be expanded to reveal its per-signal children
   (`signals[]` in the same response), each with its own availability %, completeness %, counts,
   and location count. Signal display names come from the topology (`signals[].name`); the
   availability children carry only `signal_key`. Expand/collapse is keyboard-operable with
   `aria-expanded`/`aria-controls`.
3. **Window toggle** 24h / 7d / 30d (`role="group"`, `aria-pressed`) that recomputes `since`/`until`
   as **tz-aware UTC ISO** strings (trailing `Z`) and refetches. Naive datetimes are never sent.
4. **Percent scaling + null discipline:** `availability_pct` / `completeness_pct` are **0–1
   fractions** on the wire — multiply by 100 for display (`NN.NN%`). A `null` percentage renders as
   "no data" (or equivalent), **never `0%`**. Low completeness is visibly flagged (a threshold
   indicator), but `null` is not treated as low.
5. **Progressive loading (STORY-127/128 lesson):** the `/availability` computation is slow against
   local DynamoDB; per-component fetches must be **independent** so a slow component does not block
   the others, and the page paints its frame + per-region loading immediately. Do **not** bundle
   all fetches into one blocking `Promise.all` gated behind the slowest. Each region shows its own
   loading / error (with retry) / empty state.
6. Exactly one `<h1>`; hierarchical headings; numbers use `tabular-nums`; ellipsis is `…`; units use
   non-breaking spaces; every interactive element has a visible focus state; motion follows the
   emil tokens and is `prefers-reduced-motion`-guarded (state still changes, movement removed).
7. Gates: `npm test`, `npm run build`, `npm run lint` exit 0. Every AC has ≥1 test (MSW fixtures
   derived from the real captured sample in `plan.md`).

## Reality gate
Local stack up. Scripted Chromium: rollup availability % + completeness % + verdict counts match
`GET /api/v1/availability/component/http-check` (fraction×100, exact); drill-down reveals the real
`http-check` signal child; window toggle refetches with ISO-Z bounds; **first paint is not blocked
by the slow availability fetch** (frame + loading visible immediately, observed live). 390px + 1440px,
zero console errors, no horizontal scroll.
