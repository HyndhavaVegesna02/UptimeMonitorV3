# Sprint 15 — Review

**Goal:** Finish the ready backend — per-signal Availability + Check History read endpoints
(completing the Zone 6 read API) — and make the DB-gated test suite robust on a reused DB.

**Branch:** `sprint-15` (from `sprint-15-start` @ `b665c6b`) · **HEAD:** `8305d4d`
**Committed:** 5 pts · **Stories:** STORY-014c (3) + STORY-039 (2), both Done.

## Mechanical DoD gate (orchestrator-verified, throwaway Postgres)

| Command | Result |
| --- | --- |
| `pytest` | **331 passed** (and **passed twice on the same reused container** — STORY-039 proof) |
| `lint-imports` | **5 kept, 0 broken** (`availability`+`history` in `api-feature-independence`) |
| `check_fk_direction.py` | 0 violations (10 FKs) |
| `alembic upgrade head` | exit 0 (no new migration) |
| `ruff check` / `format --check` | clean (126 files) |

Both stories were implemented by a **Sonnet implementer subagent** (PO's external quota unavailable),
then verified + reviewed by the orchestrator.

---

## STORY-014c — Availability + Check History read endpoints (3 pts)

Per-signal `GET /api/v1/availability` (reuses `AvailabilityCalculator`) and `GET /api/v1/history`
(reuses `ObservationRepository.in_window`), as two five-file features added to the
`api-feature-independence` contract. `observation_repo` wired into `create_app`.

| AC | Verdict |
| --- | --- |
| AC1 availability (+ no-data → `None` pcts) | MET |
| AC2 history (+ empty `[]`, missing `signal_key` → 422) | MET |
| AC3 window defaulting (24h via clock) + explicit since/until | MET |
| AC4 five-file shape + boundary (5/0) | MET |
| AC5 full gate + blast radius | MET |

**Documented per-signal stopgaps** (approved scope; signal→component mapping deferred to STORY-040):
`interval_seconds` query param (default 60); `maintenance` no-op. Component/group rollup waits for
STORY-040.

### Review record (one fix loop)
- **First pass:** spec **PASS**; quality **FIX REQUIRED** — 1 CRITICAL: a timezone-**naive**
  `since`/`until` (e.g. `until=2026-06-28`) passed the validators (parseability-only) then hit a
  tz-aware compare inside the calculator → **HTTP 500**. The spec suite missed it (only tz-aware
  inputs were tested).
- **Fix (`8305d4d`, orchestrator inline):** both validators now reject `tzinfo is None` → 422
  (mirroring the `maintenance` validator); added naive-input regression tests for both endpoints;
  minors (hoisted the `datetime` import, lambda→`def`).
- **Second pass:** spec **PASS** (no regression); quality **APPROVE** (0 critical / 0 major).

## STORY-039 — DB-gated test isolation (2 pts, gate-only)

A function-scoped `clean_runtime_tables` fixture in `conftest.py` truncates the runtime tables before
each DB-gated test (no production `src/` change). **Verified by the orchestrator:** the full suite
ran **twice against the same un-torn-down container → 331 passed both runs** (the AC1 reused-DB
property). This hardens the reliability of the `pytest` floor.

---

## PO verdicts requested
Per story: **accept** (merge to main) or **reject** (back to backlog). Both passed the gate and (for
STORY-014c) both Opus reviewers. No open minors.

## Backend roadmap reminder (drafts, post-sprint-15)
STORY-040 (config/topology — the orchestration prerequisite) → STORY-016a (orchestration) →
STORY-037 (Publications); then the creds/account-gated STORY-016 (live demo) + STORY-017 (deploy).
Frontend (STORY-015) remains deferred until backend is done.
