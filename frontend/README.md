# Uptime Monitor V3 — frontend

**Under active greenfield rebuild — sprint-59; structure settling across
STORY-120–122** (the PO rejected two prior attempts and directed a
from-scratch rebuild guided by the approved refimg prototype).

The operator-cockpit SPA (dossier §17, "two surfaces, not one" — this is the
internal dashboard; the public Statuspage is the other surface). Vite + React
+ TypeScript (strict), talking to the backend at `/api` (proxied to the local
FastAPI dev server; see `vite.config.ts`).

Design reference (binding): `docs/scrum/sprints/2026-07-18-ui-prototyping/
prototypes/refimg-dashboard.html` + `.../round-2-refimg-system.md` — a
light-first, cool-grey-canvas, single-sky-blue-accent system with a
7-status health palette and WCAG-AA-verified contrast tokens. Icons are
`@phosphor-icons/react`, wrapped by a thin `Icon` component. `/styleguide`
renders every primitive in every state.

Fonts are self-hosted via `@fontsource/inter` (imported in
`src/styles/global.css`, loaded from `main.tsx`) — no runtime Google-CDN
`<link>`.

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
