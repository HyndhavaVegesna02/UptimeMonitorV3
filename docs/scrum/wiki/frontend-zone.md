---
title: Frontend zone — the operator-cockpit SPA (shell)
code_refs: [frontend/package.json, frontend/vite.config.ts, frontend/index.html, frontend/src/AppShell.tsx, frontend/src/nav/tabs.ts, frontend/src/nav/Nav.tsx, frontend/src/api/client.ts, frontend/src/api/types.ts, frontend/src/theme/resolveTheme.ts, frontend/src/theme/ThemeContext.tsx, frontend/src/styles/tokens.css, frontend/src/components/index.ts, frontend/src/mocks/handlers.ts]
verified_sha: 08d91e7
verified_sprint: sprint-25
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
  ink text + accent bottom-border, inactive = ink-subtle. The five non-Dashboard pages are
  placeholders that stories 015c–015g replace wholesale.
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
  with the shell so per-tab stories don't copy-paste.
- **Typed API client:** `frontend/src/api/client.ts` — fetch-based, single `/api` base-URL seam,
  wraps network + non-2xx into a typed `ApiError`. DTO types in `frontend/src/api/types.ts`
  mirror the backend `api/v1/*/models.py` shapes. `statusMapping.ts` maps the backend
  `ComponentStatus` vocabulary onto health tokens (flagged provisional pending STORY-015b's real
  Dashboard).
- **Test I/O boundary:** MSW is the ONLY mocked edge (`frontend/src/mocks/handlers.ts` +
  `server.ts`, wired in `frontend/src/test/setup.ts`). Tests assert via accessible roles/text and
  drive real behavior (success + error→retry against MSW); no component/hook under assertion is
  mocked. 63 tests at STORY-015a.
- **The per-tab pattern to copy (015b–015g):** a page in `pages/` (or a feature under
  `features/<tab>/`) + a data-fetch that follows `features/dashboard/ComponentsProbe.tsx` —
  discriminated-union fetch state, a cancelled-guard in the effect, an `attempt`-keyed retry, and
  a four-state render (loading / error+retry / empty / success) built from the shared primitives.
  A tab story touches only its own page/feature files plus additive appends to `api/client.ts`,
  `api/types.ts`, and `mocks/handlers.ts`; the routing table `tabs.ts` is already fully populated.

## Inference (synthesis, not verified)
- The shared append-points (`api/client.ts`, `api/types.ts`, `mocks/handlers.ts`) are the only
  files multiple tab stories edit. STORY-041 (frontend pattern hardening, backlog) captures the
  reviewer's suggestion to modularize the MSW handlers and tighten the client's error-wrapping
  before those seams are copied six times.

## History
- sprint-25: created (STORY-015a — the frontend shell, second attempt, built guided by
  `DESIGN-linear.app.md`; dark+light themes; the first attempt was reverted in `521764c`).
  verified_sha = 08d91e7.
