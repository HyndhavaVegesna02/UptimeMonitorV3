---
id: STORY-103
title: Rewrite foundation — Mission Teal design system, fonts, theme engine, base primitives
type: story
---

## Context
PO directive 2026-07-18 (full rewrite, creative freedom). Binding brief:
`docs/scrum/ui-rewrite/design-brief.md` + `design-system/uptime-monitor-v3-rewrite/MASTER.md`
(brief wins on conflict). This story replaces the old design system wholesale on the
`ui-rewrite` line; the old look must not survive except where the brief carries it.

## Description
Rebuild `frontend/src/styles/` (tokens v2: Mission Teal dark-first + light theme, spacing/
radius/shadow/z scales, 7-status palette retuned per theme), swap fonts to self-hosted
Space Grotesk / Inter / JetBrains Mono (@fontsource), rebuild `theme/` (system-pref +
localStorage override + pre-paint script stays), and land the base primitives the rest of
the rewrite composes: `Tile` (bento card: padding/elevation/optional accent + interactive
variant), `Button`, `StatusBadge` (dot + label, never color alone), `Icon` (inline SVG set),
`Text/Heading` helpers or documented type classes, `RelativeTime` (ported logic). Delete or
quarantine old component CSS so no page renders the old skin from this story on.

## Acceptance Criteria
- [ ] AC1: tokens.css v2 defines both themes via `data-theme` scoping; html defaults dark;
      pre-paint script prevents flash; theme toggle + persistence work (ported contract).
- [ ] AC2: fonts load self-hosted (@fontsource imports in global.css; zero external font
      requests in the network log); headings render Space Grotesk, body Inter, data cells
      JetBrains Mono.
- [ ] AC3: primitives Tile/Button/StatusBadge/Icon/RelativeTime render from
      `components/` with Vitest coverage (variants, a11y contracts: focus-visible ring
      tokens, aria patterns); status badge text contrast ≥4.5:1 BOTH themes (token-level
      check documented in the story evidence).
- [ ] AC4: formatTime/formatLocation/useMediaQuery/breakpoints/matchMedia-stub ported with
      their tests green (salvage list in the brief).
- [ ] AC5: `npm test` / `npm run build` / `npm run lint` exit 0; the app still boots (a
      minimal AppShell placeholder using the new tokens is acceptable this story — the real
      shell is STORY-104).

## History
- 2026-07-18: filed at ui-rewrite refinement (PO-delegated); estimate 3.
- 2026-07-18: deleted the old shell (nav/Sidebar, TopBar, SampleModeBanner, sidebarState) + all
  six old pages + features/approvals/ApprovalCard (commit 52f1706) — PO-ordered full rewrite
  (2026-07-18 pivot); replacements land per-story (shell STORY-104, pages STORY-105..110);
  surviving feature hooks documented as orphaned in frontend-zone.md.
- 2026-07-18: reality-gate correction — theme precedence fixed to STORED CHOICE > DARK, period;
  the OS `prefers-color-scheme` is no longer consulted for the initial theme (most headless/
  desktop systems report `light` by default, which would make the common first impression light
  and defeat the brief's dark-first mission-control identity). `resolveTheme.ts`'s
  `getSystemTheme` was removed, `resolveInitialTheme` is now `getStoredTheme() ?? 'dark'`, and
  `index.html`'s pre-paint script was updated to match (kept logic-identical, as before).
