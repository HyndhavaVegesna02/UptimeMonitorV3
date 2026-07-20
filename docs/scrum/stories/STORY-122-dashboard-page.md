# STORY-122 — Dashboard page on real backend data

**Status:** ready · **Points:** 3 · **Sprint:** 59
**As** an operator, **I want** the Dashboard — KPIs, a response-time chart, probe locations,
recent checks, and the component roster — **so that** I get the whole system's health at a
glance, matching the approved prototype, on real data.

## Context
Built on STORY-120 + STORY-121. Data via a freshly re-derived API client typed from the live
`/api/v1` contracts (verified at the reality gate; old types read only as contract reference).
Reference: the approved prototype's Dashboard. Skills mandatory (same five); ui-ux-pro-max
**chart** domain binds the chart (periodic-refresh visuals, not streaming/ticker; markers are
shape+text not colour alone; inline SVG, no chart lib).

## Acceptance criteria
1. **KPI row** (4): overall availability (24h), avg response time, components healthy (n/total),
   pending approvals. Each value is derived from real API data (no invented fields); the two
   rate metrics show an inline SVG sparkline. Deltas use sign + arrow + colour (never colour
   alone).
2. **Response-time chart:** inline SVG line/area over the selected window with axis labels and
   a called-out latency spike; `role="img"` + descriptive `aria-label`; no animation on data
   refresh beyond an entrance transition (reduced-motion guarded).
3. **Probe-locations panel:** the real locations from history, each with health (dot+label) and
   latest latency; a segmented control (Latency/Availability/Errors) with `aria-pressed`.
4. **Upcoming-maintenance** summary sourced from the maintenance endpoint (empty → tidy empty
   state).
5. **Recent-checks feed:** latest N observations (component, location label, relative time,
   latency, health tag). **Components roster:** all components with status dot+label, 24h
   uptime, latest latency, trend.
6. Every region has loading / error / empty states; the page has exactly one `<h1>`; headings
   are hierarchical; numbers use `tabular-nums`; units use non-breaking spaces; ellipsis is `…`.
7. Gates: `npm test`, `npm run build`, `npm run lint` exit 0.

## Reality gate
Local stack up. Scripted Chromium (`tools/ui-sweep`) asserts: KPI availability/latency,
component statuses, and recent-check rows match `GET /api/v1/components|history|approvals`;
both 390px and 1440px render with **zero console errors** and no horizontal scroll.
