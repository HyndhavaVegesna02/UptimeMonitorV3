---
id: STORY-042
title: Serve the API over HTTP + documented end-to-end local dev stack
type: chore
---

## Context
The frontend dev server proxies `/api/*` → `http://localhost:8000` (`frontend/vite.config.ts`),
but there is nothing to serve there: the FastAPI app has only ever been exercised in-process via
`TestClient` in pytest. There is **no ASGI server installed** (`uvicorn` is not in `pyproject.toml`)
and **no module-level `app`** — only the `create_app(...)` factory (`backend/src/composition/app.py`).
So `npm run dev` currently floods the terminal with `ECONNREFUSED` proxy errors and every tab shows
its `ErrorState`.

This story makes the API HTTP-servable and documents the FULL local stack so every tab shows genuine
LIVE data (PO decisions 2026-07-02): the local stack is **throwaway Docker Postgres (`scripts/dev_db.py`)
+ the API server (uvicorn) + the live pull-loop (`python -m src.composition.run`, which reads the
gitignored `.env` Dynatrace/Statuspage secrets and produces observations → proposals → publications
into the same DB) + `npm run dev`**. CORS stays deferred to STORY-017 (the dev proxy makes the
frontend same-origin, so none is needed locally). Distinct from STORY-017 (cloud deploy topology +
CORS); this is the local-dev prerequisite.

## Toolchain note
Adds `uvicorn[standard]` as a dev dependency — a tooling change, surfaced at refinement/planning per
the working agreements (no active sprint at refinement time).

## Acceptance Criteria
- [ ] **AC1 — ASGI server dependency.** `uvicorn[standard]` is added to
      `[project.optional-dependencies] dev` in `pyproject.toml`; `pip install -e ".[dev]"` provides the
      `uvicorn` console script. The six backend DoD gates stay green (ruff/lint-imports/pytest/etc.).
      CLAUDE.md tooling inventory updated in the same commit (command-sync agreement).
- [ ] **AC2 — ASGI entrypoint.** A new `backend/src/composition/asgi.py` exposes a module-level
      `app` = a fully-wired FastAPI application via `create_app(...)`, reading `DATABASE_URL` from the
      environment and the topology config from `config/apps` so the boot-time topology seed runs
      (components populated). `uvicorn src.composition.asgi:app --port 8000` then serves the real
      `/api/v1/*` routes. The entrypoint lives in `composition` (the only zone permitted to import both
      the api surface and the wiring) — `lint-imports` stays green (no boundary violation).
- [ ] **AC3 — Servability proven by a test.** A DB-gated test (using the shared `migrated_db`
      fixture) constructs the app via the same entrypoint path and asserts a real HTTP route responds
      over an in-process client — e.g. `GET /api/v1/components` → 200 returning the seeded components
      (and/or `/health`). No live external service is required (recorded/seeded data only); proves the
      wiring the manual run depends on.
- [ ] **AC4 — Documented local dev stack.** CLAUDE.md gains a "Run the app locally" section: the
      ordered recipe — (1) `python scripts/dev_db.py up` (throwaway Postgres, prints both URLs);
      (2) export `DATABASE_URL`; (3) start the API server (the uvicorn command) on :8000; (4) in a
      second terminal, `python -m src.composition.run` (reads `.env` secrets) to populate
      proposals/observations/publications; (5) `cd frontend && npm run dev`. The existing stale claim
      ("a locally running uvicorn instance of the backend") is corrected to reference this real recipe.
- [ ] **AC5 — End-to-end verification (manual, PO-observed at review — per the 2026-06-29
      live-verification agreement).** With the full stack running, `npm run dev` loads with NO proxy
      `ECONNREFUSED`; the Dashboard shows the seeded components; and after the live loop runs, the
      Approvals / Check History / Publications tabs show genuine data. Because this needs the PO's live
      `.env` credentials, it is exercised at review (PO-observed) OR carved out as a tracked follow-up —
      never marked done by promise. AC1–AC4 are the mechanical gate independent of it.

## Open Questions
None (data scope = full live stack; local DB = throwaway Docker — PO 2026-07-02).

## History
- 2026-07-02: refined after the `npm run dev` ECONNREFUSED question surfaced that the API was never
  HTTP-servable (no uvicorn, no ASGI entrypoint). PO chose the full local stack (API + live loop) on a
  throwaway Docker Postgres. Estimate 3.
