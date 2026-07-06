---
title: Deployment topology — Railway (api + worker) + Vercel, config-as-code + CORS
code_refs: [pyproject.toml, railway.toml, frontend/vercel.json, docs/DEPLOY.md, backend/src/composition/app.py, backend/src/composition/settings.py]
verified_sha: 0ae56a2
verified_sprint: sprint-35
status: verified
---

## Facts (verified against code)

### Two Railway services, one repo (D3, dossier §17)
- `api` (`uvicorn src.composition.asgi:app --host 0.0.0.0 --port $PORT`) and
  `worker` (`python -m src.composition.run`) are two independent
  long-running Railway services created from the SAME repo/branch, both
  reading the POOLED `DATABASE_URL`. Neither has a hard runtime dependency
  on the other being up.
- A release step, `alembic upgrade head`, runs ONCE before `api` serves, on
  the DIRECT `DATABASE_URL_DIRECT` (CLAUDE.md "URL dialect note": the direct
  URL must carry the `postgresql+psycopg://` prefix since the release step
  runs the built image, not the dev venv). `worker` has no release step —
  it never migrates. AC3's fail-safe (a failing migration halts the deploy,
  previous container keeps serving) is Railway's own release-command
  semantics, not custom code.
- Both processes seed topology at boot from `config/apps/*.yaml`
  (`composition/seed.py::seed_topology`, upserts) — double-seeding across
  both services, or across a restart, is safe by construction (see
  [[config-layer]], [[migrations-and-db]]).

### D1 — `uvicorn[standard]` is a runtime dependency
- `pyproject.toml` `[project.dependencies]` now includes `uvicorn[standard]`
  (moved from the `dev` optional-dependencies group, sprint-35 task 1) — it
  IS the production ASGI server the `api` service's start command invokes,
  not a local-only dev convenience. `[project.optional-dependencies].dev` is
  now `["pytest", "import-linter", "ruff"]`.

