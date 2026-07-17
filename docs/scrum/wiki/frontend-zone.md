---
title: Frontend zone — the operator-cockpit SPA (shell)
code_refs: [frontend/package.json, frontend/vite.config.ts, frontend/index.html, frontend/src/AppShell.tsx, frontend/src/nav/tabs.ts, frontend/src/nav/Sidebar.tsx, frontend/src/nav/TopBar.tsx, frontend/src/nav/SampleModeBanner.tsx, frontend/src/nav/sidebarState.ts, frontend/src/nav/SidebarDrawer.tsx, frontend/src/nav/useResponsiveSidebar.ts, frontend/src/lib/breakpoints.ts, frontend/src/lib/useMediaQuery.ts, frontend/src/test/matchMedia.ts, frontend/src/features/shell/useApprovalsBadge.ts, frontend/src/api/client.ts, frontend/src/api/types.ts, frontend/src/api/statusMapping.ts, frontend/src/api/actor.ts, frontend/src/theme/resolveTheme.ts, frontend/src/theme/ThemeContext.tsx, frontend/src/styles/tokens.css, frontend/src/components/index.ts, frontend/src/components/Table/Table.tsx, frontend/src/components/UptimeBar/UptimeBar.tsx, frontend/src/components/SummaryCard/SummaryCard.tsx, frontend/src/components/Timeline/Timeline.tsx, frontend/src/components/Icon/Icon.tsx, frontend/src/components/PageHeader/PageHeader.tsx, frontend/src/components/EmptyState/EmptyState.tsx, frontend/src/lib/cx.ts, frontend/src/lib/useFetch.ts, frontend/src/mocks/handlers/index.ts, frontend/src/mocks/handlers/components.ts, frontend/src/mocks/handlers/approvals.ts, frontend/src/mocks/handlers/availability.ts, frontend/src/mocks/handlers/sampleMode.ts, frontend/src/mocks/handlers/history.ts, frontend/src/mocks/handlers/publications.ts, frontend/src/mocks/handlers/maintenance.ts, frontend/src/features/dashboard/useComponents.ts, frontend/src/features/dashboard/useMaintenanceWindows.ts, frontend/src/features/dashboard/useSampleMode.ts, frontend/src/features/dashboard/summary.ts, frontend/src/features/dashboard/useTopology.ts, frontend/src/features/dashboard/useComponentSignals.ts, frontend/src/features/dashboard/useComponentUptime.ts, frontend/src/features/approvals/useApprovals.ts, frontend/src/features/approvals/severity.ts, frontend/src/features/approvals/decisionState.ts, frontend/src/features/approvals/ApprovalCard.tsx, frontend/src/features/approvals/useApprovalsTopology.ts, frontend/src/features/approvals/useProposalEvidence.ts, frontend/src/components/StatusBadge/StatusBadge.tsx, frontend/src/features/availability/windowRange.ts, frontend/src/features/availability/useAvailability.ts, frontend/src/features/availability/format.ts, frontend/src/features/availability/segments.ts, frontend/src/features/history/observationHealth.ts, frontend/src/features/history/signals.ts, frontend/src/features/history/filterHistory.ts, frontend/src/features/history/mergeObservations.ts, frontend/src/features/history/useAllHistory.ts, frontend/src/features/publications/usePublications.ts, frontend/src/features/maintenance/windowState.ts, frontend/src/features/maintenance/fieldError.ts, frontend/src/features/maintenance/useMaintenance.ts, frontend/src/pages/DashboardPage.tsx, frontend/src/pages/ApprovalsPage.tsx, frontend/src/pages/AvailabilityPage.tsx, frontend/src/pages/CheckHistoryPage.tsx, frontend/src/pages/PublicationsPage.tsx, frontend/src/pages/MaintenancePage.tsx, frontend/src/test/setup.ts, DESIGN-linear.app.md, frontend/eslint.config.js, frontend/src/styles/global.css, frontend/src/lib/formatTime.ts, frontend/src/lib/formatLocation.ts, frontend/src/components/RelativeTime/RelativeTime.tsx, frontend/src/features/dashboard/actionCard.ts, frontend/src/features/dashboard/maintenanceSummary.ts, frontend/src/nav/useDismissibleBanner.ts, frontend/src/components/Toast/Toast.tsx]
verified_sha: beca48f
verified_sprint: sprint-54
status: verified
---

## Facts (verified against code)
- `frontend/` is a standalone Vite + React + TypeScript (strict) SPA — the operator-cockpit
  "internal dashboard" surface (dossier §17, the two-surface model; the other surface is the
  public Statuspage). It is ISOLATED from the Python backend: no import of backend source, no
  shared build step. The six backend DoD commands never touch it; its three frontend DoD
  commands (`npm test` / `npm run build` / `npm run lint`, from `frontend/`) never touch the
  backend. Design direction: `DESIGN-linear.app.md` (repo root) as a GUIDE, not a copy target
  (see the sprint-25 plan for the binding design brief). Established STORY-015a, sprint-25.
- **This is the SECOND frontend attempt.** The first (sprints 23–24, built to a since-removed
  `DESIGN-airtable.md`) was fully reverted in commit `521764c`; its code lives only on the
  `sprint-23`/`sprint-24` branches. Nothing here descends from it.
- **Toolchain** (`frontend/package.json`): Vite + React + TS strict; Vitest + React Testing
  Library + jsdom + MSW (Mock Service Worker) for tests; ESLint flat config
  (`frontend/eslint.config.js`); npm on Node 24. Scripts: `dev`, `build` (`tsc -b && vite build`
  — type-check is part of the build gate), `test` (`vitest run`, run-once), `lint` (`eslint .`).
  Playwright/E2E is DEFERRED to a later integration story.
- **Dev ↔ API seam:** the Vite dev server proxies `/api/*` → `http://localhost:8000`
  (`frontend/vite.config.ts`), a locally running uvicorn backend. No backend change and no CORS
  work was needed — CORS stays deferred to STORY-017 per the 2026-06-23 working agreement.
- **App shell + routing (rebuilt STORY-056, sprint-38):** `frontend/src/AppShell.tsx` composes a
  collapsible left icon `Sidebar` + a content column (`TopBar` + `SampleModeBanner` + a routed
  `<main>`), replacing the old single top `Nav` bar (`Nav.tsx`/`Nav.css`/`Nav.test.tsx` deleted).
  The six tabs remain a single source of truth in `frontend/src/nav/tabs.ts` (Dashboard ·
  Availability · Approvals · Check History · Maintenance · Publications) — each entry now also
  carries an `icon: IconName` (STORY-055's shared `Icon` set) alongside `path`/`label`, consumed by
  `frontend/src/nav/Sidebar.tsx`. `Sidebar` renders each tab as a routed `NavLink` (native anchor
  semantics, still deliberately NOT an ARIA tablist) — active = accent background + bold weight,
  inactive = ink-muted. Every link's accessible name is set explicitly via `aria-label` (not left
  to visible text) so it holds steady whether the sidebar is expanded (icon + visible label +
  optional badge) or collapsed (icon-only, label/badge visually hidden but the name unchanged) —
  a screen-reader user always hears e.g. "Approvals, 3 pending" regardless of the visual state. The
  collapse/expand choice is a header button (logo + title + chevron when expanded) with
  `aria-expanded` + a dynamic `aria-label` ("Collapse sidebar"/"Expand sidebar"), persisted to
  `localStorage` by `frontend/src/nav/sidebarState.ts` (mirrors `theme/resolveTheme.ts`'s
  stored-override pattern; defaults to expanded). The Approvals tab shows a live pending-count
  badge — `frontend/src/features/shell/useApprovalsBadge.ts` (`useFetch(getApprovals)`, count on
  success, `undefined` while loading or on failure) — rendered as a number when expanded, a
  decorative dot when collapsed, and folded into the link's `aria-label` either way; no badge
  renders on a fetch failure (graceful degradation, never a stale/fabricated count).
  `frontend/src/nav/TopBar.tsx` is the right-aligned header bar (theme toggle + the sample-mode ⚡
  trigger, see below); `frontend/src/nav/SampleModeBanner.tsx` is the dismissible warning region
  under it. A trailing catch-all `<Route path="*">` renders `pages/NotFoundPage.tsx` (Panel +
  EmptyState + a link back to Dashboard) for unknown paths (STORY-041), unchanged by the shell
  rebuild. **All six tabs are now real — Dashboard, Availability, Approvals, Check History,
  Maintenance, and Publications** (STORY-015b, 015c, 015d, 015e, 015f, 015g); there is no
  remaining placeholder page.
