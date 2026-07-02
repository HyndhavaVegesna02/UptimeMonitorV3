# Sprint 28 — Review

**Date:** 2026-07-02
**Goal:** make the FastAPI backend HTTP-servable + document the end-to-end local dev stack.
**Committed / delivered:** STORY-042 (3) = 3 pts. Done (AC1–AC4 mechanical; AC5 = manual PO step).
**Branch:** `sprint-28` (tag `sprint-28-start` @ `5172156`). Commits `1b8a0bb..6303247`.
**Mode:** in-process — Sonnet 5 implementer at high effort; Opus spec + quality reviewers.

## STORY-042 — Serve the API locally + dev stack (3 pts) — ACCEPTED PENDING PO VERDICT
Fixes the root cause of your `npm run dev` `ECONNREFUSED`: the FastAPI app had never been
HTTP-servable (no `uvicorn`, no module-level `app` — only `TestClient` in pytest).

### AC checklist
- **AC1** — `uvicorn[standard]` added to dev extras; CLAUDE.md tooling row updated same commit. MET.
- **AC2** — `backend/src/composition/asgi.py` exposes `app = create_app()` (reads `DATABASE_URL` +
  `config/apps`, so the boot seed runs); `uvicorn src.composition.asgi:app --port 8000` serves the
  real routes; stays in the `composition` zone (lint-imports 5/0). MET.
- **AC3** — `backend/tests/test_asgi.py` (DB-gated, `migrated_db`) drives `GET /api/v1/components` →
  200 with the seeded `http-check` component over a `TestClient`; the import-time-engine caveat is
  handled (module imported inside the test body after the fixture sets the env — proven via
  `--collect-only` with no DB). MET.
- **AC4** — CLAUDE.md "Run the app locally" recipe (dev_db up → export `DATABASE_URL` → uvicorn :8000
  → 2nd terminal `python -m src.composition.run` → `npm run dev`); the stale "locally running uvicorn
  instance" line corrected. MET.
- **AC5 (manual, PO-observed)** — end-to-end with live data needs your `.env` creds; carved out per
  the 2026-06-29 live-verification agreement. Mechanically enabled + smoke-proven; yours to run.

### DoD evidence — all six backend gates green at `6303247` (clean committed tree)
pytest **428 passed** (single isolated run; incl. 2 new asgi tests); lint-imports 5/0;
check_fk_direction 11/0; alembic exit 0; ruff check + format clean. Manual server smoke:
`uvicorn ... asgi:app` boots, `/api/v1/components` → 200 (seeded), `/health` → 200.

> Note: an interim gate attempt showed "364 passed, 64 errors" — that was a **test-infra collision**
> (two concurrent pytest runs sharing one throwaway DB; the truncate fixtures interfered), NOT a code
> failure. A single clean run = 428 passed.

### Reviews
- **Spec (Opus): PASS** — AC1–AC4 MET, AC5 correctly deferred; ran the asgi tests itself.
- **Quality (Opus): APPROVE** — 0 Critical, 0 Major. Proved the import-time-engine caveat holds
  (`--collect-only` builds no engine); servability test is real; thin entrypoint is the right shape;
  docstrings + command-sync + boundary all clean; recipe runnable. 3 non-blocking minors (see below).

### Non-blocking minors (captured, not fixed — none propagate)
- `test_asgi.py` `import_module` + `reload` builds the engine twice on first run (harmless in-test).
- `clean_topology` fixture duplicated from `test_seed.py` (consistent with existing pattern).
- Run-recipe mixes `.venv/Scripts/python.exe -m uvicorn` and bare `python -m ...` (intentional, matches
  the existing live-loop convention).

## How to use it now
```
python scripts/dev_db.py up                 # throwaway Postgres, prints DATABASE_URL
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:55432/uptime"
.venv/Scripts/python.exe -m uvicorn src.composition.asgi:app --port 8000
# 2nd terminal (populates proposals/observations/publications — needs .env creds):
.venv/Scripts/python.exe -m src.composition.run
# 3rd terminal:
cd frontend; npm run dev                     # proxy now reaches the API — no ECONNREFUSED
```

## Wiki compile pass (blocking; complete)
`dev-setup-and-dod.md` updated (uvicorn dev dep + the ASGI entrypoint + the run-locally recipe;
`+asgi.py` code_ref); `api-five-file-convention` / `architecture-boundary` / `config-layer`
re-verified (pyproject uvicorn dev-dep add only, Facts unaffected). Sweep: 0 stale / 0 broken across
12 articles.

## Process metrics
- Reviewer rejections: 0 (both first-pass). Fix loops: 0. Hotfixes: 0. Blocked: 0.
- Estimate accuracy: 3 pts, no overrun. Commit cadence held (3 TDD commits).
- Test-infra note: the concurrent-run DB collision cost a re-run — orchestrator-side, retro material.
- Velocity (if accepted): 3/3.
