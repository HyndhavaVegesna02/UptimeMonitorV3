---
title: Frontend zone — the operator-cockpit SPA (shell)
code_refs: [frontend/package.json, frontend/vite.config.ts, frontend/index.html, frontend/src/AppShell.tsx, frontend/src/nav/tabs.ts, frontend/src/pages/PlaceholderPage.tsx, frontend/src/pages/NotFoundPage.tsx, frontend/src/features/shell/useApprovalsBadge.ts, frontend/src/api/client.ts, frontend/src/api/types.ts, frontend/src/api/statusMapping.ts, frontend/src/api/actor.ts, frontend/src/theme/resolveTheme.ts, frontend/src/theme/ThemeContext.tsx, frontend/src/styles/tokens.css, frontend/src/styles/global.css, frontend/src/components/index.ts, frontend/src/components/Tile/Tile.tsx, frontend/src/components/Button/Button.tsx, frontend/src/components/StatusBadge/StatusBadge.tsx, frontend/src/components/Icon/Icon.tsx, frontend/src/components/RelativeTime/RelativeTime.tsx, frontend/src/components/Table/Table.tsx, frontend/src/components/UptimeBar/UptimeBar.tsx, frontend/src/components/SummaryCard/SummaryCard.tsx, frontend/src/components/Timeline/Timeline.tsx, frontend/src/lib/cx.ts, frontend/src/lib/useFetch.ts, frontend/src/lib/formatTime.ts, frontend/src/lib/formatLocation.ts, frontend/src/lib/useMediaQuery.ts, frontend/src/lib/breakpoints.ts, frontend/src/test/matchMedia.ts, frontend/src/mocks/handlers/index.ts, frontend/src/mocks/handlers/components.ts, frontend/src/mocks/handlers/approvals.ts, frontend/src/mocks/handlers/availability.ts, frontend/src/mocks/handlers/sampleMode.ts, frontend/src/mocks/handlers/history.ts, frontend/src/mocks/handlers/publications.ts, frontend/src/mocks/handlers/maintenance.ts, frontend/src/features/dashboard/useComponents.ts, frontend/src/features/dashboard/useMaintenanceWindows.ts, frontend/src/features/dashboard/useSampleMode.ts, frontend/src/features/dashboard/summary.ts, frontend/src/features/dashboard/useTopology.ts, frontend/src/features/dashboard/useComponentSignals.ts, frontend/src/features/dashboard/useComponentUptime.ts, frontend/src/features/approvals/useApprovals.ts, frontend/src/features/approvals/severity.ts, frontend/src/features/approvals/decisionState.ts, frontend/src/features/availability/windowRange.ts, frontend/src/features/availability/useAvailability.ts, frontend/src/features/availability/format.ts, frontend/src/features/availability/segments.ts, frontend/src/features/history/observationHealth.ts, frontend/src/features/history/signals.ts, frontend/src/features/history/filterHistory.ts, frontend/src/features/history/mergeObservations.ts, frontend/src/features/history/useAllHistory.ts, frontend/src/features/publications/usePublications.ts, frontend/src/features/maintenance/windowState.ts, frontend/src/features/maintenance/fieldError.ts, frontend/src/features/maintenance/useMaintenance.ts, frontend/src/test/setup.ts, docs/scrum/ui-rewrite/design-brief.md, frontend/eslint.config.js]
verified_sha: 52f1706
verified_sprint: sprint-55
status: verified
---

## Facts (verified against code)