- **Theme system (dark + light):** `frontend/src/theme/resolveTheme.ts` resolves the active
  theme (localStorage override → else `prefers-color-scheme`). An inline pre-paint script in
  `frontend/index.html` applies it before first paint (no flash), mirroring `resolveTheme.ts`.
  `ThemeContext.tsx` + `useTheme.ts` expose it to React and back the toggle button in `TopBar`
  (override persisted to localStorage; moved there from the old `Nav` at STORY-056 — same
  `useTheme()` call, same persistence, only the button's location and icon changed: it now shows
  the CURRENT theme, sun/moon, rather than the old glyph's target-theme convention). Both surfaces
  read the SAME resolution logic.
- **Token layer:** `frontend/src/styles/tokens.css` holds ALL visual values as CSS custom
  properties scoped per theme (`:root[data-theme='dark']` / `[data-theme='light']`) — surfaces,
  hairlines, a 4-step ink scale, the accent set (+ `--color-accent-bg`), a 7-status health palette
  (up/degraded/partial/down/maintenance/unknown/missing, each with a `-subtle` badge-background
  variant), a `--shadow` token (none in dark, a subtle two-layer shadow in light), radii, spacing,
  type. **Components consume tokens only — no raw hex outside `styles/`** (enforced by review;
  grep-verified clean at STORY-015a). Fonts are self-hosted Geist + Geist Mono via `@fontsource`
  (imported in `frontend/src/styles/global.css`, loaded by `main.tsx`; bundled, no runtime
  font-CDN `<link>`) — retuned from Inter/JetBrains Mono at STORY-055 (sprint-38), which also
  retuned the palette/type-scale VALUES to the imported *Operator Dashboard* mock while keeping
  every existing token NAME (see the Sprint-38 history entry below).
- **Shell primitives** (`frontend/src/components/`, barrel `components/index.ts`): `Button`
  (primary/secondary/tertiary), `StatusBadge` (pill; `aria-hidden` status dot + ink text label —
  status is NEVER color-alone; 7-value `HealthStatus` union as of STORY-055), `Panel` (surface-1 +
  hairline + 8px radius + `--shadow`, `headingLevel` prop defaulting to `h2`), `LoadingState`,
  `ErrorState` (retry callback; warning glyph now the shared `Icon` set), `EmptyState`
  (`EmptyState.tsx` — STORY-097 gave it an optional `icon`/`tone` pair, purely additive to the
  pre-existing `message`/`detail` shape: an icon renders a 44px decorative circle above the
  centered message, `tone="neutral"` (default, a plain surface tint) or `tone="positive"` (the
  health-up subtle pair, for a "nothing to do" good-news state) — see the "Page scaffold" entry
  below for its adopters), `PageHeader` (`PageHeader.tsx` — STORY-097, see below), `Icon`
  (STORY-055 — 18 inline feather-style SVGs, decorative/`aria-hidden` by default, opt-in
  `role="img"`+`<title>` for a standalone meaningful icon), `Table`/`TableHead`/`TableBody`/
  `TableRow`/`TableHeaderCell`/`TableCell` (STORY-055 — extracts the th/td/hairline/uppercase-
  caption styling previously copy-pasted per page; `TableHeaderCell` defaults `scope="col"`),
  `UptimeBar` (STORY-055 — N-segment sparkline colored by `HealthStatus`, per-segment `title`
  tooltip, hatched "missing" fill, explicit "No data" state for zero segments), `SummaryCard`
  (STORY-055 — dot + uppercase label + big mono value + sub, tone variants mapped to the health
  tokens), `Timeline`/`TimelineItem` (STORY-055 — semantic `<ul>`/`<li>` vertical line + dot list).
  These ship with the shell so per-tab stories don't copy-paste. Classnames are composed with the
  shared `cx(...)` helper (`frontend/src/lib/cx.ts`, STORY-041) — filters falsy, joins on a space.
- **Typed API client:** `frontend/src/api/client.ts` — fetch-based, single `/api` base-URL seam.
  Both `getJson` (GET) and `postJson` (POST — JSON body, `Content-Type: application/json`) funnel
  their response through a shared `readOkJson(response, path)` that gives ONE uniform error
  contract (STORY-015c): EVERY failure is a typed `ApiError` — network rejection (no status),
  non-2xx (`.status` carried), and a malformed-body `SyntaxError` on a 2xx (with status). The
  readable `.status` is what lets a mutating tab branch on 404/409. `ApiError` also carries an
  optional `.detail` (STORY-015f AC3) — a best-effort, `.clone()`-based parse of a non-2xx body's
  `{"detail": "..."}` string (FastAPI's shape for a manually-raised `HTTPException`, e.g.
  `maintenance/service.py`'s 422s); `undefined` for network failures, malformed bodies, or a body
  without a string `detail`. This is what lets the Maintenance tab map a 422's message onto the
  specific field it names (`features/maintenance/fieldError.ts::fieldErrorFromDetail`) without
  every caller re-parsing the response body itself — purely additive to the existing `ApiError`
  shape, so no prior `.status`-only assertion broke. A third helper, `putJson`
  (STORY-049), mirrors `postJson` for PUT bodies, funneling through the same `readOkJson`. Endpoint
  fns: `getComponents`, `getApprovals`, `postDecision(proposalId, body)`, `getTopology`,
  `getComponentAvailability(componentId, { since, until })` (STORY-015d — query-string encodes
  `since`/`until`, both REQUIRED to be tz-aware ISO strings since the backend 422s a naive
  datetime), `getSampleMode()` / `putSampleMode(enabled)` (STORY-049 — a TEMPORARY-feature seam,
  see `docs/scrum/wiki/sample-mode.md`), `getHistory({ signal_key, since, until, limit? })`
  (STORY-015e AC1, AC2 — query-string encodes `signal_key`/`since`/`until`; `since`/`until`
  REQUIRED tz-aware ISO strings, the same discipline as `getComponentAvailability`; NO
  client-driven pagination for the Check History tab, which still omits `limit` and caps what it
  RENDERS instead. STORY-094 added the server-side optional `limit` cap; STORY-100 is the FIRST
  caller to actually send it — `optional limit?: number`, additive, omitted entirely from the
  query string when `undefined` so every pre-STORY-100 call site (Check History, Dashboard,
  Availability) is unaffected — used by `features/approvals/useProposalEvidence.ts` to fetch a
  small, server-capped slice per proposal rather than the render-side-capped full window), `getPublications()`
  (STORY-037/STORY-015g AC1 — `GET /api/v1/publications`, no
  params; the endpoint itself caps at the repository's most-recent 50 server-side, so unlike
  `/history` there is no client-side render cap to add), and `getMaintenance()`/`postMaintenance(body)`
  (STORY-036/STORY-015f AC1, AC2 — `GET`/`POST /api/v1/maintenance`; `postMaintenance` funnels
  through `postJson`, not `putJson`, so the sample-mode REMOVAL recipe's "no other endpoint has
  adopted `putJson`" caveat still holds). DTO types in `frontend/src/api/types.ts`
  (`ComponentDTO`,
  `ProposalDTO`, `DecisionRequest`, `DecisionResponse`, `TopologySignalDTO`, `ComponentTopologyDTO`,
  `AvailabilityDTO`, `SignalAvailabilityDTO`, `ComponentAvailabilityDTO`, `SampleModeDTO`,
  `ObservationDTO`, `PublicationDTO`, `MaintenanceWindowDTO`, `CreateMaintenanceRequest`) mirror
  the backend `api/v1/*/models.py` shapes — `ObservationDTO` gained `response_status_code:
  number | null` and `check_type: string` (STORY-064; Facts updated below in the Check History
  bullet) — note `SignalAvailabilityDTO` (a per-signal availability
  result) carries `signal_key` but NOT a display `name`; the name lives only on the topology
  response's nested `TopologySignalDTO`, so a two-grain consumer must join the two responses by
  `signal_key` to label a child row (STORY-015d AC1; see `AvailabilityPage.tsx`).
  `frontend/src/api/statusMapping.ts::toHealthStatus` is the
  authoritative map from the backend `ComponentStatus` vocabulary (operational / degraded /
  partial_outage / major_outage) onto the health tokens (operational→up, degraded→degraded,
  partial_outage→partial, major_outage→down, else→unknown). **STORY-055 (sprint-38):**
  `partial_outage` now maps to its own `'partial'` token (previously folded into `'degraded'`)
  now that the palette has a dedicated partial-outage color; the `DashboardPage` test covering the
  all-statuses fixture was rewritten to assert "Partial outage" instead of "Degraded" for that
  case. **There is now a SECOND, deliberately
  separate health mapper:** `frontend/src/features/history/observationHealth.ts::observationHealth`
  maps the OBSERVATION vocabulary (`ObservationDTO.health`: `"up" | "down" | "degraded"`, else→
  unknown) onto the SAME health tokens `StatusBadge` consumes (STORY-015e AC3). The two mappers'
  input vocabularies overlap only on the string `"degraded"` — `ComponentStatus` has no `"up"`
  value, so `toHealthStatus` would wrongly fold an observation's `"up"` into `unknown`; keeping
  them separate means a future contract change to either vocabulary never ripples into the other
  tab. `PublicationDTO.status` (STORY-015g) IS the `ComponentStatus` vocabulary (same producing
  type as `ComponentDTO.status`), so the Publications tab reuses the EXISTING `toHealthStatus`
  directly — no third mapper.
- **Actor seam (auth deferred):** `frontend/src/api/actor.ts::getActor()` returns a FIXED
  placeholder (`"dashboard-operator"`) — the SINGLE swap-point for real identity when STORY-017
  auth + scopes land. Every decision POST reads the actor from here; the value is not scattered.
  (STORY-015c; PO decision 2026-07-02.)
- **Test I/O boundary:** MSW is the ONLY mocked edge. Handlers are modularized per feature
  (`frontend/src/mocks/handlers/<feature>.ts`, e.g. `components.ts` / `availability.ts` exporting
  their handlers + fixtures) composed into the `handlers` array in
  `frontend/src/mocks/handlers/index.ts`, which `mocks/server.ts` registers (wired in
  `frontend/src/test/setup.ts`). A tab story adds its own `handlers/<feature>.ts` and spreads it
  in — touching no other feature's handlers (STORY-041 refactor). Tests assert via accessible
  roles/text and drive real behavior (success + empty + error→retry against MSW; for a mutating
  tab, the actual POST/PUT body MSW received; for STORY-015d, the actual `since`/`until` query
  params a selector change sent); no component/hook under assertion is mocked. 355 tests across 50
  files at HEAD of sprint-38 (`npm test`, all green).
- **Shared fetch machinery:** `frontend/src/lib/useFetch.ts::useFetch<T>(fetcher)` is the single
  home of the read-fetch state machine (STORY-015c, extracted from 015b's `useComponents` — the
  parallel-shape agreement): returns `{ state, retry }` over a discriminated-union `FetchState<T>`
  (loading|error|success), a cancelled-guarded effect (no set-state after stale/unmount), and an
  `attempt`-keyed `retry`. **Sharp edge:** `fetcher` MUST be a STABLE reference (module-scoped fn),
  never an inline closure, or the effect refetches every render — documented in the JSDoc and
  honored at both call sites. `features/dashboard/useComponents.ts` = `useFetch(getComponents)` and
  `features/approvals/useApprovals.ts` = `useFetch(getApprovals)` are thin wrappers with zero
  duplicated effect body.
  **Parameterized fetch — the STORY-015d pattern:** `useFetch`'s effect already lists `fetcher` as
  a dependency, so a hook whose fetch depends on caller-supplied args (e.g. a selectable window)
  does NOT need `useFetch` itself changed — wrap the parameterized call in `useCallback` keyed on
  the arg object (`features/availability/useAvailability.ts::useAvailability(range)` =
  `useCallback(() => fetchAvailabilityBundle(range), [range])`), and have the CALLER memoize that
  arg object (`useMemo` keyed on the selector's own state, e.g. `AvailabilityPage`'s
  `useMemo(() => windowToRange(preset), [preset])`) so the fetcher's identity is stable while the
  selection is unchanged and changes — triggering exactly one refetch — only when the selection
  does. No `useFetch` contract change, no rewritten `useFetch` tests; this is the sanctioned
  extension for 015e–015g if a future tab needs the same shape.
- **The per-tab pattern (Wave 0/1 established it; Wave 2, sprint-38, rebuilt every page onto the
  Operator Dashboard mock while keeping the shape):** a page in `pages/<Tab>Page.tsx` + one or more
  `features/<tab>/use<Thing>.ts` hooks built on the shared `useFetch<T>`, rendering a four-state
  view (loading / error+retry / empty / success) from the shared primitives. The six tabs at HEAD:
  - **Dashboard (STORY-057 rebuild of 015b/046):** `useComponents()` is still the PRIMARY, blocking
    fetch (only its failure blocks the page) gating a `SummaryCard` row —
    `features/dashboard/summary.ts::summarizeComponents` derives REAL bucket counts (up / degraded /
    partial / down, led by a "Components" total card) from `toHealthStatus`, adding a trailing
    "Unknown" card only when that bucket actually has a member — never a permanent zero-value card.
    Below it, one expandable `<table>` row per component (`pages/DashboardPage.tsx::ComponentRow`):
    a `UptimeBar` sparkline + mono `formatPct`, and a `StatusBadge` (plus a SECOND "Under
    maintenance" `StatusBadge`, STORY-046, unchanged, alongside — never replacing — the health one).
    THREE more hooks layer on as graceful-degradation ENHANCEMENTS, per AC2 — a failure/loading
    state in any of them degrades to "no expand affordance" / "no uptime data" / "no maintenance
    badge" and never blocks or clears the primary table: `features/dashboard/useTopology.ts` (thin
    `useFetch(getTopology)`, feeds the expand affordance), `features/dashboard/
    useComponentUptime.ts::useComponentUptime(topology, range)` (a fixed 24h `range` — no selector
    on this tab — combining the rollup `availability_pct` from `getComponentAvailability` with a
    `buildUptimeSegments` sparkline built from the component's FIRST topology signal's raw
    `getHistory`, capped at `MAX_UPTIME_SEGMENTS = 30`; `fetchComponentUptime` NEVER rejects — a
    per-component failure degrades to `{ pct: null, segments: [] }` so one troubled component can't
    blank every other row), and `features/dashboard/useMaintenanceWindows.ts` (STORY-046,
    unchanged). Expanding a row (a real `<button aria-expanded>`, `Set<string>` of expanded ids in
    local state) lazily mounts `SignalsDrilldown`, which calls
    `features/dashboard/useComponentSignals.ts::useComponentSignals(signals, range)` — its
    `buildSignalRows` collapses each signal's observations to "latest per location" (the newest-
    first `getHistory` contract means the FIRST observation seen per location IS the latest), and a
    signal with zero observations in the window contributes one honest `'missing'`-status row rather
    than being silently dropped; the drill-down's own loading/error/empty states are scoped to that
    region alone. See `pages/DashboardPage.tsx`, `features/dashboard/{summary,useTopology,
    useComponentSignals,useComponentUptime}.ts`.
  - **Availability (STORY-058 rebuild of 015d):** a two-column grid replacing the old single
    Availability column — `AvailabilityCell` (a big mono `formatPct` colored by
    `features/availability/format.ts::availabilityBand`'s four real-percentage bands — up ≥99.9% /
    degraded ≥99% / partial ≥95% / else down — plus `formatDownLabel`'s sublabel derived from the
    REAL verdict counts `total − passing − maintenance`, never a fabricated count) and
    `CompletenessCell` (mono `completeness_pct` + a hatched split bar, `isCompletenessLow` flagging
    a REAL completeness below the 98% `COMPLETENESS_LOW_THRESHOLD` with a "missing data" chip — a
    `null` pct is deliberately NOT "low", a distinct "no data" case). The rollup row's own
    `UptimeBar` sparkline is `features/availability/segments.ts::buildAvailabilitySegments` (a
    line-for-line copy of the Dashboard's `buildUptimeSegments`, `MAX_AVAILABILITY_SEGMENTS = 30`,
    kept as its own file per the sprint-38 Wave-2 file-scope isolation rule since parallel
    implementers worked in separate worktrees); a per-signal drill-down child row renders the same
    `AvailabilityCell`/`CompletenessCell` pair with `showBar={false}` (mirroring the Dashboard
    drill-down's bar-less convention). A legend (down/missing swatches) plus the 24h/7d/30d window
    toggle (`features/availability/windowRange.ts`, unchanged, also reused by Check History) sit in
    the header. The two-grain expand/collapse mechanics (a real `<button aria-expanded>`, per-signal
    name resolved from topology since `SignalAvailabilityDTO` carries no `name`) are unchanged from
    015d. See `pages/AvailabilityPage.tsx`, `features/availability/{segments,format}.ts`.
  - **Approvals (STORY-059 rebuild of 015c; evidence-first per STORY-100, sprint-54 — see its own
    subsection below for the full detail):** one `ApprovalCard` per open proposal (`<ul
    className="approval-list">`, now wrapped in the standard `Panel`) with a left severity-accent
    stripe — `features/approvals/severity.ts::deriveSeverity(to_status)` maps `major_outage → down/"Major"`,
    `partial_outage → partial/"Partial"`, `degraded → degraded/"Degraded"` onto the SAME 7-status
    health tokens every other indicator uses (a defensive `'unknown'` fallback for the
    else-case, which `core/services/decide.py` makes practically unreachable — an open proposal is
    always a degradation, never a recovery). The `from_status → to_status` transition is two
    `StatusBadge`s (`from_status === null` renders "New" — a component's first-ever proposal has no
    prior status) plus an `Icon name="arrow-right"`. The idle → confirming → submitting → failed
    state machine (`features/approvals/decisionState.ts`) is narrowed
    per-card via `toCardDecisionState` so a card never compares proposal ids itself; the 409/404
    notice banner still lives one level up in `ApprovalsPage` (not scoped to a single card). A
    friendly component name, per-location evidence, a "View checks" deep link, and the approve
    confirm's publish-consequence copy are STORY-100 additions (see below); the reason/source/
    detected-ago/triggering-signals fields are still OMITTED, never faked — deferred to STORY-063.
    See `pages/ApprovalsPage.tsx`, `features/approvals/
    {severity,decisionState,ApprovalCard,useApprovalsTopology,useProposalEvidence}.tsx`.
  - **Check History (STORY-060 rebuild of 015e — now a SYSTEM-WIDE ledger, not one signal at a
    time):** `features/history/useAllHistory.ts` enumerates every topology signal via the EXISTING
    `getTopology()` (reusing `features/history/signals.ts::flattenSignals`), fires one `getHistory`
    call per signal IN PARALLEL for the selected 24h/7d/30d window, and merges the results via
    `features/history/mergeObservations.ts::mergeObservations` — each signal's own observations
    arrive newest-first, but interleaving multiple signals means the merged list must be RE-SORTED
    by `observed_at` descending to stay newest-first overall; `HistoryRow` extends `ObservationDTO`
    with a `componentName` resolved at merge time from the topology join. This ONE `useFetch`
    fetcher supersedes and REMOVES the old per-signal-selector pair `features/history/
    useSignalOptions.ts` + `useHistory.ts` (deleted — no longer in `code_refs`). A filter toolbar
    (free-text search + a result `<select>` + a location `<select>`, `features/history/
    filterHistory.ts::filterHistoryRows`/`uniqueLocations`) then narrows the ALREADY-LOADED list
    client-side — none of the three filters triggers a refetch, only the window toggle does; the
    location options are populated from the currently-loaded window's REAL data (no dedicated
    locations-enumeration endpoint). The dense grid replaced the old selector-driven single-signal
    table. The 1,000-row render cap (STORY-015e, `/history` has no CLIENT-DRIVEN pagination — the
    server gained an optional `limit` cap in STORY-094 that this client does not send) is preserved but now
    an INJECTABLE `maxRenderedRows` prop (default `DEFAULT_MAX_RENDERED_ROWS = 1000`) — added in the
    STORY-060 review fix so a test can pin a small cap without the STORY-054 flake (rendering
    ~1,000+ rows was slow enough under `npm test` file-parallelism to occasionally exceed Vitest's
    per-test timeout); production always renders via the default. **STORY-064 (sprint-44):** the
    grid gained Type and Code columns (between Timestamp/Component and Result/Latency
    respectively) — `pages/CheckHistoryPage.tsx` renders `row.check_type.toUpperCase()` (e.g.
    `"http"` -> `"HTTP"`) and `formatResponseStatusCode(row.response_status_code)` (raw int, or an
    em-dash for `null` — the SAME convention as `formatLatency`, covering both a missing/unparsable
    source value and a pre-migration row). `mocks/handlers/history.ts`'s `makeObservation` factory
    defaults both fields to a REAL `/api/v1/history` response captured during implementation off
    the 2026-07-12 live-Grail probe sample (`response_status_code: 200, check_type: 'http'`); the
    degraded/down fixture rows use `response_status_code: null` (the real "no failure code
    captured" state — see [[dynatrace-adapter]]'s TBD-failure-code note — never an invented
    failure status). **STORY-100 (sprint-54):** the toolbar's search filter is now URL-driven for
    its INITIAL value only — `features/history/filterHistory.ts::initialHistoryFilters(searchParams)`
    seeds `filters.query` from an optional `?signal=` param (falling back to
    `DEFAULT_HISTORY_FILTERS` when absent), read via `react-router-dom`'s `useSearchParams()` in a
    lazy `useState` initializer; the toolbar remains fully editable afterwards and is never
    re-synced back to the URL. This is the deep-link seam the Approvals evidence card's "View
    checks" link (`/check-history?signal=<signal_key>`) lands on — the SAME free-text `query` field
    already substring-matches a row's `signal_key` (documented above), so no new filter dimension
    was added. `CheckHistoryPage.test.tsx` now wraps every render in a `MemoryRouter`
    (`renderCheckHistory()` helper, mirroring `DashboardPage.test.tsx`'s STORY-099 pattern) since
    `useSearchParams` throws outside a Router. See `pages/CheckHistoryPage.tsx`,
    `features/history/{filterHistory,mergeObservations,useAllHistory}.ts`.
  - **Publications (STORY-062 rebuild of 015g; STORY-072 added the outcome chip):** a vertical
    `Timeline`/`TimelineItem` (the STORY-055 shared primitive) replacing the old changelog table —
    one `TimelineItem` per publication, newest-first exactly as `usePublications()`
    (`useFetch(getPublications)`, unchanged shape) returns them, toned via the EXISTING
    `toHealthStatus` (unchanged — `PublicationDTO.status` is the SAME `ComponentStatus` vocabulary).
    Each row NOW also renders `PublicationDTO.outcome` (`'succeeded' | 'failed'`, STORY-072 — every
    approve publish ATTEMPT is recorded independent of whether the Statuspage call itself succeeded)
    as an `OutcomeChip` (`pages/PublicationsPage.tsx::OutcomeChip`) — a REUSE of `StatusBadge` mapped
    `succeeded -> 'up'` / `failed -> 'down'` with a `'Succeeded'`/`'Failed'` label override, so it
    stays dot+text/token-only with no new CSS. The mock's author/incident fields are still OMITTED —
    not on `PublicationDTO` — deferred to STORY-066; the 50-item server-side cap is still stated as
    permanent header copy (never a conditional note, since the frontend never learns the true total
    row count for this endpoint); `proposal_id: null` still renders an em-dash. See
    `pages/PublicationsPage.tsx`.
  - **Maintenance (STORY-061 rebuild of 015f/052):** a two-column layout — a `ScheduleForm` card
    ("New window": Title/Component/Start/End, "Title" a client-only label submitted as `reason`;
    `fieldErrorFromDetail`/`deriveWindowState`/`useComponents()` for its options all UNCHANGED from
    015f) beside a windows list, each entry showing its title/reason (`formatReason`, `null` →
    em-dash), a `WindowStateBadge` (unchanged since 015f — deliberately SEPARATE from
    `StatusBadge`/`HealthStatus`, since a window's scheduling state is a different concept from
    component health), and `component_id · starts_at–ends_at`. The per-window delete control is
    OMITTED — no `DELETE /api/v1/maintenance/{id}` on the wire — deferred to STORY-065.
    `useMaintenance` (load+mutate-in-one-hook, calling the list's `retry()` on a successful create)
    is UNCHANGED. See `pages/MaintenancePage.tsx`.
  - **The adapt-to-real-data decisions across all six rebuilds are tracked as explicit follow-up
    stories, never silently fabricated fields:** STORY-063 (Approvals: proposal
    reason/source/detected-ago/checks), STORY-064 (Check History: observation Code/Type columns —
    LANDED sprint-44, see the Check History bullet above), STORY-065 (Maintenance: a real title field + delete), STORY-066
    (Publications: author/incident metadata — `outcome` itself landed in STORY-072, see above),
    STORY-067 (component grouping on Dashboard —
    today's rebuild renders ONE flat section, no `group` field on the wire yet — and a dedicated
    per-component uptime-bucket API, so both Dashboard's `useComponentUptime` and Availability's
    `useAvailability` independently adapt today by composing the existing per-component
    `getComponentAvailability` rollup with a sparkline built from the FIRST topology signal's raw
    `getHistory` — two near-identical `buildXSegments` helpers kept as separate files per the
    sprint-38 Wave-2 file-scope isolation rule, not a shared one, since parallel implementers worked
    in separate worktrees).
  - **A load+mutate widget owned by the shell, not a tab (sample-mode trigger, STORY-049,
    relocated STORY-056, TEMPORARY — see `docs/scrum/wiki/sample-mode.md`):**
    `features/dashboard/useSampleMode.ts` still owns BOTH the load (`useFetch(getSampleMode)`) and
    the mutate (`setEnabled`, PUTting and updating an internal `override` state from the PUT
    RESPONSE only) in one hook, unchanged since STORY-049 — a single boolean, no "list to refresh"
    to reconcile against. `enabled` is still computed on every render as `override ??
    state.data.enabled` (never effect-synced) to avoid a one-frame flash. What CHANGED at
    STORY-056: the hook is no longer called from `DashboardPage` — `AppShell.tsx` calls it ONCE and
    passes the result down as a prop to both `nav/TopBar.tsx` (the ⚡ trigger — still a real
    `<button role="switch" aria-checked aria-label="Sample mode">`, rendering nothing until
    `state.phase` leaves `'loading'`, a retry affordance on a load failure instead of the switch)
    and `nav/SampleModeBanner.tsx` (the warning, now dismissible — session-scoped local state that
    re-arms whenever the derived `visible` boolean transitions false → true again). This "lift once,
    thread down as a prop" shape is DELIBERATE: two independent `useSampleMode()` calls (one in the
    trigger, one in the banner) would each run their own GET/override cycle and could disagree the
    instant one of them PUTs — see `TopBar.tsx`'s and `SampleModeBanner.tsx`'s header comments.
    `DashboardPage.tsx` no longer renders or imports anything sample-mode-related. See
    `AppShell.tsx`, `nav/TopBar.tsx`, `nav/SampleModeBanner.tsx`.
  - The Dashboard maintenance indicator (STORY-046 — the frontend health vocabulary's `maintenance`
    `HealthStatus` value, otherwise dead code since the backend `ComponentStatus`
    `toHealthStatus` maps is a closed 4-value set with no maintenance state) is unchanged by the
    STORY-057 rebuild: `isUnderActiveMaintenance`/`deriveWindowState`/`useMaintenanceWindows` all
    carry over verbatim, folded into the new `ComponentRow` (documented above).
  - The field-mapping fix from STORY-052 (sprint-37: the backend's `ends_at`/`starts_at` ordering
    422 mentions BOTH fields, so `features/maintenance/fieldError.ts::fieldErrorFromDetail` checks
    for the "strictly greater than" phrase FIRST — before the generic per-field substring scan — and
    maps it to `ends_at`, the field actually at fault) is preserved unchanged by the STORY-061
    two-column rebuild.
  - A tab story touches only its own `pages/` + `features/<tab>/` files, appends a
    `mocks/handlers/<feature>.ts`, and adds its DTO + `getX()`/`postX()` to `api/types.ts` /
    `api/client.ts`; the routing table `tabs.ts` is already fully populated. (STORY-015a's throwaway
    `ComponentsProbe` was absorbed into `useComponents` + `DashboardPage` and deleted in 015b.)

## Inference (synthesis, not verified)
- The shared append-points a tab story still edits are `api/types.ts` + `api/client.ts` (its DTO +
  `getX()`/`postX()`) and a new `mocks/handlers/<feature>.ts`; the routing table, MSW composition,
  and the shared `useFetch<T>` are structured for additive-only edits, so sequential tab stories
  don't collide.
- **The shared `useFetch<T>` (done in 015c) is now the foundation for every read hook through
  sprint-38** — the parallel-shape trigger the Sprint-26 retro flagged has been discharged, and held
  up across a much wider set of shapes than originally anticipated: a read tab with NO
  selector/args is a thin `useFetch(getX)`; one WITH a selector (015d's window, or Dashboard's fixed
  24h `range`) wraps its parameterized call in `useCallback` keyed on a caller-memoized arg object;
  and STORY-057's `useComponentUptime`/`useComponentSignals` show the pattern generalizes to a
  compound key (`[topology, range]` / `[signals, range]`) with no `useFetch` change either. The one
  sharp edge to watch throughout is still the stable-`fetcher`-reference rule. A mutating tab still
  reuses the Approvals local-state-machine + `ApiError.status`-branching pattern rather than
  re-inventing it.

## History
- sprint-38 (sprint-close compile pass, this update): recompiled for Wave 2 of the Operator
  Dashboard redesign — STORY-057 (Dashboard: summary-card row + expandable per-component signal
  drill-down + `UptimeBar` uptime column, `features/dashboard/{summary,useTopology,
  useComponentSignals,useComponentUptime}.ts`), STORY-058 (Availability: two-column
  availability/completeness grid with hatched-completeness split bar + a legend,
  `features/availability/segments.ts` + new `format.ts` helpers `formatDownLabel`/
  `isCompletenessLow`/`availabilityBand`), STORY-059 (Approvals: `ApprovalCard` list with a
  severity-accent stripe, `features/approvals/severity.ts::deriveSeverity`), STORY-060 (Check
  History: rebuilt as a SYSTEM-WIDE ledger — `features/history/useAllHistory.ts` +
  `mergeObservations.ts` + `filterHistory.ts` replace the deleted single-signal-selector pair
  `useSignalOptions.ts`/`useHistory.ts`; the 1,000-row cap gained an injectable `maxRenderedRows`
  prop, STORY-060 review fix, resolving the STORY-054 flake), STORY-061 (Maintenance: two-column
  form+list layout, delete control omitted → STORY-065), and STORY-062 (Publications: vertical
  `Timeline`/`TimelineItem` replacing the changelog table, metadata omitted → STORY-066). All six
  tabs now sit on the STORY-055 design system + STORY-056 shell (documented in the entries below,
  unchanged by Wave 2). Backend diff empty for the whole sprint (frontend-only). `code_refs`: removed
  the deleted `frontend/src/features/history/{useSignalOptions,useHistory}.ts`; added the STORY-055
  shared-primitive defining files (`components/{Table,UptimeBar,SummaryCard,Timeline,Icon}/*.tsx`,
  previously only covered via the `components/index.ts` barrel) and every new Wave-2 defining
  feature module (`dashboard/{summary,useTopology,useComponentSignals,useComponentUptime}.ts`,
  `availability/segments.ts`, `approvals/{severity,decisionState,ApprovalCard}.ts(x)`,
  `history/{filterHistory,mergeObservations,useAllHistory}.ts`). Test count at HEAD: 355 tests / 50
  files (`npm test`, all green). verified_sha = 977e9ea.
- sprint-38: updated for STORY-056 (Wave 1 of the Operator Dashboard redesign — the app shell,
  wrapping every page). Replaced the top `Nav` bar with a collapsible left icon `Sidebar` (routed
  `NavLink`s carrying `aria-label`s that stay correct across expand/collapse, a
  `localStorage`-persisted expand choice via the new `nav/sidebarState.ts`, an Approvals
  pending-count badge from the new `features/shell/useApprovalsBadge.ts`) + a `TopBar` (theme
  toggle, relocated sample-mode ⚡ trigger) + a dismissible `SampleModeBanner`, all composed by a
  rewritten `AppShell.tsx`. `nav/tabs.ts`'s `TabDefinition` gained an `icon: IconName` field
  (STORY-055's shared `Icon` set already had every needed glyph — no `Icon` additions this story).
  `useSampleMode()` is now called ONCE in `AppShell` and threaded down as a prop to both `TopBar`
  and `SampleModeBanner` (documented above) rather than embedded in `DashboardPage`, which lost its
  `SampleModeToggle` component/CSS/tests entirely (moved, not dropped — equivalent coverage now
  lives in `TopBar.test.tsx`/`SampleModeBanner.test.tsx`/`AppShell.test.tsx`). `Nav.tsx`/`Nav.css`/
  `Nav.test.tsx` deleted. Sonnet-5-implementer TDD pass, one commit per green step; frontend-only;
  six backend gates untouched (empty diff since `sprint-38-start`). `code_refs` +=
  `nav/{Sidebar,TopBar,SampleModeBanner,sidebarState}`, `features/shell/useApprovalsBadge.ts`; `Nav.tsx`
  removed. verified_sha = 4daf4c6.
- sprint-25: created (STORY-015a — the frontend shell, second attempt, built guided by
  `DESIGN-linear.app.md`; dark+light themes; the first attempt was reverted in `521764c`).
  verified_sha = 08d91e7.
- sprint-26: updated for STORY-041 (shell hardening — client wraps malformed-2xx bodies into
  `ApiError`; shared `cx()` helper in `lib/cx.ts`; MSW handlers modularized into
  `mocks/handlers/<feature>.ts` composed in `handlers/index.ts`; catch-all route →
  `NotFoundPage.tsx`) AND STORY-015b (the first REAL tab — `features/dashboard/useComponents.ts`
  hook + a semantic-table `DashboardPage.tsx`; the throwaway `ComponentsProbe` was absorbed and
  deleted; `statusMapping.ts` is now the authoritative health map). Both frontend-only; the six
  backend gates untouched-green. `code_refs` re-scoped (dead `mocks/handlers.ts` → `handlers/`;
  added `lib/cx.ts`, `useComponents.ts`, `DashboardPage.tsx`, `statusMapping.ts`). verified_sha = 6d44c22.
- sprint-27: updated for STORY-015c (the Approvals tab — the human approval gate, and the first
  MUTATING tab). Landed the shared `lib/useFetch.ts::useFetch<T>` (extracted from `useComponents`,
  which + the new `useApprovals` are now thin wrappers — parallel-shape agreement discharged); a
  `postJson` client helper + `getApprovals`/`postDecision` funneling through a shared `readOkJson`
  (one uniform `ApiError` contract with readable `.status` for 409/404 branching); the `api/actor.ts`
  swappable placeholder seam (auth deferred to STORY-017); `ProposalDTO`/decision types;
  `mocks/handlers/approvals.ts`; and `pages/ApprovalsPage.tsx` (confirm → POST → 409/404/error
  branch → list refresh). Both Opus reviewers first-pass; frontend-only; six backend gates
  untouched-green. `code_refs` += actor.ts, useFetch.ts, approvals handler/hook, ApprovalsPage.
  verified_sha = 50bf57b.
- sprint-32: updated for STORY-015d (the Availability tab — two-grain availability: a
  component-grain rollup headline row expandable to per-signal children, on the STORY-044
  `/topology` + `/availability/component/{id}` endpoints). Landed `TopologySignalDTO` /
  `ComponentTopologyDTO` / `AvailabilityDTO` / `SignalAvailabilityDTO` / `ComponentAvailabilityDTO`
  in `api/types.ts`; `getTopology`/`getComponentAvailability` on the client;
  `mocks/handlers/availability.ts` (multi-signal / single-signal / zero-signal / no-data-window
  fixtures); `features/availability/windowRange.ts::windowToRange` (the tz-discipline seam — 24h/
  7d/30d preset → tz-aware ISO `since`/`until`); `features/availability/useAvailability.ts`
  (topology + per-component `Promise.all`, merged; the "parameterized fetch" `useCallback` pattern
  documented above, discharging the T3 refetch-on-range-change question with NO change to
  `useFetch` itself); `features/availability/format.ts::formatPct` (two-decimal, "no data" for
  null); and `pages/AvailabilityPage.tsx` (24h/7d/30d selector, expandable rows, all four states).
  Sonnet-5-implementer TDD pass, one commit per green step; frontend-only; six backend gates
  untouched-green (empty diff). `code_refs` += mocks/handlers/availability.ts,
  features/availability/{windowRange,useAvailability,format}.ts, pages/AvailabilityPage.tsx.
  verified_sha = c2e865c.
- sprint-32: updated for STORY-049 (the Dashboard sample-mode toggle — a TEMPORARY feature, see
  `docs/scrum/wiki/sample-mode.md`). Landed `SampleModeDTO` in `api/types.ts`; `getSampleMode`/
  `putSampleMode` on the client plus a new `putJson` helper (mirrors `postJson` for PUT bodies,
  same `readOkJson`/`ApiError` contract); `mocks/handlers/sampleMode.ts` (stateless GET-default-off
  + PUT-echoes-body handlers, matching the approvals/components convention of per-test
  `server.use()` overrides for stateful scenarios rather than global mutable fixture state);
  `features/dashboard/useSampleMode.ts` (the load+mutate-in-one-hook pattern documented above);
  and `DashboardPage.tsx` gained an embedded `SampleModeToggle` (switch + tokens-styled warning).
  Sonnet-5-implementer TDD pass, one commit per green step; frontend-only; six backend gates
  untouched-green (empty diff — no backend source change). `code_refs` +=
  mocks/handlers/sampleMode.ts, features/dashboard/useSampleMode.ts. verified_sha = 63886bc.
- sprint-32: fix — STORY-015d shipped with a WRONG scale assumption. The backend
  (`core/queries/availability.py`) puts `availability_pct`/`completeness_pct` on the wire as 0–1
  FRACTIONS (`1.0` = 100%, never pre-multiplied), confirmed against a live response; the frontend
  had been treating them as already percent-scale, so `formatPct` rendered `1.0` as `1.00%` and the
  Availability bar drew a fully-up component at ~1% width. Fixed `features/availability/format.ts::
  formatPct` to scale ×100 before formatting (doc-comment now states the wire scale explicitly);
  `pages/AvailabilityPage.tsx::AvailabilityStat`'s bar-width calc to the same scale; and every fixture
  value in `mocks/handlers/availability.ts` to true 0–1-fraction scale (tests rewritten to assert the
  same human-readable display text from the corrected fixtures, per the 2026-06-29
  rewrite-tests-to-the-new-contract agreement — none deleted). No other frontend consumer of these
  two fields found (checked `api/types.ts`, `api/client.test.ts`,
  `features/availability/useAvailability.test.tsx` — none assumed the wrong scale). Backend
  untouched; six backend gates not run (no backend diff). verified_sha = eff33d3.
- sprint-33: updated for STORY-015e (the Check History tab — a dense, chronological, per-signal
  observation ledger on the existing `GET /api/v1/history` endpoint, STORY-014c). Landed
  `ObservationDTO` in `api/types.ts`; `getHistory({ signal_key, since, until })` on the client;
  `mocks/handlers/history.ts` (fixtures DERIVED from the sprint-33 plan's pinned live wire sample —
  fractional-second ISO UTC timestamps, integer-ms latencies, raw vendor location strings, all
  three observation-health values, a `latency_ms: null` row); the NEW, deliberately separate
  `features/history/observationHealth.ts::observationHealth` mapper (documented above); the signal-
  enumeration pair `features/history/signals.ts::flattenSignals` + `features/history/
  useSignalOptions.ts` (both reusing the EXISTING `getTopology()`, no new endpoint);
  `features/history/useHistory.ts` (the two-axis coupled-selector fetch, documented above); and
  `pages/CheckHistoryPage.tsx` (signal + 24h/7d/30d window selectors, a semantic table — timestamp/
  latency/location in the mono token, `StatusBadge` via `observationHealth` — newest-first exactly
  as returned, the 1,000-row render cap with a visible count note, and full loading/empty/error+
  retry coverage for both the signal-enumeration fetch and the observation fetch). Design decision:
  used a semantic `<table>` (matching Dashboard/Approvals/Availability) rather than a non-table
  "changelog row" list the story's Description suggested, for accessibility/consistency parity with
  the three existing real tabs — noted as a design decision, not a deviation from any AC (AC1–AC4
  only specify content/values, not markup shape). Sonnet-5-implementer TDD pass, one commit per
  green step; frontend-only; six backend gates untouched-green (empty diff — no backend source
  change). `code_refs` += mocks/handlers/history.ts, features/history/{observationHealth,signals,
  useSignalOptions,useHistory}.ts, pages/CheckHistoryPage.tsx. verified_sha = 0a1ef52.
- sprint-33: updated for STORY-015g (the Publications tab — a read-only audit trail of what was
  actually pushed to the public Statuspage and when, on the existing `GET /api/v1/publications`
  endpoint, STORY-037). Landed `PublicationDTO` in `api/types.ts`; `getPublications()` on the
  client (no params — the endpoint's own `list_recent` caps at 50 server-side, so unlike
  `/history` there is no client-side render cap); `mocks/handlers/publications.ts` (fixtures
  DERIVED from the backend's own `test_publications_endpoint.py`/`test_publication_domain.py`
  fixtures per the 2026-07-04 real-sample agreement — component_id checkout/login, a non-
  operational status incl. `major_outage`, a `proposal_id: null` case); the SIMPLEST read-tab hook
  yet, `features/publications/usePublications.ts = useFetch(getPublications)` (documented above);
  and `pages/PublicationsPage.tsx` (a changelog table newest-first — published_at mono, component_id,
  a single `StatusBadge` via the EXISTING `toHealthStatus` (no new mapper — `PublicationDTO.status`
  is the SAME `ComponentStatus` vocabulary `ComponentDTO.status` uses), proposal_id mono with
  `null` -> em-dash, the 50-item cap stated as permanent header copy, and full loading/empty
  ("nothing published yet")/error+retry coverage). Sonnet-5-implementer TDD pass, one commit per
  green step; frontend-only; six backend gates untouched-green (empty diff — no backend source
  change). `code_refs` += mocks/handlers/publications.ts, features/publications/usePublications.ts,
  pages/PublicationsPage.tsx. verified_sha = b7811cf.
- sprint-34: updated for STORY-015f (the Maintenance tab — the second MUTATING tab, on the
  STORY-036 `GET`/`POST /api/v1/maintenance` endpoints; all six tabs are now real, no placeholder
  page remains). Landed `MaintenanceWindowDTO`/`CreateMaintenanceRequest` in `api/types.ts`;
  `getMaintenance`/`postMaintenance` on the client (funneled through `postJson`, not `putJson`);
  a new optional `ApiError.detail` (a best-effort parse of a non-2xx `{"detail": ...}` body, purely
  additive to the existing `.status`-only contract); `mocks/handlers/maintenance.ts` (fixtures
  derived from the sprint-34 plan's pinned live wire sample, plus a `reason: null` window for the
  em-dash case); `features/maintenance/windowState.ts::deriveWindowState` (the half-open
  upcoming/active/past derivation, both boundary instants unit-pinned); `features/maintenance/
  fieldError.ts::fieldErrorFromDetail` (422 detail message -> form field mapping); `features/
  maintenance/useMaintenance.ts` (the "load+mutate in one hook" shape documented above); and
  `pages/MaintenancePage.tsx` (windows list with a page-local `WindowStateBadge` + a schedule form
  reusing `useComponents()` for its component options, full loading/empty/error+retry coverage,
  and AC3's inline 422 field-error rendering). Sonnet-5-implementer TDD pass, one commit per green
  step; frontend-only; six backend gates untouched-green (empty diff — no backend source change).
  `code_refs` += mocks/handlers/maintenance.ts, features/maintenance/{windowState,fieldError,
  useMaintenance}.ts, pages/MaintenancePage.tsx. verified_sha = b9f65f9.
- sprint-37: updated for STORY-052 (defect fix — a raw Pydantic 422 blob mis-mapping onto the
  Component field for an `ends_at<=starts_at` scheduling error). `features/maintenance/
  fieldError.ts::fieldErrorFromDetail` gained an early check for the ordering message, mapping it
  to `ends_at` instead of the first-mentioned `starts_at` (see the updated Maintenance-tab bullet
  above); its stale "two real backend 422 cases" doc comment was rewritten to name the current
  three `validate_maintenance_request` cases. No `pages/MaintenancePage.tsx` change was needed —
  its existing per-field inline-render wiring already covers `ends_at`. Frontend-only; six backend
  gates untouched-green (the paired backend fix is `api/v1/maintenance/validation.py`, tracked in
  [[api-five-file-convention]], not this article's code_refs). `code_refs` unchanged (no new
  files). verified_sha = 240666e.
- sprint-37: updated for STORY-046 (Dashboard maintenance indicator — the dead-code `maintenance`
  `HealthStatus` value is now reachable: the PO's chosen Option A overlays a maintenance indicator
  on the Dashboard, derived CLIENT-SIDE from `GET /api/v1/maintenance`, never from
  `ComponentStatus`). Landed `features/dashboard/useMaintenanceWindows.ts = useFetch(getMaintenance)`
  (documented above) and wired `DashboardPage.tsx` to render a second `StatusBadge` next to the
  health badge for any component with an ACTIVE window (half-open boundary, both `starts_at`/
  `ends_at` instants tested) — coexisting with, never replacing, the health badge, and carrying a
  text label so it is not color-only. `statusMapping.ts`/`ComponentStatus`/`StatusBadge.tsx`
  UNCHANGED. Graceful degradation: a maintenance-fetch failure or loading state renders as "no
  active windows", never blocking the components table. Sonnet-5-implementer TDD pass, one commit
  per green step; frontend-only; six backend gates untouched-green (empty diff — no backend source
  change). `code_refs` += features/dashboard/useMaintenanceWindows.ts. verified_sha = 0f42798.
- sprint-38: updated for STORY-055 (Wave 0 of the Operator Dashboard redesign — design-system
  foundation + four shared primitives; every later sprint-38 story inherits this). Retuned
  `tokens.css` to the sprint-38 plan.md palette remap table for BOTH themes under the EXISTING
  token names (surfaces/hairlines/ink/accent + new `--color-accent-bg`), extended the health
  palette 5->7 (`partial`+`missing` added, each with a `-subtle`), added a `--shadow` token and a
  compact operator-console type scale, kept the `data-theme` scoping + `index.html` pre-paint
  script mechanism untouched. Extended `HealthStatus`/`StatusBadge` `DEFAULT_LABELS` with
  `partial` ("Partial outage") / `missing` ("Missing data"); `statusMapping.ts` now maps
  `partial_outage -> 'partial'` (documented above). Self-hosted Geist + Geist Mono replacing
  Inter/JetBrains Mono (`@fontsource/geist` + `@fontsource/geist-mono`, `package.json` +
  `global.css` updated in the same commit as `CLAUDE.md`/`frontend/README.md`'s font line, per the
  2026-06-23 command-sync agreement); added global `font-variant-numeric: tabular-nums`. Added the
  `Icon` component (18 feather-style SVGs) and four new shared primitives — `Table`/`UptimeBar`/
  `SummaryCard`/`Timeline` (documented above) — each with co-located CSS + its own Vitest test.
  Restyled `Button`/`Panel`/`LoadingState`/`ErrorState`/`EmptyState` to the new tokens (existing
  tests green, accessible names unchanged); `ErrorState`'s bare warning glyph now renders through
  `Icon`. Sonnet-5-implementer TDD pass, one commit per green step; frontend-only; six backend
  gates untouched (empty diff since `sprint-38-start` — no backend/scripts/config/migrations/
  pyproject/alembic change). `code_refs` unchanged (no new top-level file paths beyond
  `components/index.ts`, already listed). verified_sha = 298f170.
- sprint-40: updated for STORY-072 (record-always publication outcome; see [[statuspage-publish]] and
  [[persistence-adapters]] for the backend side). `PublicationDTO` (`api/types.ts`) gained
  `outcome: 'succeeded' | 'failed'`; `PublicationsPage.tsx` renders it per row via a new
  `OutcomeChip` helper that REUSES `StatusBadge` (`succeeded -> 'up'`, `failed -> 'down'`, custom
  `'Succeeded'`/`'Failed'` labels) — no new component, no new CSS (documented above). MSW fixtures
  (`mocks/handlers/publications.ts`) updated to carry `outcome` on all three `FIXTURE_PUBLICATIONS`
  rows (the `login`/`major_outage` row is the one `failed` attempt, mirroring the real 401 root
  cause that motivated this story) — `PublicationsPage.test.tsx` drives both outcomes. Frontend-only;
  the paired backend change (migration + record-always `RecordingPublisher` + `PublicationDTO`) is
  tracked in [[statuspage-publish]]/[[persistence-adapters]]/[[canonical-types-and-ports]], not this
  article's code_refs. `code_refs` unchanged (no new file paths). verified_sha = 144bcc0.
- sprint-43 (STORY-078): Repointed availability path from core/services/ to core/queries/ in text. verified_sha = 05f640e.
- sprint-44 (STORY-064, mechanical staleness sweep): Facts updated for the Check History Type +
  Code columns — `api/types.ts::ObservationDTO` gained `response_status_code`/`check_type`,
  `CheckHistoryPage.tsx` renders them ("—" for null code), `mocks/handlers/history.ts` fixtures
  derive from the real 2026-07-12 wire capture (null code for degraded rows — no invented
  failure status). `code_refs` unchanged (no new file paths). verified_sha = 0da9568. (Article
  body was the implementer's; the frontmatter/History tail completed by the orchestrator after
  the implementer's connection-drop crash — edge-case #13 trivial-tail completion.)
- sprint-44 (STORY-079, Facts-coverage cleanup): `yt_wiki.py facts` flagged four uncovered
  citations: `frontend/src/test/setup.ts` (the MSW test-I/O-boundary wiring), `DESIGN-linear.app.md`
  (the frontend's stated design direction), `frontend/eslint.config.js` (the toolchain's lint
  config), and `frontend/src/styles/global.css` (where the self-hosted Geist/Geist Mono fonts are
  imported). All four are genuinely defining files for the shell/toolchain subject this article
  documents; added to `code_refs`. No Fact text changed. verified_sha = 678ff0d.
- sprint-45 (STORY-065/STORY-066): verified after implementing Maintenance title + DELETE endpoint and Publication author metadata. MaintenanceWindowDTO gained optional `title`, PublicationDTO gained optional `author`, and useMaintenance hook and MaintenancePage UI were updated to support deletion with inline two-step confirm. verified_sha -> f6f589fd4dcb6e3a2a565453c43b0fb95d7e5787.
- 2026-07-13 (sprint-45 gate closure): re-stale was the trailing ruff/lint commit 48fba51 (behavior-neutral — trailing-blank trims; MaintenancePage dropped the now-unused formatReason helper + added a type import). Facts unchanged. Re-verified; verified_sha -> 2db6c70.
- sprint-45 (STORY-065 styling fix & STORY-066 minor): moved static inline styles in MaintenancePage to MaintenancePage.css, defined proper BEM class rules, and updated publications MSW mock authors to dashboard-operator. verified_sha -> cbe628bcc849707ffea21aee4d45f433bd76dd12.
- sprint-51 (STORY-094, docs-only): the backend `/history` endpoint gained an optional server-side
  `limit` query param (see [[api-five-file-convention]]); `client.ts::getHistory`'s comment and the
  `CheckHistoryPage.tsx` render-cap comment (Facts updated above) now note the server accepts it
  but this client deliberately does not send it — no code path, DTO, or contract changed.
  verified_sha -> 2859b95.

### Responsive shell (STORY-096, sprint-52 — ui-redesign wave 1)
- Breakpoints live in `frontend/src/lib/breakpoints.ts` (tablet 1024 / mobile 768, mirrored as
  documentation-only custom properties in `tokens.css` — `@media` cannot read `var()`), consumed
  via the hand-rolled `frontend/src/lib/useMediaQuery.ts` (modern `addEventListener('change')`
  API only; tests stub it with the shared `frontend/src/test/matchMedia.ts` helper).
- `frontend/src/nav/useResponsiveSidebar.ts` owns shell nav state: ≤1024px forces the icon rail
  (a non-persisting narrow-mode override — the user's manual expand works while narrow and the
  stored `uptime-monitor-sidebar-expanded` preference is restored on re-widen); ≤768px switches
  to drawer mode.
- `frontend/src/nav/SidebarDrawer.tsx` is the ≤768px overlay: `role="dialog" aria-modal`,
  scrim (z 90) under panel (z 91) under skip-link (z 100), Escape/scrim-click/nav-link-activation
  all close it (nav-link close added by the sprint-52 reality gate — the drawer otherwise covered
  the destination page), Tab focus trap both directions, focus in on open / back to the top-bar
  hamburger ("Open navigation menu") on close, mount animation transform/opacity-only and
  disabled under `prefers-reduced-motion`. It renders the same `Sidebar` with `variant="drawer"`
  (always-labeled, header button closes) — not a copy.
- `Table.tsx` wraps every table in `.table-wrapper` (`overflow-x: auto`): wide tables scroll in
  their own container, never the page; `documentElement.scrollWidth == 390` at 390×844 was
  live-verified on all six tabs (sprint-52 gate evidence, `gate-096/`).

### Page scaffold (STORY-097, sprint-52 — ui-redesign wave 1)
- `frontend/src/components/PageHeader/PageHeader.tsx` is the new shared shell primitive (title +
  optional subtitle + optional `actions` slot) every one of the six tabs now renders as its OWN
  root-level h1, OUTSIDE its content `Panel`/card — fixing the pre-097 split where Dashboard/
  Approvals/Maintenance put the h1 outside the card but Check History/Publications put it inside
  (`Panel title=... headingLevel="h1"`). Exactly one `<h1>` per route (verified — the only
  `<h1>` in `frontend/src/` is `PageHeader.tsx`'s own); `Panel`'s content heading (when it has a
  `title`) defaults to `h2`, so every route's heading order stays sequential (h1 → h2, never
  skipped).
- **Container-width policy**: a single `--container-width: 960px` token (`styles/tokens.css`) +
  two utility classes in `styles/global.css` — `.page` (the default: `max-width:
  var(--container-width); margin: 0 auto`) and `.page--wide` (`max-width: none`, an explicit
  opt-out for a dense data page). 960px was chosen to MATCH Approvals' pre-existing shipped
  width rather than inventing a new number (journal D1 — evolve, don't re-theme). Each page's
  root element carries `page` plus, for the three dense-table/grid tabs, `page--wide`:
  `dashboard-page page page--wide`, `availability-page page page--wide`, `check-history-page page
  page--wide` (full width — the pre-097 status quo for these three, now an explicit opt-in rather
  than a silent default); `approvals-page page`, `maintenance-page page`, `publications-page page`
  (960px centered — Approvals' width extended to the other two card/list/timeline tabs, replacing
  their pre-097 unbounded width).
- Check History and Publications, which previously used `<Panel title="..." headingLevel="h1">`
  as their OWN page root (no wrapping div), each gained a root `<div className="…-page page
  page--wide">`/`page` wrapping a `PageHeader` + a title-less `Panel` (the toolbar/timeline moved
  one level in, unchanged in content). Check History's `PageHeader` also gained a subtitle it
  never had before (`Panel` carried no subtitle prop).
- Availability's legend (down/missing swatches) and 24h/7d/30d window switcher — previously a
  bespoke `availability-page__header`/`__controls` row — now render through `PageHeader`'s
  `actions` prop; no behavior/markup/test change to the legend or switcher themselves, only their
  parent.
- `EmptyState` (see the Shell primitives Fact above for its new `icon`/`tone` API) is now adopted
  with a designed icon + helpful body line by: Approvals ("Queue clear", `icon="check"
  tone="positive"`, replacing its fully bespoke inline `approvals-page__empty*` JSX — the
  surrounding bordered card div is KEPT as page-specific CSS since Approvals is the one tab with
  no `Panel` wrapper around its list), Maintenance ("No maintenance scheduled", `icon="maintenance"`),
  Publications ("Nothing published yet", `icon="publications"`), and Check History's
  filtered-to-zero state ("No observations match your filters", `icon="search"`) — Check History's
  OTHER empty state ("No observations in this window", zero rows before any filter is applied)
  deliberately keeps the bare message-only shape (not named in STORY-097 AC3).
- Publications' "Showing the latest 50 publications" cap-note paragraph now renders ONLY inside
  the populated (`state.data.length > 0`) branch, never above the empty state — it no longer
  contradicts "Nothing published yet" when the endpoint returns zero rows.
- Every accessible name/route/DOM-role assertion the STORY-056/documented-above per-tab Facts
  describe is unchanged by this story (h1 text, nav labels, table roles, filter behavior) — only
  the h1's DOM position (outside vs inside the card), the root container's width class, the
  Availability header's internal composition, and the four EmptyState call sites changed.

### Human time & identity (STORY-098, sprint-53 — ui-redesign wave 2)
- One shared time-formatting module, `frontend/src/lib/formatTime.ts` (journal decision D3, no new
  date-library dependency — hand-rolled against `Intl.*` per the sprint-53 scope fence):
  `formatRelativeTime(iso, now?)` (floors to whole minutes/hours/days, "just now" under a minute
  either direction, `"in Xm"` for the future, raw-string passthrough on invalid input — never
  throws), `formatAbsoluteLocal`/`formatTooltip` (locale-default absolute local time with the
  timezone spelled out via `timeStyle: 'long'`, plus the raw ISO-UTC instant, for a tooltip/
  `title`), `formatLocalRange(startIso, endIso)` (the MAINTENANCE-surface counterpart — absolute
  LOCAL start–end text with a single trailing explicit timezone label extracted via
  `Intl.DateTimeFormat({timeZoneName:'short'}).formatToParts`, plus a raw-UTC-range `.tooltip`),
  and `useRelativeTime(iso, now?)` (a render hook ticking forward every 60s via `setInterval`,
  skipping the tick while `document.visibilityState === 'hidden'`; `now` is injectable for test
  hermeticity, defaulting to the real clock). `frontend/src/lib/formatLocation.ts::
  formatLocationLabel` shortens ANY location id to a generic `"Location …<last-4-chars>"` display
  form — deliberately NOT a vendor-specific mapping (no `SYNTHETIC_LOCATION`-prefix special-casing),
  so a future vendor's id shape shortens the same way; empty input passes through unchanged.
- `frontend/src/components/RelativeTime/RelativeTime.tsx` is the shared rendering primitive
  wrapping `useRelativeTime` — a `<time dateTime={iso} title={tooltip}>{relativeText}</time>`, in
  the `components/index.ts` barrel. Every RECENCY-oriented surface adopts it directly:
  `CheckHistoryPage.tsx`'s Timestamp column, the Dashboard signal drill-down's "Last observed"
  cell (`DashboardPage.tsx::SignalsDrilldown`, `null` still renders as an em-dash — never wrapped),
  `ApprovalCard.tsx`'s "Proposed …" line, and `PublicationsPage.tsx`'s per-item timestamp — none of
  these four re-implement the ticking/tooltip mechanics themselves. The SCHEDULING surface
  (`MaintenancePage.tsx`'s per-window `component · range` line) instead calls `formatLocalRange`
  directly and renders a plain `<span title={range.tooltip}>{range.text}</span>` (AC3 only requires
  a tooltip, not a `<time dateTime>`, for a two-instant range) — the schedule FORM's own
  `datetime-local` input is UNCHANGED, this is a display-only change.
- `CheckHistoryPage.tsx` and `DashboardPage.tsx`'s signal drill-down also adopt
  `formatLocationLabel` for their Location cell/column — the cell keeps the RAW id as its `title`
  tooltip (`getByTitle` in tests). `CheckHistoryPage.tsx`'s location-FILTER `<select>` keeps raw ids
  as OPTION VALUES (its filtering behavior/selection is unchanged) — only the visible OPTION TEXT is
  now prettified through the same helper.
- No raw ISO-8601/microsecond string or bare vendor location id is left as PRIMARY rendered text on
  any of the five converted surfaces (AC1) — every existing page test asserting the old raw-text
  contract was REWRITTEN (2026-06-29 contract-change agreement) to assert the new relative/local/
  short-label text plus the `dateTime`/`title` attributes instead of deleting coverage; several
  tests now pin a fixed `vi.setSystemTime(...)` (mirroring the pre-existing `MaintenancePage.test.tsx`
  pattern) so the relative-time assertions are deterministic. Frontend-only; six backend gates
  untouched-green (empty diff — no backend source change). `code_refs` += `lib/formatTime.ts`,
  `lib/formatLocation.ts`, `components/RelativeTime/RelativeTime.tsx`. Test count at HEAD: 442
  tests / 58 files (`npm test`, all green). verified_sha = aa6dcb5.

### Signal quality — dashboard + availability (STORY-099, sprint-53 — ui-redesign wave 2)
- `components/SummaryCard/SummaryCard.tsx::SummaryCard` gained two opt-in props (journal D4 —
  "color carries state only when non-nominal"): `neutralAtZero` (a numeric `value` of exactly `0`
  overrides the given `tone` to `'neutral'`; `value` above `0` restores it; a non-numeric `value`,
  e.g. a formatted percentage string, is never neutralized — only a REAL `0` triggers it) and
  `href` (the whole card renders as a single routed `react-router-dom` `Link` — one focusable/
  clickable element for the entire card, never a nested control; the app-wide `a:focus-visible`
  rule in `styles/global.css` already covers its focus ring, no local override needed). Both
  default to off/`undefined` — every pre-existing `SummaryCard` call site is a plain, non-
  interactive `<div>` exactly as before unless it opts in.
- `features/dashboard/summary.ts::summarizeComponents` DROPPED the "Components" total card (it
  only ever duplicated "Operational N of N" — journal #7) and added a `neutralAtZero: boolean`
  field to `SummaryCardViewModel`: `true` for the "bad state" buckets (`degraded`/`partial`/`down`
  — a 0 count there is good news, not an alert) and `false` for `up` (Operational always keeps
  its green, by design, regardless of count) — `DashboardPage.tsx` passes this straight through to
  `SummaryCard`'s new `neutralAtZero` prop.
- Two new pure helpers replace that slot with cross-tab awareness action cards (journal #8):
  `features/dashboard/maintenanceSummary.ts::countActiveOrUpcomingWindows` (counts
  `MaintenanceWindowDTO[]` whose `features/maintenance/windowState.ts::deriveWindowState` is
  `'active'` or `'upcoming'`, mirroring its half-open boundary rule exactly rather than
  re-deriving it) and `features/dashboard/actionCard.ts::actionCardView` (derives `{value, tone}`
  from a `number | undefined` count: `undefined` — loading OR error, the same graceful-
  degradation convention as `features/shell/useApprovalsBadge.ts` — renders an honest em-dash in
  the neutral tone, NEVER a fabricated `0`; a resolved `0` stays neutral too; any count above `0`
  gets the `'accent'` tone, i.e. the indigo/info token, deliberately never the alert-red health
  vocabulary). `pages/DashboardPage.tsx::DashboardPage` renders these as the first two
  `SummaryCard`s in the row — "Pending approvals" (`features/shell/useApprovalsBadge.ts`, linking
  to `/approvals`) and "Maintenance" (`useMaintenanceWindows` + `countActiveOrUpcomingWindows`,
  linking to `/maintenance`) — both ahead of the (now Components-less) status cards from
  `summarizeComponents`.
- `features/dashboard/useComponents.ts::useComponents` gained a `lastUpdatedAt: string | null`
  field (display-layer state only, no API change) — `null` until the first successful
  `GET /api/v1/components` fetch, re-stamped to `new Date().toISOString()` on EVERY later success
  (e.g. a manual retry), and untouched by a failure. Stamped by comparing the incoming `state`
  reference against a `seenState` tracked in a second `useState`, adjusted DURING RENDER (the
  documented "adjusting state when a derived value changes" pattern) rather than inside a
  `useEffect` body — avoids the `react-hooks/set-state-in-effect` cascading-render lint rule
  `lib/useFetch.ts`'s own `retry` callback already steers clear of. `DashboardPage.tsx` renders it
  through a compact "Updated <RelativeTime iso={lastUpdatedAt} />" indicator in the shared
  `PageHeader`'s `actions` slot (STORY-098's `RelativeTime`, never a raw ISO string) — hidden
  entirely (not a placeholder) before the first successful load.
- `pages/AvailabilityPage.tsx::CompletenessCell` relabeled the "Data completeness" cell (journal
  #9 — "8.33% • missing data" read as if the number itself were the missing share): the old
  conditional "missing data" chip next to the value is GONE; every real (non-null) completeness
  value now carries an unconditional "of expected checks received" sub-label instead, so the
  number can only be read as a RECEIVED share. The low-completeness visual cue
  (`availability-cell__value--low`, still driven by `features/availability/format.ts::
  isCompletenessLow`) is preserved as a color-only cue on the value — the ambiguous adjacent TEXT
  is what's gone, not the signal; the shared page legend's "Missing data" swatch and the split
  bar's hatched fill (unchanged) still carry that meaning. A `null` completeness (`formatPct` ->
  "no data") omits the sub-label entirely — never fabricates a "received share" for a component
  with no data at all. Column header ("Data completeness") and bar semantics are unchanged.
- Every DashboardPage test render call now wraps in `react-router-dom`'s `MemoryRouter`
  (`renderDashboard()` helper in `DashboardPage.test.tsx`) — required now that the summary row's
  two action cards render as a real `Link`, which throws outside a Router context; this is a
  TEST-ONLY change, `DashboardPage.tsx` itself needs no Router prop (the real app always mounts it
  under `App.tsx`'s `BrowserRouter`). Frontend-only; six backend gates untouched-green (empty
  diff — no backend source change). `code_refs` += `features/dashboard/actionCard.ts`,
  `features/dashboard/maintenanceSummary.ts`. Test count at HEAD: 471 tests / 60 files (`npm
  test`, all green). verified_sha = 94a2a12.

### Mode & nav affordances (STORY-102, sprint-53 — ui-redesign wave 2)
- Sample-mode control relabel (journal #12): `nav/TopBar.tsx`'s `role="switch"` trigger now renders
  a visible `<span className="top-bar__trigger-label" aria-hidden="true">Sample mode</span>` next
  to the ⚡ icon whenever `!useMediaQuery(QUERY_MOBILE_DOWN)` (desktop widths — the `aria-label`
  itself is unchanged/always-present, so this span is purely a sighted-user affordance, marked
  `aria-hidden` to avoid a duplicate accessible-name announcement). `TopBar.css`'s
  `.top-bar__trigger` (OFF) no longer overrides color at all — it inherits `.top-bar__button`'s
  plain neutral (hairline border, muted ink); `.top-bar__trigger--active` (ON) now uses the
  `--color-health-degraded`/`-subtle` (amber/warning) token pair instead of `--color-health-down`
  (red) — red is reserved for the genuinely-distinct `.top-bar__trigger--error` (a real GET
  failure), which is unchanged. The theme toggle's `title` is now the SAME dynamic string as its
  `aria-label` ("Switch to light/dark theme") instead of the static "Toggle theme" (Description's
  "theme toggle gains a tooltip naming the action").
- Persistent "SAMPLE" chip (journal #12's "banner dismissed, red icon is the only remaining
  indicator"): the banner's dismiss/re-arm state moved OUT of `SampleModeBanner` (previously
  private `useState`) into a new hook, `nav/useDismissibleBanner.ts::useDismissibleBanner(visible)`
  — `{dismissed, dismiss, restore}`, re-arming (`dismissed` back to `false`) on the same
  `visible` false->true transition rule the banner used to implement itself. `AppShell.tsx` is now
  the SINGLE caller (alongside its existing single `useSampleMode()` call): it computes
  `bannerVisible` as before and threads `dismissed`/`dismiss` into `SampleModeBanner` (now a fully
  CONTROLLED component — `visible`/`dismissed`/`onDismiss` props, no internal state) and
  `showSampleChip={bannerVisible && dismissed}` / `onRestoreBanner={restore}` into `TopBar`. `TopBar`
  renders a `.top-bar__sample-chip` button (text "SAMPLE", `aria-label="Sample mode is on — signals
  recorded as DOWN. Click to show details."`) exactly when `showSampleChip` is true; clicking it
  calls `onRestoreBanner` (i.e. `restore()`), which re-shows the banner and hides the chip on the
  very next render (both driven by the one lifted `dismissed` boolean, so they can never disagree).
  Since `TopBar` is shell-level (STORY-056), the chip is visible on every tab, not just the one the
  operator dismissed it from.
- Collapsed-rail tooltips + badge label (journal #16): `nav/Sidebar.tsx` replaced its per-tab native
  `title={tab.label}` with an `aria-describedby`-linked tooltip `<span role="tooltip">` (id
  `sidebar-tooltip-${tab.icon}`), rendered ONLY when the rail is collapsed (`!showLabels` — the
  expanded/drawer layouts are unchanged, no tooltip element at all, since their labels are already
  visible on-screen). `Sidebar.css`'s new `.sidebar__tooltip` is absolutely positioned to the right
  of the icon, `opacity: 0`/`pointer-events: none` by default, revealed via `:hover` AND
  `:focus-visible` on the parent `.sidebar__tab` (a native `title` attribute alone does not reveal
  on keyboard focus) — `.sidebar__nav`'s `overflow` was split from a single `auto` to `overflow-y:
  auto; overflow-x: visible` so this tooltip is never horizontally clipped by the scrolling nav
  list. The Approvals badge dot (`.sidebar__badge-dot`, collapsed-rail-only) gained its own
  `aria-label={`${badgeCount} pending approvals`}` (previously `aria-hidden`) — a second,
  independent accessible-name source alongside the tab link's own `aria-label` (which already
  included the count via ", N pending"), not a replacement for it.
- Maintenance form validation + toast (journal #15): `features/maintenance/fieldError.ts` widened
  `MaintenanceFormField` to include `'title'` and gained `validateMaintenanceForm(values)` — client-
  side, pre-submit checks (required Title/Component/Start/End, plus the SAME end-after-start rule
  the server 422s on) returning an ORDERED `{field, message}[]` (submit order: Title, Component,
  Start, End) so the caller can focus the FIRST failure; empty when valid. `pages/
  MaintenancePage.tsx::ScheduleForm` gained `noValidate` on the `<form>` (the browser's own bubble
  UI never fires) and now runs `validateMaintenanceForm` FIRST on submit — any failure renders
  STYLED inline text (the SAME `.maintenance-form__error` treatment the server-422 path already
  used) under every invalid field via a merged `fieldMessage(field)` helper (`clientErrors[field] ??
  (serverErroredField === field ? mutationError?.detail : undefined)`) and moves focus to the first
  invalid field's ref (new `titleRef`/`componentRef`/`startRef`/`endRef`), WITHOUT ever calling
  `onSubmit` — the server round trip (and `fieldErrorFromDetail`'s existing mapping, unchanged)
  only happens once the client check passes. Title's `<input>` gained `required` (previously the
  only unrequired field) and the same `aria-invalid`/`aria-describedby` wiring as the other three.
  A new shared component, `components/Toast/Toast.tsx` (`role="status"`, `aria-live="polite"`,
  auto-dismiss via a `setTimeout` that restarts whenever its `message`/`duration` prop changes,
  default 4000ms, never calls `.focus()`) renders "Window scheduled"/"Window deleted" from new
  `MaintenancePage`-local `toastMessage` state, set ONLY on the success path of `schedule`/
  `deleteWindow` (a failure keeps using the pre-existing `role="alert"` inline/banner rendering,
  never this toast) — added to the `components/index.ts` barrel alongside the other shell
  primitives.
- Frontend-only; six backend gates untouched-green (empty diff — no backend source change).
  `code_refs` += `nav/useDismissibleBanner.ts`, `components/Toast/Toast.tsx`. Test count at HEAD:
  515 tests / 62 files (`npm test`, all green). verified_sha = f3d30ff.

### Approvals decision support — evidence-first cards (STORY-100, sprint-54 — ui-redesign wave 3)
- Closes journal findings #4 ("approval cards give zero decision evidence") and #14 (approve
  confirm carries no consequence copy), decision D5, ONLY from data already exposed by existing
  endpoints (components/topology/history/approvals) — no backend change.
- `features/approvals/useApprovalsTopology.ts` is a thin `useFetch(getTopology)` wrapper (mirrors
  `features/dashboard/useTopology.ts`'s pattern exactly, its own file per-feature) —
  `ApprovalsPage.tsx` joins each proposal's `component_id` against it (`Object.fromEntries` keyed
  by `component.id`, `{}` while loading/failed) for the friendly name + primary signal every card
  needs; a topology failure/loading tick degrades every card to its raw `component_id` slug and no
  evidence rather than blocking the queue.
- `features/approvals/useProposalEvidence.ts::useProposalEvidence(signalKey)` is the evidence
  fetch: `ProposalDTO`/`core/domain/proposal.py::StatusProposal` carry NO `signal_key` on the wire
  (a proposal is per-COMPONENT, not per-signal), so the caller resolves `signalKey` from the
  component's topology — its FIRST signal (`component.signals[0]`), the SAME single-signal
  adaptation `features/dashboard/useComponentUptime.ts` already uses for the identical reason (no
  dedicated per-proposal signal API; the live deployment's one real app/component has exactly one
  signal anyway — `config/apps/httpcheck.yaml`). `signalKey === undefined` short-circuits to an
  always-successful empty result, never fetching. Otherwise calls the EXISTING `getHistory` over a
  fixed 24h window (`features/availability/windowRange.ts::windowToRange('24h')`, reused) WITH the
  STORY-094 `limit` param (small, server-side cap — `EVIDENCE_HISTORY_LIMIT = 20`) rather than the
  render-side cap Check History uses, then `latestPerLocation` collapses the newest-first
  observations to one row per distinct location (the FIRST observation seen per location IS its
  latest — the same convention `features/dashboard/useComponentSignals.ts::buildSignalRows` uses).
  A REAL history-fetch failure surfaces as this hook's OWN `'error'` state; it never throws for a
  missing signal.
- `features/approvals/ApprovalCard.tsx` renders (top to bottom): friendly component name (bold) +
  the raw `component_id` as a secondary mono slug; the severity chip; the `from_status -> to_status`
  transition (unchanged from STORY-059); "Proposed <RelativeTime>" (unchanged from STORY-098); the
  evidence block — a compact pulsing skeleton while `useProposalEvidence` loads, a quiet italic
  "Evidence unavailable" line on its error state (the card stays FULLY actionable — Approve/Reject
  render regardless), "No recent checks recorded" for a genuine empty success, or one row per
  location (`formatLocationLabel` short label + raw-id tooltip, a `StatusBadge`, latency via a
  file-local `formatLatencyMs` em-dash convention, and a `RelativeTime`); then a "View checks" link
  (`react-router-dom`'s `Link`, omitted entirely when no primary signal resolved) to
  `/check-history?signal=<signal_key>` (`encodeURIComponent`-escaped). The approve confirm step's
  prompt now states the consequence — `features/approvals/decisionState.ts::confirmPrompt(action,
  {componentLabel, targetStatusLabel})` renders "Publishes '<component>: <target status>' to the
  public status page." for `'approve'`, where `targetStatusLabel` is
  `components/StatusBadge/StatusBadge.tsx::defaultStatusLabel(toHealthStatus(proposal.to_status))`
  — reusing the SAME word the transition badge itself already shows rather than a second
  vocabulary; `'reject'` is UNCHANGED ("Reject this proposal?"). `CONFIRM_COPY` (the old static
  `Record<DecisionAction, {prompt, confirmLabel}>`) was REPLACED by `confirmPrompt` (function) +
  `CONFIRM_LABEL` (the confirm-button labels, unchanged text) — a genuine contract change, so the
  covering tests were rewritten to the new shape (2026-06-29 agreement), not deleted.
  `ApprovalsPage.tsx` now wraps the card list (and the "Queue clear" `EmptyState`) in the standard
  `Panel` (review-52 accepted-with-notes item — Approvals was the one tab with no `Panel` around
  its list; the bespoke `.approvals-page__empty` bordered-card CSS is REMOVED, `Panel` supplies the
  surface/border/shadow now).
- `client.ts::getHistory` gained an optional `limit?: number` param (additive — every pre-existing
  call site omits it and is unaffected; STORY-100 is the first caller to send it, documented
  above). `StatusBadge.tsx` exported its private `DEFAULT_LABELS` lookup through a new
  `defaultStatusLabel(status)` function (in the `components/index.ts` barrel) rather than
  exporting the record itself, so a consumer asks for one status's word instead of importing a
  lookup table.
- Check History's search filter gained a URL-driven INITIAL value (the "View checks" deep-link
  seam) — see the Check History bullet above for the full detail
  (`features/history/filterHistory.ts::initialHistoryFilters`).
- Both `ApprovalsPage.test.tsx` and `CheckHistoryPage.test.tsx` now wrap every render in a
  `MemoryRouter` (`renderApprovalsPage()`/`renderCheckHistory()` helpers, mirroring
  `DashboardPage.test.tsx`'s STORY-099 pattern) since a routed `Link`/`useSearchParams` throws
  outside a Router — test-infra-only changes, landed as their own behavior-neutral commits before
  the Link/URL-param features themselves.
- Sonnet-5-implementer TDD pass, one commit per green step; frontend-only; six backend gates
  untouched-green (empty diff — no backend source change, confirmed via `git diff --stat backend/`).
  `code_refs` += `features/approvals/{useApprovalsTopology,useProposalEvidence}.ts`,
  `components/StatusBadge/StatusBadge.tsx` (previously covered only via the `components/index.ts`
  barrel). Test count at HEAD: 550 tests / 65 files (`npm test`, all green). verified_sha = beca48f.
