# Sprint 14 — Review

**Goal:** Stand up the Maintenance feature module (`MaintenanceRepository` over the existing
`maintenance_windows` table + `GET`/`POST /api/v1/maintenance`) and harden the import floor with the
5th `src→tests` linter contract.

**Branch:** `sprint-14` (from `sprint-14-start` @ `03a3931`) · **HEAD:** `83af36a`
**Committed:** 6 pts · **Stories:** STORY-038 (1) + STORY-036 (5), both Done.

## Mechanical DoD gate (orchestrator-verified, throwaway Postgres)

| Command | Result |
| --- | --- |
| `pytest` | **317 passed** |
| `lint-imports` | **5 kept, 0 broken** (NEW `src-no-tests`) |
| `check_fk_direction.py` | 0 violations (10 FKs) |
| `alembic upgrade head` | exit 0 (no new migration) |
| `ruff check` / `format --check` | clean (114 files) |

---

## STORY-038 — 5th import-linter contract: src must not import tests (1 pt, gate-only)

- **Done.** `src-no-tests` forbidden contract added (`source=src`, `forbidden=tests`); proven
  non-vacuous (reverted spike); `lint-imports` 5/0. Command-sync: `definition-of-done.md` + `CLAUDE.md`
  (4→5 contracts) + `architecture-boundary.md` updated in the contract commit; `dev-setup-and-dod.md`
  re-verified. This mechanizes the `src→tests` class that slipped the gate in sprint 13.

## STORY-036 — Maintenance feature module (5 pts)

`MaintenanceWindow` domain type (UTC validation + `ends_at > starts_at` invariant) +
`MaintenanceRepository` (port + Postgres adapter + fake; `list_windows` / `create` /
`is_under_maintenance`) + the `api/v1/maintenance` five-file feature (`GET` list + `POST` schedule),
added to the `api-feature-independence` contract. No migration (table existed); no pipeline wiring
(none exists — the repo provides `is_under_maintenance` for a future consumer).

| AC | Verdict |
| --- | --- |
| AC1 domain type + `ends_at>starts_at` + UTC invariants | MET |
| AC2 repository + fake/adapter parity (inclusive-start/exclusive-end boundary) | MET |
| AC3 GET list (+ empty) | MET |
| AC4 POST create (201; 422 on `ends<=starts` and on malformed body) | MET |
| AC5 five-file shape + boundary | MET |
| AC6 full gate + blast radius | MET |

- **Opus spec reviewer: PASS** (all six AC MET; both 422 paths and the exact boundary parity verified).
- **Opus quality reviewer: APPROVE** (0 critical / 0 major; hexagonal boundary held, invariant
  enforced for real, fake/adapter parity confirmed against the live DB, no `tests` import in `src`,
  the sprint-13 `tests.fakes`-in-`create_app` MAJOR was NOT reintroduced).

### Execution note (PO quota cutoff)
The external implementer (Gemini/Antigravity) hit its quota mid-story. A **Sonnet implementer
subagent** (PO-authorized; consistent with the implementer-on-Sonnet agreement) finished the wiki
blast-radius + gate. In doing so it caught two things the Gemini implementer left broken: **ruff
violations in ~7 files** (so the gate was not actually green at the intermediate commits) and a
**stale `dev-setup-and-dod.md`** (missed in STORY-038's blast radius). Both fixed before review.

### Non-blocking minors (→ retro / follow-up)
1. `maintenance/service.py` — `id=w.id if w.id is not None else 0` invents a fake `0` id. This is the
   SAME dead-coercion pattern removed from `approvals/service.py` in sprint 13, reintroduced here.
   Align to `id=w.id` (sibling pattern).
2. `POST /api/v1/maintenance` has no `actor` field (story text mentioned a self-declared actor; AC4
   did not require it). Auth is deferred regardless.

---

## PO verdicts requested
Per story: **accept** (merge to main) or **reject** (back to backlog). Both passed the gate and (for
STORY-036) both Opus reviewers. The two minors can fold into the accept (a ~2-line Sonnet fix) or
become a follow-up chore.