**REWRITE ERA (sprint-55, STORY-103 onward).** PO directive 2026-07-18: a full
UI/frontend rewrite ("Mission Teal"), complete creative freedom within
`docs/scrum/ui-rewrite/design-brief.md` (the binding design authority — a
generated base, `design-system/uptime-monitor-v3-rewrite/MASTER.md`, exists but
the brief overrides it on every conflict, notably fonts and motion). The
previous incremental redesign (`ui-redesign` branch, sprints 52-54, itself a
retune of the STORY-055/056 "Operator Dashboard" shell) is PARKED - its LOOK
was rejected; a short salvage list of its UX logic (time/location formatters,
a media-query hook, a `RelativeTime` primitive) was ported verbatim into this
rewrite (see the STORY-103 bullet below). `sprint-55`/`ui-rewrite` branch off
`main` at the sprint-51 close (517fc38), NOT off `ui-redesign` - the
STORY-055/056/057-062 "Operator Dashboard" shell/pages this article used to
describe are DELETED on this line (STORY-103); their underlying FEATURE HOOKS
(data-fetching/derivation logic, no presentation) survive untouched and are
documented in their own subsection below, orphaned until each tab's rewrite
story (sprint-56+: STORY-105 dashboard, 106 availability, etc.) re-wires them
onto a new page. Everything above this banner in Facts you'd expect from a
"pre-rewrite" article - DESIGN-linear.app.md as the design guide, the
Sidebar/TopBar/SampleModeBanner shell, the six rebuilt Wave-2 pages - is GONE;
see History below for exactly what STORY-103 deleted and why.

- `frontend/` is a standalone Vite + React + TypeScript (strict) SPA — the
  operator-cockpit "internal dashboard" surface (dossier §17, the two-surface
  model; the other surface is the public Statuspage). It is ISOLATED from the
  Python backend: no import of backend source, no shared build step. The six
  backend DoD commands never touch it; its three frontend DoD commands
  (`npm test` / `npm run build` / `npm run lint`, from `frontend/`) never
  touch the backend. Design authority is NOW `docs/scrum/ui-rewrite/
  design-brief.md` (STORY-103) — `DESIGN-linear.app.md` (the sprint-25/38
  design guide) is retired, superseded by the brief.
- **This is the THIRD frontend design generation.** The first (sprints 23-24,
  `DESIGN-airtable.md`) was fully reverted in `521764c` (code lives only on
  `sprint-23`/`sprint-24`). The second (`DESIGN-linear.app.md` -> STORY-055's
  "Operator Dashboard" retune) ran sprints 25-54 and is now torn out on this
  line by STORY-103 (PO-ordered full rewrite) — its code survives only on
  `main`/`ui-redesign` up to sprint-54. Nothing in the current tree descends
  from either prior generation's PRESENTATION layer; the surviving feature
  hooks predate both generations' visual language and were always
  design-agnostic.
- **Toolchain** (`frontend/package.json`): Vite + React + TS strict; Vitest +
  React Testing Library + jsdom + MSW (Mock Service Worker) for tests; ESLint
  flat config (`frontend/eslint.config.js`); npm on Node 24. Scripts: `dev`,
  `build` (`tsc -b && vite build` — type-check is part of the build gate),
  `test` (`vitest run`, run-once), `lint` (`eslint .`) — UNCHANGED by the
  rewrite; the three frontend DoD gate commands are the same commands they've
  always been. Playwright/E2E is still deferred to a later integration story.
  STORY-103 Step 0 added three font packages (`@fontsource/space-grotesk`,
  `@fontsource/inter`, `@fontsource/jetbrains-mono`), replacing the
  STORY-055-era `@fontsource/geist`/`@fontsource/geist-mono` — the sole
  `package.json` dependency change this story made (declared at sprint-55
  planning, tooling-freeze compliant).
- **Dev <-> API seam (unchanged):** the Vite dev server proxies `/api/*` ->
  `http://localhost:8000` (`frontend/vite.config.ts`), a locally running
  uvicorn backend. No backend change and no CORS work was needed — CORS
  stays deferred to STORY-017 per the 2026-06-23 working agreement.

