# Sprint 3 — Plan

**Goal:** Zone 2 closes — repository adapters implement the persistence ports against the
spine, on a shared throwaway-DB harness so every later DB-gated story stops hand-rolling
Postgres.

**Branch:** `sprint-3` · **Start tag:** `sprint-3-start` · **Started:** 2026-06-24
**Committed:** 6 pts (capacity ≈ 7; deliberate 1-pt under-commit).
**Green baseline re-verified on main @ `d5dd2c8`:** alembic head → `3a8254bcfe59` · pytest 77
passed · lint-imports 3 kept/0 broken · FK-direction 10 checked/0 violations.

**Model assignment (PO rule, binding):** implementers → **Sonnet**; reviewers → **Opus**.

---

## Execution order
1. **STORY-019** first — builds the shared DB fixture, so STORY-007's integration tests are
   written against it from the start (Sprint 2 retro sequencing call). De-risks the fixture
   design before 007 depends on it.
2. **STORY-007** second — implements the two persistence ports against the accepted spine,
   consuming the 019 fixture. Zone-2 closer.

---

## STORY-019 — Shared throwaway-DB harness (3 pts, full pipeline)

Python helper `scripts/dev_db.py` (`up`/`down`) + a pytest **session-scoped** fixture in
`backend/tests/conftest.py`: reuse external `DATABASE_URL`/`DATABASE_URL_DIRECT` if set
(ensuring migrated), else spawn `postgres:16`, wait, migrate, yield, tear down on a finalizer
(even on failure); skip cleanly when neither external DB nor Docker is available.

- [x] 1. Write a failing test for the fixture contract: depending on the fixture yields a
      live, migrated connection (the eleven spine tables exist); see it fail (no fixture yet).
- [x] 2. Implement the session fixture in `conftest.py` — external-URL reuse branch first
      (assume a provided DB), migrate-and-connect, make step-1 test pass; commit.
- [x] 3. Add the container-spawn branch (Docker present, no external URL): start `postgres:16`,
      wait ready, set both URLs in correct dialects, `alembic upgrade head`; teardown finalizer
      that runs on failure. Test the teardown-on-failure path; commit.
- [x] 4. Add the clean-skip branch (no external DB, no Docker) — DB-gated tests skip, no error;
      test it; commit.
- [ ] 5. Refactor `test_spine_schema.py` onto the fixture (drop its local `skipif`/`conn`);
      confirm its tests still pass through the fixture; leave `test_fk_direction.py` (pure unit)
      untouched; commit.
- [x] 6. Write `scripts/dev_db.py` `up`/`down`; `up` → start+wait+migrate+emit both URLs,
      `down` → remove container. Prove `up` then `check_fk_direction.py` exits 0; commit.
- [x] 7. Update `CLAUDE.md` (command-sync agreement): document `scripts/dev_db.py` as the
      standard local way to run the DB gates; point the throwaway-Postgres section at it; commit.
- [x] 8. Run the four DoD gates; resolve forward blast radius (dev-setup-and-dod.md /
      migrations-and-db.md reference CLAUDE.md + the one-liner — update/re-verify); record
      evidence; → review.

## STORY-007 — Repository adapters behind the ports (3 pts, full pipeline)

Neon/Postgres implementations of `ObservationRepository` (`save_new` → `INSERT … ON CONFLICT
(source_event_id) DO NOTHING`, returns newly-inserted count) and `WatermarkRepository`
(`get`/`advance`) in `adapters/persistence/`, against the spine, using the 019 fixture.

- [ ] 1. Failing test: `ObservationRepository.save_new` inserts a batch and returns the count;
      read it back. (Uses the 019 session fixture.) See it fail (no adapter yet); commit on green.
- [ ] 2. Implement the concrete `ObservationRepository` in `adapters/persistence/` (SQLAlchemy
      2 / psycopg 3, injected engine/session); make the insert+readback test pass; commit.
- [ ] 3. Failing test for idempotency: re-inserting the same `source_event_id`s inserts 0 new
      rows, returned count reflects only new rows (`ON CONFLICT DO NOTHING`); make it pass; commit.
- [ ] 4. Failing tests for `WatermarkRepository`: `get` None before advance, the advanced UTC
      instant after, monotonic re-advance; implement the concrete repo; make them pass; commit.
- [ ] 5. Confirm no SQL above the repository layer — `lint-imports` green (core-independence
      forbids `sqlalchemy` in core); self-review for leaks; commit any test/cleanup.
- [ ] 6. Run the four DoD gates; resolve forward blast radius (confirm no port-signature drift
      vs canonical-types-and-ports.md); record evidence; → review.
