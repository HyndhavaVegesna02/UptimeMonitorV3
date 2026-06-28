# Sprint 12 — Review

**Goal:** Open Zone 6 — establish the five-file API convention (dossier §13) and the 4th
import-linter contract via the decision/approve exemplar, after rehabilitating the 7
reformat-stale wiki articles.

**Branch:** `sprint-12` (from `sprint-12-start` @ `2656416`) · **HEAD:** `dac378c`
**Committed:** 7 pts · **Stories:** STORY-034 (2) + STORY-014 (5), both Done.

## Mechanical DoD gate (orchestrator-verified, throwaway Postgres)

| Command | Result |
| --- | --- |
| `pytest` | **290 passed** |
| `lint-imports` | **4 kept, 0 broken** (new `api-feature-independence`) |
| `python scripts/check_fk_direction.py` | 0 violations (10 FKs) |
| `alembic upgrade head` | exit 0 |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 88 files formatted |

---

## STORY-034 — Rehabilitate the 7 reformat-stale wiki articles (2 pts) — gate-only

- **Done.** All 7 articles (`architecture-boundary`, `canonical-types-and-ports`,
  `dynatrace-adapter`, `ingest-service-and-pull-loop`, `migrations-and-db`,
  `persistence-adapters`, `statuspage-publish`) rehabbed to symbol-based citations
  (`file.py::Symbol`) and flipped `stale` → `verified` (`verified_sprint: sprint-12`).
- AC1–AC4 met; gate green; no `src/` touched.

## STORY-014 — Five-file API convention + 4th linter contract + decision exemplar (5 pts)

Spans three zones: core `ApprovalService`, composition app-factory/provider, `api/v1/decisions`
five-file feature + `api/v1/health`. The 4th import-linter contract (`api-feature-independence`)
forbids horizontal feature imports; DoD/CLAUDE/wiki synced in-commit (command-sync).

| AC | Verdict |
| --- | --- |
| AC1 five-file shape + import rules | MET (after fix — see below) |
| AC2 4th independence contract (4/0, non-vacuous) | MET |
| AC3 thin edge, logic in core, core-independence KEPT | MET |
| AC4 endpoint 200/200/404/409/422 | MET |
| AC5 best-effort side effects (reduced: commit-before-return) | MET |
| AC6 full six-command gate + blast radius | MET |

### Review record (one fix loop)
- **First pass — both reviewers blocking:**
  - Spec **FAIL** (AC1): `controller.py` imported the core `ApprovalService`; no test asserted
    the five-file shape.
  - Quality **FIX REQUIRED** (1 MAJOR): concurrent double-submit → HTTP 500 instead of 409
    (Postgres `resolve()` raised a bare `ValueError` the edge didn't map).
- **Fix (`eb147ef`, PO-authorized orchestrator inline, incl. the minors):** moved the DI provider
  into the feature `service.py` so the controller imports only models+service; added a five-file
  shape assertion; moved the proposal errors to `core/domain/proposal.py` and made both `resolve()`
  impls raise `ProposalNotOpenError` (→ 409, fake/adapter parity) with a regression test; fixed the
  minors (health docstrings, `raise … from e`, dead `result.id` guard).
- **Second pass:** Spec **PASS** (all AC MET, no regression); Quality **APPROVE** (0 critical / 0 major).

### Non-blocking minors carried out of the sprint (retro / follow-up candidates)
1. Composition app SQLAlchemy engine is never disposed on shutdown (process-lifetime engine; low risk).
2. `httpx`/`starlette.testclient` deprecation warning ("install httpx2") — dependency note.

---

## Deferred (created this sprint, not in scope)
- **STORY-014b** (draft) — the five read-only tab endpoints (Dashboard, Availability, Check
  History, Maintenance, Publications) + the Approvals list. To be refined with STORY-015.

## PO verdicts requested
Per story: **accept** (merge to main) or **reject** (back to backlog). Both stories passed the
mechanical gate and (for STORY-014) both Opus reviewers.
