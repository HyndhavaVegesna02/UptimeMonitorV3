---
title: Zone 7 — the frontend SPA (shell, design tokens, API client, test harness)
code_refs: [frontend/package.json, frontend/vite.config.ts, frontend/src/App.tsx, frontend/src/apiClient.ts, frontend/src/index.css, frontend/src/mocks/handlers.ts, frontend/src/mocks/server.ts, frontend/src/setupTests.ts, frontend/src/App.test.tsx, frontend/index.html, DESIGN-airtable.md, CLAUDE.md]
verified_sha: ad7d8f2
verified_sprint: sprint-23
status: verified          # verified | stale | archived
---

## Facts (verified against code)

Zone 7 is the operator cockpit — a React + TypeScript SPA under `frontend/`, separate from the Python
backend (Zones 1–6). Introduced by STORY-015a (Sprint 23) as the SHELL; the six tab bodies are filled in
by STORY-015b–015g. The dossier §17 two-surface model + six-tab IA is the spec.

### Toolchain (`frontend/package.json`, `frontend/vite.config.ts`)
- **Vite + React 18 + TypeScript (strict)**, SPA — NOT Next.js (the backend is a separate FastAPI service).
  npm is the package manager (Node v24).
- **Tests:** Vitest + React Testing Library + **MSW** (Mock Service Worker). `vite.config.ts` sets
  `test: { globals: true, environment: 'jsdom', setupFiles: './src/setupTests.ts' }`. No test hits a live
  API — MSW mocks the network edge (`frontend/src/mocks/handlers.ts` + `server.ts`).
- **Dev ↔ API:** `vite.config.ts` proxies `/api` → `http://localhost:8000` (`server.proxy`), so dev needs
  no CORS. Real cross-origin CORS (Vercel→Railway) is deferred to STORY-017 (deployment).
- **E2E:** Playwright is the chosen committed E2E layer but DEFERRED to a later story (not installed yet).
- **Frontend DoD gate** (four commands, run from `frontend/`, each exits 0 — see [[dev-setup-and-dod]]):
  `npm run typecheck` (`tsc --noEmit`) · `npm run lint` (eslint) · `npm run test` (`vitest run`) ·
  `npm run build` (`vite build`). Parallel to the backend six-command gate, never part of it.

### Design tokens (`frontend/src/index.css`) — sourced from `DESIGN-airtable.md`
- The binding visual design is **`DESIGN-airtable.md`** (repo root) — an Airtable-style editorial token
  system (PO-supplied, NOT machine-generated; recorded in the `frontend-design-reference` auto-memory).
  `index.css`'s
  `:root` mirrors its tokens verbatim as CSS variables: `--colors-*` (primary `#181d26`, canvas, body
  `#333840`, hairline `#dddddd`, link `#1b61c9`, info `#254fad`, success `#006400`, the signature palette),
  `--rounded-*` (2/6/10/12/9999), `--spacing-*` (4px base → 96px section), and the Inter / Inter Display
  type scale (Haas substitute — Haas is licensed).
- **Health-state semantic tokens** (the spec lacks them; added in the shell, reused by every tab):
  `--colors-health-up` → success `#006400`, `--colors-health-down` → signature-coral `#aa2d00`,
  `--colors-health-degraded` → signature-mustard `#d9a441`, `--colors-health-maintenance` → info `#254fad`,
  plus `--colors-health-down-surface` (coral at 4% alpha, for error panels). Status is NEVER conveyed by
  color alone — each badge pairs a distinct inline **SVG** glyph + a text label (`App.tsx::getStatusBadge`).
- **Editorial→dashboard adaptation:** the design LANGUAGE is adopted (palette, type, spacing, radii,
  `button-primary`/`button-secondary`, hairline surfaces, white-canvas calm, modest weights); the
  marketing-only chrome (hero-band, full-bleed signature cards, pricing pills, logo strips) is NOT used as
  app chrome. No `:hover` styling — `DESIGN-airtable.md` documents Default + Active/Pressed only (no-hover
  policy); affordance lives on `.nav-link.nav-state-active`.

### Shell structure (`frontend/src/App.tsx`)
- `TABS` is the six-tab IA (`dashboard`, `availability`, `approvals`, `check-history`, `maintenance`,
  `publications`). Routing is **hash-based**: a `hashchange` listener maps `window.location.hash` → the
  active tab (`App.tsx:22-38`), defaulting to `dashboard`. The active tab carries `aria-current="page"`;
  nav is a semantic `<nav aria-label>`, content a `<main id="main-content">`.
- Only the **Dashboard** tab is wired to real data as the proving example; the other five render
  placeholder "coming soon" panels (their real bodies are STORY-015b–015g).

### Typed API client (`frontend/src/apiClient.ts`)
- A thin fetch seam: `API_BASE = '/api'`; `fetchComponents(): Promise<ComponentDTO[]>` calls
  `GET /api/v1/components` and throws `Error("Failed to fetch components: <status> <statusText>")` on a
  non-ok response. `ComponentDTO = { id, name, status }` mirrors the backend component-status DTO.
- The Dashboard fetch lives in `App.tsx` (`loadComponents`) with loading / error / retry UI; the error path
  is driven in tests by an MSW 500 override.

### Tests (`frontend/src/App.test.tsx`, MSW)
- Four tests render the REAL `<App />` and assert user-visible behavior; MSW (`mocks/handlers.ts` returns
  four components spanning all four health states) mocks only the network edge. Coverage: all six nav tabs
  render + routing switches the panel; the Dashboard loading→success render; an MSW-500 error panel; and
  the "Try Again" retry recovery (real handler reset). This is a genuine success+error+retry path, not a
  stub (verified at the STORY-015a review).

## Inference (synthesis, not verified)
- Hash routing is a deliberate shell-simplicity choice (no router dependency yet); a per-tab data-fetching
  story may introduce a router + a data hook (the current Dashboard fetch is split across an effect + the
  refresh handler, with an `eslint-disable react-hooks/set-state-in-effect` at `App.tsx:59` — a candidate
  cleanup when the tabs land).
- Inter is loaded via a Google Fonts `@import` in `index.css`; self-hosting is a noted follow-up (the
  system-font fallback chain already degrades gracefully).

## History
- sprint-23: created (STORY-015a — the frontend shell). Vite+React+TS SPA, six-tab hash-routed nav, typed
  API client (one proving endpoint, MSW-mocked), the `DESIGN-airtable.md` token layer + four health tokens,
  and the four-command frontend DoD gate. Review fixes (ad7d8f2): dropped dead Vite-scaffold assets
  (incl. the design-forbidden `hero.png`), removed the `:hover` rule (no-hover policy), tokenized the
  error-panel coral tint, neutral favicon + real title. Verified at ad7d8f2.
