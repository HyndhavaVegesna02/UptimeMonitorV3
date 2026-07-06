# Deployment runbook — Uptime Monitor V3 (STORY-017, dossier §17)

PO-driven console runbook (2026-07-06 modality decision): the team prepared
all config/code (this branch); the PO executes the numbered steps below in
the Railway and Vercel consoles. No secret VALUE appears anywhere in this
document — every table below lists env var NAMES only (AC5).

Topology (pinned facts, `docs/scrum/sprints/2026-07-06-sprint-35/plan.md`):
- **Railway**: two long-running services from this one repo —
  `api` (`uvicorn src.composition.asgi:app`) and
  `worker` (`python -m src.composition.run`) — both reading the POOLED
  `DATABASE_URL`. A release step (`alembic upgrade head`) runs on the DIRECT
  `DATABASE_URL_DIRECT` before `api` serves (config-as-code — `railway.toml`
  at the repo root). Both processes seed topology at boot from
  `config/apps/*.yaml`; the seed is idempotent upserts, so double-seeding
  (both services booting, or a restart) is always safe.
- **Vercel**: `frontend/` deployed as a Vite SPA. `frontend/vercel.json`
  rewrites `/api/*` to the Railway `api` service's public origin and falls
  back every other path to `/index.html` (client-side routing —
  `App.tsx`'s `BrowserRouter` serves real paths: `/availability`,
  `/approvals`, `/check-history`, `/maintenance`, `/publications`).
  `frontend/src/api/client.ts::API_BASE_URL` stays `'/api'` — the browser
  never talks cross-origin.
- **CORS**: the `api` service restricts cross-origin requests to
  `CORS_ALLOWED_ORIGINS` (comma-separated; unset defaults to
  `http://localhost:5173` only) — defense-in-depth behind the Vercel
  rewrite, per the 2026-06-23 agreement.

