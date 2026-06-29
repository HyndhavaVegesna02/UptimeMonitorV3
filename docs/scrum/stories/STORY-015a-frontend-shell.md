---
id: STORY-015a
title: Frontend shell — Vite/React/TS SPA scaffold, six-tab nav, typed API client, design system, test harness
type: feature
---

## Context
Spec: dossier §17 (two-surface model; six-tab IA). Zone 7 (frontend). Split-child of STORY-015 (which
the seed flagged as an 8 — split at refinement 2026-06-29 into this shell + six per-tab stories
015b–015g). This is the **frontend Sprint-0 equivalent**: it stands up the React + TypeScript SPA, the
six-tab navigation shell, the typed API client, the design system, and the frontend test harness + DoD
gate — so every subsequent per-tab story is purely "fill in one tab." No tab renders real data yet
(that is 015b–015g); the shell proves the scaffold, routing, client, and gates end to end with one
trivially-wired example.

## Toolchain (PO-approved at Sprint 23 planning, 2026-06-29)
- **Build/dev:** Vite + React 18 + TypeScript (strict), SPA (NOT Next.js — the backend is a separate
  FastAPI service). Package manager: **npm** (Node v24, npm v11 already on the box).
- **Tests:** Vitest + React Testing Library + **MSW (Mock Service Worker)** to mock the API — no live
  backend in any test (honors the 2026-06-23 "pure core, mockable edges" agreement, frontend edition).
- **E2E:** Playwright, **DEFERRED** to a later integration story (set up once real tabs + a live API
  exist). Chrome DevTools MCP is retained as an agent-driven dev/verification aid, not the committed E2E
  layer.
- **Dev ↔ API:** Vite dev-server **proxy** (`/api` → the local backend), so the shell needs NO backend
  change and NO CORS work — **CORS stays deferred to STORY-017 (deployment)**, per the 2026-06-23 agreement.

## Acceptance Criteria
- [ ] **AC1 — SPA scaffold builds & runs.** A `frontend/` package (Vite + React + TS strict) builds
      (`npm run build` exits 0) and runs in dev (`npm run dev`). `frontend/` is isolated from the Python
      backend; the Python DoD gate is unaffected (no backend source changes in this story).
- [ ] **AC2 — Six-tab nav + routing.** The app shell renders persistent navigation with all six tabs —
      Dashboard · Availability · Approvals · Check History · Maintenance · Publications — wired to client-
      side routes (one route per tab). The active tab is visually indicated (`nav-state-active`). Each tab
      route renders a placeholder "coming soon" panel (real content is 015b–015g). A component test
      (Vitest + RTL) asserts all six nav items render and routing switches the active panel.
- [ ] **AC3 — Typed API client + MSW harness.** A typed `apiClient` (fetch-based, TS types matching the
      backend DTOs) with a single base-URL seam pointing at `/api` (proxied in dev). One endpoint is wired
      end to end as the proving example (e.g. the Dashboard's `GET /api/v1/components` or `/health`), shown
      in a placeholder, with loading + error states. MSW handlers back the tests so no live API is hit; a
      Vitest test drives the client against an MSW-mocked response (success + error path).
- [ ] **AC4 — Design system implemented from `DESIGN-airtable.md` (the reference design, PO-supplied).**
      `DESIGN-airtable.md` (repo root, tracked) is THE design source of truth — an Airtable-style editorial
      system with a full token set (colors, Haas/Inter-Display typography scale, 4px/96px spacing, radii,
      and component specs). The shell implements a token layer (CSS variables / Tailwind config) that
      mirrors its `colors` / `typography` / `rounded` / `spacing` / `components` tokens verbatim — no raw
      hex in components (`color-semantic`); every value references a token. Do NOT generate a design system
      with `ui-ux-pro-max` (that step is removed); `ui-ux-pro-max` is used ONLY for its UX/accessibility
      floor (AC6).
      - **Editorial→dashboard adaptation:** the spec is a marketing/editorial language; this app is a
        data-dense operator cockpit. Adopt the LANGUAGE — palette, type scale, spacing rhythm, radii,
        `button-primary`/`button-secondary`, `text-input`, card surfaces, hairline borders, white-canvas
        calm, modest type weights (400 display, 500 labels/buttons; never bold-for-its-own-sake). Do NOT
        import the marketing-only patterns (hero-band, signature full-bleed cards as primary chrome,
        pricing pills, logo strips) as app chrome — they may inspire empty/section states but the cockpit
        is tables/badges/lists.
      - **Health-state semantic tokens (define these — the spec has no down/degraded/maintenance):**
        `up`→`success` (#006400), `down`→`signature-coral` (#aa2d00), `degraded`→`signature-mustard`
        (#d9a441), `maintenance`→`info` (#254fad). Status must never be conveyed by color alone (icon+label
        too). These four health tokens are part of the committed token layer and are reused by every tab.
      - **Fonts:** Haas is licensed/unavailable — use the spec's documented substitute **Inter / Inter
        Display** (variable) via a self-hosted or system fallback chain; do not fetch a paid font.
- [ ] **AC5 — Frontend DoD gate is real and green, and documented.** Four npm scripts exist and exit 0 on
      a clean tree: `typecheck` (`tsc --noEmit`), `lint` (eslint, TS + react-hooks rules), `test`
      (`vitest run`), `build` (`vite build`). These four constitute the **frontend DoD gate** (parallel to,
      not replacing, the Python six-command gate). CLAUDE.md is updated IN THIS STORY's commits (command-
      sync agreement): a "Frontend" key-commands section + the frontend gate + the tooling inventory
      (Node/Vite/Vitest/RTL/MSW; Playwright noted as deferred).
- [ ] **AC6 — Accessibility & responsive baseline.** The shell meets the `ui-ux-pro-max` CRITICAL floor:
      keyboard-navigable nav with visible focus rings, semantic landmarks (`nav`/`main`), nav contrast
      ≥4.5:1, no horizontal scroll at 375px, `viewport` meta present. (Per-tab a11y is re-checked in each
      tab story.)

## Out of scope (explicit)
- Any real tab content/data rendering beyond the one proving example (Dashboard/Availability/Approvals/
  History/Maintenance/Publications bodies are 015b–015g).
- Approve/reject mutations (015c).
- Playwright/E2E (deferred), and production CORS / Vercel deploy (STORY-017).

## Skills to use
- **`DESIGN-airtable.md` (repo root) — the design source of truth (AC4).** Token layer mirrors it.
- `ui-ux-pro-max` — UX/accessibility floor ONLY (AC6); do NOT use it to generate a design system.
- `vercel-react-best-practices` — the code-quality reviewer's checklist for this and every frontend story.
- `design-taste-frontend` / `web-design-guidelines` — visual polish of the shell layout, within the
  `DESIGN-airtable.md` language.

## History
- 2026-06-29: created as the shell split-child of STORY-015 (an 8, split into shell + six tabs). Toolchain
  + E2E + scope approved at Sprint 23 planning. 5 pts.
