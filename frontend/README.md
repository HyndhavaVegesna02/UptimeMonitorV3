# Uptime Monitor V3 — frontend

The operator-cockpit SPA (dossier §17, "two surfaces, not one" — this is the
internal dashboard; the public Statuspage is the other surface). Vite + React
+ TypeScript (strict), talking to the backend at `/api` (proxied to the local
FastAPI dev server; see `vite.config.ts`).

**Design reference (current):** the PO-built UI at `C:\Hyn\new ui\ops-pulse-react`
— a *visual* reference only (no data layer). The in-repo capture is authoritative:
`docs/scrum/sprints/2026-07-28-sprint-62/` holds `newui-01..08-*.png` (all six
routes at 1440 light+dark and 390) plus `ui-backend-gap-analysis.md`, which maps
every screen to the `api/v1` surface. The design system gets ported from it
(tokens, glass surfaces, dark inset sidebar), ending with a PO look-and-feel
checkpoint on the styleguide + shell *before* pages are built on the language.

*Design lineage (history, not guidance):* `../DESIGN-linear.app.md` guided the
sprint-25 shell; sprint 38 retuned the palette/type-scale values to an imported
*Operator Dashboard* mock while keeping that shape. Both are superseded by the
reference above.

Fonts are self-hosted via `@fontsource/geist` + `@fontsource/geist-mono`
(imported in `src/styles/global.css`, loaded from `main.tsx`) — no runtime
Google-CDN `<link>`.

## Commands

| Task           | Command         |
| -------------- | --------------- |
| Install        | `npm install`   |
| Dev server     | `npm run dev`   |
| Build (+ tsc)  | `npm run build` |
| Test (Vitest)  | `npm test`      |
| Lint (ESLint)  | `npm run lint`  |

The dev server proxies `/api/*` to `http://localhost:8000` (the local
`uvicorn` run of the backend). Start the backend separately per the root
`CLAUDE.md`.