### Mission Teal design system v2 (STORY-103)
- **Tokens** (`frontend/src/styles/tokens.css`): a from-scratch v2 token set,
  DARK-first (`:root, :root[data-theme='dark']` carries the dark values
  directly, so the theme is correct even before any JS runs — `:root
  [data-theme='light']` is the explicit light override). Dark canvas
  `#0A0E14` / elevated tile surface `#111823`; light canvas `#F0FDFA`
  (mint-tinted, per the brief exactly) / white tiles. Primary accent is teal:
  `#14B8A6` (teal-500) in dark, `#0F766E` (teal-700, "on-light contrast") in
  light — paired with a THEME-SPECIFIC `--color-on-accent` rather than a
  fixed white/black, because white-on-teal-500 fails 4.5:1 in dark theme
  (verified in `tokens.test.ts`; dark on-accent is a near-black `#04140F`,
  light on-accent is white on the darker teal-700). A NEW
  `--color-danger`/`--color-danger-hover`/`--color-on-danger` triple backs
  `Button`'s `danger` variant — deliberately NOT a reuse of
  `--color-health-down` (that hue is tuned as a TEXT/dot color against a
  canvas; white text on it fails 4.5:1 in dark theme). The 7-status health
  palette (up/degraded/partial/down/maintenance/unknown/missing, each with a
  `-subtle` badge-background variant) keeps the SAME hex values the
  STORY-055 retune landed (already proven accessible against near-identical
  background luminances) — every value re-checked by `tokens.test.ts`
  against the new canvas colors, all still >= 4.5:1. NEW radius token
  `--radius-tile: 16px` ("rounded-xl tiles" per the brief); NEW elevation
  scale `--shadow-sm/-md/-lg` (border-glow hairline-plus-shadow in dark,
  soft layered shadow in light) alongside the pre-existing single-level
  `--shadow` alias (kept for the primitives this story doesn't touch —
  Panel/SummaryCard); NEW motion tokens `--motion-fast/-base/-slow` (150ms/
  200ms/250ms) + `--ease-standard`; NEW z-scale (`--z-base` through
  `--z-toast`). `--target-min` raised 40px -> 44px (the brief's "44px touch
  targets" floor). Every OTHER pre-existing token NAME (`--color-surface-1`,
  `--color-ink-muted`, `--fs-h1`, `--space-4`, `--radius-control`, etc.) is
  UNCHANGED, so every primitive this story does NOT rewrite (Panel,
  LoadingState, EmptyState, Table, UptimeBar, SummaryCard, Timeline) needed
  zero code changes — only their rendered colors/sizes shifted. Six
  now-unused tokens whose sole consumers were deleted this story
  (`--nav-height`, `--nav-width-expanded`, `--nav-width-collapsed`,
  `--header-height`, `--radius-badge`, `--border-badge-width`) were dropped.
  `frontend/src/styles/tokens.test.ts` is a NEW token-level contract test
  (reads the raw CSS text via Vite's `?raw` import — NOT `node:fs`, which
  `tsconfig.app.json`'s browser-target `src/` deliberately excludes from
  node types — and NOT jsdom computed style, which doesn't reliably cascade
  custom properties through attribute-selector scoping): asserts the exact
  dark/light canvas and accent hex values, the font-family tokens, the
  150-250ms motion band, and — the AC3 evidence — a WCAG contrast-ratio
  check (hand-rolled relative-luminance formula, self-tested against
  black-on-white = 21:1) for `--color-ink-muted` (the `StatusBadge` label
  color) against both badge-hosting surfaces, EVERY health-dot color against
  the canvas, and `--color-on-accent`/`--color-on-danger` against their
  fills — all >= 4.5:1, BOTH themes (74 assertions total).
