# Sprint 0 — Review

**Goal:** A running backend skeleton with the four CI contracts green on an empty build —
the boundary gates exist before any business logic.

**Branch:** `sprint-0` (from `main` @ `aa6b3b4`). **Committed:** 8 pts. **Done:** 8 pts (3/3 stories).
**Status going into review:** all three stories Done, full DoD gate independently re-run green.

## Demo — the gates are real (re-run by the orchestrator against a fresh Postgres)

| DoD command | Result |
| --- | --- |
| `pytest` | **exit 0** — `10 passed` |
| `lint-imports` | **exit 0** — `Contracts: 3 kept, 0 broken` (core-independence, core-internal-layering, adapters-independence) |
| `alembic upgrade head` (+ reversible `downgrade base`→`upgrade head`) | **exit 0** both ways — baseline applied |
| `python scripts/check_fk_direction.py` | **exit 0** — `0 foreign key(s) checked, 0 violations` |

The boundary actually bites: injecting `import sqlalchemy` into `core/services` flips
`lint-imports` to `core-independence BROKEN`, exit 1 (demonstrated and reverted in STORY-002).
Injecting a real `components → incidents` FK makes the FK check exit 1 (demonstrated in STORY-002).

---

## STORY-001 — Repo scaffold + four-zone structure (3 pts) · pipeline: full
Commits: 862f44a, 29afbb3, c641664, d9441c2 · Spec review **PASS** · Quality review **APPROVE**

- [x] AC1 — `pytest` exits 0 (smoke test imports all zones). Evidence: `1 passed`.
- [x] AC2 — Four zones exist as importable packages; `import src.core, src.adapters, src.composition, src.api` → exit 0.
- [x] AC3 — `CLAUDE.md` present: overview, stack, key commands, tooling inventory, verbatim YourTeam pointer.
- [x] AC4 — `pyproject.toml` makes `src` importable from `backend/`; `pip install -e ".[dev]"` succeeds in a fresh `.venv`.
- Note (minor, non-blocking): bare `pytest` currently relies on the editable install; a
  `pythonpath = ["backend"]` would make the harness self-contained — recorded as a candidate tweak.

## STORY-002 — CI contracts = the DoD floor (3 pts) · pipeline: full
Commits: 3c030c9, a69d3eb, efc4c69, 4c4a3ac, 2c5f9c8, eff37c9 · Spec review **PASS** · Quality review **APPROVE**

- [x] AC1 — `lint-imports` exits 0 with all three contracts active.
- [x] AC2 — A forbidden import makes `lint-imports` exit nonzero (demonstrated, reverted; reproduced by the spec reviewer).
- [x] AC3 — `scripts/check_fk_direction.py` reads real FKs from `information_schema`, §9 SPINE allowlist, exits 0 on empty DB.
- [x] AC4 — Both `lint-imports` and the FK check are the bare DoD commands.
- [x] AC5 — Unit test pins the violation logic in BOTH directions (spine→feature flagged, feature→spine not). `5` FK tests pass.
- Notes (minor): composite-FK dedup (`SELECT DISTINCT`) cosmetic; comment the deliberate function-local `psycopg` import.

## STORY-003 — Alembic + Neon two-connection setup (2 pts) · pipeline: light
Commits: 68540c5, f44a0ff, 14eef2a, 916c0c0, 772a98e · DoD gate **green** (first story exercising all four commands)

- [x] AC1 — `alembic upgrade head` exits 0 on a fresh empty DB (empty baseline).
- [x] AC2 — Migrations read `DATABASE_URL_DIRECT`; app settings read `DATABASE_URL` (pooled); distinct, visible in code; unit-tested.
- [x] AC3 — Alembic at repo top level; real `versions/eda70ac11454_baseline.py`; no `create_all`.
- [x] AC4 — Baseline reversible — round-trip exits 0 both ways.
- [x] AC5 — `CLAUDE.md` documents the migration command, the two-var convention, and the throwaway-Postgres one-liner.

---

## Wiki compile pass (blocks review — done)
Seeded three verified articles (verified_sha `2ee3266`, sprint-0):
`architecture-boundary.md`, `migrations-and-db.md`, `dev-setup-and-dod.md`. No internal links to lint.

## Carried to retro / backlog (non-blocking)
1. Two Definition-of-Done files (root companion vs `.scrum/` canonical) — dedup / cross-link to prevent drift.
2. `pythonpath = ["backend"]` so bare `pytest` needs no editable install (CI portability).
3. `migrations/env.py` resolves the URL at import time — minor `alembic revision` ergonomics.
4. Composite-FK `SELECT DISTINCT` + comment the deliberate function-local psycopg import.

## Verdict requested from the PO
Per story: **accept** (→ merge to `main`) or **reject** (→ back to backlog with feedback).
All three met every AC with green, independently re-run gates.
