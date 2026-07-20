---
title: Frontend design system — tokens, Phosphor icons, primitives, /styleguide
code_refs: [frontend/package.json, frontend/index.html, frontend/tsconfig.app.json, frontend/src/main.tsx, frontend/src/App.tsx, frontend/src/AppShell.tsx, frontend/src/lib/cx.ts, frontend/src/styles/tokens.css, frontend/src/styles/global.css, frontend/src/styles/parseTokens.ts, frontend/src/styles/contrastRatio.ts, frontend/src/styles/tokens.contrast.test.ts, frontend/src/styles/noRawHex.test.ts, frontend/src/styles/motionTokens.test.ts, frontend/src/components/Icon/Icon.tsx, frontend/src/components/Button/Button.tsx, frontend/src/components/Panel/Panel.tsx, frontend/src/components/StatusBadge/StatusBadge.tsx, frontend/src/components/SummaryCard/SummaryCard.tsx, frontend/src/components/Sparkline/Sparkline.tsx, frontend/src/components/LoadingState/LoadingState.tsx, frontend/src/components/ErrorState/ErrorState.tsx, frontend/src/components/EmptyState/EmptyState.tsx, frontend/src/pages/StyleguidePage/StyleguidePage.tsx, frontend/src/pages/StyleguidePage/StyleguideSection.tsx]
verified_sha: 6e957f1
verified_sprint: sprint-59
status: verified
---

## Context (read first)
**This is the THIRD frontend attempt.** The first (sprints 23–24, `DESIGN-airtable.md`) was
reverted in `521764c`. The second (sprint-25 onward, `DESIGN-linear.app.md` then retuned at
STORY-055/sprint-38 to an imported Operator Dashboard mock) was PO-rejected twice on 2026-07-19/
2026-07-21; its whole `frontend/src/**` tree (components, pages, features, api client, MSW mocks,
theme system) was deleted in this story's first commit — see `docs/scrum/wiki/frontend-zone.md`
(now stale, describes the deleted tree; the orchestrator handles its rehab at sprint close). ONLY
the build toolchain survived unmodified: `vite.config.ts`, `eslint.config.js`, `tsconfig*.json`
(gained one line, see below), `frontend/package.json`'s scripts block. STORY-120 (sprint-59) builds this
THIRD system fresh, guided by the PO-approved refimg prototype (`docs/scrum/sprints/
2026-07-18-ui-prototyping/prototypes/refimg-dashboard.html`) and its derived-tokens doc
(`docs/scrum/sprints/2026-07-18-ui-prototyping/round-2-refimg-system.md`) — adapted with craft,
not copied pixel-for-pixel.

## Facts (verified against code)

