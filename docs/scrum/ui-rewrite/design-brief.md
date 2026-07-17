# UI Rewrite — Design Brief ("Mission Teal")

PO directive 2026-07-18: full UI/frontend rewrite on the same backend; complete creative
freedom; new branch from main (`ui-rewrite`); same YourTeam + Playwright loop until fully
done. The previous incremental redesign (`ui-redesign` branch, sprints 52–54) is parked —
its LOOK was rejected; its UX semantics were accepted and several are ported (see §Salvage).

Generated base: `design-system/uptime-monitor-v3-rewrite/MASTER.md` (ui-ux-pro-max,
variance 8 / density 8 / motion 5). This brief is the BINDING overlay — where it disagrees
with MASTER.md, this wins.

## Identity
- **Style: Bento grid, dark-first.** The app is a mission-control surface: the default
  theme is deep space-dark (`#0A0E14` family backgrounds, elevated tiles `#111823`,
  hairlines low-contrast), with a FULL light theme (mint-tinted `#F0FDFA` background per
  MASTER) — both WCAG AA minimum, checked per theme.
- **Color: teal system.** Primary `#14B8A6` (teal-500 family; `#0F766E` for on-light
  contrast), accent blue `#0369A1` for links/info. STATUS COLORS keep their semantics
  (up/green, degraded/amber, partial/orange, down/red, maintenance/blue, unknown/gray,
  missing/hatched) — retuned per theme, never repurposed. Color carries state only when
  state is non-nominal (carried over from redesign D4).
- **Type (OVERRIDES MASTER's Cinzel/Josefin — luxury-property mood, wrong for ops):**
  Space Grotesk (display/headings) + Inter (UI/body) + JetBrains Mono (tabular data,
  timestamps, latency, IDs). All self-hosted via @fontsource (project rule: no runtime
  Google-CDN links).
- **Shape/depth:** rounded-xl tiles (16px), soft layered shadows in light / border-glow
  elevation in dark, generous tile padding with dense interior data (density 8).
- **Motion (OVERRIDES MASTER's GSAP overlay — no new deps, ops tools must feel instant):**
  CSS-only; 150–250ms; transform/opacity; hover scale ≤1.01 on interactive tiles; every
  animation guarded by `prefers-reduced-motion`.

## IA — deliberately different from the old shell
- **No left sidebar.** Slim top command bar: brand + live overall-status dot, horizontal
  tab nav (6 tabs), right cluster (sample-mode switch + SAMPLE chip, theme toggle,
  last-updated). ≤768px: tab nav collapses into a hamburger sheet (focus-managed, Escape/
  scrim close — port the a11y contract from the parked drawer).
- **Dashboard = bento.** Asymmetric grid: hero "system status" tile (overall state, big),
  per-component tiles (uptime bar + latency spark + status), action tiles (pending
  approvals / maintenance — neutral at zero, accented when >0), live "recent checks" feed
  tile. One page = one decision: is anything wrong, and where.
- Other tabs keep their jobs with the new skin and the ported UX semantics.

## Non-negotiables (carried from the initiative + house rules)
- Toolchain unchanged: Vite + React + TS strict + Vitest + RTL + MSW + ESLint; the three
  frontend DoD gates stay exactly `npm test` / `npm run build` / `npm run lint`.
- `api/` client/types/statusMapping + `mocks/` are NOT UI — keep (extend only additively).
- A11y floor: visible :focus-visible rings, skip link, aria-labels, one h1/page, status
  never by color alone, 44px touch targets, keyboard-complete nav.
- Every timestamp: relative + `<time dateTime>` + local/UTC tooltip. No raw ISO, no raw
  vendor IDs as primary text. Maintenance times WYSIWYG local.
- 390/768/1024/1440 all first-class; no page-level horizontal scroll.

## Salvage list (port from `ui-redesign` branch — logic, not looks)
`git show ui-redesign:frontend/src/<path>`: lib/formatTime.ts(+tests), lib/formatLocation.ts
(+tests), lib/useMediaQuery.ts + lib/breakpoints.ts + test/matchMedia.ts, the evidence-hook
concept (features/approvals/useProposalEvidence.ts), maintenance validateMaintenanceForm,
Toast a11y contract, drawer focus-trap contract. Re-skin freely; keep the tested behavior.

## New dependencies (declared at planning, tooling-freeze compliant)
@fontsource/space-grotesk, @fontsource/inter, @fontsource/jetbrains-mono — fonts only,
no runtime JS deps added.
