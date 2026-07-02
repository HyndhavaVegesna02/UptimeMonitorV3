---
id: STORY-017
title: Deployment topology
type: chore
---

## Context
Spec: dossier §17 (deployment topology). The five pieces in three categories; migrations
as a separate release step before serving.

## Description
Backend on Railway (single instance; `alembic upgrade head` as a release step on the
Neon DIRECT connection, then app boots: seed topology → start scheduler → serve on the
pooled connection). Frontend on Vercel. Sock Shop on Railway service #2 + the toggle-able
failure shim in front of one monitored route. Secrets in Railway env (config references
env var NAMES, never values). Tuned demo cadence (~1-min monitors, short poll interval).
CORS restricted to the Vercel origin.

## Acceptance Criteria (draft — confirm at refinement)
- [ ] AC1: A push deploys via the migrate-release-then-serve flow.
- [ ] AC2: A failed migration halts the deploy and leaves the old container serving
      (fail-safe, not crash-loop).
- [ ] AC3: The demo thread (STORY-016) runs on the deployed infra.
- [ ] AC4: Secrets live in Railway env; CORS restricted to the Vercel origin.

## Audit inputs (2026-07-02 full-codebase audit — fold into the AC at refinement)
- **D1 — uvicorn dependency home:** `uvicorn[standard]` currently lives in the DEV extras
  (`pyproject.toml`, STORY-042) but on Railway it IS the production ASGI server. Move it to runtime
  deps (or a dedicated deploy extra Railway installs) as part of this story.
- **D2 — frontend production API routing:** `frontend/src/api/client.ts::API_BASE_URL = '/api'` is
  reachable in dev only via the Vite proxy. On Vercel this needs a rewrite (vercel.json `/api/*` →
  the Railway origin) or an env-injected absolute base URL + the CORS work this story owns. The
  single-seam client was built for exactly this swap.
- **D3 — two processes, not one:** the API server (`composition/asgi.py`) and the pull-loop
  (`python -m src.composition.run`) are separate long-running processes sharing the pooled
  `DATABASE_URL` — Railway needs both (two services or a service + worker). Both seed topology at
  boot; the seed is idempotent upserts, so double-seeding is safe — state that explicitly in the
  plan.
- **Secrets:** production reads REAL env vars (Railway), so the STORY-043 `.env` entrypoint loading
  must remain a no-op in production (`load_dotenv` semantics: never override set env vars).

## Open Questions
- Confirm Railway/Vercel/Neon account access and the secret-provisioning plan at refinement.
- D2 mechanism choice: Vercel rewrite (keeps same-origin, no CORS for the browser) vs absolute base
  URL + CORS. The dossier says CORS restricted to the Vercel origin — decide which shape at
  refinement.

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §17. Status: draft — refine before its sprint.
- 2026-07-02: audit inputs D1–D3 + secrets note appended from the full-codebase audit (deployment
  lens). Still draft — refine before its sprint.
