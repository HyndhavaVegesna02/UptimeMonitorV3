---
title: Frontend zone — the operator-cockpit SPA (rebuilt, sprint-59/60)
code_refs: [frontend/package.json, frontend/index.html, frontend/vite.config.ts, frontend/eslint.config.js, frontend/src/main.tsx, frontend/src/App.tsx, frontend/src/routes.tsx, frontend/src/nav/tabs.ts, frontend/src/styles/tokens.css, frontend/src/styles/global.css, frontend/src/styles/contrastRatio.ts, frontend/src/styles/parseTokens.ts, frontend/src/components/Icon/Icon.tsx, frontend/src/components/Button/Button.tsx, frontend/src/components/Panel/Panel.tsx, frontend/src/components/StatusBadge/StatusBadge.tsx, frontend/src/components/SummaryCard/SummaryCard.tsx, frontend/src/components/Sparkline/Sparkline.tsx, frontend/src/components/LoadingState/LoadingState.tsx, frontend/src/components/ErrorState/ErrorState.tsx, frontend/src/components/EmptyState/EmptyState.tsx, frontend/src/shell/ShellLayout.tsx, frontend/src/shell/Sidebar/Sidebar.tsx, frontend/src/shell/Sidebar/NavItem.tsx, frontend/src/shell/Topbar/Topbar.tsx, frontend/src/shell/Topbar/formatLastUpdated.ts, frontend/src/shell/Topbar/NotificationsButton.tsx, frontend/src/shell/useSidebarCollapse.ts, frontend/src/shell/useMediaQuery.ts, frontend/src/shell/TooltipGroupProvider.tsx, frontend/src/shell/tooltipGroupContext.ts, frontend/src/api/client.ts, frontend/src/api/types.ts, frontend/src/api/statusMapping.ts, frontend/src/lib/useFetch.ts, frontend/src/lib/fetchDedup.ts, frontend/src/lib/cx.ts, frontend/src/lib/format.ts, frontend/src/lib/relativeTime.ts, frontend/src/lib/overallStatus.ts, frontend/src/lib/healthIcons.ts, frontend/src/lib/combineFetchStates.ts, frontend/src/lib/niceAxis.ts, frontend/src/features/dashboard/useSignalsData.ts, frontend/src/features/dashboard/deriveKpis.ts, frontend/src/features/dashboard/deriveChartData.ts, frontend/src/features/dashboard/deriveProbeLocations.ts, frontend/src/features/dashboard/deriveRecentChecks.ts, frontend/src/features/dashboard/deriveRoster.ts, frontend/src/features/dashboard/aggregateSignals.ts, frontend/src/features/dashboard/KpiRow.tsx, frontend/src/features/dashboard/locationLabel.ts, frontend/src/features/dashboard/KpiMeter.tsx, frontend/src/features/dashboard/deriveKpiTone.ts, frontend/src/features/dashboard/ResponseTimeChart.tsx, frontend/src/features/dashboard/ProbeLocationsPanel.tsx, frontend/src/features/dashboard/MaintenancePanel.tsx, frontend/src/features/dashboard/RecentChecksFeed.tsx, frontend/src/features/dashboard/ComponentsRoster.tsx, frontend/src/features/availability/ComponentAvailabilityCard.tsx, frontend/src/features/availability/WindowToggle.tsx, frontend/src/features/availability/windowRange.ts, frontend/src/features/availability/format.ts, frontend/src/features/availability/joinSignalAvailability.ts, frontend/src/pages/DashboardPage/DashboardPage.tsx, frontend/src/pages/AvailabilityPage/AvailabilityPage.tsx, frontend/src/pages/HistoryPage/HistoryPage.tsx, frontend/src/pages/ApprovalsPage/ApprovalsPage.tsx, frontend/src/pages/StyleguidePage/StyleguidePage.tsx, frontend/src/features/history/mergeHistoryRows.ts, frontend/src/features/history/filterHistoryRows.ts, frontend/src/features/history/capRows.ts, frontend/src/features/history/formatTimestamp.ts, frontend/src/features/history/observationHealth.ts, frontend/src/features/history/useHistoryData.ts, frontend/src/features/history/HistoryFilterBar.tsx, frontend/src/features/history/HistoryGrid.tsx, frontend/src/features/approvals/operatorActor.ts, frontend/src/features/approvals/useApprovalsDecisions.ts, frontend/src/features/approvals/ProposalCard.tsx, frontend/src/features/maintenance/deriveWindowState.ts, frontend/src/features/maintenance/mapMaintenanceError.ts, frontend/src/features/maintenance/localDateTimeToUtcIso.ts, frontend/src/features/maintenance/formatWindowRange.ts, frontend/src/features/maintenance/WindowStateBadge.tsx, frontend/src/features/maintenance/useScheduleMaintenance.ts, frontend/src/features/maintenance/useMaintenanceDeletion.ts, frontend/src/features/maintenance/MaintenanceWindowCard.tsx, frontend/src/features/maintenance/ScheduleMaintenanceForm.tsx, frontend/src/pages/MaintenancePage/MaintenancePage.tsx, frontend/src/features/publications/OutcomeChip.tsx, frontend/src/features/publications/PublicationsTimeline.tsx, frontend/src/pages/PublicationsPage/PublicationsPage.tsx, frontend/src/mocks/handlers/index.ts, frontend/src/mocks/handlers/topology.ts, frontend/src/mocks/handlers/availability.ts, frontend/src/mocks/handlers/history.ts, frontend/src/mocks/handlers/approvals.ts, frontend/src/mocks/handlers/maintenance.ts, frontend/src/mocks/handlers/publications.ts, frontend/src/test/setup.ts]
verified_sha: 5781630
verified_sprint: sprint-61
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
    `SummaryCard`, `Sparkline` (inline SVG), `LoadingState` (an optional `compact` prop, STORY-136
    AC2, renders it inline with no block padding/centering — first consumer: the topbar's
    overall-status slot), `ErrorState`, `EmptyState`.
    `PlaceholderPage` (the shared not-yet-built-tab stub) was DELETED in STORY-133 once
    `PublicationsPage` — its last mount — became a real page; no component under `src/` references
    it anymore.
  - `shell/` — `ShellLayout.tsx` composes the collapsible `Sidebar/` (grouped nav + `NavItem`) and
    the `Topbar/` (page title + worst-of status pill + last-updated + notifications + "＋
    Maintenance") around a routed `<Outlet>`. `Topbar`'s `overallStatus` prop is `HealthStatus |
    null` (STORY-136 AC2 fix) — `ShellLayout` passes `null` until its `getComponents` fetch
    SUCCEEDS (loading OR error both read as `null`), and `Topbar` renders `LoadingState`'s compact
    variant ("Updating status…") for `null` instead of `deriveOverallStatus([])`'s `unknown`; the
    `unknown` `StatusBadge` now only ever renders for a succeeded fetch that is genuinely unknown.
    `useSidebarCollapse.ts` persists the collapse choice
    to `localStorage` (key + `SIDEBAR_COLLAPSE_PREPAINT_CLASS` shared with the `index.html`
    pre-paint script, which is removed via `useLayoutEffect` after mount so it never outlives
    hydration — STORY-121 review-fix). `useMediaQuery.ts` (a `useSyncExternalStore` wrapper) gates
    the desktop rail (≥861px) vs the off-canvas mobile sheet (≤860px). `TooltipGroupProvider` +
    `tooltipGroupContext` implement the emil delayed-tooltip pattern for the collapsed rail.
    **`Topbar`'s notifications control is no longer a dead button (STORY-141 AC1, sprint-61):**
    `Topbar.tsx` now renders `shell/Topbar/NotificationsButton.tsx`, a self-contained disclosure
    popover — trigger wires `aria-haspopup="dialog"`/`aria-expanded`/`aria-controls` to a
    `role="dialog"` `Panel` anchored under it; opening moves focus INTO the panel (`tabIndex={-1}`
    + `.focus()`), Escape or an outside `mousedown` closes it and returns focus to the trigger
    (mirroring `ShellLayout.tsx::closeMobileNav`'s own close-and-refocus convention). There is no
    notifications data source in scope, so the panel's only content is an `EmptyState` ("No
    notifications") — not fabricated data. **The mobile off-canvas sheet also gained an in-drawer
    header (STORY-141 AC2, sprint-61):** `Sidebar.tsx` now renders a `.shell-sidebar__mobile-header`
    (brand text "Uptime Monitor" + an explicit `X` close button, `aria-label="Close menu"`, calling
    the same `onCloseMobile` the backdrop/Escape paths already used) ahead of the existing collapse
    toggle — CSS-hidden at the ≥861px desktop breakpoint (`Sidebar.css`), the same
    always-render-CSS-gate convention `.shell-sidebar__toggle` already used. Backdrop + Escape
    dismissal are unchanged; the drawer now has three ways to close it.
  - `routes.tsx` / `nav/tabs.ts` — the six routes (Dashboard, Availability, History, Approvals,
    Maintenance, Publications) plus a sibling `/styleguide`. `App.tsx` / `main.tsx` boot it.
  - `pages/` — `DashboardPage` (STORY-122; layout unified STORY-138 sprint-61, below), `AvailabilityPage` (STORY-129), `HistoryPage`
    (STORY-130), `ApprovalsPage` (STORY-131), `MaintenancePage` (STORY-132), and `PublicationsPage`
    (STORY-133) are ALL real pages now — **every one of the six nav routes renders real content,
    no placeholder remains** (`StyleguidePage` renders every primitive × state, STORY-120, and is
    the one non-tab sibling route).
  - `api/` — `client.ts` (typed fetch client, `/api` base), `types.ts` (DTOs mirroring
    `backend/src/api/v1/*/models.py`), `statusMapping.ts` (vendor → health).
  - `features/dashboard/` — the STORY-122 dashboard: `useSignalsData` (derives signal keys from
    components, fetches per-signal history + availability), the pure derivations (`deriveKpis`,
    `deriveChartData`, `deriveProbeLocations`, `deriveRecentChecks`, `deriveRoster`,
    `aggregateSignals`, `deriveKpiTone` — STORY-138, below), and the view components (`KpiRow`,
    `KpiMeter` — STORY-138, below — `ResponseTimeChart`, `ProbeLocationsPanel`, `MaintenancePanel`,
    `RecentChecksFeed`, `ComponentsRoster`).
    `deriveKpiTone.ts::componentsHealthTone`/`approvalsTone` (STORY-138 AC4) are the KPI-card
    accent-by-rule functions `KpiRow.tsx` calls for the two cards that don't have a real time
    series to plot: `componentsHealthTone(healthy, total)` is `positive` when every component is
    up, `negative` when at least one isn't, `neutral` for the explicit `total === 0` empty case;
    `approvalsTone(pendingApprovals)` is `accent` when something is pending, else `neutral`. Each
    feeds a `KpiMeter` (a thin filled-bar meter, `aria-hidden`, clamped `ratio` 0-1 — `1` renders a
    solid flat bar for "Pending approvals", which has no denominator) rendered as that card's
    `children`, so all 4 `KpiRow` cards now render SOME footer visual inside
    `SummaryCard`'s `.summary-card__extra` slot (a `Sparkline` for the two trend cards, a
    `KpiMeter` for these two) — see [[frontend-design-system]] for the shared-footprint CSS detail.
    **`KpiRow`'s availability and response-time cards render a "No data yet" empty treatment
    (STORY-140 AC1, sprint-61) when their value is genuinely `null`**, via
    `SummaryCard`'s new `empty?: { message; detail? }` prop (swaps the value/unit/sub block for a
    compact `EmptyState` — `EmptyState.tsx` gained a `compact` modifier, no block padding, for this
    embedding) — never the prior bare "— %"/"— ms" plus a misleading "Across 0 probe locations" sub
    line. `locationLabel.ts` (STORY-122, revised STORY-140 AC3) now renders a `#`-prefixed short id
    (`#0047`, the ticket/PR-number idiom) instead of the ellipsis-prefixed tail (`…0047`, which read
    as "truncated, something hidden") for `HistoryGrid`, `HistoryFilterBar`, `RecentChecksFeed`,
    `ProbeLocationsPanel`, and `ResponseTimeChart`'s spike legend — still only an id presentation,
    never an invented name; a true human-readable location name needs a backend `location_name`
    field that does not exist on `ObservationDTO` today, filed as STORY-144 (backend, out of this
    zone's scope).
    `deriveRecentChecks.ts` now keys each row by its FINAL sorted+capped position, NOT
    `` `${signalKey}-${observed_at}-${location}` `` (STORY-136 AC1 fix — the same live-wire
    collision class STORY-130 fixed on `mergeHistoryRows.ts`; two synthetic probe observations can
    share that triple).
    `ResponseTimeChart.tsx`'s Y-axis (STORY-139) is a real 0 baseline, not the data minimum:
    `deriveChartData.ts::deriveChartData` scales every plotted point and gridline against
    `[0, niceMax]`, where `niceMax`/its ticks come from the new pure `frontend/src/lib/
    niceAxis.ts::computeNiceAxis` (a Heckpert-style ceiling nice-number picker over
    {1, 2, 2.5, 5, 10} × 10^n — always `>= maxValue`, never a raw data-derived value like the old
    max→min gridline labels). `deriveChartData.ts::AXIS_GUTTER` (48px) reserves a left label
    column: `ChartGridline.labelX`/`labelY` sit inside it (`labelX < AXIS_GUTTER`, `labelY ===
    y`, vertically centered — no more 4px-above-the-line overlap), and every plotted `ChartPoint.x`
    plus the gridlines' `x1` start at `AXIS_GUTTER`, not `0`. The empty/no-data `EmptyState` path
    and the chart's `role="img"`/`aria-label` are unchanged.
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
    timezone-independent; carries an explicit trailing `" UTC"` label since STORY-140 AC2 (sprint-61),
    matching `features/maintenance/formatWindowRange.ts`'s existing "UTC"
    convention so History-row timestamps are no longer the one unlabelled absolute time on the
    Dashboard/History surfaces), `useHistoryData.ts` (per-signal WINDOWED fetches in parallel, sequenced
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
  - `features/maintenance/` — the STORY-132 Maintenance page's pieces, the sprint's SECOND mutating
    feature (schedule + delete): `deriveWindowState.ts::deriveMaintenanceWindowState` (the DTO has
    NO state field — half-open `[starts_at, ends_at)` rule against a caller-supplied `now`, `now ===
    starts_at` is ACTIVE, `now === ends_at` is PAST, boundary instants pinned+tested),
    `mapMaintenanceError.ts::mapMaintenanceError` (THE crux of this page — order-sensitive 422
    `detail`-string → field mapping; "strictly greater than" is checked BEFORE the plain
    "starts_at" check, so the end-before-start message maps to `ends_at`, not the `starts_at` it
    also names), `localDateTimeToUtcIso.ts` (`datetime-local` wall-clock → tz-aware UTC ISO,
    round-trip tested), `formatWindowRange.ts` (UTC same-day vs multi-day range text),
    `WindowStateBadge` (dot + text upcoming/active/past — a DISTINCT small vocabulary from
    `StatusBadge`'s `HealthStatus`, not an overload of it), `useScheduleMaintenance` (client-side
    guards `component_id` non-blank and `ends_at > starts_at` BEFORE ever calling the API; maps a
    server 422 through `mapMaintenanceError`; resets/refreshes the list on 201; never throws),
    `useMaintenanceDeletion` (the SAME confirm/submit shape as Approvals'
    `useApprovalsDecisions`, simplified to one action — delete is NOT idempotent, so a 404 sets a
    non-destructive notice AND still calls the refresh, never a silent success),
    `MaintenanceWindowCard` (title tidy-fallback "Maintenance window", the state badge, UTC range,
    reason `—` when null, inline delete confirm — the delete trigger stays MOUNTED [only disabled]
    through confirm/submit rather than being replaced, so a single stable ref refocuses it after
    Cancel, unlike `ProposalCard`'s two-trigger `data-role` workaround), and
    `ScheduleMaintenanceForm` (UNCONTROLLED inputs read via `FormData` on submit rather than
    per-keystroke controlled state — vercel-react-best-practices; its OWN `getComponents`
    fetch/loading/error, independent of the windows list's per AC5; field errors carry
    `aria-invalid`/`aria-describedby`/`role="alert"`; a detail naming no field renders a
    form-level banner; the shared `Button` primitive can't be the submit button since it hardcodes
    `type="button"` — a plain native `<button type="submit">` is used instead, same visual
    classes).
  - `features/publications/` — the STORY-133 Publications page's pieces, the sprint's LAST page and
    its simplest (read-only, no mutation): `OutcomeChip` (dot + text `succeeded`/`failed` pill,
    using the `--color-pos-*`/`--color-neg-*` semantic tokens — a DELIBERATELY separate vocabulary
    from `StatusBadge`'s health tokens, since `outcome` [the Statuspage-call result] and `status`
    [the published health] are different concepts that must never visually conflate, even when a
    `failed` outcome pairs with an `operational`/"Up" status) and `PublicationsTimeline` (the dense
    grid, same `overflow-x`-scrolled-table shape as `HistoryGrid`/`ComponentAvailabilityCard`;
    renders `PublicationDTO[]` in the EXACT order given — no re-sort, since the endpoint already
    returns most-recent-first capped ~50 server-side — proven by a test that puts the
    chronologically-older fixture entry first in the array and asserts it renders first in the
    DOM; `proposal_id: null`→"—", `author: null`→"—", no `incident_id` or other fabricated field).
    Reuses `features/history/formatTimestamp.ts::formatObservedAt` for the published-at column
    rather than duplicating an identical UTC-formatting helper.
  - `lib/` — `useFetch.ts` (the read-fetch state machine — loading/error/success, cancel-guarded;
    `fetcher` must be a stable ref; STORY-136 AC3 added a `DEFAULT_FETCH_TIMEOUT_MS` [15s,
    overridable via a second `timeoutMs` argument] request timeout — a never-settling request now
    forces the `error` phase itself, surfacing the existing `ErrorState` + retry rather than
    spinning forever; the timer is cleared the moment the real fetch settles, on unmount, and per
    retry attempt), `fetchDedup.ts` (STORY-137 — `dedupedFetch`/`forgetFetch`/
    `resetFetchDedupCache`: an in-house promise-coalescing cache `useFetch` routes every fetch
    through, keyed on the fetcher's OWN identity, NOT a result cache — an entry lives in the
    module-level `Map` only while its request is in flight and is deleted the instant it settles,
    so a `retry` always genuinely re-invokes the fetcher. Two `useFetch` instances sharing the same
    stable fetcher reference — e.g. `ShellLayout` and `DashboardPage` both calling the literal
    `getComponents` export — that are in flight at the same moment now share ONE underlying
    request; two DIFFERENT fetcher references, even resolving to the same value, are NEVER
    coalesced [a `ComponentAvailabilityCard` per component keeps its own `useCallback`'d fetcher,
    so distinct components/args are always distinct identities]. `useFetch.ts::useFetch`'s effect
    calls `forgetFetch(fetcher)` from BOTH the STORY-136 timeout handler AND the effect's own
    cleanup (quality-review MAJOR fix, sprint-61) — the cleanup fires on every unmount AND on every
    dependency change (a `retry`), so a component that unmounts while its request is still hung
    (e.g. the user navigates away inside the 15s timeout window) evicts the in-flight entry too,
    rather than only the timeout path; otherwise a never-settling fetcher's promise is orphaned in
    the map forever (its own `.finally` never runs) and a LATER mount of the same stable fetcher
    silently rejoins the dead promise instead of issuing a fresh request. Harmless no-op when the
    request already settled (self-deleted) or when a still-mounted sibling shares the same promise
    instance — eviction only clears the map slot for future `dedupedFetch` calls, never an
    in-flight promise object already handed out), `overallStatus.ts` (worst-of derivation: down >
    partial > degraded > maintenance > unknown > up; empty → unknown), `healthIcons.ts`,
    `format.ts`, `relativeTime.ts`, `cx.ts`, `combineFetchStates.ts`.
  - `mocks/` — MSW is the ONLY mocked I/O edge; per-endpoint handlers
    (`handlers/{components,approvals,history,availability,maintenance,topology,publications}.ts`)
    composed in `handlers/index.ts`, wired in `test/setup.ts` — which ALSO resets
    `fetchDedup.ts`'s process-wide cache in its shared `afterEach` (STORY-137), alongside
    `server.resetHandlers()`: a test that deliberately renders against a never-resolving handler
    (to assert a loading state) would otherwise leave an orphaned in-flight entry that starves
    every LATER test sharing that same fetcher reference. Fixtures derive from REAL captured
    `/api/v1` responses (`docs/scrum/sprints/2026-07-21-sprint-59/live-api-samples.md` +
    `docs/scrum/sprints/2026-07-21-sprint-60/plan.md` §Appendix). `handlers/maintenance.ts`
    (STORY-132) now also has a populated upcoming/active/past list fixture (year 2000/2099
    instants, so the derived badge state is stable regardless of when the suite runs) plus
    `POST /api/v1/maintenance` (201) and `DELETE /api/v1/maintenance/:windowId` (204) handlers,
    alongside the pre-existing empty-list `GET` default. `handlers/publications.ts` (STORY-133)
    default-exports the real captured empty list (`FIXTURE_PUBLICATIONS = []`) plus a populated
    two-entry `FIXTURE_PUBLICATIONS_TIMELINE` (the plan appendix sample + a second entry exercising
    the `proposal_id: null`/`author: null`/`outcome: 'failed'` edges), swapped in per-test via
    `server.use(...)`.

- **API client (`api/client.ts`):** `getComponents()`, `getApprovals()`, `getHistory(signalKey,
  limit?)`, `getAvailability(signalKey)`, `getMaintenance()`, `getTopology()` (STORY-129),
  `getComponentAvailability(componentId, {since, until})` (STORY-129, component-grain rollup +
  nested signal children), `getHistoryWindow({signal_key, since, until, limit?})` (STORY-130 — the
  windowed variant `getHistory` lacks; `getHistory` itself is UNCHANGED, the Dashboard still uses
  its unwindowed shape), `postDecision(proposalId, DecisionRequest)` (STORY-131 — the sprint's
  FIRST write path: `POST /api/v1/decisions/{proposal_id}`, note the path is `/decisions/`, NOT
  nested under `/approvals`), `postMaintenance(CreateMaintenanceRequest)` (STORY-132 — `POST
  /api/v1/maintenance`, **201**) and `deleteMaintenance(windowId)` (STORY-132 — `DELETE
  /api/v1/maintenance/{window_id}`, **204**, NOT idempotent — a 404 on an already-deleted window is
  a real `ApiError.status === 404`, never a silent success), and `getPublications()` (STORY-133 —
  `GET /api/v1/publications`, the timeline read most-recent-first as returned and rendered without
  re-sorting, capped ~50 server-side, no pagination). The write path is a private
  `postJson<T>` alongside the existing `getJson`, sharing the same `readOkJson`/`ApiError` handling
  so `.status`/`.detail` populate identically for a non-2xx POST (a 409/404 the same way a GET
  caller would see them); STORY-132 adds a THIRD private helper, `deleteRequest(path):
  Promise<void>`, distinct from both because a 204 response has NO body — it never calls
  `response.json()` on the ok path (that throws on an empty body), while still extracting
  `ApiError`'s `.status`/`.detail` on a non-2xx response via the same `readDetail`. DTOs in
  `api/types.ts`: `ComponentDTO {id,name,status}`, `ProposalDTO`, `ObservationDTO {signal_key,
  observed_at, health, location, latency_ms, response_status_code, check_type}`, `AvailabilityDTO`
  (`availability_pct`/`completeness_pct` are 0–1 fractions, nullable), `MaintenanceWindowDTO`
  (`title: string | null` — TIGHTENED from `title?: string | null` in STORY-132, since the field is
  always present on the wire, just nullable), `CreateMaintenanceRequest {component_id, starts_at,
  ends_at, reason?, title?}` (STORY-132 — the `POST` body), `ComponentTopologyDTO`/
  `TopologySignalDTO` (STORY-129 — `interval_seconds` is `int | null`),
  `ComponentAvailabilityDTO`/`SignalAvailabilityDTO` (STORY-129 — the latter is `AvailabilityDTO` +
  `signal_key`, no display name), `DecisionRequest {action: "approve"|"reject", actor, notes?}` /
  `DecisionResponse {proposal_id, state, resolved_at}` (STORY-131), and `PublicationDTO {id,
  component_id, status, published_at, proposal_id: number|null, outcome: "succeeded"|"failed",
  author: string|null}` (STORY-133 — NO `incident_id`; `status` uses the SAME vendor vocabulary as
  `ComponentDTO.status`, mapped via `statusMapping.ts`; `outcome` is a SEPARATE concept, never
  conflated with `status`). Re-derived fresh from the LIVE
  contracts (verified at the STORY-121/122/129/131/132 reality gates); extends cleanly as later
  tabs need more endpoints. `statusMapping.ts` maps the vendor `ComponentStatus` vocabulary
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
- The shared `Button` primitive does not forward refs (a plain function component, not
  `forwardRef`) — `ProposalCard`'s Confirm button and `MaintenanceWindowCard`'s Delete/Confirm
  buttons (STORY-132) both had to fall back to a hand-rolled native
  `<button className="button button--primary">`/`<button type="submit" className="button
  button--primary">` to get an imperative focus target or a genuine submit button (`Button`
  hardcodes `type="button"`, so it can't be a form's submit control either —
  `ScheduleMaintenanceForm` hits this too). Three independent call sites have now hit this same
  wall; that's the trigger to add `forwardRef` (and a `type` passthrough) to `Button` once, rather
  than a fourth one-off native-button workaround.
- `Button.css`'s `--button-height` is 36px — under the 44×44px (iOS)/48×48dp (Material) minimum
  touch-target guideline (ui-ux-pro-max checklist item 2, STORY-131 review). Pre-existing
  (STORY-120), app-wide, not something a single-page story should change unilaterally.
- No sample-mode UI in the new frontend — the old consumer was removed in the rebuild; see
  [[sample-mode]] (backend feature still exists; a new consumer is unscheduled).
- STORY-125 (mobile-sheet focus-trap + `role="dialog"`), STORY-126 (skip-to-content link),
  STORY-127 (`/api/v1/availability` is slow against DynamoDB-Local → dashboard first-paint stall;
  STORY-129's `ComponentAvailabilityCard` independent-fetch pattern is the mitigation the
  Availability page itself needed, but the Dashboard's own STORY-122 KPI fetch is untouched by
  this story), STORY-128 (lazy-load the availability-dependent KPI — the OTHER half of
  STORY-128's original scope, "dedupe the components/approvals fetch", is now DONE via STORY-137's
  `fetchDedup.ts`, sprint-61).

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
- 2026-07-22 (STORY-132, sprint-60): the Maintenance page shipped — schedule + delete, the
  sprint's SECOND mutating page and its most complex mutation (form + order-sensitive 422 field
  mapping + UTC datetime conversion + a NOT-idempotent delete). Tightened
  `MaintenanceWindowDTO.title` to `title: string | null` (was optional) and added
  `CreateMaintenanceRequest`; added a THIRD private client helper, `deleteRequest` (204-body-safe,
  alongside `getJson`/`postJson`), plus `postMaintenance`/`deleteMaintenance`. New
  `features/maintenance/**` module (see the `features/` bullet above for the full breakdown) —
  every derivation/mapping/conversion pure and unit-tested BEFORE the components that use it
  (`deriveWindowState`, `mapMaintenanceError`, `localDateTimeToUtcIso`, `formatWindowRange`).
  `MaintenancePage`'s `PlaceholderPage` stub is gone (Publications is now the only remaining one).
  This sweep also re-verified the `bfcca9b` STORY-131 fixup (dropped an unused `cx` import/no-op
  call in `ProposalCard.tsx`'s reject-button `className`) that landed after STORY-131's own
  verified_sha — confirmed cosmetic only, no Fact above it was affected. verified_sha = 5129bc2.
- 2026-07-22 (STORY-133, sprint-60): the Publications page shipped — the sprint's LAST page and its
  simplest (read-only, no mutation). Added `getPublications()` and `PublicationDTO` to the API
  client (`GET /api/v1/publications`), a new `mocks/handlers/publications.ts`, and the
  `features/publications/**` module (`OutcomeChip`, `PublicationsTimeline` — see the `features/`
  bullet above). **Deleted the `PlaceholderPage` component** (`components/PlaceholderPage/`) —
  `PublicationsPage` was its last mount; a repo grep after the delete confirmed zero remaining
  references. **All six nav routes are now real pages — the placeholder era is over.** No dedicated
  wiki article existed for `PlaceholderPage` itself (it was only ever documented as a Fact inside
  this article), so there is nothing to archive/tombstone separately — this entry IS that record.
  verified_sha = 2e97408.
- 2026-07-22 (STORY-129/130/133 review refinement, sprint-60): design review found numeric grid
  columns left-aligned; right-aligned them (header + cells together, via a shared `.is-numeric`
  modifier class scoped per table for CSS specificity) in `HistoryGrid.tsx` (Status code, Latency),
  `ComponentAvailabilityCard.tsx` (Availability, Completeness, Total, Passing, Maintenance, Down,
  Gap, Locations — Component stays left), and `PublicationsTimeline.tsx` (Proposal only). No
  layout/spacing/Fact change otherwise — cosmetic, mechanical sweep confirmed no other article
  references alignment. verified_sha = e488202.
- 2026-07-22 (STORY-136, sprint-61): three design-QA-review correctness defects fixed on the
  Dashboard/shell, no new page/route. (1) `deriveRecentChecks.ts`'s row key changed from the
  colliding `` `${signalKey}-${observed_at}-${location}` `` triple to the final sorted+capped
  position (matching the STORY-130 `mergeHistoryRows.ts` fix — the same live-wire duplicate-triple
  collision class). (2) `Topbar`'s `overallStatus` prop is now `HealthStatus | null`; `ShellLayout`
  passes `null` until `getComponents` SUCCEEDS (loading or error), and `Topbar` renders
  `LoadingState`'s new `compact` variant instead of the `unknown` `StatusBadge` for that case — the
  `unknown` badge is now reserved for a genuinely-unknown SUCCEEDED fetch. (3) `useFetch` gained a
  `DEFAULT_FETCH_TIMEOUT_MS` (15s, overridable) request timeout so a never-settling fetch reaches
  the `error` phase (existing `ErrorState` + retry) instead of spinning forever; the timer is
  cleared on settle/unmount/retry so it never fires against an already-settled request. No Fact
  above was wrong, all three purely additive/corrective. verified_sha = 0a0e421.
- 2026-07-22 (STORY-138, sprint-61): Dashboard layout coherence — the headline design-QA visual
  bug. `DashboardPage.css`'s two separate per-row grids (`mid-grid` 1.85fr/1fr, `bottom-grid`
  1.1fr/1fr — a ~145px gutter jump between rows) are replaced by ONE named-line
  `.dashboard-page__content-grid` (`[main-start] minmax(0,2fr) [main-end side-start] minmax(0,1fr)
  [side-end]`) shared by everything below the KPI row; `DashboardPage.tsx` restructured its JSX
  into two flex-column stacks against those named lines: `.dashboard-page__col--main` (the
  response-time chart panel + `RecentChecksFeed`) and `.dashboard-page__col--side` (`ProbeLocationsPanel`
  + `MaintenancePanel` + `ComponentsRoster`, moved here from the old bottom-grid — a deliberate
  content rebalance so the side column's total height tracks the main column's more closely than
  the previous 1-panel-vs-1-panel per-row pairing, per AC2's "not a stretch hack that leaves
  whitespace"; both columns use `align-items: start`, never force-stretched). Same 1080px collapse
  breakpoint carries over for the mobile-collapse AC. Separately, the KPI-card accent/footprint
  inconsistency (Facts above, `deriveKpiTone.ts`/`KpiMeter.tsx`) was fixed in the same story. AC1
  (single gutter) and AC2 (no bottom-right void) and AC5 (mobile collapse) are REALITY-GATE-VERIFIED
  ONLY — jsdom cannot compute real layout/geometry, so this story's own tests assert structure
  (both stacks live inside the one shared grid container) and CSS source text (one
  `grid-template-columns` declaration, the old class names gone) as necessary-but-not-sufficient
  proof, per the tests-that-lie #7 discipline. verified_sha = d9d0bf9.
- 2026-07-22 (STORY-137, sprint-61): shared fetch dedup/cache — fixes the "shell + Dashboard page
  each fetch `/components`/`/approvals` independently" finding. New `lib/fetchDedup.ts`
  (`dedupedFetch`/`forgetFetch`/`resetFetchDedupCache`, an in-house identity-keyed promise-
  coalescing cache, explicitly NOT a result cache — no new dependency, no React Query/SWR).
  `useFetch.ts` now issues its fetch via `dedupedFetch`, and calls `forgetFetch` from its
  STORY-136 timeout handler so a never-settling request's `retry` still genuinely re-issues a
  fresh call. `test/setup.ts` resets the cache in the shared `afterEach` — discovered via TDD: the
  process-wide cache initially broke 30 tests across 6 files, because a test rendering against a
  deliberately never-resolving handler (to assert a loading state) left an orphaned in-flight
  entry that silently starved every later test in the file sharing that fetcher reference (e.g.
  `ApprovalsPage.test.tsx`). Proven: an MSW call-count test (`ShellLayout.test.tsx`) asserts each
  of `/components`/`/approvals`/`/maintenance` fires exactly once across the shell + Dashboard
  page on one mount; a companion test (verified to fail with the dedup wiring reverted) confirms
  it; a second safeguard test (`AvailabilityPage.test.tsx`) asserts two DIFFERENT components'
  `getComponentAvailability` fetches are never wrongly coalesced. No page/route/DTO change; no
  behavioral regression (full suite green, 690 tests). Folds the "dedupe the components/approvals
  fetch" half of the STORY-128 known-gap above. verified_sha = 4ed312b.
- 2026-07-22 (STORY-137 quality-review MAJOR fix, sprint-61): the unmount cleanup only cleared
  `cancelled`/`timeoutId`, never calling `forgetFetch` — so a component that unmounted BEFORE a
  never-settling request's 15s timeout fired left the `dedupedFetch` in-flight entry orphaned in
  the map forever (the promise's own `.finally` never runs, since the underlying fetch never
  settles and the STORY-136 timeout never aborts it). A later mount of the same stable fetcher
  silently rejoined the dead promise instead of issuing a fresh request, requiring a manual retry
  even once the backend recovered. Fix: `useFetch.ts::useFetch`'s effect cleanup now ALSO calls
  `forgetFetch(fetcher)`, the same call the timeout handler already made — harmless no-op when the
  request already settled or a sibling still shares the same in-flight promise instance (eviction
  only clears the map slot for future `dedupedFetch` calls, never the promise object already handed
  out). Regression test in `useFetch.test.tsx` reproduces the exact production interleaving (mount
  against a never-settling fetcher, unmount before timeout, remount the same fetcher, assert a
  genuinely fresh invocation) — verified to fail pre-fix. No Fact above was wrong beyond the one
  updated in the `lib/` bullet; AC1 dedup-count test and STORY-136 timeout tests remain green; full
  suite green, 693 tests. verified_sha = ef53653.
- 2026-07-22 (STORY-140, sprint-61): empty-state and data-formatting polish, three findings from
  the design-QA review. (1) `EmptyState.tsx` gained a `compact` modifier and `SummaryCard.tsx`
  gained an `empty?: { message; detail? }` prop; `KpiRow`'s availability/response-time cards now
  render "No data yet" instead of a bare "— %"/"— ms" plus a misleading "Across 0 probe locations"
  sub line when their value is genuinely `null`. (2) `formatTimestamp.ts::formatObservedAt` now
  appends `" UTC"`, matching `formatWindowRange`'s existing convention — History-row timestamps are
  no longer the one unlabelled absolute time on these surfaces. (3) `locationLabel.ts` now renders
  a `#`-prefixed short id (`#0047`) instead of the ellipsis tail (`…0047`) across every consumer
  (`HistoryGrid`, `HistoryFilterBar`, `RecentChecksFeed`, `ProbeLocationsPanel`,
  `ResponseTimeChart`'s spike legend) — still an id, never an invented name; true human-readable
  names are blocked on a backend `location_name` field, filed as STORY-144 (out of this zone's
  scope). Facts above updated (KpiRow/EmptyState/SummaryCard bullet, formatObservedAt bullet);
  `locationLabel.ts` added to this article's `code_refs`. Full suite green, 729 tests.
- 2026-07-22 (STORY-141, sprint-61): shell interaction polish, three findings from the design-QA
  review. (1) The notifications bell (`Topbar.tsx:71`, confirmed live dead — no `onClick`/panel) is
  now `shell/Topbar/NotificationsButton.tsx`, a fresh disclosure popover with an `EmptyState` ("No
  notifications" — no data source in scope, deliberately not fabricated) as its only content;
  `aria-haspopup`/`aria-expanded`/`aria-controls` wire trigger to panel, opening moves focus into
  the `role="dialog"` panel, Escape/outside-click close it and return focus to the trigger. (2) The
  mobile off-canvas sheet (`Sidebar.tsx`) gained a `.shell-sidebar__mobile-header` (brand text +
  explicit `X` close button, `aria-label="Close menu"`) ahead of the existing collapse toggle,
  CSS-hidden at desktop like the existing toggle — the drawer's existing backdrop/Escape dismissal
  is unchanged. (3) `StyleguidePage.tsx`'s Loading/Error/Empty gallery row gained a
  `styleguide-row--start` modifier (`align-items: flex-start`, overriding `--stack`'s `stretch`) so
  those three primitives — which each center their OWN content internally — no longer stretch to
  the full row width and read as page-centered; the Panel section's `--stack` row is untouched. Note:
  the visual left-alignment claim itself is confirmed at the live reality gate, not by jsdom (no
  real layout engine) — the co-located test only asserts the structural class, necessary but not
  sufficient. `NotificationsButton.tsx` added to this article's `code_refs`. Full suite green, 744
  tests. verified_sha = 5781630.
  verified_sha = b5bc195.
