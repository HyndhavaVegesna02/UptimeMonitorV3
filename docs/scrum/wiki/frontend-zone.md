---
title: Frontend zone — the operator-cockpit SPA (rebuilt, sprint-59/60)
code_refs: [frontend/package.json, frontend/index.html, frontend/vite.config.ts, frontend/eslint.config.js, frontend/src/main.tsx, frontend/src/App.tsx, frontend/src/routes.tsx, frontend/src/nav/tabs.ts, frontend/src/styles/tokens.css, frontend/src/styles/global.css, frontend/src/styles/contrastRatio.ts, frontend/src/styles/parseTokens.ts, frontend/src/components/Icon/Icon.tsx, frontend/src/components/Button/Button.tsx, frontend/src/components/Panel/Panel.tsx, frontend/src/components/StatusBadge/StatusBadge.tsx, frontend/src/components/SummaryCard/SummaryCard.tsx, frontend/src/components/Sparkline/Sparkline.tsx, frontend/src/components/LoadingState/LoadingState.tsx, frontend/src/components/ErrorState/ErrorState.tsx, frontend/src/components/EmptyState/EmptyState.tsx, frontend/src/components/PlaceholderPage/PlaceholderPage.tsx, frontend/src/shell/ShellLayout.tsx, frontend/src/shell/Sidebar/Sidebar.tsx, frontend/src/shell/Sidebar/NavItem.tsx, frontend/src/shell/Topbar/Topbar.tsx, frontend/src/shell/Topbar/formatLastUpdated.ts, frontend/src/shell/useSidebarCollapse.ts, frontend/src/shell/useMediaQuery.ts, frontend/src/shell/TooltipGroupProvider.tsx, frontend/src/shell/tooltipGroupContext.ts, frontend/src/api/client.ts, frontend/src/api/types.ts, frontend/src/api/statusMapping.ts, frontend/src/lib/useFetch.ts, frontend/src/lib/cx.ts, frontend/src/lib/format.ts, frontend/src/lib/relativeTime.ts, frontend/src/lib/overallStatus.ts, frontend/src/lib/healthIcons.ts, frontend/src/lib/combineFetchStates.ts, frontend/src/features/dashboard/useSignalsData.ts, frontend/src/features/dashboard/deriveKpis.ts, frontend/src/features/dashboard/deriveChartData.ts, frontend/src/features/dashboard/deriveProbeLocations.ts, frontend/src/features/dashboard/deriveRecentChecks.ts, frontend/src/features/dashboard/deriveRoster.ts, frontend/src/features/dashboard/aggregateSignals.ts, frontend/src/features/dashboard/KpiRow.tsx, frontend/src/features/dashboard/ResponseTimeChart.tsx, frontend/src/features/dashboard/ProbeLocationsPanel.tsx, frontend/src/features/dashboard/MaintenancePanel.tsx, frontend/src/features/dashboard/RecentChecksFeed.tsx, frontend/src/features/dashboard/ComponentsRoster.tsx, frontend/src/features/availability/ComponentAvailabilityCard.tsx, frontend/src/features/availability/WindowToggle.tsx, frontend/src/features/availability/windowRange.ts, frontend/src/features/availability/format.ts, frontend/src/features/availability/joinSignalAvailability.ts, frontend/src/pages/DashboardPage/DashboardPage.tsx, frontend/src/pages/AvailabilityPage/AvailabilityPage.tsx, frontend/src/pages/HistoryPage/HistoryPage.tsx, frontend/src/pages/ApprovalsPage/ApprovalsPage.tsx, frontend/src/pages/StyleguidePage/StyleguidePage.tsx, frontend/src/features/history/mergeHistoryRows.ts, frontend/src/features/history/filterHistoryRows.ts, frontend/src/features/history/capRows.ts, frontend/src/features/history/formatTimestamp.ts, frontend/src/features/history/observationHealth.ts, frontend/src/features/history/useHistoryData.ts, frontend/src/features/history/HistoryFilterBar.tsx, frontend/src/features/history/HistoryGrid.tsx, frontend/src/features/approvals/operatorActor.ts, frontend/src/features/approvals/useApprovalsDecisions.ts, frontend/src/features/approvals/ProposalCard.tsx, frontend/src/mocks/handlers/index.ts, frontend/src/mocks/handlers/topology.ts, frontend/src/mocks/handlers/availability.ts, frontend/src/mocks/handlers/history.ts, frontend/src/mocks/handlers/approvals.ts, frontend/src/test/setup.ts]
verified_sha: 3a8a2b3
verified_sprint: sprint-60
status: verified
---

