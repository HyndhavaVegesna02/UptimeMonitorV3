# Sprint 1 — Plan

**Goal:** Zone 1 complete — the canonical vocabulary and the core's owned interfaces
exist, so every later zone has vendor-neutral types and ports to build against.

**Branch:** `sprint-1` (tagged `sprint-1-start`) · **Committed:** 6 pts · **Capacity:** 8
(1 sprint of history; deliberately under-committed on a single data point)

**Baseline (verified on main before lock, 2026-06-24):** `pytest` 10 passed ·
`lint-imports` 3 kept · `alembic upgrade head` exit 0 · `check_fk_direction.py` 0
violations.

**Execution order:** STORY-004 → STORY-005. STORY-005's port signatures import the
domain types STORY-004 defines (hard dependency); the spine type is also the highest
blast-radius artifact in the zone, so it lands first. Same zone → momentum into 005.

Both stories are 3 pts → **full pipeline** (implementer + spec reviewer against AC +
code-quality reviewer + mechanical DoD gate). Both are pure-core: tested with in-memory
fixtures, no live Dynatrace/Statuspage/Neon. DoD `alembic`/FK commands still run against
the throwaway Dockerized Postgres at the gate.

---

## STORY-004 — Canonical SignalObservation type (3 pts)

Library: Pydantic v2 frozen model (`ConfigDict(frozen=True)`). New module(s) under
`src/core/domain/`.

- [x] 1. Write failing test: `Health` is a closed enum with exactly `up`/`down`/`degraded`. See it fail.
- [x] 2. Add `Health(str, Enum)` in `core/domain`. See it pass. Commit.
- [x] 3. Write failing test: `Provenance` frozen model `{system, native_id, native_kind}` constructs; mutation raises. See it fail.
- [x] 4. Add frozen `Provenance`. See it pass. Commit.
- [x] 5. Write failing test: `SignalObservation` constructs from valid §5 fields (AC1); the object is frozen (mutation raises). See it fail.
- [x] 6. Add frozen `SignalObservation` with all §5 fields (incl. optional `latency_ms`, `raw_ref`). See it pass. Commit.
- [x] 7. Write failing test: invalid `health` value raises `ValidationError` (AC2). See it fail → make pass (enum already enforces) → confirm. Commit.
- [x] 8. Write failing test: naive `observed_at` is rejected; tz-aware UTC accepted (AC3). See it fail.
- [x] 9. Add UTC validator (reject naive). See it pass. Commit.
- [x] 10. Write failing test: no field outside `source` carries a vendor id; field names read vendor-neutrally (AC4). See it fail → confirm structure satisfies → pass. Commit.
- [x] 11. Write failing test: round-trip `construct → model_dump → reconstruct` equal; missing required field raises (AC5). See it fail.
- [x] 12. Confirm round-trip + validation pass. Commit.
- [x] 13. Run full gate: `pytest`, `lint-imports` (AC6), `alembic upgrade head`, `check_fk_direction.py`. Record DoD evidence. Resolve forward blast radius (no wiki articles on core/domain yet). No command/stack/arch change → CLAUDE.md untouched.

## STORY-005 — The core ports (3 pts)

ABCs in `src/core/ports/`. Supporting domain types (`IngestResult`, `StatusChange`,
`ComponentStatus`) added to `src/core/domain/`. Fakes under `tests/`.

- [ ] 1. Write failing test: `ComponentStatus` closed enum (`operational`/`degraded`/`partial_outage`/`major_outage`) + frozen `StatusChange{component_id, status}` + `IngestResult{accepted, rejected}`. See it fail.
- [ ] 2. Add the three supporting domain types. See it pass. Commit.
- [ ] 3. Write failing test: `ClockPort` ABC cannot be instantiated; a `FakeClock` (tests/) returns injected fixed tz-aware UTC time (AC3). See it fail.
- [ ] 4. Add `ClockPort(ABC)` + `FakeClock`. See it pass. Commit.
- [ ] 5. Write failing test: `WatermarkRepository` ABC; `FakeWatermarkRepository.get` returns None unset, `advance`→`get` round-trips (AC4). See it fail.
- [ ] 6. Add `WatermarkRepository(ABC)` + fake. See it pass. Commit.
- [ ] 7. Write failing test: `ObservationRepository.save_new(batch) -> int` ABC + in-memory fake counts inserts. See it fail.
- [ ] 8. Add `ObservationRepository(ABC)` + fake. See it pass. Commit.
- [ ] 9. Write failing test: `StatusPublisherPort.publish(StatusChange) -> None` ABC + recording fake. See it fail.
- [ ] 10. Add `StatusPublisherPort(ABC)` + fake. See it pass. Commit.
- [ ] 11. Write failing test: `SignalIngestPort.ingest_observations(batch: Sequence[SignalObservation]) -> IngestResult` ABC + fake. See it fail.
- [ ] 12. Add `SignalIngestPort(ABC)` + fake. See it pass. Commit.
- [ ] 13. Confirm each fake satisfies its interface and is exercised by a test (AC2); signatures use canonical vocabulary only (AC1). Commit any test additions.
- [ ] 14. Run full gate: `pytest`, `lint-imports` (AC5 — core/ports imports domain not services), `alembic upgrade head`, `check_fk_direction.py`. Record DoD evidence. Resolve forward blast radius. No command/stack change → CLAUDE.md untouched.
