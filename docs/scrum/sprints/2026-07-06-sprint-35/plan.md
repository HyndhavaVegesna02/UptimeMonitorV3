# Sprint 35 — plan (locked 2026-07-06)

**Goal:** The system runs deployed: backend (API + pull-loop worker) on Railway against
Neon with a migrate-then-serve release step, frontend on Vercel through the `/api`
rewrite, secrets only in platform env, CORS restricted — the local stack becomes optional.

**Committed:** STORY-017 (5) alone, at measured velocity 5.
**Modality (PO decision):** the PO drives the Railway/Vercel consoles from a
team-authored runbook; console actions are sanctioned PO-interaction points mid-sprint.

---

## STORY-017 — Deployment topology (chore, 5 pts, full pipeline on the code diff)

Story file: `docs/scrum/stories/STORY-017-deployment-topology.md` (refined 2026-07-06 —
the four PO decisions and folded audit inputs D1–D3 are recorded there; AC1–AC6 binding).

### Pinned facts the implementer builds to (do not re-derive)

- Two long-running processes (D3): `api` = `uvicorn src.composition.asgi:app --host
  0.0.0.0 --port $PORT`; `worker` = `python -m src.composition.run`. Both read the POOLED
  `DATABASE_URL`; the release step runs `alembic upgrade head` on `DATABASE_URL_DIRECT`
  (dialect note: direct URL uses the `postgresql+psycopg://` form, pooled stays plain —
  CLAUDE.md "URL dialect note"). Both seed topology at boot; the seed is idempotent
  upserts, double-seeding is safe (state this in the runbook).
- Routing (D2, decided): `frontend/vercel.json` rewrites `/api/*` to the Railway api
  origin; `client.ts::API_BASE_URL = '/api'` is NOT touched. The Railway origin is a
  placeholder/env-documented value in the repo — never a hardcoded personal URL if Vercel
  supports env substitution; otherwise a clearly-marked placeholder the runbook tells the
  PO to fill.
- CORS (defense-in-depth per dossier + 2026-06-23 agreement): FastAPI `CORSMiddleware` in
  the composition layer (`create_app`/asgi wiring — NOT in core or api zones), allowlist
  driven by an env var (e.g. `CORS_ALLOWED_ORIGINS`, comma-separated) defaulting to
  localhost dev origins; config/docs reference env var NAMES only.
- Secrets (AC5): env var names per service — api: `DATABASE_URL`, `CORS_ALLOWED_ORIGINS`;
  worker: `DATABASE_URL`, `DYNATRACE_ENV_URL`, `DYNATRACE_API_TOKEN`,
  `STATUSPAGE_PAGE_ID`, `STATUSPAGE_API_KEY`; release: `DATABASE_URL_DIRECT`. No values
  anywhere in the repo, ever.
- `uvicorn[standard]` (D1) moves from `[project.optional-dependencies].dev` to runtime
  `[project.dependencies]` in `pyproject.toml`.

### Task breakdown (TDD where testable; commit after every green step)

- [x] 1. D1 pyproject move (`uvicorn[standard]` → runtime deps); reinstall editable;
      six backend gates green (pyproject is a shared wiki `code_ref` — sweep at the end
      will flag several articles).
- [x] 2. CORS, test-first: composition-layer `CORSMiddleware` wiring with env-driven
      allowlist. Tests (httpx against `create_app`): allowed origin → preflight OK +
      `access-control-allow-origin` echoed; disallowed origin → no CORS grant; request
      WITHOUT an Origin header (the rewrite's server-to-server hot path) → behavior
      unchanged. Empty/unset env → localhost-dev-only default, tested.
- [x] 3. Railway config-as-code: whatever Railway's current mechanism supports
      (railway.json/toml; else Procfile + documented console fields) expressing: build,
      the release command (`alembic upgrade head`), the api start command, the worker
      start command. Cite the Railway doc used. If two services can't share one config
      file, one config + explicit runbook fields for the second service.
- [x] 4. `frontend/vercel.json`: the `/api/*` rewrite (+ SPA fallback if Vercel needs it
      for client-side routing — verify against the six-tab router!). Three frontend gates
      green.
- [x] 5. Runbook `docs/DEPLOY.md`: numbered PO console steps — Railway project, two
      services from this repo, per-service env var NAMES table, release command
      placement, healthcheck; Vercel import of `frontend/`, the rewrite target, env vars
      if any. Includes the AC3 fail-safe demonstration step (deliberately failing
      release once — e.g. a temporarily wrong `DATABASE_URL_DIRECT` — and observing the
      old container keep serving) and the AC4 verification checklist.
- [x] 6. CLAUDE.md deployed-topology section (command-sync agreement — same commit as
      the config it documents); new wiki article `docs/scrum/wiki/deployment-topology.md`
      (`code_refs`: pyproject.toml, the Railway config file(s), frontend/vercel.json,
      docs/DEPLOY.md, the CORS wiring file).
- [ ] 7. Gates + mechanical wiki sweep (article-by-article commits).

### Orchestrator + PO tail (after reviewers pass on the code diff)

- [ ] 8. PO executes the runbook in the consoles (team standing by, step-by-step).
- [ ] 9. AC3 demonstrated: one deliberately failed release → old container still serving;
      then corrected → clean deploy.
- [ ] 10. AC4 verified live and recorded: worker ingests on Neon (watermark advances
      across two cycles — query via the api or Neon console), all six tabs render on the
      Vercel URL through the rewrite, one mutation round-trips. Evidence into
      `sprint-current.yaml` dod_evidence (2026-06-29 agreement: this runs BEFORE the
      sprint closes, never deferred).

### Conventions checklist (standing)

(a) doc comments citing dossier §17/STORY-017 on any new module; (b) CORS wiring lives in
composition (import-linter contracts must stay 5 kept / 0 broken); (c) scoped staging;
(d) tests drive the named scenarios (real preflight requests, not mocked middleware);
(e) no secret values in code, config, tests, fixtures, or docs — names only; (f) contract
changes rewrite covering tests, never delete.
