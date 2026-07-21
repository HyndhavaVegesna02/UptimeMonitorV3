---
title: Frontend zone — the operator-cockpit SPA (rebuilt, sprint-59/60)
code_refs: [frontend/package.json, frontend/index.html, frontend/vite.config.ts, frontend/eslint.config.js, frontend/src/main.tsx, frontend/src/App.tsx, frontend/src/routes.tsx, frontend/src/nav/tabs.ts, frontend/src/styles/tokens.css, frontend/src/styles/global.css, frontend/src/styles/contrastRatio.ts, frontend/src/styles/parseTokens.ts, frontend/src/components/Icon/Icon.tsx, frontend/src/components/Button/Button.tsx, frontend/src/components/Panel/Panel.tsx, frontend/src/components/StatusBadge/StatusBadge.tsx, frontend/src/components/SummaryCard/SummaryCard.tsx, frontend/src/components/Sparkline/Sparkline.tsx, frontend/src/components/LoadingState/LoadingState.tsx, frontend/src/components/ErrorState/ErrorState.tsx, frontend/src/components/EmptyState/EmptyState.tsx, frontend/src/components/PlaceholderPage/PlaceholderPage.tsx, frontend/src/shell/ShellLayout.tsx, frontend/src/shell/Sidebar/Sidebar.tsx, frontend/src/shell/Sidebar/NavItem.tsx, frontend/src/shell/Topbar/Topbar.tsx, frontend/src/shell/Topbar/formatLastUpdated.ts, frontend/src/shell/useSidebarCollapse.ts, frontend/src/shell/useMediaQuery.ts, frontend/src/shell/TooltipGroupProvider.tsx, frontend/src/shell/tooltipGroupContext.ts, frontend/src/api/client.ts, frontend/src/api/types.ts, frontend/src/api/statusMapping.ts, frontend/src/lib/useFetch.ts, frontend/src/lib/cx.ts, frontend/src/lib/format.ts, frontend/src/lib/relativeTime.ts, frontend/src/lib/overallStatus.ts, frontend/src/lib/healthIcons.ts, frontend/src/lib/combineFetchStates.ts, frontend/src/features/dashboard/useSignalsData.ts, frontend/src/features/dashboard/deriveKpis.ts, frontend/src/features/dashboard/deriveChartData.ts, frontend/src/features/dashboard/deriveProbeLocations.ts, frontend/src/features/dashboard/deriveRecentChecks.ts, frontend/src/features/dashboard/deriveRoster.ts, frontend/src/features/dashboard/aggregateSignals.ts, frontend/src/features/dashboard/KpiRow.tsx, frontend/src/features/dashboard/ResponseTimeChart.tsx, frontend/src/features/dashboard/ProbeLocationsPanel.tsx, frontend/src/features/dashboard/MaintenancePanel.tsx, frontend/src/features/dashboard/RecentChecksFeed.tsx, frontend/src/features/dashboard/ComponentsRoster.tsx, frontend/src/features/availability/ComponentAvailabilityCard.tsx, frontend/src/features/availability/WindowToggle.tsx, frontend/src/features/availability/windowRange.ts, frontend/src/features/availability/format.ts, frontend/src/features/availability/joinSignalAvailability.ts, frontend/src/pages/DashboardPage/DashboardPage.tsx, frontend/src/pages/AvailabilityPage/AvailabilityPage.tsx, frontend/src/pages/StyleguidePage/StyleguidePage.tsx, frontend/src/mocks/handlers/index.ts, frontend/src/mocks/handlers/topology.ts, frontend/src/mocks/handlers/availability.ts, frontend/src/test/setup.ts]
verified_sha: 9ffdaba
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
  - `pages/` — `DashboardPage` (STORY-122) and `AvailabilityPage` (STORY-129) are REAL pages;
    `History/Approvals/Maintenance/Publications` are still `PlaceholderPage` stubs awaiting the
    rest of sprint 60; `StyleguidePage` renders every primitive × state (STORY-120).
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
  nested signal children). DTOs in `api/types.ts`: `ComponentDTO {id,name,status}`, `ProposalDTO`,
  `ObservationDTO {signal_key, observed_at, health, location, latency_ms, response_status_code,
  check_type}`, `AvailabilityDTO` (`availability_pct`/`completeness_pct` are 0–1 fractions,
  nullable), `MaintenanceWindowDTO`, `ComponentTopologyDTO`/`TopologySignalDTO` (STORY-129 —
  `interval_seconds` is `int | null`), `ComponentAvailabilityDTO`/`SignalAvailabilityDTO`
  (STORY-129 — the latter is `AvailabilityDTO` + `signal_key`, no display name). Re-derived fresh
  from the LIVE contracts (verified at the STORY-121/122/129 reality gates); extends cleanly as
  later tabs need more endpoints. `statusMapping.ts` maps the vendor `ComponentStatus` vocabulary
  (operational/degraded_performance/partial_outage/major_outage/under_maintenance) onto the
  7-status health palette (…→up/degraded/partial/down/maintenance; else→unknown).

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
- The four remaining tabs (History/Approvals/Maintenance/Publications) are still
  `PlaceholderPage` stubs — real content lands later in sprint 60.
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
