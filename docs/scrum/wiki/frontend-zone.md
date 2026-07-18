---
title: Frontend zone — the operator-cockpit SPA (shell)
code_refs: [frontend/package.json, frontend/vite.config.ts, frontend/index.html, frontend/src/AppShell.tsx, frontend/src/nav/tabs.ts, frontend/src/nav/CommandBar.tsx, frontend/src/nav/TabNav.tsx, frontend/src/nav/StatusDot.tsx, frontend/src/nav/NavSheet.tsx, frontend/src/nav/useNavSheet.ts, frontend/src/nav/SampleModeSwitch.tsx, frontend/src/nav/SampleModeChip.tsx, frontend/src/nav/SampleModeBanner.tsx, frontend/src/nav/useDismissibleBanner.ts, frontend/src/features/shell/deriveOverallStatus.ts, frontend/src/pages/PlaceholderPage.tsx, frontend/src/pages/NotFoundPage.tsx, frontend/src/pages/DashboardPage.tsx, frontend/src/pages/AvailabilityPage.tsx, frontend/src/pages/ApprovalsPage.tsx, frontend/src/features/shell/useApprovalsBadge.ts, frontend/src/api/client.ts, frontend/src/api/types.ts, frontend/src/api/statusMapping.ts, frontend/src/api/actor.ts, frontend/src/theme/resolveTheme.ts, frontend/src/theme/ThemeContext.tsx, frontend/src/styles/tokens.css, frontend/src/styles/global.css, frontend/src/components/index.ts, frontend/src/components/Tile/Tile.tsx, frontend/src/components/Button/Button.tsx, frontend/src/components/StatusBadge/StatusBadge.tsx, frontend/src/components/StatusBadge/labels.ts, frontend/src/components/Icon/Icon.tsx, frontend/src/components/RelativeTime/RelativeTime.tsx, frontend/src/components/Table/Table.tsx, frontend/src/components/UptimeBar/UptimeBar.tsx, frontend/src/components/SummaryCard/SummaryCard.tsx, frontend/src/components/Timeline/Timeline.tsx, frontend/src/components/LatencySpark/LatencySpark.tsx, frontend/src/lib/cx.ts, frontend/src/lib/useFetch.ts, frontend/src/lib/formatTime.ts, frontend/src/lib/formatLocation.ts, frontend/src/lib/useMediaQuery.ts, frontend/src/lib/breakpoints.ts, frontend/src/test/matchMedia.ts, frontend/src/mocks/handlers/index.ts, frontend/src/mocks/handlers/components.ts, frontend/src/mocks/handlers/approvals.ts, frontend/src/mocks/handlers/availability.ts, frontend/src/mocks/handlers/sampleMode.ts, frontend/src/mocks/handlers/history.ts, frontend/src/mocks/handlers/publications.ts, frontend/src/mocks/handlers/maintenance.ts, frontend/src/features/dashboard/useComponents.ts, frontend/src/features/dashboard/useMaintenanceWindows.ts, frontend/src/features/dashboard/useSampleMode.ts, frontend/src/features/dashboard/summary.ts, frontend/src/features/dashboard/useTopology.ts, frontend/src/features/dashboard/useComponentSignals.ts, frontend/src/features/dashboard/useComponentUptime.ts, frontend/src/features/dashboard/latencyPoints.ts, frontend/src/features/dashboard/maintenanceSummary.ts, frontend/src/features/approvals/useApprovals.ts, frontend/src/features/approvals/severity.ts, frontend/src/features/approvals/decisionState.ts, frontend/src/features/approvals/useProposalEvidence.ts, frontend/src/features/approvals/useApprovalsTopology.ts, frontend/src/features/approvals/ApprovalCard.tsx, frontend/src/features/availability/windowRange.ts, frontend/src/features/availability/useAvailability.ts, frontend/src/features/availability/format.ts, frontend/src/features/availability/segments.ts, frontend/src/features/history/observationHealth.ts, frontend/src/features/history/signals.ts, frontend/src/features/history/filterHistory.ts, frontend/src/features/history/mergeObservations.ts, frontend/src/features/history/useAllHistory.ts, frontend/src/features/publications/usePublications.ts, frontend/src/features/maintenance/windowState.ts, frontend/src/features/maintenance/fieldError.ts, frontend/src/features/maintenance/useMaintenance.ts, frontend/src/test/setup.ts, docs/scrum/ui-rewrite/design-brief.md, frontend/eslint.config.js, design-system/uptime-monitor-v3-rewrite/MASTER.md, DESIGN-linear.app.md, frontend/src/styles/tokens.test.ts]
verified_sha: bb7644e
verified_sprint: sprint-57
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
- **Theme engine, STORED CHOICE > DARK, period** (`frontend/src/theme/
  resolveTheme.ts`; corrected at the STORY-103 REALITY GATE, 2026-07-18 —
  superseding an earlier in-story attempt that still consulted
  `prefers-color-scheme`): `resolveInitialTheme()` is now
  `getStoredTheme() ?? 'dark'` — the OS/browser `prefers-color-scheme` is
  NEVER read. Rationale: most headless/desktop systems report
  `prefers-color-scheme: light` by default, so honoring it would make the
  common first impression light and defeat the brief's dark-first
  mission-control identity; the user's own explicit toggle (persisted) is
  the only thing that can ever move the app to light. `getSystemTheme()` was
  REMOVED entirely (dead code once system preference is never consulted).
  `frontend/index.html`'s inline pre-paint script mirrors the same
  two-branch rule (stored -> that value, else `'dark'`) so there is still no
  flash of the wrong theme before first paint — the two implementations are
  DELIBERATELY duplicated (the script must run before any module loads).
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

