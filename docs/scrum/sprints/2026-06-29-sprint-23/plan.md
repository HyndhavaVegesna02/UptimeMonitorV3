# Sprint 23 — Plan

**Goal.** Stand up Zone 7 (frontend) — the operator cockpit's foundation. STORY-015 (an 8) was split at
refinement into a **shell + six per-tab stories** (015a–015g); this sprint delivers the **shell (015a)**.
A Vite + React + TypeScript SPA under `frontend/`, six-tab nav + routing (placeholder panels), a typed API
client with ONE endpoint wired end to end (MSW-mocked in tests), a design system generated + persisted from
the `ui-ux-pro-max` skill, and a real **frontend DoD gate** (typecheck + lint + vitest + build). No tab
renders real data yet (015b–015g).

**Single story: STORY-015a (5 pts).** Pipeline: `impl (Sonnet) + Opus spec & quality reviewers + DoD gate`.

## Baseline
- Branch `sprint-23` cut from `main` @ `69a85bc` (sprint-22 merged). `start_tag`: `sprint-23-start`.
- Node v24 + npm v11 already installed. No backend change in this story (Vite dev proxy → local API).

## Toolchain (PO-approved at planning, 2026-06-29)
- **Build/dev:** Vite + React 18 + TypeScript (strict mode), SPA (NOT Next.js — the backend is a separate
  FastAPI service). Package manager **npm**.
- **Tests:** Vitest + React Testing Library + **MSW** (mock the API; NO live backend in any test).
- **E2E:** Playwright, **DEFERRED** to a later integration story. Chrome DevTools MCP = agent-driven
  dev/verification aid only, not the committed E2E layer. (Do NOT install Playwright this sprint.)
- **Dev ↔ API:** Vite dev-server proxy (`/api` → the local backend); **no CORS work** (deferred to STORY-017).

## Tasks (TDD where it fits; commit after each green step; scoped staging — never `git add -A`)

### T1 — Scaffold the SPA  *(AC1)*
- Create `frontend/` with Vite + React + TS (strict). `package.json` with scripts: `dev`, `build`,
  `typecheck` (`tsc --noEmit`), `lint` (eslint w/ TS + react-hooks), `test` (`vitest run`). `.gitignore`
  for `node_modules`/`dist`. Keep it ISOLATED from the Python backend — no change under `backend/`,
  `migrations/`, `scripts/`, or the Python `pyproject.toml`.
- Confirm `npm install` + `npm run build` exit 0.

### T2 — Generate + persist the design system  *(AC4)*
- Run `python .agents/skills/ui-ux-pro-max/scripts/search.py "operator monitoring status dashboard dark
  data-dense" --design-system --persist -p "Uptime Monitor"` and commit the resulting
  `frontend/design-system/MASTER.md` (move/point it under `frontend/` if the script writes elsewhere).
- Implement a small token layer (CSS variables or a Tailwind config) FROM the MASTER: typography scale,
  spacing rhythm, and SEMANTIC color tokens including health states (up / degraded / down / maintenance) +
  dark mode. No raw hex in components (`color-semantic`). MASTER.md is the design source of truth every
  later tab story reads.

### T3 — App shell: six-tab nav + routing  *(AC2, AC6)*
- A persistent nav with all six tabs (Dashboard · Availability · Approvals · Check History · Maintenance ·
  Publications) wired to client-side routes (one per tab); active tab visually indicated
  (`nav-state-active`). Each route renders a placeholder "coming soon" panel.
- Semantic landmarks (`nav`/`main`), keyboard-navigable with visible focus rings, nav contrast ≥4.5:1,
  `viewport` meta, no horizontal scroll at 375px.
- Vitest + RTL test: all six nav items render; activating a tab switches the visible panel + active state.

### T4 — Typed API client + MSW harness + one proving endpoint  *(AC3)*
- A fetch-based typed `apiClient` with a single base-URL seam → `/api` (proxied in dev). TS types mirror
  the backend DTOs for the ONE endpoint wired as the proving example (recommend the Dashboard's
  `GET /api/v1/components`, or `/health` if simpler) shown in its placeholder with loading + error states.
- MSW: handlers + Vitest setup so tests run against mocked responses. Tests drive the client's success AND
  error path against MSW — NO live API call anywhere in the suite.

### T5 — Frontend DoD gate + CLAUDE.md  *(AC5)*
- Ensure the four scripts exit 0 on a clean tree: `npm run typecheck`, `npm run lint`, `npm run test`,
  `npm run build`. These four ARE the frontend DoD gate (parallel to the Python six-command gate).
- Update `CLAUDE.md` IN THIS STORY's commits (command-sync agreement): a "Frontend (Zone 7)" key-commands
  section, the four-command frontend gate, and the tooling inventory rows (Node/npm/Vite/Vitest/RTL/MSW;
  Playwright noted as deferred). Do NOT modify PO-authored sections; append only.

## Conventions checklist (held at quality review — frontend edition)
- **vercel-react-best-practices** is the quality reviewer's checklist: no components defined inside
  components (§5.4); derive state during render, don't mirror props in effects (§5.1); narrow effect deps;
  no barrel-import bloat; explicit conditional rendering; stable keys.
- **Real-component tests** — RTL renders the REAL component/shell and asserts user-visible behavior; MSW
  mocks only the network edge, never the unit under test (the frontend reading of the real-object-tests
  agreement).
- **ui-ux-pro-max CRITICAL floor** — accessibility (contrast, focus, keyboard, color-not-only), touch
  targets, no layout-shift; SVG icons not emoji.
- **Empty/error/loading states** — the proving endpoint shows all three; tests cover success + error.
- **Clean committed tree** — commit any formatter (prettier/eslint --fix) output in the SAME step; never
  leave it uncommitted. Scoped staging; never `git add -A`.
- **Command-sync** — the new frontend commands + gate land in CLAUDE.md in-story.

## DoD gate
- **Frontend gate (new, established here), all exit 0 on a clean committed tree, run from `frontend/`:**
  `npm run typecheck` · `npm run lint` · `npm run test` · `npm run build`.
- **Python six-command gate must stay green** (expected trivially — no backend change): `pytest`,
  `lint-imports`, `python scripts/check_fk_direction.py`, `alembic upgrade head`, `ruff check`,
  `ruff format --check`. The `.agents` ruff-exclude from STORY-016c stays; add `frontend` to the ruff
  exclude IF (and only if) `ruff` starts scanning it (it shouldn't — different tree; confirm, don't assume).

## Guardrails for the implementer
Build to THIS plan + the STORY-015a AC + dossier §17 + the named skills (`ui-ux-pro-max` for the design
system, `vercel-react-best-practices` for code quality). This is the FRONTEND SPRINT 0 — the shell, not the
tabs: wire exactly ONE endpoint as the proving example; the six tab bodies are 015b–015g and must stay
placeholders. Do NOT touch the Python backend (use the Vite dev proxy). Do NOT install Playwright (E2E is
deferred). Do NOT write `.scrum/` board state. Do NOT run the reviewers or merge. Stop-and-report on genuine
ambiguity or a 3× effort overrun. The `ui-ux-pro-max` script is Python (`python .agents/skills/...`); the
`.agents/` dir is excluded from ruff already — do not lint it.
