---
id: STORY-017
title: Deployment topology
type: chore
---

## Context
Spec: dossier §17 (deployment topology). Migrations run as a separate release step before
serving. Refined 2026-07-06 with the PO's four planning decisions (below); the Sock Shop /
failure-shim / demo-cadence tail was SPLIT OUT to STORY-053 — the Dynatrace monitor
already has a live target producing real results, so the deployment does not depend on it.

**PO decisions (2026-07-06 refinement):**
1. **Modality:** accounts exist; the PO drives the Railway/Vercel consoles — the team
   prepares all config/code plus an exact step-by-step runbook; console actions are
   sanctioned PO-interaction points during the sprint (not blockers).
2. **Database:** Neon project exists; the PO supplies the pooled (`DATABASE_URL`) and
   direct (`DATABASE_URL_DIRECT`) connection strings directly into Railway env vars —
   never committed.
3. **D2 routing:** Vercel rewrite — `vercel.json` rewrites `/api/*` to the Railway origin
   so the browser stays same-origin (`client.ts::API_BASE_URL = '/api'` unchanged);
   server-side CORS restricted to the Vercel origin (+ localhost dev) ships anyway as
   defense-in-depth per the dossier and the 2026-06-23 defer-auth-cleanly agreement.
4. **Estimate:** re-pointed 3 → 5 (two cloud surfaces, a release phase, D1–D3, live
   verification); sole story of sprint 35.

**Audit inputs folded (2026-07-02):** D1 `uvicorn[standard]` moves from dev extras to
runtime deps (it IS the production ASGI server). D2 — resolved by decision 3. D3 — two
long-running processes: Railway runs an `api` service (`uvicorn src.composition.asgi:app`)
AND a `worker` service (`python -m src.composition.run`), both on the pooled URL; both
seed topology at boot — the seed is idempotent upserts, double-seeding is safe. Production
reads REAL env vars; nothing in the entrypoints may require a `.env` file (STORY-043's
local-loading fix, still backlogged, must never override set env vars when it lands).

## Description
Backend on Railway (api + worker services; `alembic upgrade head` as the release step on
the Neon DIRECT connection, then serve/loop on the POOLED connection). Frontend on Vercel
with the `/api/*` rewrite. Secrets live in Railway/Vercel env (config references env var
NAMES, never values). CORS restricted to the Vercel origin + localhost dev.

## Acceptance Criteria
- [ ] AC1 (repo deploy config): `uvicorn[standard]` is a runtime dependency (D1); the
      repo carries the Railway service config — api service start command, worker start
      command, and the migrate-release-step (`alembic upgrade head` on
      `DATABASE_URL_DIRECT`) — and `frontend/vercel.json` with the `/api/*` rewrite to
      the Railway origin (mechanism: env-substituted or documented placeholder). Six
      backend gates green after the pyproject move.
- [ ] AC2 (CORS): the API serves CORS restricted to the configured Vercel origin plus
      localhost dev origins, driven by env/settings (names, not values, in config);
      tested — allowed origin passes preflight + echo, disallowed origin gets no CORS
      grant, no-Origin (server-to-server, the rewrite's hot path) is unaffected.
- [ ] AC3 (fail-safe release): a failing migration halts the deploy with the previous
      container still serving — demonstrated on Railway during the live deploy (or
      evidenced by Railway's release-command semantics with the failure path exercised
      once), never a crash-loop.
- [ ] AC4 (live, PO-driven): the deployed stack works end-to-end — worker ingests real
      Grail observations on Neon (watermark advances across two cycles), the Vercel
      frontend renders all six tabs from the deployed API through the rewrite, and a
      mutation (sample-mode toggle or maintenance schedule) round-trips. Verified in the
      session with the PO; evidence recorded.
- [ ] AC5 (secrets hygiene): no secret value in the repo at any commit of the sprint;
      Dynatrace/Statuspage/Neon values exist only in Railway env vars; the runbook lists
      every env var NAME per service.
- [ ] AC6 (docs, command-sync agreement): CLAUDE.md gains the deployed-topology section
      (services, release step, env var names, deploy-verification commands) in the same
      story; a `deployment-topology` wiki article is created with `code_refs` to the
      deploy config files.

## Open Questions
None — the four refinement decisions above resolved account access, database, routing
mechanism, and scope/estimate.

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §17. Status: draft.
- 2026-07-02: audit inputs D1–D3 + secrets note appended.
- 2026-07-06: refined to READY at sprint-35 planning — PO answered all four open
  decisions (console-driven modality, existing Neon, Vercel-rewrite routing, trim+5pts);
  Sock Shop / failure shim / demo cadence split to STORY-053. Estimate 3 → 5.