### The real app shell (STORY-104 — replaces STORY-103's minimal top-bar-stub)
`frontend/src/AppShell.tsx` now composes the design brief's §IA shell exactly:
a slim top `CommandBar` (brand + live overall-status dot + horizontal `TabNav`
+ the mode-controls right cluster), a dismissible `SampleModeBanner`, the
mobile `NavSheet` overlay, and a routed `<main id="main-content">`. There is
NO left sidebar anywhere in the DOM (design brief §IA, "deliberately
different from the old shell") — `AppShell.test.tsx` asserts no `<aside>`/
`.sidebar` element exists on any route. `frontend/src/nav/tabs.ts`'s `TABS`
array is UNCHANGED (still the single six-tab source of truth); each tab still
renders `frontend/src/pages/PlaceholderPage.tsx` (a per-tab rewrite is
sprint-56+'s job, not this story's) via the same `<Routes>` shape. `AppShell`
calls `useComponents()` and `useSampleMode()` each exactly ONCE and threads
their results down as props — never a second independent hook call anywhere
in the tree — so every consumer of a given fetch (the status dot, the
"Updated Xs ago" text, the switch, the banner, the chip) agrees about its
current state on the same render.
- **`nav/CommandBar.tsx`** (NEW): the top bar itself. Left to right: an
  optional hamburger menu-trigger button (`aria-label="Open navigation
  menu"`, JS-conditional on `showMenuTrigger` — never CSS-only, so a test can
  assert its absence at desktop widths the same way the ported
  `SidebarDrawer`'s `showMenuTrigger` prop always worked); the brand block
  (`Icon name="logo"` + "Uptime Monitor" text, CSS-hidden at <=480px — see
  the 390px note below — + the `StatusDot`); the horizontal `TabNav`
  (`flex: 1`, CSS-hidden at <=768px, `BREAKPOINT_MOBILE_MAX_PX` hardcoded in
  CSS per the existing `lib/breakpoints.ts` convention); and the right
  cluster (`margin-left: auto`): the persistent `SampleModeChip` (only when
  `showSampleChip`), `SampleModeSwitch`, the theme toggle (`useTheme()`
  called directly here, same as the old `TopBar`), and "Updated
  `<RelativeTime>`" (only once `fetchedAtIso` is set).
- **`nav/TabNav.tsx`** (NEW): the six routed `NavLink`s, icon + VISIBLE text
  label always together (ui-ux-pro-max Navigation guideline: never icon-only
  in a top bar) — react-router's `NavLink` sets `aria-current="page"`
  automatically on the active route (AC1), and the `tab-nav__tab--active`
  class adds a teal underline (`::after`) + a font-weight bump so the active
  tab is never color-only. An `onNavigate` prop (wired to a sheet's close
  handler) lets the SAME component serve both the desktop bar (horizontal,
  `tab-nav` class) and the mobile sheet (vertical, `tab-nav--sheet` class
  modifier) without duplicating the tab list.
- **`nav/StatusDot.tsx`** + **`features/shell/deriveOverallStatus.ts`** (NEW,
  AC2): `deriveOverallStatus(components: ComponentDTO[]): HealthStatus` is
  the worst-of reducer over a fixed `down > partial > degraded > maintenance
  > unknown > missing > up` rank table (the brief's exact ordering,
  `toHealthStatus` never itself producing `maintenance`/`missing` today — the
  table is total over the whole vocabulary for future-proofing); an EMPTY
  component list returns `'unknown'` (no signal to assess, never a
  fabricated "all up" — the explicit, tested empty-input case). `StatusDot`
  renders a decorative colored dot (`aria-hidden`) plus an `.sr-only`
  "Overall status: {label}" text — deliberately NOT a reuse of `StatusBadge`
  (whose label is always VISIBLE, a table/list-cell shape too wide for a
  slim top bar); `undefined` (loading) renders as "Unknown".
- **`features/dashboard/useComponents.ts`** gained an ADDITIVE
  `fetchedAtIso: string | undefined` field (STORY-104, "Updated Xs ago"):
  tracked via the "compare a mirrored previous-`phase` state during render"
  pattern (same as `useDismissibleBanner`/`useMediaQuery` below — required
  by `eslint-plugin-react-hooks`'s `set-state-in-effect` rule), stamping
  `new Date().toISOString()` every time `state.phase` transitions INTO
  `'success'`. Display-layer only — never persisted, never sent to the
  server, not part of the `ComponentDTO` wire shape; every other consumer of
  `useComponents()`'s existing `{ state, retry }` shape is unaffected.
- **Sample-mode re-wired into the shell (AC3, ported `ui-redesign`
  STORY-056/102 contracts — salvage list, re-skinned onto Mission Teal
  tokens, logic byte-identical):** `nav/SampleModeSwitch.tsx` (the
  `role="switch"`/`aria-checked` trigger, a visible "Sample mode" text label
  at >=768px via `useMediaQuery(QUERY_MOBILE_DOWN)`, neutral OFF /
  degraded-amber ON — never red, which is reserved for the GET-failure retry
  affordance), `nav/SampleModeChip.tsx` (the persistent "SAMPLE" chip,
  clicking it calls `onRestore`), `nav/SampleModeBanner.tsx` (the
  dismissible `role="status"` warning), and `nav/useDismissibleBanner.ts`
  (lifts the dismiss/re-arm state so the chip and the banner can never
  disagree — re-arms whenever `visible` cycles `false -> true`). `AppShell`
  computes `bannerVisible = sampleMode.state.phase === 'success' &&
  sampleMode.enabled === true` and `showSampleChip = bannerVisible &&
  dismissed`, threading both down. `features/dashboard/useSampleMode.ts`
  itself is UNCHANGED — only its caller/wiring moved (STORY-056 -> STORY-104,
  same as the STORY-038 sidebar->STORY-056 topbar move before it).
- **Mobile <=768px hamburger sheet (AC4, ported `SidebarDrawer` focus-trap
  contract — salvage list):** `nav/useNavSheet.ts` (`isMobile` via
  `useMediaQuery(QUERY_MOBILE_DOWN)` + an `open` boolean that auto-closes
  the moment the viewport widens past mobile — the "adjusting state when a
  prop changes" pattern again) and `nav/NavSheet.tsx` (a `role="dialog"
  aria-modal` overlay dropping down from under the command bar — NOT a left
  rail, this IA has no sidebar concept at all — wrapping the SAME `TabNav`
  vertically). Focus management is a straight port of `SidebarDrawer`'s
  contract: focus moves to the sheet's first focusable element (the header's
  "Close navigation" button) on open, returns to the hamburger trigger on
  close regardless of what closed it (Escape, scrim click, the close
  button, or a nav-link activation — `TabNav`'s `onNavigate` wired to
  `onClose`), and a same-sheet Tab/Shift+Tab focus trap never lets keyboard
  focus escape into the page behind the scrim. Enter animation only
  (150-250ms transform/opacity, no exit animation since the sheet unmounts
  entirely while closed, matching the ported contract's "renders nothing (no
  dialog) while closed" test) — both guarded by the existing global
  `prefers-reduced-motion` reset (STORY-103).
- **390px hardening:** at <=480px the command bar hides its lowest-priority
  text (`.command-bar__brand-text`, `.command-bar__updated`) and tightens
  its own padding/gap, so `[hamburger + brand icon/dot + SAMPLE chip +
  switch (icon-only at mobile) + theme toggle]` — the worst-case set of
  simultaneously-visible controls — stays under a 390px viewport with no
  page-level horizontal scroll (AC4); nothing hidden here is a CONTROL, only
  supplementary text.
- **`components/Icon/Icon.tsx`** gained one new glyph, `menu` (three
  horizontal lines, same feather-style stroke), for the hamburger trigger —
  the only `Icon` set change this story needed.
- **DELETED, PO-ordered full rewrite (STORY-103, unchanged by this story):**
  `nav/Sidebar.{tsx,css}`, `nav/TopBar.{tsx,css}`, the OLD
  `nav/SampleModeBanner.{tsx,css}` (STORY-104 ships a NEW same-named
  component at the same path, re-skinned/re-wired — see above),
  `nav/sidebarState.ts`, and all SIX per-tab pages (`pages/{Dashboard,
  Approvals,Availability,CheckHistory,Maintenance,Publications}Page.{tsx,css}`
  — the STORY-057-062 "Operator Dashboard" Wave-2 rebuilds) plus
  `features/approvals/ApprovalCard.{tsx,css}` remain deleted; a per-tab
  rewrite is sprint-56+'s job.

### The Dashboard tab (STORY-105 — bento mission-control page)
`pages/DashboardPage.tsx` (NEW, routed at `/` in `AppShell.tsx` — the one tab
path that no longer renders `PlaceholderPage`) is the first sprint-56+ tab
rewrite, per the design brief §IA "Dashboard = bento" spec: a hero
system-status tile, one tile per monitored component, two action tiles
(pending approvals / maintenance), and a "recent checks" feed tile, laid out
by `DashboardPage.css`'s mobile-first `.dashboard-grid` (single column at
<768px, two columns at >=768px, an asymmetric 4-column grid with the hero and
feed tiles each spanning a 2x2 block at >=1024px — `grid-auto-flow: row
dense` lets the per-component/action tiles fill the remaining cells at any
count). This RE-WIRES most of the "surviving feature hooks" the STORY-103
rewrite orphaned (see below) rather than reinventing them — the one genuinely
new data-shaping piece is `features/dashboard/latencyPoints.ts::
buildLatencyPoints` (mirrors `features/history/uptimeSegments.ts::
buildUptimeSegments`'s cap-and-reverse shape at a smaller cap,
`MAX_LATENCY_POINTS = 20`, dropping any `latency_ms: null` observation) plus
two ADDITIVE fields on `features/dashboard/useComponentUptime.ts::
ComponentUptime` — `latencyPoints: number[]` and `lastObservedIso: string |
null` — both derived from the SAME per-component `observations` fetch
`segments` already uses, so the per-component tile's latency spark and
"Last observed" `RelativeTime` cost zero extra network calls.
- **`components/LatencySpark/LatencySpark.tsx`** (NEW primitive): an inline
  `<svg role="img">` sparkline (ui-ux-pro-max chart-domain guidance — data
  refreshes ~1/min, so this is a static periodic-refresh visual, never a
  streaming/ticker chart; the point volume is small enough that a hand-rolled
  `<svg>` is correct, no chart library, no new dependency). Renders an
  explicit "No data" state (never a fabricated flat line) for an empty
  series; otherwise a `<polyline>` scaled into a fixed `0 0 100 24` viewBox
  (a flat/single-point series draws a mid-line rather than dividing by a zero
  range), an `aria-label`/`<title>` stating the latest value in words
  ("`<label>`: latest `<n>` ms") — the accessible name, never color/shape
  alone.
- **`features/dashboard/maintenanceSummary.ts::countActiveOrUpcomingWindows`**
  (ported VERBATIM, with its test, from the parked `ui-redesign` branch's
  STORY-099 — design brief §Salvage instruction): counts
  `MaintenanceWindowDTO`s currently `'active'` or `'upcoming'` per
  `features/maintenance/windowState.ts::deriveWindowState`'s existing
  half-open rule (never re-derived) — backs the Maintenance action tile's
  count. An empty list returns `0`.
- **Hero tile:** `features/shell/deriveOverallStatus.ts` (STORY-104's
  worst-of reducer, REUSED here — not re-derived) over `useComponents()`'s
  data, rendered as a large `--font-heading` KPI word (a page-local
  `HERO_STATUS_LABELS` map, matching `StatusBadge`'s own label text) plus a
  `StatusBadge` (never color-only) and an honest "N of M components
  operational" subline (an empty component list falls back to "No
  components configured", never a fabricated count).
- **Per-component tiles:** `useComponents()` (health/name) joined against
  `useTopology()` (by `component.id`, for the primary signal's `signal_key`)
  and `useComponentUptime(topology, range)` (pct/segments/latencyPoints/
  lastObservedIso) over a FIXED 24h window (`windowToRange('24h')`, memoized
  once — there is no window selector on this tab, that is Availability's
  job). A component with a primary signal renders as a whole-tile `Tile
  href="/check-history?signal=<signal_key>"` link (STORY-106+ will build the
  page this points at); a component with no topology signals (still loading,
  or genuinely zero signals) renders the SAME content as a plain
  non-interactive tile rather than a broken link — graceful degradation,
  mirroring the pre-rewrite Dashboard's convention.
- **Action tiles:** "Pending approvals" reads `features/shell/
  useApprovalsBadge.ts` (now WIRED — see the updated Shell bullet below);
  "Maintenance" reads `useMaintenanceWindows()` + `countActiveOrUpcomingWindows`
  directly (not the badge hook) since it needs the FULL `FetchState` to show
  a genuine error+retry branch, which `useApprovalsBadge`'s collapsed
  `number | undefined` contract cannot distinguish from loading — the
  Approvals tile's `count === undefined` case (loading OR a fetch failure,
  per that hook's own documented contract) renders a loading affordance
  rather than a blank tile, a known, accepted limitation of reusing that
  specific orphaned hook as directed (candidate: give it a distinguishable
  error state in a future story). Both tiles are whole-tile links (`Tile
  href`), neutral (no accent class) at count `0`, teal-accented
  (`.dashboard-grid__action--active`) at count `> 0` — the count and its
  sublabel ("open" / "active or upcoming") are always visible text, so the
  accent is a reinforcing cue, never the sole one.
- **Feed tile:** `features/history/useAllHistory(range)` (the SAME fixed 24h
  range) — the latest 8 rows (`RECENT_CHECKS_LIMIT`) of its newest-first,
  system-wide merged ledger, each row a `StatusBadge`
  (`observationHealth`) + component name + `formatLocationLabel` (never the
  raw vendor location id) + latency (a page-local `formatLatency`, em-dash
  for `null`) + `RelativeTime` (never a raw ISO string as visible text — the
  raw instant only ever appears in the `<time dateTime>` attribute/tooltip).
  An empty result renders `EmptyState` ("No checks recorded yet").
- **Per-tile fault isolation (AC4):** every tile's data comes from an
  INDEPENDENT fetch (`useComponents`/`useTopology`/`useComponentUptime`/
  `useApprovalsBadge`/`useMaintenanceWindows`/`useAllHistory`) — a components
  fetch failure surfaces as the hero tile's OWN `ErrorState` + retry while
  the action/feed tiles keep rendering their real data; a maintenance or
  history fetch failure surfaces as THAT tile's own `ErrorState` + retry
  without touching any other tile; a topology fetch failure degrades every
  component tile to its non-link, no-uptime-data shape (never blanks the
  page). `LoadingState` is reused for every tile's loading skeleton — its
  spinner is already `prefers-reduced-motion`-guarded globally
  (`global.css`, STORY-103), so no new reduced-motion plumbing was needed.
  `DashboardPage.test.tsx` proves each of these fault-isolation paths
  individually (components/maintenance/history/topology/approvals failures,
  each asserted NOT to blank sibling tiles).
- **`AppShell.test.tsx`'s existing "Dashboard placeholder" assertions are
  UNCHANGED** — `DashboardPage`'s own `<h1>` text is still exactly
  `"Dashboard"` (matching `nav/tabs.ts`'s tab label), so the shell-level
  routing tests needed no edits.

### The Availability tab (STORY-106 — windowed uptime vs completeness, new skin)
`pages/AvailabilityPage.tsx`/`.css` (NEW, routed at `/availability` in
`AppShell.tsx` — the second tab, after Dashboard, that no longer renders
`PlaceholderPage`) is the STORY-106 rewrite of the STORY-058/015d
incarnation: one `<h1>Availability</h1>`, a subtitle, a 24h/7d/30d window
switcher in the page header, a legend, and one `Tile` per topology
component — an Availability metric (%, colored by `availabilityBand`, +
the "down" sublabel + the windowed `UptimeBar` sparkline) and a Data
completeness metric, expandable to per-signal drill-down rows. RE-WIRES the
surviving `features/availability/{windowRange,useAvailability,format,
segments}.ts` hooks VERBATIM (design brief §Salvage: "re-skin freely; keep
the tested behavior") — no hook-level change, only the presentation layer
is new.
- **Header + window switcher (AC1):** `WindowSwitcher` (a page-local
  component, not a new shared primitive — a single `role="group"` button
  set is this page's only consumer) renders the three `WindowPreset` values
  as real `<button>`s (`>= 44px` via `--target-min`, natively keyboard-
  operable), the active preset carrying `aria-pressed="true"` (never color
  alone — the active class also bumps background/font-weight). `preset`
  state lives in the page; `range = useMemo(() => windowToRange(preset),
  [preset])` keeps `useAvailability`'s fetcher identity stable while the
  selection is unchanged and gives it a NEW identity (triggering a refetch)
  exactly when the preset changes — the SAME memoization contract the
  parked `ui-redesign` `AvailabilityPage` used, unchanged.
- **Legend (AC2):** `AvailabilityLegend` renders a solid swatch + "Down /
  outage" and a HATCHED swatch (the exact same `repeating-linear-gradient`
  `UptimeBar.css`'s missing-segment fill uses, duplicated here as a static
  swatch rather than imported, since it is not an interactive bar) + "Missing
  data" — pattern plus text, never color alone.
- **Availability + Data completeness metrics (AC2):** `AvailabilityMetric`
  (the large `--fs-stat` JetBrains Mono % + `formatDownLabel`'s real
  verdict-derived sublabel +, for a rollup row, the `UptimeBar` sparkline;
  `showBar={false}` for a per-signal drill-down row — there is no dedicated
  per-signal history fetch) and `CompletenessMetric` carry the EXACT
  unambiguous phrasing carried from the accepted `ui-redesign` STORY-099
  relabel: the formatted percentage immediately followed by the visible text
  "of expected checks received" (never a separate ambiguous "missing data"
  chip next to a RECEIVED-share number). A `null` completeness (no data at
  all) omits that sub-label entirely — `formatPct`'s own "no data" text is
  the only thing rendered, matching `isCompletenessLow`'s existing contract
  that a null pct is a distinct "no data" condition, not a low-completeness
  warning.
- **Signal-level drill-down (AC3):** `ComponentTile` renders a real
  `<button aria-expanded aria-controls>` toggle (an `Icon name="chevron-
  right"` that rotates 90° when expanded, CSS-only, `prefers-reduced-motion`
  guarded globally) for any component with `topology.signals.length > 0`;
  toggling reveals a `<ul>` of per-signal rows, each its own bar-less
  `AvailabilityMetric` + `CompletenessMetric` pair, signal display name
  sourced from the SAME topology response the rollup used (the availability
  response's per-signal children carry only `signal_key`, no `name` —
  matching the pre-rewrite convention). A zero-signal component renders a
  plain, non-interactive name — no broken expand affordance ever appears.
- **Fault isolation:** unlike `DashboardPage`'s six independent fetches,
  `useAvailability` is ONE merged `useFetch` call (topology +
  `Promise.all(getComponentAvailability)` + `Promise.all` segment history)
  — a single loading/error/empty state covers the whole grid, matching the
  hook's own existing contract (rewired, not rewritten, per the design
  brief's salvage instruction) rather than a new per-component fault-
  isolation shape; the header (h1 + subtitle + window switcher + legend)
  still survives any fetch failure (`ErrorState` + retry replaces only the
  grid). NOT the same fault-isolation granularity Dashboard's bento tiles
  have — a candidate backlog item if per-component independent fetches are
  ever wanted here, out of this story's scope (existing hook contract
  reused, per the brief).
- **`AppShell.test.tsx`** gained one new assertion
  (`'renders the REAL Availability page (not a placeholder) at
  /availability'`) proving the route now renders `AvailabilityPage` rather
  than `PlaceholderPage` — the pre-existing `it.each(TABS)` placeholder-
  heading assertion needed no change (`AvailabilityPage`'s own `<h1>` is
  still exactly "Availability", matching `nav/tabs.ts`'s tab label).

### The Approvals tab (STORY-107 — evidence-first queue, new skin)
`pages/ApprovalsPage.tsx`/`.css` + `features/approvals/ApprovalCard.tsx`/`.css`
(NEW, routed at `/approvals` in `AppShell.tsx` — the third tab, after
Dashboard and Availability, that no longer renders `PlaceholderPage`) is the
STORY-107 rewrite of the STORY-059/015c incarnation, re-skinning the
evidence-first concept design brief §Salvage names as review-APPROVED on the
parked `ui-redesign` branch (its STORY-100 work, itself never merged past
`sprint-54` — the PO's full-rewrite pivot parked that branch mid-review): a
severity-accented `Tile` per open proposal, the `from_status -> to_status`
transition, per-location "latest result" evidence rows, a "View checks" deep
link, and the idle -> confirming -> submitting -> failed decision flow with
an approve-confirm consequence copy.
- **Two hooks PORTED verbatim from `ui-redesign`'s (unmerged, parked)
  `sprint-54` line, unchanged in logic** — `features/approvals/
  useProposalEvidence.ts::useProposalEvidence`/`latestPerLocation` (a small
  server-side-capped `GET /api/v1/history` call — `EVIDENCE_HISTORY_LIMIT =
  20` — collapsed to one row per distinct location, the FIRST observation
  seen for a location being its latest since the wire order is newest-first;
  `signalKey === undefined` short-circuits to an always-successful empty
  result rather than blocking the card) and `features/approvals/
  useApprovalsTopology.ts::useApprovalsTopology` (a thin `useFetch(getTopology)`
  wrapper, kept as ITS OWN file rather than reusing `features/dashboard/
  useTopology.ts` so the Approvals tab's topology usage evolves
  independently). `ProposalDTO` carries no `signal_key` on the wire (a
  proposal is per-COMPONENT) — the card resolves `signalKey` from the
  joined topology component's PRIMARY (first) signal, the SAME
  single-signal adaptation `features/dashboard/useComponentUptime.ts`
  already uses for the identical reason (documented precedent, per the
  dispatch brief).
- **`api/client.ts::getHistory` gained an ADDITIVE optional `limit` query
  param** (STORY-094 added server-side `limit` support; this is the FIRST
  client caller to send it — the existing Check History caller still
  deliberately omits it, unchanged). Omitted entirely when not given, never
  sent as `"undefined"`.
- **`components/StatusBadge/labels.ts` (NEW)** — `DEFAULT_LABELS`/
  `defaultStatusLabel` extracted OUT of `StatusBadge.tsx` into their own
  non-component module (a quality fix ported from the same parked
  `ui-redesign` line, where it cleared exactly this same
  `react-refresh/only-export-components` lint warning): `StatusBadge.tsx`
  imports `DEFAULT_LABELS` from here for its own internal default; both are
  still re-exported through `components/index.ts` unchanged for existing
  callers. `defaultStatusLabel` feeds the approve-confirm consequence copy
  below — the SAME word the transition `StatusBadge` already renders for
  the target status, never a second vocabulary.
- **`features/approvals/decisionState.ts` gained `confirmPrompt`/
  `ConfirmContext`/`CONFIRM_LABEL`** (replacing the previous, unused
  `CONFIRM_COPY` — no other consumer existed): approve's confirm step now
  states the publish consequence explicitly — `"Publishes '<component>:
  <target status>' to the public status page."` — built from the joined
  topology's friendly component name and `defaultStatusLabel`; reject's
  prompt is UNCHANGED ("Reject this proposal?", since a reject never
  touches the public status page). `severity.ts::deriveSeverity` and
  `useApprovals.ts` were untouched by this story (already correctly shaped).
- **`ApprovalCard.tsx`** renders as a `Tile` (`elevation="md"`,
  `accent={severity.tone}` — reusing `Tile`'s own colored-left-edge
  affordance rather than a bespoke stripe, unlike the pre-rewrite
  `ApprovalCard.css`'s own `.approval-card__stripe`): friendly component
  name + the raw `component_id` as a mono secondary slug (falls back to the
  slug for BOTH when topology hasn't resolved, AC4), a severity chip, the
  from -> to `StatusBadge` transition (`from_status === null` renders "New"
  instead of a badge), "Proposed `<RelativeTime>`", per-location evidence
  rows (short location label + `StatusBadge` + latency + `RelativeTime`), a
  static pulsing skeleton while evidence loads (`prefers-reduced-motion`
  guarded), a quiet "Evidence unavailable" line on a fetch failure with
  Approve/Reject STILL rendered and actionable (AC4), "No recent checks
  recorded" on a genuine empty result, and — when a primary signal resolved
  — a "View checks" `Link` to `/check-history?signal=<signal_key>` (AC2;
  Check History's rewrite, STORY-108, is what actually consumes the param —
  this story lands the link contract against the still-placeholder page,
  which ignores query params harmlessly). Approve (`primary`)/Reject
  (`ghost`) in the idle phase; on confirm, the SAME two buttons persist with
  the Confirm button's `loading` prop true during `'submitting'` (spinner +
  `aria-busy` + disabled, label still visible — `Button`'s own STORY-103
  contract) and Cancel disabled alongside it (can't dismiss mid-request); a
  `'failed'` decision renders the shared `ErrorState` + retry.
- **`ApprovalsPage.tsx`** owns the page-level `DecisionUiState` (only one
  proposal mid-decision at a time) and the 409 ("already been resolved")/404
  ("no longer exists") notice banner (`role="status"`, not scoped to a
  single card) — carried over unchanged in behavior from the STORY-015c/059
  incarnation, only the markup is new. A topology fetch failure/loading tick
  degrades every card to its raw `component_id` slug and no evidence — never
  blocks the queue (AC4) — by joining against an empty `{}` map rather than
  surfacing its own error state on this page. The "Queue clear" empty state
  (`EmptyState` message + "No proposals awaiting review." detail) and the
  loading/error states are each wrapped in a plain `Tile` (mirroring
  `AvailabilityPage`'s convention for non-card content) rather than the
  pre-rewrite `Panel`.
- **`AppShell.test.tsx`** gained one new assertion (`'renders the REAL
  Approvals page (not a placeholder) at /approvals'`); the pre-existing
  `it.each(TABS)` placeholder-heading assertion needed no change
  (`ApprovalsPage`'s own `<h1>` is still exactly "Approvals").
- **Deferred to the sprint-57 AC4 "live pass" step** (not part of this
  implementer dispatch's scope, per the dispatch's own numbered
  IMPLEMENTATION SHAPE, which enumerated Steps 1-5 only): a live sample-mode
  proposal round-trip (evidence rows vs the real API, the confirm copy,
  reject, sample mode off after) against a running local stack. NOT YET
  LIVE-VERIFIED on this line — a candidate follow-up, not a contradiction of
  anything Facts above state (all of which are unit/hook/component-test
  verified against MSW).

### Surviving feature hooks (logic UNCHANGED, presentation gone until their tab's rewrite story)
Every file below still exists and is still unit/hook-tested against MSW
exactly as before. Files marked "wired" below ARE now imported by a routed
page (the shell, or `DashboardPage` as of STORY-105); the rest are still
genuinely orphaned, documented here so a sprint-56+ implementer rebuilding a
tab knows this logic already exists and does not need reinventing:
- **Dashboard:** `features/dashboard/useComponents.ts`
  (`useFetch(getComponents)`, PLUS the STORY-104 additive `fetchedAtIso`),
  `features/dashboard/useSampleMode.ts` (load+mutate-in-one-hook — called by
  the shell, STORY-104), `features/dashboard/useTopology.ts`
  (`useFetch(getTopology)`), `features/dashboard/useComponentUptime.ts`
  (combines the rollup `availability_pct` with a `buildUptimeSegments`
  sparkline capped at 30 segments PLUS the STORY-105 additive
  `latencyPoints`/`lastObservedIso` fields, never rejects — a per-component
  failure degrades gracefully), and `features/dashboard/
  useMaintenanceWindows.ts` (`useFetch(getMaintenance)`) are ALL wired — the
  first three into the shell/Dashboard page, the last one into
  `DashboardPage`'s maintenance action tile (STORY-105). Still genuinely
  orphaned: `features/dashboard/summary.ts::summarizeComponents` (real
  up/degraded/partial/down bucket counts — the pre-rewrite Dashboard's
  summary-card row; STORY-105's hero tile derives its own subline
  differently, via `deriveOverallStatus`, so this helper's per-status-bucket
  shape wasn't needed) and `features/dashboard/useComponentSignals.ts`
  (latest-per-location signal rows, a zero-observation signal renders an
  honest `'missing'` row — the pre-rewrite Dashboard's expandable
  drill-down; STORY-105's per-component tile instead LINKS to Check History
  rather than expanding inline, so this hook wasn't needed either — a future
  Check History rewrite (STORY-108+) is its most likely next consumer).
- **Approvals:** ALL wired as of STORY-107 (see the new "The Approvals tab"
  Facts subsection above) — `features/approvals/useApprovals.ts`
  (`useFetch(getApprovals)`), `features/approvals/severity.ts::
  deriveSeverity` (maps `to_status` onto the 7-status health tokens),
  `features/approvals/decisionState.ts` (the idle -> confirming ->
  submitting -> failed state machine + its per-card narrowing type, PLUS the
  STORY-107 additive `confirmPrompt`/`ConfirmContext`/`CONFIRM_LABEL`), and
  the two STORY-107-ported hooks `useProposalEvidence.ts`/
  `useApprovalsTopology.ts`. The STORY-103-deleted rendering component was
  rebuilt fresh as `ApprovalCard.tsx` on the new Tile language (STORY-107),
  not restored — it was pure presentation coupled to the old `Button`
  variant set with no independent test, same as every other deleted Wave-2
  page component.
- **Availability:** `features/availability/{windowRange,useAvailability,
  format,segments}.ts` — the 24h/7d/30d window-to-range conversion, the
  topology+per-component fetch/merge, `availabilityBand`/`formatDownLabel`/
  `isCompletenessLow`, and the sparkline-segment builder — ALL wired as of
  STORY-106 into `pages/AvailabilityPage.tsx` (see the new "The Availability
  tab" Facts subsection below), rewired verbatim (design brief: "re-skin
  freely; keep the tested behavior"), no hook-level change.
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
  pending-count badge fetch (`useFetch(getApprovals)`). Unused by the command
  bar/`TabNav` itself (still no pending-count badge on the Approvals nav
  link — that remains deferred, per the STORY-104 candidate-backlog note),
  but no longer orphaned overall: STORY-105 wired it into `DashboardPage`'s
  "Pending approvals" action tile — a DIFFERENT consumer than the one the
  STORY-104 note anticipated, same hook, unchanged.

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
- sprint-55 (STORY-103 reality-gate correction, 2026-07-18): the theme-engine Facts entry directly
  above described an INTERMEDIATE precedence (stored -> explicit system dark -> explicit system
  light -> dark) that the orchestrator's live gate then corrected to STORED CHOICE > DARK, period
  — the OS `prefers-color-scheme` is no longer consulted at all (rationale: most headless/desktop
  systems report `light` by default, defeating the dark-first identity for the common first
  impression). `resolveTheme.ts::getSystemTheme` was REMOVED; `resolveInitialTheme` is now
  `getStoredTheme() ?? 'dark'`; `index.html`'s pre-paint script updated to match (still logic-
  duplicated by design). The Facts entry above has been rewritten in place to describe this FINAL
  precedence (not the superseded intermediate one) — this History bullet records that a correction
  happened, per the standing "a contract change rewrites its covering tests/Facts, recorded in
  History" convention. `resolveTheme.test.ts`/`ThemeContext.test.tsx` rewritten to the new
  precedence table; frontend suite still green (369 tests / 47 files — three fewer than the prior
  372 since the now-pointless three-way `getSystemTheme` test cases were removed, not replaced).
  verified_sha = 06ba847 (retroactively filled in by the STORY-104
  implementer — the frontmatter `verified_sha` was left at 52f1706 through
  this correction; this bullet's own commit is 06ba847, confirmed via
  `git log --oneline`).

- sprint-55 (STORY-104 — the real app shell): built the design brief §IA
  shell described in the new "The real app shell" Facts subsection above —
  `nav/CommandBar.tsx` + `nav/TabNav.tsx` (AC1: brand + 6 tabs, aria-current,
  teal active indicator, keyboard-operable via real `NavLink`s), `nav/
  StatusDot.tsx` + `features/shell/deriveOverallStatus.ts` (AC2: worst-of
  overall-status dot), the sample-mode switch/chip/banner re-wire (AC3,
  ported `ui-redesign` STORY-056/102 contracts — `nav/SampleModeSwitch.tsx`,
  `nav/SampleModeChip.tsx`, `nav/SampleModeBanner.tsx`, `nav/
  useDismissibleBanner.ts`), and the mobile <=768px hamburger `nav/
  NavSheet.tsx` + `nav/useNavSheet.ts` (AC4, ported `SidebarDrawer`
  focus-trap contract) — all rewired through a rewritten `AppShell.tsx`
  (`AppShell.test.tsx` rewritten to the new contract: routing, the
  overall-status dot, sample-mode/banner/chip, theme toggle, the mobile
  sheet, and a "no sidebar in the DOM" assertion). `features/dashboard/
  useComponents.ts` gained an additive `fetchedAtIso` field ("Updated Xs
  ago", display-layer only); `components/Icon/Icon.tsx` gained one new
  `menu` glyph. Frontend-only; six backend gates untouched (empty diff).
  Suite: 461 tests / 57 files, all green; `npm run build`/`npm run lint`
  both exit 0. `code_refs` += every new `nav/*`/`features/shell/
  deriveOverallStatus.ts` file listed above. verified_sha = 5dd72ce.

- sprint-56 (STORY-105 — bento Dashboard, the first sprint-56+ tab rewrite):
  built `pages/DashboardPage.tsx`/`.css` per the design brief §IA "Dashboard
  = bento" spec (documented in the new "The Dashboard tab" Facts subsection
  above) — hero/per-component/action/feed tiles on a mobile-first asymmetric
  CSS grid, routed at `/` in `AppShell.tsx` (the one tab no longer rendering
  `PlaceholderPage`). RE-WIRED five previously-orphaned feature hooks
  (`useComponents`, `useTopology`, `useComponentUptime`,
  `useMaintenanceWindows`, `useApprovalsBadge`) plus `useAllHistory` and
  `deriveOverallStatus` rather than reinventing any of them. New: the
  `LatencySpark` primitive (inline-SVG sparkline, no chart library/new
  dependency), `features/dashboard/latencyPoints.ts::buildLatencyPoints`, two
  ADDITIVE `ComponentUptime` fields (`latencyPoints`/`lastObservedIso`,
  zero extra network calls — reuses the fetch `segments` already made), and
  `features/dashboard/maintenanceSummary.ts::countActiveOrUpcomingWindows`
  (ported verbatim from the parked `ui-redesign` branch's STORY-099, per the
  brief's §Salvage instruction). `AppShell.test.tsx`'s Dashboard-route
  assertions needed no changes (the page's own `<h1>` is still exactly
  "Dashboard"). Sonnet-5-implementer TDD pass, one commit per green step;
  frontend-only; six backend gates untouched (empty diff). Suite: 493 tests /
  63 files, all green; `npm run build`/`npm run lint` both exit 0. `code_refs`
  += `pages/DashboardPage.tsx`, `components/LatencySpark/LatencySpark.tsx`,
  `features/dashboard/{latencyPoints,maintenanceSummary}.ts`. verified_sha =
  07b49c4.

- sprint-56 (STORY-106 — Availability rewrite, windowed uptime vs
  completeness): built `pages/AvailabilityPage.tsx`/`.css` (documented in
  the new "The Availability tab" Facts subsection above) — one h1, a
  24h/7d/30d window switcher in the header (AC1), a down/missing legend and
  per-component availability%/windowed-bar/completeness metrics (AC2), and
  an `aria-expanded` signal-level drill-down (AC3), routed at
  `/availability` in `AppShell.tsx` (the second tab no longer rendering
  `PlaceholderPage`). RE-WIRED the surviving
  `features/availability/{windowRange,useAvailability,format,segments}.ts`
  hooks VERBATIM (design brief §Salvage: "re-skin freely; keep the tested
  behavior") — no new feature-hook file, no hook-level change; the single
  merged `useAvailability` fetch's existing loading/error/empty contract is
  reused as-is rather than re-split into per-component fetches (a
  candidate-backlog note, not a deviation — Dashboard's per-tile fault
  isolation was a STORY-105 decision this story did not need to match).
  `AppShell.test.tsx` gained one assertion proving `/availability` renders
  the real page (not `PlaceholderPage`); its pre-existing `it.each(TABS)`
  placeholder-heading assertion needed no change (`AvailabilityPage`'s own
  `<h1>` is still exactly "Availability"). Sonnet-5-implementer TDD pass,
  one commit per green step (page scaffold + switcher/routing; per-component
  metrics + legend; signal drill-down); frontend-only; six backend gates
  untouched (empty diff). Suite: 508 tests / 62 files, all green; `npm run
  build`/`npm run lint` both exit 0. `code_refs` += `pages/
  AvailabilityPage.tsx`. verified_sha = 3e4c634.

- sprint-57 (STORY-107 — Approvals rewrite, evidence-first queue on the new
  skin): built `pages/ApprovalsPage.tsx`/`.css` +
  `features/approvals/ApprovalCard.tsx`/`.css` (documented in the new "The
  Approvals tab" Facts subsection above), routed at `/approvals` in
  `AppShell.tsx` (the third tab no longer rendering `PlaceholderPage`).
  PORTED two hooks verbatim from the parked `ui-redesign` branch's unmerged
  `sprint-54` line (`features/approvals/useProposalEvidence.ts`/
  `useApprovalsTopology.ts`, per the design brief's §Salvage instruction — the
  evidence-first concept was review-approved there before the PO's
  full-rewrite pivot parked it): per-location latest-result evidence off the
  existing `GET /api/v1/history` (a NEW additive `limit` query param on
  `api/client.ts::getHistory`, its first caller) and a thin
  `useFetch(getTopology)` wrapper. RE-WIRED the surviving
  `features/approvals/{useApprovals,severity,decisionState}.ts` hooks —
  `decisionState.ts` gained additive `confirmPrompt`/`ConfirmContext`/
  `CONFIRM_LABEL` (AC3: approve states the publish consequence naming the
  component + target status via the NEW `components/StatusBadge/labels.ts::
  defaultStatusLabel` export — extracted out of `StatusBadge.tsx` itself,
  also a ported quality fix from the same parked line, clearing a
  `react-refresh/only-export-components` lint warning; reject's prompt is
  UNCHANGED). `ApprovalCard.tsx` (rebuilt fresh, not restored — the
  STORY-103-deleted version was pure presentation on the old `Button`
  variant set) renders as a severity-accented `Tile` (reusing `Tile`'s own
  colored-edge affordance, not a bespoke stripe) with a static
  reduced-motion-guarded evidence skeleton, a quiet "Evidence unavailable"
  degrade-gracefully-still-actionable note (AC4), and a "View checks" deep
  link to `/check-history?signal=<signal_key>` (AC2 — the link contract
  lands now; STORY-108 is what makes the target page consume it).
  `AppShell.test.tsx` gained one assertion proving `/approvals` renders the
  real page; its pre-existing `it.each(TABS)` placeholder-heading assertion
  needed no change (`ApprovalsPage`'s own `<h1>` is still exactly
  "Approvals"). Sonnet-5-implementer TDD pass, one commit per green step;
  frontend-only; six backend gates untouched (empty diff — no backend source
  change). Suite: 558 tests / 68 files, all green; `npm run build`/`npm run
  lint` both exit 0. AC4's live sample-mode round-trip pass was OUT OF this
  dispatch's scope (the dispatch's own numbered IMPLEMENTATION SHAPE
  enumerated Steps 1-5 only, matching the sprint-57 plan's Steps 1-5; Step 6
  "live gate" is a distinct follow-up, not yet run on this line). `code_refs`
  += `pages/ApprovalsPage.tsx`, `features/approvals/{useProposalEvidence,
  useApprovalsTopology,ApprovalCard}`, `components/StatusBadge/labels.ts`.
  verified_sha = bb7644e.