### Railway config-as-code — `railway.toml` (repo root)
- Built to [Config as Code](https://docs.railway.com/config-as-code),
  [its reference](https://docs.railway.com/reference/config-as-code), and
  the live [JSON Schema](https://railway.com/railway.schema.json) (fetched
  and the file validated against it via `tomllib` at authoring time).
- `[build] builder = "RAILPACK"` — Railway's current default builder
  (Nixpacks' successor; auto-detects the Python project via
  `pyproject.toml`).
- `[deploy] preDeployCommand = "alembic upgrade head"` — Railway's actual
  field name for what the story calls the "release command"; runs on
  `DATABASE_URL_DIRECT` before the new deployment is promoted.
- `[deploy] startCommand = "uvicorn src.composition.asgi:app --host 0.0.0.0
  --port $PORT"` and `[deploy] healthcheckPath = "/api/v1/health"` — the
  `api` service only.
- **This file expresses ONLY the `api` service.** Railway's config-as-code
  rule ("configuration defined in code will always override values from the
  dashboard") means a SECOND service resolving the same file would inherit
  `startCommand`/`healthcheckPath`, which is wrong for `worker` (no HTTP
  port). Per Railway's own [monorepo doc](https://docs.railway.com/deployments/monorepo)
  ("Deploying a shared monorepo": "define a separate custom start command in
  Service Settings for each project") and the
  [Help Station guidance](https://station.railway.com/questions/pre-deploy-command-from-railway-config-f-b5328546)
  for exactly this two-service-one-repo shape, `worker`'s start command is a
  CONSOLE-ONLY field — `docs/DEPLOY.md` Part A4 tells the PO to set it
  directly in `worker`'s Settings and disable its healthcheck, and to verify
  post-deploy (via the deployment details "config source" panel) that
  `worker` actually resolved to `python -m src.composition.run`, not the
  api's uvicorn command.

### Vercel — `frontend/vercel.json`
- Two rewrites, evaluated in array order (first match wins): `/api/:path*`
  → `https://REPLACE_WITH_RAILWAY_API_ORIGIN/api/:path*` (a placeholder —
  see below), THEN `/(.*)` → `/index.html` (SPA fallback). Order matters:
  the API rule must precede the catch-all or the catch-all would swallow
  API calls.
- The SPA fallback is REQUIRED, not optional: `frontend/src/App.tsx` uses
  `react-router-dom`'s `BrowserRouter` with real client-side paths
  (`/availability`, `/approvals`, `/check-history`, `/maintenance`,
  `/publications` — `frontend/src/nav/tabs.ts`), so a direct load of any of
  those five paths on Vercel 404s without the fallback rewrite.
- The `destination` origin is a clearly-marked placeholder
  (`REPLACE_WITH_RAILWAY_API_ORIGIN`), not env-substituted — verified
  against [Vercel's project configuration doc](https://vercel.com/docs/project-configuration),
  which states vercel.json "should not include any environment variables,
  API calls, or other build-time logic." `docs/DEPLOY.md` Part B1 has the PO
  fill in the real Railway `api` origin and commit that one-line edit before
  importing the Vercel project.
- `frontend/src/api/client.ts::API_BASE_URL` is untouched (`'/api'`) — the
  browser only ever calls same-origin paths; Vercel's edge does the
  cross-origin hop server-side.

### CORS — composition-layer `CORSMiddleware` (AC2)
- `backend/src/composition/settings.py::load_cors_allowed_origins` reads
  `CORS_ALLOWED_ORIGINS` (comma-separated; blank entries dropped after
  stripping whitespace) — unset/empty falls back to
  `DEFAULT_CORS_ALLOWED_ORIGINS = ("http://localhost:5173",)` (Vite's
  default dev port; `frontend/vite.config.ts` sets no explicit
  `server.port`). Env var NAME only — no value is ever read into this repo.
- `backend/src/composition/app.py::create_app` wires
  `fastapi.middleware.cors.CORSMiddleware` (imported from
  `fastapi.middleware.cors`, NOT `starlette` directly, though it is the same
  class re-exported) with `allow_origins=load_cors_allowed_origins()`,
  `allow_credentials=False` (no cookie/session auth exists yet — the
  2026-06-23 defer-auth-cleanly agreement), `allow_methods=["*"]`,
  `allow_headers=["*"]`. Lives in the composition zone only — `core`/`api`
  are untouched; `lint-imports` stays 5 kept / 0 broken.
- Tested test-first, real requests against `create_app` (no mocked
  middleware — `backend/tests/test_cors.py`): allowed-origin preflight
  (`OPTIONS` + `Access-Control-Request-Method`) returns 200 with
  `access-control-allow-origin` echoing the origin; an allowed-origin simple
  `GET` also echoes it; a disallowed origin gets NO `access-control-allow-
  origin` header (the request itself still succeeds server-side — CORS is a
  browser-enforced contract, not a server-side block); a request with NO
  `Origin` header (the Vercel rewrite's server-to-server hot path) is
  completely unaffected — no CORS header either way; the unset-env default
  is pinned by asserting `http://localhost:5173` is granted and an arbitrary
  other origin is not.

### The runbook — `docs/DEPLOY.md`
- Numbered PO console steps for both platforms (project/service creation,
  the exact env var NAME tables per service — no values), the release-step
  field placement, the healthcheck path, and the Vercel rewrite-placeholder
  fill-in step.
- AC3 fail-safe demonstration procedure: temporarily set a wrong
  `DATABASE_URL_DIRECT` on `api`, redeploy, observe the release step fail
  and the OLD deployment keep serving (`/api/v1/health` never drops), fix,
  redeploy clean.
- AC4 live-verification checklist: watermark advances across two cycles
  (Neon query or `worker` logs), all six tabs render through the Vercel
  rewrite, one mutation round-trips end-to-end through the deployed stack
  (the sample-mode toggle — [[sample-mode]] — or a maintenance-window
  schedule).

## Inference (synthesis, not verified)
- The two-Railway-service, one-repo shape is a genuine platform limitation
  (config-as-code has no native multi-start-command expression), not a
  design choice this project could have avoided by writing the config
  differently — hence the console-field fallback is permanent, not a
  stopgap pending a better Railway feature.
- `railway.toml`'s TOML format (over `railway.json`) was chosen specifically
  because TOML supports `#` comments, letting the file self-document its own
  single-service scope and citations inline — `railway.schema.json`'s root
  object has `additionalProperties: false`, so a JSON sibling could not
  carry an equivalent inline citation without risking schema-validation
  rejection on a live deploy.

## History
- sprint-35 (STORY-017 review-minors fix): re-verified at HEAD — DEPLOY.md gained the trailing-slash CORS warning (review MINOR-3); also clears the spec reviewer's note that verified_sha (1727c49) trailed HEAD. No Facts changed. verified_sha = 0ae56a2.
- sprint-35 (STORY-017): created. D1 (`uvicorn[standard]` → runtime deps),
  AC2 (composition-layer CORS, env-driven allowlist, test-first), AC1/AC3
  (`railway.toml`, the `api`-service-only config-as-code file), AC1/D2
  (`frontend/vercel.json`, the `/api/*` rewrite + SPA fallback), and AC5/AC6
  (`docs/DEPLOY.md`, this article) landed together. Six backend gates: five
  green (`pytest` deferred — the throwaway DB + API server + live loop were
  live-running against the shared DB during this session, so pytest itself
  was left for an orchestrator run against a stopped stack, single-writer
  rule); `lint-imports` 5 kept / 0 broken; FK-direction 11/0; `alembic
  upgrade head` clean; `ruff check`/`ruff format --check` clean. Three
  frontend gates green (`npm test` 222 passed, `npm run build`, `npm run
  lint`). verified_sha = 1727c49.
