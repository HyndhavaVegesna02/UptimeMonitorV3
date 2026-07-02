---
id: STORY-015a
title: Frontend shell — Vite/React/TS SPA scaffold, six-tab nav, typed API client, Linear-guided theme system (dark+light), test harness
type: feature
---

## Context
Spec: dossier §17 (two-surface model; six-tab IA). Zone 7 (frontend). Split-child of STORY-015
(seed-flagged as an 8 — split at refinement 2026-07-02 into this shell + six per-tab stories
015b–015g). Second attempt at the frontend zone: the first (sprints 23–24, built to the
now-removed DESIGN-airtable.md) was fully reverted by the PO in `521764c`; its history is
preserved on the `sprint-23`/`sprint-24` branches. This story is the **frontend Sprint-0
equivalent**: it stands up the React + TypeScript SPA, the six-tab navigation shell, the typed
API client, the themed design-token system, and the frontend test harness + DoD gates — so every
subsequent per-tab story is purely "fill in one tab." No tab renders real data yet (that is
015b–015g); the shell proves the scaffold, routing, client, theming, and gates end to end with
one trivially-wired example.

## Design direction (PO, 2026-07-02)
`DESIGN-linear.app.md` (repo root, tracked) is the design reference — **a guide, not a copy
target**. The PO grants creative freedom to combine it with the `.agents/skills/` skills for the
best operator-cockpit UI: clean, intuitive, effective. Concretely:
- **Adopt the language:** surface-ladder hierarchy with hairline borders (no drop shadows), a
  single chromatic accent (lavender-blue `#5e6ad2`) reserved for interactive emphasis (primary
  buttons, focus rings, active-tab indicator, links), quiet negative-tracked headings, compact
  8px-radius controls, 12px-radius panels, mono type for machine values (monitor IDs, timestamps,
  latencies).
- **Depart where the reference is marketing-only:** no hero bands, no 80px display type, no
  pricing/logo-strip patterns. This is a data-dense cockpit: tables, badges, lists. The reference
  itself notes Linear's real product UI uses a richer semantic palette than its marketing site —
  the health palette below is our equivalent.
- **Both themes ship** (PO decision 2026-07-02): dark is the reference-native theme (its token
  values apply nearly verbatim); light is derived from the reference's inverse tokens plus
  designed equivalents. Components must be theme-blind (consume semantic CSS variables only).
- `ui-ux-pro-max` is used ONLY as a UX/accessibility review floor — never to generate a design
  system. `web-design-guidelines` provides the final audit pass. `vercel-react-best-practices`
  guides the React implementation patterns.

## Toolchain (PO-approved at Sprint 25 planning, 2026-07-02 — carried over from the reverted attempt)
- **Build/dev:** Vite + React + TypeScript (strict), SPA (NOT Next.js — the backend is a separate
  FastAPI service). Package manager: npm.
- **Tests:** Vitest + React Testing Library + MSW to mock the API — no live backend in any test
  (the 2026-06-23 "pure core, mockable edges" agreement, frontend edition).
- **E2E:** Playwright DEFERRED to a later integration story. Browser tooling (agent-browser /
  Chrome DevTools MCP) is an agent-driven verification aid at review, not a committed E2E layer.
- **Dev ↔ API:** Vite dev-server proxy (`/api` → the local backend) — no backend change, no CORS
  work. **CORS stays deferred to STORY-017 (deployment)**, per the 2026-06-23 agreement.

## Acceptance Criteria
- [ ] **AC1 — SPA scaffold builds & runs, clean of generator boilerplate.** A `frontend/` package
      (Vite + React + TS strict) builds (`npm run build` exit 0) and runs in dev (`npm run dev`)
      with the `/api` proxy configured. `frontend/` is isolated from the Python backend; the
      six backend DoD commands are unaffected (no backend source change in this story). The
      scaffold generator's template assets (sample logos/SVGs, template favicon, default
      `<title>`, boilerplate README/CSS) are pruned or replaced — nothing ships that the design
      direction forbids or that no code references.
