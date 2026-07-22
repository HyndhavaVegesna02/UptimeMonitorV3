# STORY-130 — Check History page on real backend data

**Status:** ready · **Points:** 3 · **Sprint:** 60
**As** an operator, **I want** a filterable history of raw synthetic-check observations across all
signals — **so that** I can investigate what actually happened at each probe over a window.

## Context
New-frontend initiative (sprint 60, external mode), on the sprint-59 design system + shell.
Replaces the `HistoryPage` placeholder. **Design fresh** with craft via the mandatory skills + the
refimg visual language — do NOT reconstruct the old tab. Contracts in `plan.md` §History. There is
**no "all-signals" endpoint**: enumerate signals from `GET /api/v1/topology`, then fetch
`GET /api/v1/history?signal_key=…&since=…&until=…` per signal and merge. The sprint-59 client's
`getHistory(signalKey, limit?)` lacks window params — add a windowed variant (`since`/`until`) +
`getTopology()`; reuse the existing `ObservationDTO` type.

## Acceptance criteria
1. **Multi-signal merge:** fetch history for every signal in the topology in parallel, merge into
   one list, and sort **most-recent-first globally** (each signal returns newest-first, but the
   interleaving requires a global re-sort by `observed_at`). Resolve each row's component display
   name from the topology.
2. **Filter toolbar (all client-side except the window):** a text search (matches component name /
   location / signal_key, case-insensitive), a **Result** filter with the fixed wire vocabulary
   (All / Up / Degraded / Down — pinned, not derived), a **Location** filter whose options are
   derived from the loaded rows, and the 24h / 7d / 30d **window toggle** (the only control that
   refetches; recomputes tz-aware UTC ISO `since`/`until`).
3. **Dense observation grid:** timestamp, check type, component, location, result (health badge —
   never colour alone), response status code, latency. `null` latency and `null` status code render
   as "—" (never `0 ms` / `0`).
4. **Render cap:** cap rendered rows (e.g. latest 1000) with a caption "showing latest N of M" when
   truncated; the cap is client-side and configurable (injectable for tests).
5. States: loading / error (retry) / empty ("no observations in this window") / **filtered-empty**
   (distinct: "no observations match your filters") / success.
6. Exactly one `<h1>`; `tabular-nums` for numbers/timestamps; ellipsis `…`; visible focus on all
   controls; motion emil-guarded + `prefers-reduced-motion`.
7. Gates: `npm test`, `npm run build`, `npm run lint` exit 0; every AC has ≥1 test.

## Reality gate
Local stack up. Scripted Chromium: grid rows match `GET /api/v1/history?signal_key=http-check` for
the real signal (timestamps, locations `…0047`/`…0060`, latencies, `http` type, 200 codes); the
Result + Location filters narrow the set; window toggle refetches. 390px + 1440px, zero console
errors, no horizontal scroll (the wide grid scrolls within its own container).

## History
- 2026-07-22: implemented on `sprint-60`. **Deleted** the `HistoryPage` placeholder
  (`frontend/src/pages/HistoryPage/HistoryPage.tsx` — the "Coming soon" `PlaceholderPage` mount
  from STORY-121) and replaced it with the real page — no other page still uses it, and
  `PlaceholderPage` itself stays (Approvals/Maintenance/Publications still mount it). Extended
  the API client with a windowed `getHistoryWindow({signal_key, since, until, limit?})`
  (`frontend/src/api/client.ts`) alongside the existing `getHistory` (kept intact — the Dashboard
  still depends on its unwindowed shape). New `frontend/src/features/history/` module: a
  DEDICATED `observationHealth.ts::toObservationHealth` mapper (deliberately distinct from
  `api/statusMapping.ts::toHealthStatus`, which mis-maps a raw `"up"` observation to `unknown`),
  `mergeHistoryRows.ts` (multi-signal merge + a global `observed_at`-desc re-sort — proven with an
  interleave test, not just concatenation), `filterHistoryRows.ts` (the fixed Result vocabulary +
  rows-derived Location options + case-insensitive search), `capRows.ts` (injectable render cap,
  default 1000), `formatTimestamp.ts` (a deterministic hand-formatted UTC timestamp, not
  `toLocaleString`, so the grid's values don't depend on the host locale/timezone),
  `useHistoryData.ts` (per-signal windowed fetches in parallel, sequenced after topology — same
  discipline as `dashboard/useSignalsData.ts`), and the fresh presentational
  `HistoryFilterBar`/`HistoryGrid` components (a dense table scrolling in its own `overflow-x`
  container, same pattern as `ComponentAvailabilityCard`'s table). Reused STORY-129's
  `WindowToggle`/`computeWindowRange` directly rather than duplicating window math. For the
  multi-signal-merge tests, added a second synthetic `ping-check` signal (same location ids/scale
  as the real captured `http-check` sample) as a LOCAL fixture inside
  `mergeHistoryRows.test.ts`/`HistoryPage.test.tsx` (via `server.use()` overrides for the page
  test, same technique `AvailabilityPage.test.tsx`'s AC5 test already established) rather than
  mutating the shared `mocks/handlers/{topology,history}.ts` defaults — that avoids perturbing the
  Availability page's own default-fixture test coverage.
- 2026-07-22: Review refinement (PO-directed, sprint-60): numeric columns right-aligned.