## Facts (verified against code)

- **Standalone, backend-isolated SPA.** `frontend/` is a Vite + React 19 + TypeScript (strict)
  SPA — the operator-cockpit "internal dashboard" surface (dossier §17; the other surface is the
  public Statuspage). It imports NO Python-backend source and shares NO build step. Its three DoD
  commands run from `frontend/`: `npm test` (Vitest run-once), `npm run build` (`tsc -b && vite
  build`), `npm run lint` (ESLint flat config, `frontend/eslint.config.js`). The dev server
  proxies `/api/*` → `http://localhost:8000` (`frontend/vite.config.ts`).

- **This is a GREENFIELD REBUILD (sprint-59, STORY-120/121/122).** After two PO-rejected attempts,
  the PO directed (2026-07-21) a from-scratch rebuild of all of `frontend/src/**` to the approved
  *refimg*-derived visual language, keeping only the build toolchain (`vite.config.ts`,
  `eslint.config.js`, `tsconfig*.json`, the `frontend/package.json` scripts). The prior structure
  (AppShell/nav/per-tab features/theme system/Table·UptimeBar·Timeline) was deleted; its article
  is archived at `docs/scrum/wiki/archive/frontend-zone.md`. Fonts are self-hosted **Inter**
  (`@fontsource/inter`, imported in `styles/global.css`), replacing the old Geist. Icons are
  **Phosphor** (`@phosphor-icons/react`) behind the `Icon` wrapper. The design system itself is
  documented separately — see [[frontend-design-system]]; this article is the zone-level map.

