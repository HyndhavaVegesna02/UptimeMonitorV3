# Sprint 13 — Review

**Goal:** Extend Zone 6 with the two headline read surfaces — `GET /api/v1/components` (component
statuses) and `GET /api/v1/approvals` (open proposals) — adding the two new read ports they need,
and clear the two STORY-014 API minors.

**Branch:** `sprint-13` (from `sprint-13-start` @ `31d6e57`) · **HEAD:** `08c4eba`
**Committed:** 7 pts · **Stories:** STORY-014b (5) + STORY-035 (2), both Done.

## Mechanical DoD gate (orchestrator-verified, throwaway Postgres)

| Command | Result |
| --- | --- |
| `pytest` | **305 passed**, 0 deprecation warnings |
| `lint-imports` | **4 kept, 0 broken** (`components`+`approvals` in `api-feature-independence`) |
| `check_fk_direction.py` | 0 violations (10 FKs) |
| `alembic upgrade head` | exit 0 |
| `ruff check` / `format --check` | clean (104 files) |

---

## STORY-014b — Dashboard + Approvals read endpoints (5 pts)

Added `core/domain/component.py::Component`, the `ComponentRepository` port + Postgres adapter +
fake, `ProposalRepository.list_open` (port + adapter + fake), and two five-file read features
(`api/v1/components` → `GET /api/v1/components`; `api/v1/approvals` → `GET /api/v1/approvals`),
both added to the `api-feature-independence` contract.

| AC | Verdict |
| --- | --- |
| AC1 Dashboard read (+ empty case) | MET |
| AC2 Approvals list (open-only, multiple, empty) | MET (after fix) |
| AC3 new read ports + fake/adapter parity + DTO distinctness | MET |
| AC4 five-file shape + boundary (+ shape tests) | MET (after fix) |
| AC5 full gate + blast radius | MET |

### Review record (one fix loop)
- **First pass — both reviewers blocking:**
  - Spec **FAIL**: AC2 (no "multiple open proposals" test), AC4 (no five-file-shape test for the two
    new features).
  - Quality **FIX REQUIRED** (1 MAJOR): `composition/app.py` imported `tests.fakes` into production
    code on the injected-repo branch — a `src → tests` boundary violation, live (hit by
    `test_app`/`test_decisions`), would `ImportError` in a tests-stripped artifact. It slipped the
    mechanical gate because no import-linter contract forbids `src → tests`.
- **Fix (`08c4eba`, PO-authorized orchestrator inline):** dropped the `tests.fakes` import (left
  `component_repo` as-passed, symmetric with `proposal_repo`); added five-file-shape tests for
  `components` + `approvals`; added a multiple-open-proposals test; dropped a dead `id … else 0`
  coercion (minor).
- **Second pass:** Spec **PASS** (all AC MET, no regression); Quality **APPROVE** (0 critical / 0 major;
  `git grep` confirms no `tests` import remains in `src/`).

## STORY-035 — API minors (2 pts, gate-only)

- **035.1** engine disposal: `create_app` now has a FastAPI `lifespan` that disposes the SQLAlchemy
  engine on shutdown (tested).
- **035.2** deprecation: `httpx2` (real package, v2.5.0) added to dev extras; the
  `StarletteDeprecationWarning` is **gone** from the pytest run (verified: 0 occurrences).

---

## Retro candidate
The MAJOR (`src → tests` import) slipped the mechanical floor because no contract forbids it. A **5th
import-linter contract forbidding any `src.*` module from importing `tests`** would catch this class
mechanically — strong retro material (consistent with "boundary violations are build failures").

## Deferred (created this sprint, drafts)
- **STORY-014c** — Availability + Check History read endpoints.
- **STORY-036 / STORY-037** — Maintenance / Publications feature modules (need new backing state).

## PO verdicts requested
Per story: **accept** (merge to main) or **reject** (back to backlog). Both passed the gate and (for
STORY-014b) both Opus reviewers.
