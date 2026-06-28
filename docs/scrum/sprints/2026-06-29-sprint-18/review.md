# Sprint 18 — Review

**Goal:** Make Neon the seeded read model (dossier §7 Option C) — add the `signals.component_id`
migration, an idempotent `seed_topology` upsert, a CLI, and app-startup seed wiring — so the spine is
populated from `config/apps` and `GET /api/v1/components` shows real components.

**Branch:** `sprint-18` (from `sprint-18-start` @ `44eaf43`) · **Merged to main @ `82bcbc7`**
**Committed:** 5 pts · **Story:** STORY-040 — Done.

## Mechanical DoD gate (orchestrator-verified, throwaway Postgres)

| Command | Result |
| --- | --- |
| `pytest` | **385 passed** (two consecutive reused-DB runs both green) |
| `lint-imports` | **5 kept, 0 broken** |
| `check_fk_direction.py` | **11 FKs, 0 violations** (new spine→spine FK counted) |
| `alembic upgrade head` / `downgrade -1` | round-trip exit 0 (migration `eec78d2e8cbe` reverses) |
| `ruff check` / `format --check` | clean (135 files) |

Implemented by a **Sonnet implementer subagent** (PO's external quota), then verified + reviewed by
the orchestrator.

---

## STORY-040 — Topology seed + signal→component migration + boot wiring (5 pts)

- **Migration** `eec78d2e8cbe`: nullable `signals.component_id` FK→`components.id` (`ON DELETE
  RESTRICT`) + index; reversible; **spine→spine** so `check_fk_direction` stays green.
- **`composition/seed.py::seed_topology`**: idempotent `ON CONFLICT DO UPDATE` upsert apps→components
  →signals; **never writes `components.status`** (runtime state); writes the app's thresholds as typed
  JSONB into `apps.config` (NOT NULL).
- **CLI** `scripts/seed_topology.py` (exit 0/1/2). **Boot wiring:** `create_app` loads+validates config
  (fail-fast) and the lifespan startup seeds; injected/test branch skips. `CONFIG_DIR` setting added.

| AC | Verdict |
| --- | --- |
| AC1 reversible migration + FK-direction green | MET |
| AC2 idempotent seed (twice = stable values/counts) | MET |
| AC3 re-seed preserves runtime `components.status` | MET |
| AC4 boot wiring → dashboard shows seeded components; bad config fails fast | MET |
| AC5 CLI exit 0 on success / nonzero + clear message on failure | MET |
| AC6 full gate + blast radius | MET |

- **Opus spec reviewer: PASS** — all six AC MET; each "tested" clause traced to genuinely drive its
  named path (the 2026-06-29 rigor): idempotency compares values across two runs, status-preservation
  sets `degraded` then re-seeds, boot wiring goes through the lifespan, CLI exits 0/1/2.
- **Opus quality reviewer: APPROVE** (0 critical / 0 major) — genuine idempotency, status never
  clobbered, parameterized SQL, reversible migration, fail-fast boot. The implementer also added a
  `clean_topology` truncate fixture (extending STORY-039's isolation to the topology tables) and the
  reviewer confirmed **two consecutive reused-DB suite runs both pass**.

**First pass — no fix loop.** PO chose *accept + fix minors*; the orchestrator inline-cleared the three
non-blocking minors: extracted `settings.py::to_psycopg_url` (was duplicated 3×), tidied the seed CLI
path, and commented the idempotency test's `updated_at` omission.

---

## Process note (orchestrator)
The orchestrator merged immediately after the minor-fix commits, *before* committing the wiki compile
pass + board + this review on the branch (then completed them on main). No harm — the PO had accepted,
the gate was green, and the wiki was re-verified to the post-merge HEAD — but the ceremony order
(compile pass + review record on the branch, THEN merge) was not followed. Raised at the retro.

## Outcome
**The backend monitoring loop is now complete end-to-end with a seeded spine.** Remaining before
frontend: **STORY-037** (Publications module); then the creds/account-gated **STORY-016** (live demo)
and **STORY-017** (deploy). **STORY-015** (frontend) stays deferred until backend is done.