Docs this runbook builds to (cited in `railway.toml` / `frontend/vercel.json`
too): [Railway — Config as Code](https://docs.railway.com/config-as-code),
[Railway — Config as Code reference](https://docs.railway.com/reference/config-as-code),
[Railway — Monorepo](https://docs.railway.com/deployments/monorepo),
[Railway — Build and start commands](https://docs.railway.com/builds/build-and-start-commands),
[Vercel — Project configuration](https://vercel.com/docs/project-configuration),
[Vercel — Rewrites](https://vercel.com/docs/rewrites).

---

## Part A — Railway (backend: two services + release step)

### A1. Create the project
1. Railway dashboard → New Project → Deploy from GitHub repo → select this
   repo, the deploy branch (the sprint-35 merge target, e.g. `main`).
   Railway creates the FIRST service from this — call it `api` (rename it in
   Settings → General if it defaulted to the repo name).

### A2. Attach Neon Postgres
2. This project uses an EXISTING Neon project (PO decision, 2026-07-06 — not
   a Railway-provisioned Postgres plugin). No action needed here beyond
   having the two Neon connection strings (pooled + direct) ready for A4.

### A3. Configure the `api` service
3. `api` Settings → confirm the "Config File Path" resolves to the repo-root
   `railway.toml` (default when unset). This file already sets (verify, do
   not retype): `build.builder = RAILPACK`; `deploy.preDeployCommand =
   "alembic upgrade head"` (the release step — runs on `DATABASE_URL_DIRECT`,
   BEFORE `api` serves, per AC3's fail-safe: a nonzero exit halts the deploy,
   the previous container keeps serving); `deploy.startCommand = "uvicorn
   src.composition.asgi:app --host 0.0.0.0 --port $PORT"`;
   `deploy.healthcheckPath = "/api/v1/health"`.
4. `api` Settings → Networking → Generate Domain (public HTTP). Copy this
   origin — it is the value Part B needs for the Vercel rewrite.
5. `api` Settings → Variables — set exactly these NAMES (values from the PO,
   never committed):

   | Env var                | Value source                                    |
   | ----------------------- | ------------------------------------------------ |
   | `DATABASE_URL`          | Neon POOLED (PgBouncer) connection string, plain `postgresql://` form |
   | `DATABASE_URL_DIRECT`   | Neon DIRECT connection string, `postgresql+psycopg://` form (CLAUDE.md "URL dialect note" — the release step's `alembic upgrade head` runs the built image via SQLAlchemy 2/psycopg3, which needs the `+psycopg` dialect prefix explicitly) |
   | `CORS_ALLOWED_ORIGINS`  | The Vercel production origin, e.g. `https://<your-project>.vercel.app` (comma-separate a preview-URL pattern too if you also want previews to hit this API) |

### A4. Configure the `worker` service
6. In the SAME project, "+ New" → GitHub Repo → the same repo/branch again.
   Rename it `worker`.
7. `worker` Settings → Deploy → Custom Start Command:
   `python -m src.composition.run`. **Do NOT** point this service at the
   repo-root `railway.toml` for its start command — per Railway's own
   monorepo guidance and the fact that "configuration defined in code always
   overrides the dashboard", `railway.toml`'s `startCommand`/
   `healthcheckPath` are the `api` service's alone (see the comment block at
   the top of `railway.toml` for the full rationale + citations). Leave
   `worker`'s "Config File Path" unset/blank if the console offers that
   choice; otherwise verify after the first deploy via the deployment
   details page's "config source" panel that `worker` is actually running
   `python -m src.composition.run`, not the api's uvicorn command.
8. `worker` Settings → Deploy → Healthcheck: **disable/leave unset** — this
   process exposes no HTTP port; a healthcheck against it would never
   succeed and would crash-loop a perfectly healthy worker.
9. `worker` Settings → Variables — set exactly these NAMES:

   | Env var                | Value source                                    |
   | ----------------------- | ------------------------------------------------ |
   | `DATABASE_URL`          | SAME Neon POOLED connection string as `api`      |
   | `DYNATRACE_ENV_URL`     | Dynatrace tenant base URL (Grail DQL execute endpoint) |
   | `DYNATRACE_API_TOKEN`   | Dynatrace platform token (scopes `storage:buckets:read storage:events:read`) |
   | `STATUSPAGE_PAGE_ID`    | Statuspage page id                                |
   | `STATUSPAGE_API_KEY`    | Statuspage API token                              |

   `worker` does NOT need `DATABASE_URL_DIRECT` (it never migrates) or
   `CORS_ALLOWED_ORIGINS` (it serves no HTTP).

### A5. Release-step field, restated
   The ONLY release/migrate command in this topology is `api`'s
   `preDeployCommand` (`alembic upgrade head` on `DATABASE_URL_DIRECT`,
   `railway.toml`). `worker` has no release step — it never migrates, only
   reads the already-migrated schema.

### A6. First deploy + healthcheck
10. Trigger a deploy on `api` first (so migrations land before `worker`
    starts reading the schema), then `worker`.
11. Confirm `api`'s deployment goes "Active" and
    `https://<api-origin>/api/v1/health` returns `{"status": "ok"}`.
12. Confirm `worker`'s logs show the pull-loop cycling (no crash-loop).

---

## Part B — Vercel (frontend)

### B1. Fill in the rewrite target
1. Edit `frontend/vercel.json`: replace the placeholder
   `REPLACE_WITH_RAILWAY_API_ORIGIN` in the `destination` field with the real
   `api` service origin from A3 step 4 (e.g.
   `https://api-production-xxxx.up.railway.app`). Commit this one-line fill-in
   (vercel.json is deliberately static — Vercel's own docs say it "should not
   include any environment variables, API calls, or other build-time logic",
   so there is no env-substitution alternative; verified against
   https://vercel.com/docs/project-configuration).

### B2. Import the project
2. Vercel dashboard → Add New → Project → import this repo.
3. Root Directory: set to `frontend` (the SPA is isolated under
   `frontend/`, no shared build step with the backend — Vercel auto-detects
   the Vite framework preset from `frontend/package.json` once the root is
   set; no build/output overrides needed).
4. No environment variables are required for the frontend build itself
   (`API_BASE_URL` is the `'/api'` literal in `client.ts`, not an env var).
5. Deploy.

### B3. Verify
6. Load the Vercel production URL → Dashboard tab renders.
7. Directly load `https://<vercel-url>/availability` (or any of the other
   five tab paths) in a NEW tab (not client-side navigation) — must render,
   not 404, proving the SPA-fallback rewrite works.
8. Open browser devtools Network tab, confirm `/api/v1/...` calls resolve
   (same-origin, 200s) — proving the `/api/*` rewrite reaches Railway.

---

## AC3 — fail-safe release demonstration (do this once, live)

Goal: prove a failing migration halts the deploy with the OLD container
still serving — never a crash-loop.

1. Note the current `api` deployment is Active and healthy
   (`/api/v1/health` returns 200).
2. In `api` Settings → Variables, temporarily set `DATABASE_URL_DIRECT` to an
   obviously-wrong value (e.g. append a typo to the hostname — still a
   value never written to this repo).
3. Trigger a redeploy of `api` (e.g. an empty commit, or "Redeploy" in the
   dashboard).
4. Observe: the release step (`alembic upgrade head`, run against the broken
   URL) fails and exits non-zero. Railway does NOT promote the new
   deployment — confirm the OLD deployment is still "Active" and
   `/api/v1/health` keeps returning 200 throughout (no downtime, no
   crash-loop).
5. Fix: restore `DATABASE_URL_DIRECT` to the correct value.
6. Trigger a redeploy — confirm the release step now succeeds and the new
   deployment goes Active cleanly.
7. Record the evidence (screenshots/log excerpts of the failed release +
   the successful one) into `sprint-current.yaml`'s `dod_evidence` per the
   2026-06-29 agreement (this runs BEFORE the sprint closes).

## AC4 — live verification checklist (do this once, live, with the PO)

- [ ] **Worker ingests real Grail observations, watermark advances across
      two cycles.** Either query Neon directly (`select signal_key,
      last_observed_at from watermarks order by last_observed_at desc;`
      twice, ~1 cycle apart, confirm the timestamp moved forward for at
      least one signal) or watch `worker`'s Railway logs for two consecutive
      successful cycle log lines.
- [ ] **All six tabs render on the Vercel URL** through the `/api/*`
      rewrite: Dashboard, Availability, Approvals, Check History,
      Maintenance, Publications — each shows real (not error/empty-state-only)
      data once the worker has run at least one cycle.
- [ ] **One mutation round-trips.** Either:
  - the Dashboard's sample-mode toggle (`PUT /api/v1/sample-mode` →
    `GET /api/v1/sample-mode` reflects the flip — see
    `docs/scrum/wiki/sample-mode.md`), or
  - a Maintenance-window schedule (`POST /api/v1/maintenance` from the
    Maintenance tab UI → `GET /api/v1/maintenance` / the tab's list shows
    the new window).

  Confirm the round-trip through the DEPLOYED stack (Vercel UI → Railway
  `api` → Neon), not a local run.
- [ ] Evidence (what was verified, timestamps, which mutation was used)
      recorded into `sprint-current.yaml`'s `dod_evidence` before the sprint
      closes (2026-06-29 agreement — never deferred).

---

## Notes

- **Idempotent seeding**: both `api` and `worker` run the SAME boot-time
  topology seed (`config/apps/*.yaml` → `apps`/`components`/`signals` upsert)
  independently. Double-seeding across two processes, or across restarts, is
  safe — the seed is `ON CONFLICT DO NOTHING`/upsert, never a destructive
  write (see `docs/scrum/wiki/migrations-and-db.md`).
- **No `.env` file is read or required in production.** Both entrypoints
  read real process env vars set in the Railway console (`os.environ`, via
  `src.composition.settings`); STORY-043's local `.env`-loading convenience
  (still backlogged) must never override already-set env vars when it
  lands — production must never depend on a `.env` file existing.
- **Local stack stays optional but supported** — see CLAUDE.md "Run the app
  locally" for the throwaway-DB + uvicorn + live-loop + `npm run dev` recipe;
  nothing in this runbook changes that path.
- **Full env var name inventory** (AC5 — repeated here for a single
  at-a-glance table; no values, ever):

  | Service   | Env var                | Purpose                                    |
  | --------- | ----------------------- | ------------------------------------------ |
  | `api`     | `DATABASE_URL`          | pooled Neon connection (app runtime)       |
  | `api`     | `DATABASE_URL_DIRECT`   | direct Neon connection (release step only) |
  | `api`     | `CORS_ALLOWED_ORIGINS`  | comma-separated allowed browser origins    |
  | `worker`  | `DATABASE_URL`          | pooled Neon connection (app runtime)       |
  | `worker`  | `DYNATRACE_ENV_URL`     | Dynatrace tenant base URL                  |
  | `worker`  | `DYNATRACE_API_TOKEN`   | Dynatrace platform token                   |
  | `worker`  | `STATUSPAGE_PAGE_ID`    | Statuspage page id                         |
  | `worker`  | `STATUSPAGE_API_KEY`    | Statuspage API token                       |