### Toolchain deltas this story made (`frontend/package.json`, `frontend/tsconfig.app.json`)
- Dependencies: `@phosphor-icons/react` added (icon set, STORY-120 AC1); `@fontsource/inter`
  added, `@fontsource/geist`/`@fontsource/geist-mono` REMOVED (self-hosted Inter replaces
  self-hosted Geist — same self-hosting pattern, different family, matching the design-system
  doc's binding typeface choice). `frontend/package.json`'s `scripts` block (`dev`/`build`/`test`/`lint`/
  `preview`) is UNCHANGED — the three frontend DoD commands (`npm test`, `npm run build`,
  `npm run lint`) are the same as before this story.
- `frontend/tsconfig.app.json` gained `"node"` to its `types` array (alongside the existing
  `"vite/client"`) — needed because the new token/contrast tests (`tokens.contrast.test.ts`,
  `noRawHex.test.ts`, `motionTokens.test.ts`) read `tokens.css` via `node:fs`/`node:path`/
  `node:url` at test time, and `tsc -b` (part of `npm run build`) type-checks test files too
  (`tsconfig.app.json`'s `include: ["src"]`).
- `frontend/index.html` no longer carries the pre-paint dark/light theme-resolution script — this
  initiative ships light theme ONLY (PO: "light-first, dark-ready tokens... no dark UI built this
  initiative unless requested"); `<html data-theme="light">` is hardcoded instead. There is
  currently no `ThemeProvider`/`useTheme` — that whole seam was part of the deleted tree and has
  not been rebuilt, since nothing in sprint 59 needs a runtime theme switch.

### Three-layer tokens (`frontend/src/styles/tokens.css`, AC2/AC4)
- **Primitive layer** (bare `:root`, theme-independent): the cool-grey ramp (`--white` through
  `--grey-900`), the single sky-blue accent ramp (`--sky-50`…`--sky-text`), positive/negative
  (`--green-*`/`--red-*`), and the health-adjacent hues `--amber-*` (degraded), `--orange-*`
  (partial — a hue DISTINCT from degraded's amber so the two statuses are never confusable by
  color alone), `--violet-*` (maintenance), `--indigo-*` (missing). Also the type family
  (`--font-family-base`, self-hosted Inter), the full type scale (`--font-size-xs`…`--font-size-3xl`,
  `--line-height-*`, `--font-weight-*`), the 8px spacing scale (`--space-0`…`--space-12`, with a
  4px half-step), radius (`--radius-card` 16 / `--radius-ctrl` 10 / `--radius-chip` 8 /
  `--radius-pill` 999), the two-layer shadow (`--shadow-card`/`--shadow-lift`/`--shadow-pop`), and
  the motion tokens (below).
- **Semantic layer** — lives under `:root, [data-theme='light']` (both match today, since
  `index.html` hardcodes `data-theme="light"` and there is no dark theme yet): `--color-canvas`/
  `-app`/`-surface`/`-surface-subtle`/`-surface-hover`/`-border`/`-border-strong`, `--color-text`/
  `-text-secondary`/`-text-muted`, `--color-accent`/`-accent-strong`/`-accent-text`/`-accent-tint`,
  `--color-pos`/`-neg` (+ `-text`/`-tint` each), and the **7-status health palette** — `up`/
  `degraded`/`partial`/`down`/`maintenance`/`unknown`/`missing`, each with a bright `--color-{x}`
  fill (dots/icons/backgrounds ONLY), a darkened `--color-{x}-text` (the ONLY color text may use),
  and a `--color-{x}-tint` (pill background). Dossier status vocabulary -> health mapping (AC
  Notes): `operational`->up, `degraded_performance`->degraded, `partial_outage`->partial,
  `major_outage`->down, `under_maintenance`->maintenance. **This layer is theme-scoped by
  construction so a future dark theme is an ADDITIVE `[data-theme='dark']` block, not a rename** —
  no semantic token name changes when dark ships (AC2).
- **Component layer** (bare `:root`, points only at semantic tokens): `--button-radius`/`-height`,
  `--panel-radius`/`-shadow`/`-shadow-hover`, `--badge-radius`, `--kpi-chip-radius`.
- **No raw hex outside `tokens.css`** — `frontend/src/styles/noRawHex.test.ts` recursively scans
  every non-test `.css`/`.tsx` under `src/` for a hex-literal pattern (`#[0-9a-fA-F]{3,8}`),
  allow-listing ONLY `styles/tokens.css` itself (the primitive layer necessarily declares hex).
  This is a live, gate-covered test (`npm test`), not a review-time grep.

### WCAG-AA contrast proof (AC3)
- `frontend/src/styles/parseTokens.ts::parseTokenDeclarations`/`resolveToken` — a minimal CSS
  custom-property parser (regex-based, no jsdom cascade) that reads `tokens.css` as plain text and
  follows a `var(--x)` chain down to its literal value, raising a named `Error` (never a leaked
  stdlib message) on an unknown token or a circular reference.
- `frontend/src/styles/contrastRatio.ts::contrastRatio` — the WCAG 2.x relative-luminance formula
  (sRGB gamma correction, `(L1+0.05)/(L2+0.05)`), independently unit-tested against the known
  black-on-white (21:1) and `#767676`-on-white (~4.54:1) reference ratios.
- `frontend/src/styles/tokens.contrast.test.ts` composes both: reads the REAL `tokens.css` file
  off disk and asserts every text-on-surface semantic pair used by a primitive — body/secondary/
  muted text on surface and canvas, accent text on surface and accent-tint, and all 7 health
  `-text`-on-`-tint` pairs — is `>= 4.5:1`. This is the SAME "computed, not eyeballed" contrast
  discipline the STORY-055-era system used, rebuilt fresh against the new palette.

### Motion tokens (AC4, emil-design-eng)
- `--ease-out: cubic-bezier(0.23, 1, 0.32, 1)`, `--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1)`,
  `--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1)` (the last is for STORY-121's sidebar
  collapse/mobile sheet — not consumed by anything in this story). Duration tokens:
  `--duration-press: 140ms`, `--duration-control: 180ms` (both `<=200ms`, AC4), `--duration-drawer:
  220ms` (STORY-121's 200–250ms allowance per the sprint plan's "Motion is first-class" section).
  `frontend/src/styles/motionTokens.test.ts` pins the exact curve strings and duration bounds
  directly from `tokens.css`, so a future edit can't silently drift off the agreed values.
- `frontend/src/styles/global.css` carries the shared `.stagger` entrance utility (opacity +
  translateY rise, staggered per child) and every primitive's own motion (below) — ALL guarded by
  `@media (prefers-reduced-motion: no-preference)`, animating ONLY `transform`/`opacity` — AC5 is
  unqualified, so even a paint-only SVG property (e.g. `stroke-dashoffset`) is disallowed; the
  Sparkline's entrance (below) is an opacity + small `translateY` fade, not a stroke draw. No rule
  anywhere uses `transition: all`.

### Icon wrapper (`frontend/src/components/Icon/Icon.tsx`, AC1)
- Thin wrapper around a caller-supplied Phosphor icon COMPONENT (`icon: PhosphorIcon` — e.g.
  `import { CheckCircle } from '@phosphor-icons/react'`, then `<Icon icon={CheckCircle} .../>`),
  pinning the default size (18px) and weight (`'regular'`), both overridable.
- **The prop type is a discriminated union that FORCES every call site to be explicit about
  accessibility** — `{ 'aria-hidden': true; label?: undefined }` (decorative) OR `{ label: string;
  'aria-hidden'?: undefined }` (the icon IS the accessible name, rendered `role="img"` +
  `aria-label`). There is no third shape that renders silently as neither. `Icon.test.tsx` proves
  a decorative icon exposes NO accessible name (`aria-hidden="true"`, no `role`) and a labelled one
  IS found by `getByRole('img', { name })`.

### Primitives (`frontend/src/components/*`, AC5) — each co-located `.tsx` + `.css` + `.test.tsx`
- **Button** (`Button.tsx`): `type="button"` by default (never submits a form); `variant:
  'primary' | 'secondary' | 'ghost'`; an `iconOnly` mode that TYPE-requires `aria-label`.
  `:active` press-scale (`0.97`) and `:hover`/`:focus-visible` per variant, guarded by
  `prefers-reduced-motion`, animating only `transform`.
- **Panel** (`Panel.tsx`): the base surface — white card, hairline border, `--panel-radius` (16px),
  `--panel-shadow`. Optional `title`/`headingLevel` (defaults `h2`; pass `h1` for a page's single
  top-level panel). Optional `interactive` prop adds the hover-lift affordance (`translateY(-2px)`
  + `--panel-shadow-hover`), gated to `@media (hover: hover) and (pointer: fine)` AND
  `prefers-reduced-motion: no-preference`.
- **StatusBadge** (`StatusBadge.tsx`): the 7-status `HealthStatus` union (`up`/`degraded`/
  `partial`/`down`/`maintenance`/`unknown`/`missing`) as a dot+label pill. The dot is
  `aria-hidden`; the label — using the contrast-verified `-text` token, never the dot color alone
  — IS the accessible name. Default labels: Up/Degraded/Partial outage/Down/Maintenance/Unknown/
  Missing data, all overridable via `label`.
- **SummaryCard** (`SummaryCard.tsx`): the KPI card — icon chip, label, big `tabular-nums` value +
  optional unit, optional delta pill (`sentiment: 'positive' | 'negative'` is the COLOR, decoupled
  from `direction: 'up' | 'down'`, the arrow — a latency DECREASE is `positive`/green even though
  its arrow points down), optional sub line, and a generic `children` slot (a `Sparkline`, a
  mini-segment strip, etc.). Renders as a whole-card `<a>` when `href` is given (the "Pending
  approvals" attention card is ONE clickable surface, not a card plus a separate link) — hover-lift
  + `:active` scale(0.99) + `:focus-visible`, all reduced-motion guarded; otherwise an `<article>`.
- **Sparkline** (`Sparkline.tsx`): minimal inline-SVG trend line, `aria-hidden` by DEFAULT (the KPI
  number + delta already carry the meaning). Normalizes `data: number[]` to a 0–1 range per point;
  a FLAT series (`min === max`) draws a level mid-height line instead of dividing by zero; an empty
  array renders the `<svg>` with no `<polyline>` (no crash). One-shot entrance fade (`opacity` +
  a small `translateY`, `transform`/`opacity` only per AC5) on mount, `prefers-reduced-motion`
  guarded — never replays on data refresh (no periodic-refresh animation, per the ui-ux-pro-max
  chart-domain rule this sprint's plan calls out for STORY-122).
- **LoadingState** (`LoadingState.tsx`): `role="status"` + a visible label (default `"Loading…"`);
  the spinner is `aria-hidden`, rotates via `transform: rotate()`, linear easing (constant motion,
  per the emil decision framework), reduced-motion guarded.
- **ErrorState** (`ErrorState.tsx`): `role="alert"` + a visible message (default `"Something went
  wrong"`); the warning `Icon` is colored `--color-down` and marked `aria-hidden` — the TEXT never
  depends on color to convey the error. An optional `onRetry` renders a secondary `Button`.
- **EmptyState** (`EmptyState.tsx`): required `message` + optional `detail` — the explicit
  "no items yet" affordance every list-rendering surface needs (ui-ux-pro-max: "show a helpful
  message and action", not a blank white space).

### `/styleguide` gallery (`frontend/src/pages/StyleguidePage/`, AC6)
- `StyleguidePage.tsx` renders every primitive above in every state, each wrapped in a
  `StyleguideSection` (`<section aria-label={title}>`, implicit ARIA `role="region"` since it has
  an accessible name) — independently addressable by screen-reader landmark navigation and by
  `StyleguidePage.test.tsx`'s `within(screen.getByRole('region', {name}))` queries.
- `frontend/src/AppShell.tsx` is currently a MINIMAL frame (no sidebar/topbar — that is STORY-121):
  `<Routes>` maps `/` and `/styleguide` both to `StyleguidePage`, and `*` redirects to
  `/styleguide` too. `App.test.tsx` renders `<App/>` (which mounts `AppShell` inside a
  `BrowserRouter`) and asserts the "Design system" `h1` is present at the default route — the
  render-test proof that `/styleguide` is reachable in the running app (AC6).

### Test discipline
- Every primitive's test co-reads its own `.css` file via `node:fs` (not jsdom computed styles) to
  assert the hover/`:active`/`:focus-visible` selectors and the `prefers-reduced-motion` guard
  exist as text — jsdom does not apply real CSS cascade/pseudo-classes, so this is the reliable way
  to gate-check "the affordance is declared" without a real browser.
- 126 tests across 17 files at this story's HEAD (`npm test`, all green); `npm run build`
  (`tsc -b && vite build`) and `npm run lint` (`eslint .`) both exit 0.

## History
- sprint-59 (STORY-120, created): the third frontend attempt's design-system foundation —
  greenfield-cleaned `frontend/src/**` (deleted the second attempt's whole tree; kept only the
  toolchain), `@phosphor-icons/react` + self-hosted `@fontsource/inter` (Geist retired), the
  three-layer `tokens.css` (color + type/spacing/radius/shadow/motion), a WCAG-AA contrast test and
  a no-raw-hex test (both live `npm test` gates), the `Icon` wrapper, eight core primitives
  (Button/Panel/StatusBadge/SummaryCard/Sparkline/Loading/Error/EmptyState), and the `/styleguide`
  gallery route. `docs/scrum/wiki/frontend-zone.md` — which describes the DELETED second-attempt
  tree in detail — is now stale; flagged for the orchestrator's sprint-close rehab rather than
  rewritten here (STORY-121/122 will still change large parts of it as the shell/Dashboard rebuild
  lands). `docs/scrum/wiki/sample-mode.md` is ALSO now stale for the same reason (its "frontend
  consumer" section describes files this story deleted — `AppShell.tsx`'s sample-mode wiring,
  `nav/TopBar.tsx`, `nav/SampleModeBanner.tsx`, `useSampleMode.ts` — none of which exist in the
  fresh tree yet); also flagged, not rewritten, since whether/how sample mode returns to the new
  frontend is a product decision outside this story's scope. verified_sha = 6e957f1.
