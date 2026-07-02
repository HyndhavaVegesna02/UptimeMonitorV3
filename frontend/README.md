# Uptime Monitor V3 — frontend

The operator-cockpit SPA (dossier §17, "two surfaces, not one" — this is the
internal dashboard; the public Statuspage is the other surface). Vite + React
+ TypeScript (strict), talking to the backend at `/api` (proxied to the local
FastAPI dev server; see `vite.config.ts`).

Design reference: `../DESIGN-linear.app.md` (a guide, not a copy target — see
`docs/scrum/sprints/2026-07-02-sprint-25/plan.md` for the binding design brief).

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
