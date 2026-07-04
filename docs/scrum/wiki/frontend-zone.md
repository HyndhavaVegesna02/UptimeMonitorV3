---
title: Frontend zone — the operator-cockpit SPA (shell)
code_refs: [frontend/package.json, frontend/vite.config.ts, frontend/index.html, frontend/src/AppShell.tsx, frontend/src/nav/tabs.ts, frontend/src/nav/Nav.tsx, frontend/src/api/client.ts, frontend/src/api/types.ts, frontend/src/api/statusMapping.ts, frontend/src/api/actor.ts, frontend/src/theme/resolveTheme.ts, frontend/src/theme/ThemeContext.tsx, frontend/src/styles/tokens.css, frontend/src/components/index.ts, frontend/src/lib/cx.ts, frontend/src/lib/useFetch.ts, frontend/src/mocks/handlers/index.ts, frontend/src/mocks/handlers/components.ts, frontend/src/mocks/handlers/approvals.ts, frontend/src/mocks/handlers/availability.ts, frontend/src/mocks/handlers/sampleMode.ts, frontend/src/mocks/handlers/history.ts, frontend/src/features/dashboard/useComponents.ts, frontend/src/features/dashboard/useSampleMode.ts, frontend/src/features/approvals/useApprovals.ts, frontend/src/features/availability/windowRange.ts, frontend/src/features/availability/useAvailability.ts, frontend/src/features/availability/format.ts, frontend/src/features/history/observationHealth.ts, frontend/src/features/history/signals.ts, frontend/src/features/history/useSignalOptions.ts, frontend/src/features/history/useHistory.ts, frontend/src/pages/DashboardPage.tsx, frontend/src/pages/ApprovalsPage.tsx, frontend/src/pages/AvailabilityPage.tsx, frontend/src/pages/CheckHistoryPage.tsx]
verified_sha: 0a1ef52
verified_sprint: sprint-33
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
- **App shell + routing:** `frontend/src/AppShell.tsx` composes the persistent `Nav` + a routed
  `<main>`. The six tabs are a single source of truth in `frontend/src/nav/tabs.ts` (Dashboard ·
  Availability · Approvals · Check History · Maintenance · Publications), each mapping a path to
  its page component under `frontend/src/pages/`. `Nav` (`frontend/src/nav/Nav.tsx`) renders the
  tabs as routed `NavLink` anchors (native anchor semantics, not an ARIA tablist) — active tab =
  ink text + accent bottom-border, inactive = ink-subtle. A trailing catch-all `<Route path="*">`
  renders `pages/NotFoundPage.tsx` (Panel + EmptyState + a link back to Dashboard) for unknown
  paths (STORY-041). The two remaining not-yet-built pages (Maintenance, Publications) are
  placeholders that story 015g replaces wholesale; **Dashboard, Approvals, Availability, and Check
  History are the four real tabs so far** (STORY-015b, 015c, 015d, 015e).
- **Theme system (dark + light):** `frontend/src/theme/resolveTheme.ts` resolves the active
  theme (localStorage override → else `prefers-color-scheme`). An inline pre-paint script in
  `frontend/index.html` applies it before first paint (no flash), mirroring `resolveTheme.ts`.
  `ThemeContext.tsx` + `useTheme.ts` expose it to React and back the nav toggle (override
  persisted to localStorage). Both surfaces read the SAME resolution logic.
- **Token layer:** `frontend/src/styles/tokens.css` holds ALL visual values as CSS custom
  properties scoped per theme (`:root[data-theme='dark']` / `[data-theme='light']`) — surfaces,
  hairlines, a 4-step ink scale, the lavender accent set, a health palette
  (up/down/degraded/maintenance + unknown, each with a `-subtle` badge-background variant), radii,
  spacing, type. **Components consume tokens only — no raw hex outside `styles/`** (enforced by
  review; grep-verified clean at STORY-015a). Fonts (Inter + JetBrains Mono) load via `@fontsource`
  (bundled, no runtime font-CDN fetch).
- **Shell primitives** (`frontend/src/components/`, barrel `components/index.ts`): `Button`
  (primary/secondary/tertiary), `StatusBadge` (pill; `aria-hidden` status dot + ink text label —
  status is NEVER color-alone), `Panel` (surface-1 + hairline + 12px radius, `headingLevel` prop
  defaulting to `h2`), `LoadingState`, `ErrorState` (retry callback), `EmptyState`. These ship
  with the shell so per-tab stories don't copy-paste. Classnames are composed with the shared
  `cx(...)` helper (`frontend/src/lib/cx.ts`, STORY-041) — filters falsy, joins on a space.