- **Fonts** (`frontend/src/styles/global.css`): self-hosted Space Grotesk
  (headings — `h1`/`h2`/`h3` and `.text-h1/-h2/-h3` all set
  `font-family: var(--font-heading)`), Inter (body — `--font-sans`),
  JetBrains Mono (tabular data/timestamps/latency/IDs — `--font-mono`), all
  via `@fontsource/*` imports — replacing Geist/Geist Mono. Zero runtime
  Google-Fonts CDN request (verified: the production `dist/` build was
  grepped for `fonts.googleapis.com`/`fonts.gstatic.com`, zero matches; all
  font files are bundled `.woff`/`.woff2` assets). `global.css` also carries
  a `@media (prefers-reduced-motion: reduce)` guard collapsing every
  animation/transition duration to ~0 — the brief's "every animation guarded
  by prefers-reduced-motion" rule — and the two-tone focus-ring rule now
  additionally covers `[role='switch']` (a future sample-mode-switch/tab
  affordance).
- **Theme engine, now dark-FIRST** (`frontend/src/theme/resolveTheme.ts`):
  `getSystemTheme()` no longer collapses to `dark ? dark : light` — it checks
  `(prefers-color-scheme: dark)` explicitly, THEN `(prefers-color-scheme:
  light)` explicitly, and only falls back to `'dark'` if NEITHER query
  matches (no stated OS preference, or no `matchMedia` support at all).
  `resolveInitialTheme()`'s precedence is otherwise unchanged: a
  `localStorage`-persisted override always wins over the system/default
  resolution. `frontend/index.html`'s inline pre-paint script was rewritten
  to the same three-way branch (stored -> explicit dark -> explicit light ->
  dark) so there is still no flash of the wrong theme before first paint.
  `ThemeContext.tsx`/`useTheme.ts`/`theme-context.ts` are UNCHANGED (same
  `{ theme, toggleTheme }` contract, same persistence).

### Base primitives (STORY-103) — the set the rewrite composes from
- **`Tile`** (`frontend/src/components/Tile/Tile.tsx`, NEW): the bento-grid
  card primitive. Renders as a react-router `Link` when `href` is given
  (real anchor semantics), a `<button>` when `onClick` is given without
  `href` (native focusability/keyboard-activation — never a `div` +
  `onClick`), or a plain `<div>` otherwise. `elevation` (`'sm'|'md'|'lg'`,
  default `'md'`) maps to the new `--shadow-sm/-md/-lg` scale; an optional
  `accent` (the same 7-value `HealthStatus` union) draws a 3px colored left
  edge, never the sole cue. `interactive` (default: `true` whenever `href`
  or `onClick` is given, override-able) adds a `<=1.01` hover scale + the
  shared two-tone focus ring — capped per the brief's "no layout-shifting
  hovers" rule.
- **`Button`** (`frontend/src/components/Button/Button.tsx`, REWRITTEN): the
  variant set changed from `primary`/`secondary`/`tertiary` to
  `primary`/`ghost`/`danger` — a BREAKING prop-shape change (this is why the
  one remaining old consumer, `ErrorState`'s retry button, needed touching:
  `variant="secondary"` -> `variant="ghost"`; the OTHER old consumer,
  `ApprovalCard.tsx`, was deleted outright since it was pure presentation
  coupled to the old variant set with no independent test). New
  `loading?: boolean` prop: renders a decorative `.button__spinner`
  (`aria-hidden`), sets `aria-busy="true"`, and disables the button (can't be
  re-triggered mid-request) WITHOUT removing its accessible name — the label
  stays visible alongside the spinner, never replaced by it. Still `>=44px`
  target height (`--target-min`), tokens only, defaults `type="button"`.
- **`StatusBadge`** (`frontend/src/components/StatusBadge/StatusBadge.tsx`,
  UNCHANGED): kept as-is — its dot+label/7-status/tokens-only shape already
  matched the brief exactly (status never conveyed by color alone; the label
  is the accessible name, not the dot), so it re-skins automatically via the
  new token values with zero code change. Its label-contrast requirement
  (AC3) is covered by `tokens.test.ts` (documented above).
