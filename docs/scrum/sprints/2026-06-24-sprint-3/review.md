# Sprint 3 — Review

**Date:** 2026-06-25 · **Goal:** repository adapters implement the persistence ports against
the spine, on a shared throwaway-DB harness so every later DB-gated story stops hand-rolling
Postgres. **Goal met.**

**Committed 6 pts · accepted 6 pts (2/2 stories).** Branch `sprint-3` off tag `sprint-3-start`
(22 commits). Merged to `main` on acceptance.

## STORY-019 — Shared throwaway-DB harness (3 pts) — ACCEPTED
`scripts/dev_db.py` (`up`/`down`) + session-scoped `migrated_db` pytest fixture
(reuse-external / spawn `postgres:16` / clean-skip, with teardown-on-failure).
- Spec review (Opus): PASS (5/5 AC). Quality review (Opus): APPROVE **after one fix loop**.
- Fix loop closed two findings: a MAJOR **spawn-time container leak** (`resolve_db()` could
  raise after `start_container` but before the fixture finalizer registered → leaked container)
  and a **flaky teardown test** (nested-subprocess container race, ~1/4 runs). Fixes: guarded
  the spawn path (`try/except BaseException -> stop_container -> raise`) + regression test; made
  the teardown test deterministic via a `provide_migrated_db()` generator + `.throw()` (no
  subprocess, no temp file). 5/5 consecutive green full runs.
- Process note: the implementer agent hit `API Error: Connection closed mid-response` twice
  mid-fix (infra, not logic), leaving uncommitted work + a leaked temp test file. Recovered by
  preserving the coherent committed work, cleaning the artifact, and finishing via a fresh
  implementer. No work lost. (Retro item.)
- DoD gate (orchestrator-run @ 0a6dd27): alembic 0 · pytest 84 (5x green) · lint 3 kept · FK 10/0.

## STORY-007 — Repository adapters behind the ports (3 pts) — ACCEPTED
`PostgresObservationRepository.save_new` (`ON CONFLICT (source_event_id) DO NOTHING`,
RETURNING-based newly-inserted count) + `PostgresWatermarkRepository.get`/`advance` (upsert,
tz-aware UTC), injected `Engine`, tested on the STORY-019 `migrated_db` fixture.
- Spec review (Opus): PASS (6/6 AC, incl. a partial-overlap dedup proving the count is strictly
  newly-inserted). Quality review (Opus): APPROVE (0 critical/major); 2 minor notes recorded.
- DoD gate (orchestrator-run @ f11a7be): alembic 0 · pytest 89 · lint 3 kept · FK 10/0.

## Wiki compile pass (completed before review)
- STORY-019 folded into `dev-setup-and-dod.md` + `migrations-and-db.md` (re-verified → `0a6dd27`).
- New `persistence-adapters.md` article (engine injection, ON CONFLICT idempotency, tz-aware
  watermark, FK-seeding convention).
- `architecture-boundary.md` re-verified (structure unchanged → `f11a7be`); link-lint clean; no
  stale articles.

## Outcome
Both accepted → merged to `main`. Velocity: 6 accepted (sprint 3). Zone 2 complete (schema +
repositories) plus the shared DB harness; ingest (Zone 3) is next.