- [ ] **AC2 — Six-tab nav + routing.** A persistent top navigation (app title left; tabs;
      theme toggle right) renders all six tabs — Dashboard · Availability · Approvals ·
      Check History · Maintenance · Publications — wired to client-side routes (one route per
      tab). The active tab is visually indicated (ink text + accent indicator; inactive tabs
      ink-subtle). Each tab route renders a placeholder panel (real content is 015b–015g). A
      Vitest+RTL test asserts all six nav items render and routing switches the active panel.
- [ ] **AC3 — Typed API client + MSW harness, one endpoint proven.** A typed `apiClient`
      (fetch-based, TS types matching the backend DTOs) with a single base-URL seam pointing at
      `/api`. One endpoint is wired end to end as the proving example (`GET /api/v1/health` or
      `GET /api/v1/components`) and shown in a placeholder, with loading, error, and retry
      states. MSW handlers back the tests; a Vitest test drives the client against MSW for both
      the success and the error→retry path.
- [ ] **AC4 — Theme-scoped token layer + primitive components.** All visual values live as CSS
      custom properties scoped per theme (e.g. `:root[data-theme="dark"]` /
      `:root[data-theme="light"]`); components consume only semantic tokens — **no raw hex in
      components**. Dark theme uses the reference's values (canvas `#010102`; surfaces
      `#0f1011`/`#141516`/`#18191a`/`#191a1b`; hairlines `#23252a`/`#34343a`; ink
      `#f7f8f8`/`#d0d6e0`/`#8a8f98`/`#62666d`; accent `#5e6ad2`, hover `#828fff`, focus
      `#5e69d1`). Light theme derives from the reference's inverse tokens (`#ffffff` canvas,
      `#f5f6f6`/`#f6f7f7` surfaces) with designed hairline/ink equivalents and the same accent.
      Fonts: **Inter** (400/500/600, negative tracking on headings per the reference scale,
      adapted to app sizes ≤28px) + **JetBrains Mono** for machine values; self-hosted or
      @fontsource (no runtime Google Fonts fetch). **Health tokens** exist in BOTH themes as
      part of the committed token layer, reused by every tab: `up` (green), `down` (red),
      `degraded` (amber), `maintenance` (blue — visually distinct from the lavender accent),
      each with a subtle surface variant for badge backgrounds. Primitive components ship with
      the shell so tabs don't copy-paste: `Button` (primary/secondary/tertiary), `StatusBadge`
      (pill; status dot/icon + label), `Panel` (surface-1, hairline, 12px radius), and
      loading/error/empty state components.
- [ ] **AC5 — Theme toggle.** Default theme follows `prefers-color-scheme`; a toggle in the nav
      overrides it; the override persists (localStorage) and is applied before first paint (no
      theme flash). A test covers: system-default resolution, toggle override, persistence.
- [ ] **AC6 — Accessibility floor (both themes).** Tabs and toggle are keyboard-operable with a
      visible focus ring (accent, per the reference's focus spec). Status is never conveyed by
      color alone (dot/icon + text label). All label/body text uses ink tokens meeting WCAG
      4.5:1 against its surface in BOTH themes — health colors appear in non-text cues (dots,
      badge backgrounds, borders), not as text color. Interactive targets ≥40px. Verified at
      review against the `ui-ux-pro-max` a11y checklist + `web-design-guidelines` audit.
- [ ] **AC7 — Frontend DoD gates live.** `npm test` (Vitest, run-once mode), `npm run build`
      (includes `tsc` type-check), and `npm run lint` (ESLint) all exit 0 and are activated in
      `.scrum/definition-of-done.md` (replacing the placeholder note) + documented in CLAUDE.md
      **in the same commit** (command-sync agreement, 2026-06-23).

## Open Questions
None — toolchain, themes, and design direction PO-approved 2026-07-02.

## History
- 2026-06-29: first version built to DESIGN-airtable.md (sprint 23), accepted, then fully
  reverted with the UI rollback `521764c` (2026-06-29). Old work preserved on `sprint-23`/`24`.
- 2026-07-02: re-refined against DESIGN-linear.app.md (guide-not-copy) with dark+light themes
  (PO decisions at refinement). Status: ready. Committed to Sprint 25.