- **`Icon`** (`frontend/src/components/Icon/Icon.tsx`, UNCHANGED): the
  18-glyph feather-style set is already `currentColor`/token-free, so it
  needed no rewrite to fit the new palette; no new glyphs were needed for
  this story's minimal shell (`logo`/`sun`/`moon` already covered the brand
  mark + theme toggle). Extending the set is deferred to whichever
  sprint-56+ story first needs a glyph it doesn't have.
- **`RelativeTime`** (`frontend/src/components/RelativeTime/RelativeTime.tsx`,
  PORTED from `ui-redesign` STORY-098 verbatim): a `<time dateTime>` whose
  text is `formatRelativeTime` ("4m ago"/"in 2h", ticking forward at least
  once a minute) and whose `title` carries the absolute-local time + raw
  ISO-UTC instant. Depends on the newly-ported `lib/formatTime.ts` below.
- **Salvage-ported `lib/` logic** (`design-brief.md` §Salvage — ported
  VERBATIM from `ui-redesign`, with their tests, per the 2026-07-18 PO
  directive; design-agnostic, review-approved on the parked line):
  `lib/formatTime.ts` (`formatRelativeTime`/`formatAbsoluteLocal`/
  `formatTooltip`/`formatLocalRange`/`useRelativeTime` — the shared
  relative/absolute time formatting contract, invalid input always falls
  back to the raw string, never throws), `lib/formatLocation.ts`
  (`formatLocationLabel` — shortens any vendor location id to "Location
  ...tail", generically off the trailing 4 characters, no vendor-specific
  mapping), `lib/useMediaQuery.ts` (a hand-rolled `matchMedia` subscription
  hook — no new dependency for a single listener), `lib/breakpoints.ts`
  (`BREAKPOINT_TABLET_MAX_PX = 1024` / `BREAKPOINT_MOBILE_MAX_PX = 768` +
  their `QUERY_*_DOWN` media-query strings — the shared JS-side breakpoint
  source of truth STORY-104's hamburger-sheet nav will consume), and
  `test/matchMedia.ts::stubMatchMedia` (a live-updatable `matchMedia` stub
  for any test needing to simulate a viewport crossing a breakpoint, not
  just a static initial value).

### Minimal placeholder shell (STORY-103 AC5 — STORY-104 builds the real one)
- `frontend/src/AppShell.tsx` is now a MINIMAL top-bar-stub shell: a
  `<header>` (brand — `Icon name="logo"` + "Uptime Monitor" — and a theme
  toggle button whose `aria-label`/icon reflect the CURRENT theme, e.g.
  "Switch to light theme" + a moon glyph while dark) plus a routed
  `<main id="main-content">`. `frontend/src/nav/tabs.ts`'s `TABS` array
  (UNCHANGED — still the single six-tab source of truth: Dashboard ·
  Availability · Approvals · Check History · Maintenance · Publications,
  each carrying `path`/`label`/`icon`) drives the `<Routes>` — each tab
  renders `frontend/src/pages/PlaceholderPage.tsx` (NEW: a `Tile` with one
  `<h1>` {label} + "Rewrite in progress" copy — one real level-one heading
  per route, the a11y floor). An unknown path renders
  `frontend/src/pages/NotFoundPage.tsx` (re-skinned onto `Tile`, same job as
  before: a heading + a link back to `/`). A skip link (`#main-content`
  target) is still present (a11y floor, cheap to keep even in the minimal
  shell). **There is currently NO visible tab-navigation UI** (no sidebar,
  no horizontal tab bar) — routes are only reachable by direct
  URL/programmatic navigation until STORY-104 builds the real "top command
  bar + horizontal tab nav" per the brief's IA section.
- **DELETED, PO-ordered full rewrite (STORY-103):** `nav/Sidebar.{tsx,css}`,
  `nav/TopBar.{tsx,css}`, `nav/SampleModeBanner.{tsx,css}`,
  `nav/sidebarState.ts` (the STORY-056 collapsible-icon-sidebar shell,
  including the sample-mode trigger switch/chip and its dismissible banner)
  and all SIX per-tab pages (`pages/{Dashboard,Approvals,Availability,
  CheckHistory,Maintenance,Publications}Page.{tsx,css}` — the STORY-057-062
  "Operator Dashboard" Wave-2 rebuilds) plus `features/approvals/
  ApprovalCard.{tsx,css}` (the old Button-variant-dependent Approvals card
  presentation). **Consequence for sample-mode:** the frontend sample-mode
  switch/banner integration described in [[sample-mode]] is TEMPORARILY
  ABSENT from the routed app — `AppShell.tsx` no longer calls
  `useSampleMode()` or renders any switch/banner at all. The HOOK itself
  (`features/dashboard/useSampleMode.ts`) and its test are untouched and
  still green; STORY-104 Step 3 ("sample-mode switch/chip/banner, ported
  contracts") re-wires it into the new shell. See [[sample-mode]] for the
  full detail.

### Surviving feature hooks (logic UNCHANGED, presentation gone — orphaned until their tab's rewrite story)
Every file below still exists, is still unit/hook-tested against MSW exactly
as before, and is NOT currently imported by any routed page (their pages were
deleted, see above). They are documented here so a sprint-56+ implementer
rebuilding a tab knows this logic already exists and does not need
reinventing:
- **Dashboard:** `features/dashboard/useComponents.ts`
  (`useFetch(getComponents)`), `features/dashboard/summary.ts::
  summarizeComponents` (real up/degraded/partial/down bucket counts),
  `features/dashboard/useTopology.ts` (`useFetch(getTopology)`),
  `features/dashboard/useComponentUptime.ts` (combines the rollup
  `availability_pct` with a `buildUptimeSegments` sparkline, capped at 30
  segments, never rejects — a per-component failure degrades gracefully),
  `features/dashboard/useComponentSignals.ts` (latest-per-location signal
  rows, a zero-observation signal renders an honest `'missing'` row),
  `features/dashboard/useMaintenanceWindows.ts` (`useFetch(getMaintenance)`),
  `features/dashboard/useSampleMode.ts` (load+mutate-in-one-hook; see the
  sample-mode note above).
- **Approvals:** `features/approvals/useApprovals.ts`
  (`useFetch(getApprovals)`), `features/approvals/severity.ts::
  deriveSeverity` (maps `to_status` onto the 7-status health tokens),
  `features/approvals/decisionState.ts` (the idle -> confirming ->
  submitting -> failed state machine + its per-card narrowing type). The
  rendering component (`ApprovalCard.tsx`) is the one piece of this feature
  actually DELETED (see above) since it was pure presentation coupled to
  the old `Button` variant set.
- **Availability:** `features/availability/{windowRange,useAvailability,
  format,segments}.ts` — the 24h/7d/30d window-to-range conversion, the
  topology+per-component fetch/merge, `availabilityBand`/`formatDownLabel`/
  `isCompletenessLow`, and the sparkline-segment builder.
- **Check History:** `features/history/{observationHealth,signals,
  filterHistory,mergeObservations,useAllHistory}.ts` — the system-wide
  per-signal-parallel-fetch-and-merge ledger, the client-side filter
  toolbar logic, and the separate observation-vocabulary health mapper.
- **Publications:** `features/publications/usePublications.ts` — the
  simplest read hook, `useFetch(getPublications)`.
- **Maintenance:** `features/maintenance/{windowState,fieldError,
  useMaintenance}.ts` — the half-open upcoming/active/past window-state
  derivation, the 422-detail-to-field mapper, and the load+mutate hook.
- **Shell:** `features/shell/useApprovalsBadge.ts` — the Approvals
  pending-count badge fetch (`useFetch(getApprovals)`), currently unused
  since the minimal shell has no nav UI to badge; STORY-104 will likely
  re-wire it into the new top command bar.

### Typed API client, actor seam, test boundary, shared fetch (UNCHANGED by the rewrite)
- **Typed API client:** `frontend/src/api/client.ts` — fetch-based, single
  `/api` base-URL seam. `getJson`/`postJson`/`putJson` all funnel through a
  shared `readOkJson(response, path)` giving ONE uniform `ApiError` contract
  (network rejection, non-2xx with `.status`, malformed-2xx-body
  `SyntaxError`, plus an optional best-effort `.detail` parse of a 422 JSON
  body). Endpoint fns: `getComponents`, `getApprovals`,
  `postDecision(proposalId, body)`, `getTopology`,
  `getComponentAvailability(componentId, { since, until })`,
  `getSampleMode()`/`putSampleMode(enabled)`, `getHistory({ signal_key,
  since, until })` (server accepts an optional `limit` cap since STORY-094;
  this client deliberately does not send it — the render-side cap stays
  authoritative), `getPublications()`, `getMaintenance()`/
  `postMaintenance(body)`. DTO types in `frontend/src/api/types.ts` mirror
  the backend `api/v1/*/models.py` shapes.
  `frontend/src/api/statusMapping.ts::toHealthStatus` is the authoritative
  map from the backend `ComponentStatus` vocabulary onto the 7 health tokens
  (`operational`->`up`, `degraded`->`degraded`, `partial_outage`->`partial`,
  `major_outage`->`down`, else->`unknown`). A SECOND, deliberately separate
  mapper, `features/history/observationHealth.ts::observationHealth`, maps
  the OBSERVATION vocabulary (`ObservationDTO.health`) onto the same tokens
  — the two mappers' input vocabularies overlap only on `"degraded"`, kept
  separate so a future contract change to either never ripples into the
  other.
- **Actor seam (auth deferred):** `frontend/src/api/actor.ts::getActor()`
  returns a fixed placeholder (`"dashboard-operator"`) — the single
  swap-point for real identity when STORY-017 auth lands.
- **Test I/O boundary:** MSW is the ONLY mocked edge. Handlers are
  modularized per feature (`frontend/src/mocks/handlers/<feature>.ts`)
  composed into `mocks/handlers/index.ts`, registered by `mocks/server.ts`
  (wired in `frontend/src/test/setup.ts`). All eight handler modules survive
  untouched — the deleted pages were their CONSUMERS, not their producers;
  every hook above still exercises its handler directly via
  `renderHook`/MSW.
- **Shared fetch machinery:** `frontend/src/lib/useFetch.ts::useFetch<T>` —
  the single home of the read-fetch state machine (`{ state, retry }` over a
  `loading|error|success` discriminated union, a cancelled-guarded effect,
  an `attempt`-keyed `retry`). `fetcher` MUST be a stable reference. Every
  surviving hook above still builds on it — unchanged, untouched, still the
  foundation the sprint-56+ rebuilds will keep composing from.
- **Shared classname helper:** `frontend/src/lib/cx.ts::cx(...)` — filters
  falsy parts, joins on a space. Used by every primitive, old and new.

## Inference (synthesis, not verified)
- **Pre-rewrite (STORY-055-062), still expected to hold for the sprint-56+ rebuilds since the
  hooks themselves are untouched:** the shared append-points a tab story edits are `api/types.ts` +
  `api/client.ts` (its DTO + `getX()`/`postX()`) and a new `mocks/handlers/<feature>.ts`; the
  routing table, MSW composition, and the shared `useFetch<T>` are structured for additive-only
  edits, so sequential tab stories don't collide. **The shared `useFetch<T>` is STILL the
  foundation every surviving read hook builds on** — a read tab with NO selector/args is a thin
  `useFetch(getX)`; one WITH a selector wraps its parameterized call in `useCallback` keyed on a
  caller-memoized arg object; a compound key (`[topology, range]` / `[signals, range]`) needs no
  `useFetch` change either. The one sharp edge to watch is still the stable-`fetcher`-reference
  rule. A future mutating tab can likely reuse the Approvals `decisionState.ts` state-machine +
  `ApiError.status`-branching pattern rather than re-inventing it — NOT YET RE-VERIFIED against an
  actual STORY-103+ rebuilt page, since none exists yet on this branch.
- A sprint-56+ per-tab rewrite story will likely need to decide: does the new page render inside a
  `Tile` (bento-grid placement) or reuse `Panel`/`Table` for tabular data, or some mix? STORY-103
  deliberately left this open — the brief's dashboard description ("asymmetric grid: hero tile,
  per-component tiles, action tiles, feed tile") suggests `Tile` for Dashboard specifically, but
  Check History's dense ledger may still want `Table`. NOT VERIFIED — a design decision for those
  stories, not this one.

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
- sprint-55 (STORY-103, PO-ordered full UI rewrite — "Mission Teal", REWRITE ERA begins): rebuilt
  `styles/tokens.css` v2 (dark-first + full light theme, new spacing/radius/shadow/z/motion
  scales, `tokens.test.ts` contract tests incl. WCAG contrast checks) and `styles/global.css`
  (self-hosted Space Grotesk/Inter/JetBrains Mono replacing Geist/Geist Mono, a
  `prefers-reduced-motion` guard); made the theme engine dark-first
  (`resolveTheme.ts::getSystemTheme` now checks both media queries explicitly, defaulting to dark
  only when NEITHER matches; `index.html`'s pre-paint script mirrors it); rewrote `Button` (new
  primary/ghost/danger variants + a `loading` state) and added three new primitives — `Tile`
  (the bento-card base unit), `RelativeTime`, and the salvage-ported `lib/{formatTime,
  formatLocation,useMediaQuery,breakpoints}.ts` + `test/matchMedia.ts` (verbatim from the parked
  `ui-redesign` branch's STORY-096/098, review-approved there); left `StatusBadge`/`Icon`/`Panel`/
  `LoadingState`/`EmptyState`/`Table`/`UptimeBar`/`SummaryCard`/`Timeline` UNCHANGED (already
  token-only, re-skin automatically). DELETED the entire STORY-056 sidebar/topbar/
  sample-mode-banner shell and all six STORY-057-062 per-tab pages (`pages/*Page.{tsx,css,
  test.tsx}`) plus `features/approvals/ApprovalCard.{tsx,css}` — replaced with a MINIMAL
  placeholder `AppShell.tsx` (brand + theme toggle top bar, one `PlaceholderPage`/`Tile` per
  route via the unchanged `nav/tabs.ts`). Every other feature hook (`features/{dashboard,
  approvals,availability,history,maintenance,publications,shell}/*.ts`, excluding
  `ApprovalCard.tsx`) and the entire `api/`/`mocks/` layer are UNTOUCHED and still green — see the
  new "Surviving feature hooks" Facts subsection. Frontend suite: 372 tests / 47 files, all green;
  `npm run build`/`npm run lint` both exit 0. Backend diff is empty except the cherry-picked
  `pyproject.toml` `.claude`-ruff-exclude line (see [[dev-setup-and-dod]]/[[architecture-boundary]]/
  [[config-layer]]/[[api-five-file-convention]]). `code_refs` heavily re-scoped: removed every
  deleted file path, added `components/Tile/Tile.tsx`, `components/RelativeTime/RelativeTime.tsx`,
  `lib/{formatTime,formatLocation,useMediaQuery,breakpoints}.ts`, `test/matchMedia.ts`,
  `pages/PlaceholderPage.tsx`, `styles/global.css`, and `docs/scrum/ui-rewrite/design-brief.md`
  (the new design authority, replacing `DESIGN-linear.app.md`). verified_sha = 52f1706.

