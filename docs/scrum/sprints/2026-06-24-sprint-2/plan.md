# Sprint 2 — Plan

**Goal:** Zone 2 spine exists — the eleven-table data model is migrated, reversible, and
FK-direction-clean, so the repositories (Sprint 3) and every later zone have real tables to
attach to.

**Branch:** `sprint-2` · **Start tag:** `sprint-2-start` · **Started:** 2026-06-24
**Committed:** 6 pts (capacity ≈ 7; deliberate 1-pt under-commit behind one foundation story).
**Green baseline re-verified on main @ `8374de1`:** pytest 45 passed · lint-imports 3 kept,
0 broken · alembic upgrade head → `eda70ac11454` · FK-direction 0 violations.

**Model assignment (PO rule, binding):** implementers → **Sonnet**; reviewers → **Opus**.

---

## Execution order

1. **STORY-006** first — the sprint's reason for existing and highest blast radius (every
   later zone FKs into it). Front-loaded so a block surfaces early with the back half open.
2. **STORY-018** second — 1-pt chore, independent of the schema, can't block on 006; clean
   closer that also clears Sprint 1 retro debt.

---

## STORY-006 — Spine schema migration (5 pts, full pipeline)

Build the full eleven-table spine in one reversible Alembic migration on top of the
`eda70ac11454` baseline. Decisions locked at refinement: full spine (not split); per-app
config = JSONB `config` column on `apps`; explicit `ON DELETE RESTRICT` on FKs into topology.

DoD DB gates use a throwaway Dockerized Postgres (Docker 28.5.2; see CLAUDE.md one-liner).

- [x] 1. Write a test that asserts all eleven spine tables exist after `upgrade head`
      (query `information_schema.tables`); see it fail against the baseline.
- [x] 2. Author the migration: topology group (`apps` w/ `config jsonb not null`, `signals`,
      `components`) with `timestamptz` columns; minimal upgrade to make the table test pass; commit.
- [x] 3. Add the signals group (`observations` mirroring the canonical `SignalObservation`
      fields, `problem_signals`, `watermarks` keyed by `signal_key`, `rejected_observations`
      w/ JSONB payload); `observations.source` as `jsonb`; commit on green.
- [x] 4. Add the workflow group (`status_proposals`, `approval_events`, `publications`,
      `maintenance_windows`); commit on green.
- [x] 5. Add the three required indexes: `UNIQUE(observations.source_event_id)`, composite
      `(observations.signal_key, observed_at)`, partial-unique on `status_proposals(component_id)`
      filtered to active proposals. Test their presence via `information_schema` / `pg_indexes`; commit.
- [x] 6. Declare every FK with explicit `ON DELETE RESTRICT` into topology; runtime/workflow
      FK inward only. Test against `information_schema.referential_constraints`; commit.
- [x] 7. Write the reversibility test: `upgrade head` → `downgrade base` → `upgrade head`
      each exit 0; make `downgrade` drop every spine object cleanly; commit.
- [x] 8. Run the four DoD gates against the throwaway DB; resolve the forward blast-radius
      check (match new tables against `architecture-boundary.md` / any §9 schema article,
      update or re-verify `verified_sha`); record DoD evidence; → review.

## STORY-018 — .gitattributes line-ending normalization (1 pt, lite pipeline)

- [x] 1. Add repo-root `.gitattributes`: `* text=auto eol=lf` + explicit `binary` rules for
      `*.png *.jpg *.jpeg *.gif *.ico *.pdf *.woff *.woff2`.
- [x] 2. `git add --renormalize .`; commit the normalization. (Nothing to renormalize — the
      index was already LF-clean; `.gitattributes` now prevents future CRLF churn going forward.)
- [x] 3. Verify a subsequent text-file edit-and-commit emits no `LF will be replaced by CRLF`
      warning; run the four DoD gates (non-functional change → stay green); record evidence; → review.