- **Typed API client:** `frontend/src/api/client.ts` — fetch-based, single `/api` base-URL seam.
  Both `getJson` (GET) and `postJson` (POST — JSON body, `Content-Type: application/json`) funnel
  their response through a shared `readOkJson(response, path)` that gives ONE uniform error
  contract (STORY-015c): EVERY failure is a typed `ApiError` — network rejection (no status),
  non-2xx (`.status` carried), and a malformed-body `SyntaxError` on a 2xx (with status). The
  readable `.status` is what lets a mutating tab branch on 404/409. A third helper, `putJson`
  (STORY-049), mirrors `postJson` for PUT bodies, funneling through the same `readOkJson`. Endpoint
  fns: `getComponents`, `getApprovals`, `postDecision(proposalId, body)`, `getTopology`,
  `getComponentAvailability(componentId, { since, until })` (STORY-015d — query-string encodes
  `since`/`until`, both REQUIRED to be tz-aware ISO strings since the backend 422s a naive
  datetime), `getSampleMode()` / `putSampleMode(enabled)` (STORY-049 — a TEMPORARY-feature seam,
  see `docs/scrum/wiki/sample-mode.md`), `getHistory({ signal_key, since, until })` (STORY-015e
  AC1, AC2 — query-string encodes all three; `since`/`until` REQUIRED tz-aware ISO strings, the
  same discipline as `getComponentAvailability`; NO pagination — the endpoint can return many
  thousands of rows for a wide window, so the Check History tab caps what it RENDERS, not what it
  requests). DTO types in `frontend/src/api/types.ts` (`ComponentDTO`,
  `ProposalDTO`, `DecisionRequest`, `DecisionResponse`, `TopologySignalDTO`, `ComponentTopologyDTO`,
  `AvailabilityDTO`, `SignalAvailabilityDTO`, `ComponentAvailabilityDTO`, `SampleModeDTO`,
  `ObservationDTO`) mirror
  the backend `api/v1/*/models.py` shapes — note `SignalAvailabilityDTO` (a per-signal availability
  result) carries `signal_key` but NOT a display `name`; the name lives only on the topology
  response's nested `TopologySignalDTO`, so a two-grain consumer must join the two responses by
  `signal_key` to label a child row (STORY-015d AC1; see `AvailabilityPage.tsx`).
  `frontend/src/api/statusMapping.ts::toHealthStatus` is the
  authoritative map from the backend `ComponentStatus` vocabulary (operational / degraded /
  partial_outage / major_outage) onto the health tokens (operational→up, degraded→degraded,
  partial_outage→degraded, major_outage→down, else→unknown). **There is now a SECOND, deliberately
  separate health mapper:** `frontend/src/features/history/observationHealth.ts::observationHealth`
  maps the OBSERVATION vocabulary (`ObservationDTO.health`: `"up" | "down" | "degraded"`, else→
  unknown) onto the SAME health tokens `StatusBadge` consumes (STORY-015e AC3). The two mappers'
  input vocabularies overlap only on the string `"degraded"` — `ComponentStatus` has no `"up"`
  value, so `toHealthStatus` would wrongly fold an observation's `"up"` into `unknown`; keeping
  them separate means a future contract change to either vocabulary never ripples into the other
  tab.
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
  params a selector change sent); no component/hook under assertion is mocked. 146 tests at
  STORY-049.
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
- **The per-tab pattern to copy (015e–015g)** — three real tabs now set it:
  - **Read tab (Dashboard, 015b):** a page in `pages/<Tab>Page.tsx` + a one-line
    `features/<tab>/use<Tab>.ts` = `useFetch(<moduleScopedFetcher>)`, rendering a four-state view
    (loading / error+retry / empty / success) from the shared primitives — success branch a
    semantic `<table>` (`<th scope="col">`, one row per item).
  - **Mutating tab (Approvals, 015c):** on top of the read pattern, a per-page local UI state
    machine (`idle → confirming → submitting → failed`) kept SEPARATE from the list's `useFetch`
    state; double-submit guarded by UNMOUNTING the confirm control (not merely disabling); on
    confirm, POST via the typed client reading `getActor()`; branch on `ApiError.status` for domain
    outcomes (409 lost-race / 404 gone → inline notice; else → `ErrorState`); always call the list's
    `retry()` after a resolved decision (success OR terminal conflict) so the view reconciles with
    the server. See `pages/ApprovalsPage.tsx`.
  - **Two-grain drill-down read tab (Availability, 015d):** on top of the read pattern, TWO
    additional shapes: (1) a **selector-driven, parameterized fetch** — see the
    "parameterized fetch" note above `useFetch`'s sharp edge; (2) **expandable parent/child rows**
    within one semantic `<table>` — a real `<button aria-expanded>` per parent row toggles rendering
    additional `<tr className="…__child">` rows for that parent's children (a `Set<string>` of
    expanded ids in local state, NOT a `useFetch`/server concern), and a component with zero
    children renders a plain (non-interactive) name cell instead of a dead-end expand control. Every
    numeric cell renders its value as TEXT even when it also draws a token-styled bar (the bar is
    never the sole carrier), and a `null` percentage renders an explicit "no data" label (never
    `0%`/`NaN%`). See `pages/AvailabilityPage.tsx`.
  - **A two-axis coupled-selector read tab (Check History, 015e):** on top of the read pattern, TWO
    independently-changeable selectors (which SIGNAL, which WINDOW) both feed one fetch —
    `features/history/useHistory.ts::useHistory({ signalKey, range })` wraps `getHistory(...)` in
    `useCallback` keyed on `[signalKey, range]` (the SAME parameterized-fetch pattern as 015d's
    single-axis `range`, just keyed on two independent values instead of one — no `useFetch` change
    needed here either). The signal enumeration is a SEPARATE small `useFetch(getTopology)` wrapper
    (`features/history/useSignalOptions.ts`) plus a pure `features/history/signals.ts::
    flattenSignals` helper — reusing the EXISTING topology endpoint (STORY-044/015d) rather than
    adding a new one; `CheckHistoryPage` computes the effective selection as
    `selectedSignalKey ?? signals[0]?.signal_key` on every render (never effect-synced into state)
    so the default appears the instant topology resolves, with the SAME one-frame-flash rationale
    as the sample-mode toggle's `enabled` computation below. The API's own newest-first order is
    rendered AS-IS (never re-sorted — the order is the contract). Because `/history` has no
    pagination, the page caps what it RENDERS (not what it requests) at the latest 1,000 rows, with
    a visible "showing latest 1,000 of N observations" note when the fetched count exceeds that —
    the FULL fetched array is what gets sliced, so the note's `N` is always the real total. See
    `pages/CheckHistoryPage.tsx`.
  - **A load+mutate widget embedded in a read tab (Dashboard sample-mode toggle, STORY-049,
    TEMPORARY — see `docs/scrum/wiki/sample-mode.md`):** unlike Approvals' split (a read
    `useFetch` hook plus page-local mutation state), `features/dashboard/useSampleMode.ts` owns
    BOTH the load (`useFetch(getSampleMode)`) and the mutate (`setEnabled`, PUTting and updating an
    internal `override` state from the PUT RESPONSE only) in one hook, because the widget is a
    single boolean rather than a list — there is no "list to refresh" to reconcile against, so
    reusing the exact Approvals split would add a needless refetch round-trip. `enabled` is
    computed on every render as `override ?? state.data.enabled` (never effect-synced into a
    separate piece of state) specifically to avoid a one-frame flash of a stale/default value the
    instant the GET resolves — an effect-based mirror was tried first and exhibited exactly that
    race in a real MSW test. A real `<button role="switch" aria-checked aria-label>` (not a
    checkbox) carries the control; the widget renders nothing until the load's `state.phase`
    leaves `'loading'`, and falls back to the shell `ErrorState` + `retry` on a load failure,
    mirroring the read pattern above it. See `pages/DashboardPage.tsx` (`SampleModeToggle`).
  - A tab story touches only its own `pages/` + `features/<tab>/` files, appends a
    `mocks/handlers/<feature>.ts`, and adds its DTO + `getX()`/`postX()` to `api/types.ts` /
    `api/client.ts`; the routing table `tabs.ts` is already fully populated. (STORY-015a's throwaway
    `ComponentsProbe` was absorbed into `useComponents` + `DashboardPage` and deleted in 015b.)

## Inference (synthesis, not verified)
- The shared append-points a tab story still edits are `api/types.ts` + `api/client.ts` (its DTO +
  `getX()`/`postX()`) and a new `mocks/handlers/<feature>.ts`; the routing table, MSW composition,
  and the shared `useFetch<T>` are structured for additive-only edits, so sequential tab stories
  don't collide.
- **The shared `useFetch<T>` (done in 015c) is now the foundation for 015d–015g** — the
  parallel-shape trigger the Sprint-26 retro flagged has been discharged. A read tab with NO
  selector/args is a thin `useFetch(getX)`; one WITH a selector (015d's window) wraps its
  parameterized call in `useCallback` keyed on a caller-memoized arg object instead — the one
  sharp edge to watch either way is the stable-`fetcher`-reference rule. A future mutating tab
  reuses the Approvals local-state-machine + `ApiError.status`-branching pattern rather than
  re-inventing it.

## History
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
  (`core/services/availability.py`) puts `availability_pct`/`completeness_pct` on the wire as 0–1
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
