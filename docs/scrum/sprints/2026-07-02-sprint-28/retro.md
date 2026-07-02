# Sprint 28 — Retro

**Date:** 2026-07-02
**Sprint:** STORY-042 (3 pts committed / 3 accepted). Make the API HTTP-servable + document the
end-to-end local dev stack (uvicorn + `composition/asgi.py`).

## What went well
- **Fourth clean sprint in a row (code-wise).** Both Opus reviewers first-pass (spec PASS AC1–AC4 /
  quality APPROVE 0 Critical, 0 Major), zero fix loops. The quality reviewer went beyond the diff and
  *proved* the story's one real subtlety — the import-time-engine caveat — with `pytest
  --collect-only` (no engine build, no DB connection at collection).
- **A user question turned into a real gap caught + closed.** The `npm run dev` `ECONNREFUSED`
  surfaced that the FastAPI app had never been HTTP-servable (no uvicorn, no ASGI entrypoint — only
  `TestClient`). Refined → estimated → built → merged in one focused sprint; the app now runs locally.
- **The tab-AC-vs-DTO agreement correctly self-identified as N/A** (no consumer-tab AC this sprint) —
  the checklist scales down as well as up.

## What hurt (the amendment)
- **A concurrent-pytest-on-one-DB collision produced a false-red gate.** Running the six-command
  backend gate, the pytest step appeared slow, so the orchestrator launched a SECOND pytest run while
  the first was still executing — both against the same throwaway Postgres. The `migrated_db` fixture
  reuses an already-set `DATABASE_URL` (it does NOT spawn a per-run container when the env is present),
  and `clean_runtime_tables` truncates the runtime tables before each DB-gated test — so two concurrent
  runners truncated each other's data mid-test, yielding "364 passed, 64 errors" (all DB-gated). A
  single isolated run was 428 passed. The code was never at fault; the false-red cost a diagnose +
  kill-strays + reset-DB + re-run cycle, and a less careful reading could have triggered a needless fix
  loop against phantom failures.

## Amendment ADOPTED (PO-approved 2026-07-02)
1. **DB-gated gate commands run as a SINGLE, non-concurrent invocation against a throwaway DB.** The
   orchestrator never runs two `pytest` (or `check_fk_direction` / `alembic`) invocations against the
   same throwaway Postgres at the same time — the shared `migrated_db` fixture reuses an already-set
   `DATABASE_URL` and the per-test truncation makes concurrent runs corrupt each other. If a DB-gated
   run appears slow or stuck, DIAGNOSE it (check the process / container / output) before starting
   another — never launch a second run that shares a live run's `DATABASE_URL`. A gate result produced
   while a second run was concurrently hitting the same DB is INVALID and must be re-run cleanly before
   it is recorded as evidence. (Motivated by Sprint 28, STORY-042: a second pytest launched over a slow
   first run collided on the shared throwaway DB and produced a false "64 errors"; a single clean run
   was 428 passed.) Written into `.scrum/working-agreements.md` (2026-07-02) with its motivating incident.

## Carry-forward (backlog / next-planning, not amendments)
- **AC5 (the live end-to-end run)** is the PO's to exercise with real `.env` credentials: full stack up
  → `npm run dev` shows no proxy errors, Dashboard shows components, and after the live loop the
  Approvals/History/Publications tabs populate. If it surfaces anything, it becomes a defect story.
- **015d (Availability) + 015e (Check History)** still carry the tz-aware query-param integration risk
  flagged in Sprint 27 — verify the `since`/`until` contract at their planning (the tab-AC-vs-DTO
  agreement routes this).

## Process metrics
- Reviewer rejections: 0 (both first-pass). Fix loops: 0. Hotfixes: 0. Blocked: 0.
- Estimate accuracy: 3 pts, no overrun. Commit cadence held (3 TDD commits).
- Velocity: 3/3. Recorded last-3 entries (26, 27, 28) = 5, 5, 3 → next-sprint mean 4.33.
- Frontend: 3 of 6 tabs done; the backend is now locally runnable (STORY-042). 015d–015g remain.