- **`src/` layout:**
  - `styles/` — `tokens.css` (three-layer design tokens: primitive → semantic → component; light
    theme, dark-ready scoping) plus `contrastRatio.ts` / `parseTokens.ts` (the WCAG-AA token
    contrast test's engine). See [[frontend-design-system]].
  - `components/` — the primitives: `Icon` (Phosphor wrapper; decorative-`aria-hidden`-or-labelled
    is prop-enforced), `Button`, `Panel`, `StatusBadge` (dot + icon + text; never colour alone),
    `SummaryCard`, `Sparkline` (inline SVG), `LoadingState`, `ErrorState`, `EmptyState`, and
    `PlaceholderPage` (the shared stub the not-yet-built tabs render).
  - `shell/` — `ShellLayout.tsx` composes the collapsible `Sidebar/` (grouped nav + `NavItem`) and
    the `Topbar/` (page title + worst-of status pill + last-updated + notifications + "＋
    Maintenance") around a routed `<Outlet>`. `useSidebarCollapse.ts` persists the collapse choice
    to `localStorage` (key + `SIDEBAR_COLLAPSE_PREPAINT_CLASS` shared with the `index.html`
    pre-paint script, which is removed via `useLayoutEffect` after mount so it never outlives
    hydration — STORY-121 review-fix). `useMediaQuery.ts` (a `useSyncExternalStore` wrapper) gates
    the desktop rail (≥861px) vs the off-canvas mobile sheet (≤860px). `TooltipGroupProvider` +
    `tooltipGroupContext` implement the emil delayed-tooltip pattern for the collapsed rail.
  - `routes.tsx` / `nav/tabs.ts` — the six routes (Dashboard, Availability, History, Approvals,
    Maintenance, Publications) plus a sibling `/styleguide`. `App.tsx` / `main.tsx` boot it.
  - `pages/` — `DashboardPage` (STORY-122), `AvailabilityPage` (STORY-129), `HistoryPage`
    (STORY-130), and `ApprovalsPage` (STORY-131) are REAL pages; `Maintenance`/`Publications` are
    still `PlaceholderPage` stubs awaiting the rest of sprint 60; `StyleguidePage` renders every
    primitive × state (STORY-120).
  - `api/` — `client.ts` (typed fetch client, `/api` base), `types.ts` (DTOs mirroring
    `backend/src/api/v1/*/models.py`), `statusMapping.ts` (vendor → health).
  - `features/dashboard/` — the STORY-122 dashboard: `useSignalsData` (derives signal keys from
    components, fetches per-signal history + availability), the pure derivations (`deriveKpis`,
    `deriveChartData`, `deriveProbeLocations`, `deriveRecentChecks`, `deriveRoster`,
    `aggregateSignals`), and the view components (`KpiRow`, `ResponseTimeChart`,
    `ProbeLocationsPanel`, `MaintenancePanel`, `RecentChecksFeed`, `ComponentsRoster`).
  - `features/availability/` — the STORY-129 Availability page's pieces: `WindowToggle`
    (24h/7d/30d `role="group"`/`aria-pressed`), `windowRange.ts` (`computeWindowRange` — tz-aware
    UTC ISO `since`/`until`, `Z`-suffixed, pinned to a caller-supplied `now`), `format.ts`
    (`formatAvailabilityPercent` — 0–1 fraction → 2-decimal string, `null`→"No data", never a
    fabricated `0%`; `isLowCompleteness`; `availabilityBand`; `deriveDownCount = total − passing
    − maintenance`), `joinSignalAvailability.ts` (joins the availability endpoint's
    `signal_key`-only children onto their topology display name/interval), and
    `ComponentAvailabilityCard` (one component's own independent `useFetch` — never bundled with
    any other component's — rendering a rollup `<tr>` plus, when `hasSignals`, an
    `aria-expanded`/`aria-controls` toggle revealing a second `hidden`-attribute-gated `<tbody>`
    of per-signal rows).
  - `features/history/` — the STORY-130 Check History page's pieces:
    `observationHealth.ts::toObservationHealth` (a DEDICATED raw-observation-vocabulary mapper —
    up/down/degraded → tokens, unknown → `unknown` — deliberately NOT `statusMapping.ts`'s
    vendor-status mapper, which mis-maps a raw `"up"` observation onto `unknown`),
    `mergeHistoryRows.ts` (merges every signal's observations into one list and re-sorts it
    GLOBALLY by `observed_at` desc — proven by an interleave test, not a per-signal
    concatenation — joining each row's component name from the topology),
    `filterHistoryRows.ts` (`RESULT_FILTER_OPTIONS` — the fixed All/Up/Degraded/Down wire
    vocabulary, pinned, never derived — plus `deriveLocationOptions` from the loaded rows and the
    case-insensitive search predicate), `capRows.ts` (`DEFAULT_RENDER_CAP` = 1000, injectable),
    `formatTimestamp.ts::formatObservedAt` (hand-formatted UTC, not `toLocaleString` — locale/
    timezone-independent), `useHistoryData.ts` (per-signal WINDOWED fetches in parallel, sequenced
    after topology, re-keyed on `since`/`until` so only the window toggle refetches — same
    discipline as `dashboard/useSignalsData.ts`), and the presentational `HistoryFilterBar`
    (labelled search/Result-select/Location-select) + `HistoryGrid` (the dense table, its own
    `overflow-x` scroll container). Reuses `features/availability/{WindowToggle,windowRange}`
    directly rather than duplicating window math.
  - `features/approvals/` — the STORY-131 Approvals page's pieces, and the sprint's FIRST mutating
    feature module: `operatorActor.ts::OPERATOR_ACTOR` (the single fixed-actor swap-point for
    future auth), `useApprovalsDecisions.ts` (the confirm/submit state machine — idle → confirming
    → submitting, LIFTED to one shared slice so "only one proposal mid-decision at a time" is
    structural rather than a per-card convention; a 409/404 both call the caller's refresh with a
    non-destructive notice, any OTHER failure stays confirming with an inline retry and does NOT
    refresh — a mutation never throws to the console, proven with a `console.error` spy across
    every path), and `ProposalCard.tsx` (from→to health badges via `statusMapping.ts::
    toHealthStatus` — proposals carry the SAME vendor vocabulary as `ComponentDTO.status`, unlike
    `ObservationDTO.health`, which needed `features/history`'s dedicated mapper; `from_status: null`
    → "New"; the two-step Approve/Reject → Confirm/Cancel prompt is keyboard-dismissable via Escape
    and focus-managed — Confirm gets focus on open, the ORIGINAL trigger gets it back on cancel,
    found by a `data-role` container query rather than a captured DOM ref, since the trigger buttons
    live in a different subtree than the confirm block and unmount/remount across that transition).
  - `lib/` — `useFetch.ts` (the read-fetch state machine — loading/error/success, cancel-guarded;
    `fetcher` must be a stable ref), `overallStatus.ts` (worst-of derivation: down > partial >
    degraded > maintenance > unknown > up; empty → unknown), `healthIcons.ts`, `format.ts`,
    `relativeTime.ts`, `cx.ts`, `combineFetchStates.ts`.
  - `mocks/` — MSW is the ONLY mocked I/O edge; per-endpoint handlers
    (`handlers/{components,approvals,history,availability,maintenance,topology}.ts`) composed in
    `handlers/index.ts`, wired in `test/setup.ts`. Fixtures derive from REAL captured `/api/v1`
    responses (`docs/scrum/sprints/2026-07-21-sprint-59/live-api-samples.md` +
    `docs/scrum/sprints/2026-07-21-sprint-60/plan.md` §Appendix).

- **API client (`api/client.ts`):** `getComponents()`, `getApprovals()`, `getHistory(signalKey,
  limit?)`, `getAvailability(signalKey)`, `getMaintenance()`, `getTopology()` (STORY-129),
  `getComponentAvailability(componentId, {since, until})` (STORY-129, component-grain rollup +
  nested signal children), `getHistoryWindow({signal_key, since, until, limit?})` (STORY-130 — the
  windowed variant `getHistory` lacks; `getHistory` itself is UNCHANGED, the Dashboard still uses
  its unwindowed shape), `postDecision(proposalId, DecisionRequest)` (STORY-131 — the sprint's
  FIRST write path: `POST /api/v1/decisions/{proposal_id}`, note the path is `/decisions/`, NOT
  nested under `/approvals`). The write path is a private `postJson<T>` alongside the existing
  `getJson`, sharing the same `readOkJson`/`ApiError` handling so `.status`/`.detail` populate
  identically for a non-2xx POST (a 409/404 the same way a GET caller would see them) — built to be
  reused as-is by STORY-132's Maintenance mutations. DTOs in `api/types.ts`: `ComponentDTO
  {id,name,status}`, `ProposalDTO`, `ObservationDTO {signal_key, observed_at, health, location,
  latency_ms, response_status_code, check_type}`, `AvailabilityDTO` (`availability_pct`/
  `completeness_pct` are 0–1 fractions, nullable), `MaintenanceWindowDTO`,
  `ComponentTopologyDTO`/`TopologySignalDTO` (STORY-129 — `interval_seconds` is `int | null`),
  `ComponentAvailabilityDTO`/`SignalAvailabilityDTO` (STORY-129 — the latter is `AvailabilityDTO` +
  `signal_key`, no display name), `DecisionRequest {action: "approve"|"reject", actor, notes?}` /
  `DecisionResponse {proposal_id, state, resolved_at}` (STORY-131). Re-derived fresh from the LIVE
  contracts (verified at the STORY-121/122/129/131 reality gates); extends cleanly as later tabs
  need more endpoints. `statusMapping.ts` maps the vendor `ComponentStatus` vocabulary
  (operational/degraded_performance/partial_outage/major_outage/under_maintenance) onto the
  7-status health palette (…→up/degraded/partial/down/maintenance; else→unknown) — STORY-131's
  Approvals page reuses this SAME mapper for a proposal's `from_status`/`to_status` (both carry the
  vendor vocabulary too), contrasting with STORY-130's dedicated `observationHealth.ts` mapper
  (raw observation health is a DIFFERENT vocabulary that this mapper mis-maps).

- **Verified live quirk (STORY-129, plan-verifier 2026-07-22):** `GET /api/v1/availability/
  component/{id}`'s `rollup.distinct_locations` reads `0` while each `signals[]` child reads the
  real count — a backend rollup-group quirk. `ComponentAvailabilityCard` renders it honestly
  (no client-side "fix-up") — see the fixture in `mocks/handlers/availability.ts`
  (`FIXTURE_COMPONENT_AVAILABILITY`).

- **Truthful rendering (the PO's core requirement).** Every rendered value derives from a real API
  field — no invented numbers, components, locations, or deltas. Where no real baseline exists
  (e.g. a period-over-period delta) the value is OMITTED, never fabricated. Verified at the
  reality gates: with the live backend holding one component + zero approvals, the Dashboard shows
  exactly that (availability 100%, 1/1 healthy, 0 approvals, 2 probe locations), not the
  prototype's richer mock data.

- **Motion is first-class (emil discipline).** Sidebar collapse/expand, the mobile sheet, and
  chart/data entrance animate `transform`/`opacity` only (never `transition: all`), ≤250ms, with
  custom eases and `prefers-reduced-motion` guards (movement removed, state still changes);
  chart/data entrance is one-shot with no motion on refresh. Pinned by `styles/*.test` +
  per-component `motionGuards`-style tests and confirmed live under emulated `reduce`.

## Inference (synthesis, not verified)
- The append-points a later page-story edits are `api/client.ts` + `api/types.ts` (new endpoint +
  DTO), a `mocks/handlers/<feature>.ts`, and its own `pages/<Tab>Page/` + `features/<tab>/` — the
  routing table and `useFetch<T>` are structured for additive-only edits, so the sprint-60/61 tab
  fills should not collide.

## Known gaps / deferred (filed to backlog)
- The two remaining tabs (Maintenance/Publications) are still `PlaceholderPage` stubs — real
  content lands later in sprint 60.
- The shared `Button` primitive does not forward refs (a plain function component, not
  `forwardRef`) — `ProposalCard`'s Confirm button had to fall back to a hand-rolled native
  `<button className="button button--primary">` to get an imperative focus target. If a future
  story needs a ref into `Button` again, that's the trigger to add `forwardRef` there once, rather
  than a third one-off native-button workaround.
- `Button.css`'s `--button-height` is 36px — under the 44×44px (iOS)/48×48dp (Material) minimum
  touch-target guideline (ui-ux-pro-max checklist item 2, STORY-131 review). Pre-existing
  (STORY-120), app-wide, not something a single-page story should change unilaterally.
- No sample-mode UI in the new frontend — the old consumer was removed in the rebuild; see
  [[sample-mode]] (backend feature still exists; a new consumer is unscheduled).
- STORY-125 (mobile-sheet focus-trap + `role="dialog"`), STORY-126 (skip-to-content link),
  STORY-127 (`/api/v1/availability` is slow against DynamoDB-Local → dashboard first-paint stall;
  STORY-129's `ComponentAvailabilityCard` independent-fetch pattern is the mitigation the
  Availability page itself needed, but the Dashboard's own STORY-122 KPI fetch is untouched by
  this story), STORY-128 (lazy-load the availability-dependent KPI + dedupe the
  components/approvals fetch).

## History
- sprint-59 (STORY-120/121/122, greenfield rebuild — sprint-close compile pass): the old article
  (the sprint-23/24 + sprint-38 "second attempt": AppShell/nav/per-tab features/theme system/
  Table·UptimeBar·Timeline) was archived to `docs/scrum/wiki/archive/frontend-zone.md` with a
  tombstone; this article was rewritten for the rebuilt frontend — three-layer design system +
  Phosphor `Icon` (STORY-120, see [[frontend-design-system]]), collapsible-sidebar/topbar shell
  with first-class motion (STORY-121), and the Dashboard on real data (STORY-122). Fonts Geist→
  Inter; icons → Phosphor. Frontend-only; backend untouched. verified_sha = 113e2be.
- 2026-07-22 (STORY-129, sprint-60): the Availability page shipped as a fresh design (PO
  directive — not a reconstruction of the pre-sprint-59 tab). Added `getTopology()` +
  `getComponentAvailability()` to the API client, the four new topology/component-availability
  DTOs, and `features/availability/**` (`WindowToggle`, `ComponentAvailabilityCard`,
  `windowRange`/`format`/`joinSignalAvailability` pure helpers). Each component's availability
  fetch is independent (its own `useFetch` per `ComponentAvailabilityCard`, never a shared
  `Promise.all`) — the STORY-122/127 first-paint lesson applied proactively this time.
  `AvailabilityPage`'s `PlaceholderPage` stub is gone; the other four tabs are unaffected.
  verified_sha = 9ffdaba.
- 2026-07-22 (STORY-130, sprint-60): the Check History page shipped as a fresh design, reusing
  STORY-129's `WindowToggle`/`computeWindowRange` rather than duplicating window math. Added
  `getHistoryWindow()` to the API client (kept `getHistory` unchanged — the Dashboard still uses
  it) and the `features/history/**` module (merge + global re-sort, filter, render-cap, a
  DEDICATED observation-health mapper distinct from the vendor-status one, and a windowed
  per-signal-parallel fetch hook). `HistoryPage`'s `PlaceholderPage` stub is gone; the other three
  tabs are unaffected. verified_sha = f67ff1a.
- 2026-07-22 (STORY-131, sprint-60): the Approvals page shipped — the sprint's FIRST mutating page,
  introducing the write path. Added a private `postJson<T>` (mirrors `getJson`'s `readOkJson`/
  `ApiError` handling) and `postDecision()` to the API client, `DecisionRequest`/`DecisionResponse`
  to `api/types.ts`, and the `features/approvals/**` module (`operatorActor`,
  `useApprovalsDecisions`, `ProposalCard`). A 409/404 both refresh the list with a non-destructive
  notice; any other failure stays confirming with an inline retry and never throws to the console
  (page-level forced-409/404 tests assert BOTH the friendly notice and a genuine second
  `getApprovals` fetch, not just local card removal). `ApprovalsPage`'s `PlaceholderPage` stub is
  gone; Maintenance/Publications are unaffected. Also folded in a pre-existing wiki-staleness gap
  from STORY-130: its own wiki-verified_sha (`f67ff1a`) predated three later fixup commits on this
  same branch (`ebd413f` non-unique merged-row-key fix + its regression test, `1d447d7` a `tsc`
  build fix) that the STORY-130 wiki pass never re-verified against — `mergeHistoryRows.ts` now
  keys each row by its FINAL sorted position, not `${signalKey}-${observedAt}-${location}` (not
  unique on the real wire — two synthetic locations can share an identical millisecond
  `observed_at`). No Fact above was wrong, just unconfirmed against the newer commits; this sweep
  re-verified it. verified_sha = 3a8a2b3.
