# Sprint 7 — Plan

**Goal:** Zone 4's calculator lands — a pure, derive-on-read availability engine computes
two-grain availability% + location-aware completeness% (and a min-of-children group rollup) from
canonical observations, persisting nothing; plus the Verdict maintenance-invariant guard.

**Branch:** `sprint-7` · **Start tag:** `sprint-7-start` · **Started:** 2026-06-25
**Capacity:** ~6 (velocity 8/6/6/6/5/6/6, last-3 mean) · **Committed:** 6 (STORY-011 = 5, STORY-025 = 1)

**Order:** STORY-011 first (high-risk new calculator), then STORY-025.
**Model assignment (PO rule, mandatory):** implementer → Sonnet; reviewers → Opus.

---

## STORY-011 — Availability calculator: two-grain math + group rollup (5 pts, full pipeline)

Spec: dossier §11. PURE core in `core/services/availability.py` — compute-only, derive-on-read,
persists nothing (D-1), never consults the streak (P4). Reuses `collapse` (STORY-010). The skew
flag is OUT (STORY-026). `interval`/`window` are INJECTED parameters (no per-app config dependency,
same approach as STORY-010 injecting maintenance).

Result shape (dossier §11, frozen — a frozen Pydantic model alongside the service, mirroring how
`Streak` lives in `pipeline.py`; or a frozen dataclass if you prefer §11's literal form — match the
codebase's Pydantic style where reasonable):
`AvailabilityResult{availability_pct: float|None, completeness_pct: float|None, total_verdicts,
passing_verdicts, maintenance_verdicts, gap_verdicts, distinct_locations: int, window: str,
computed_at: datetime}`.

Read `backend/src/core/services/pipeline.py` (collapse + Streak style), `core/ports/
observation_repository.py` + `watermark.py` (port style), and `backend/src/adapters/persistence/
observation_repository.py` + `backend/tests/test_persistence_adapters.py` (Postgres repo + DB-gated
test pattern) FIRST.

TDD steps (commit after every green step; stage only files you touched — never `git add -A`):

- [x] 1. Add an observation-READ capability to the persistence boundary: an abstract method on
        `ObservationRepository` (e.g. `in_window(signal_key, since, until) -> Sequence[
        SignalObservation]`) — keep ALL SQL behind the port. Failing test via a fake; wire the
        signature. `pytest` + `lint-imports` green. Commit.
- [x] 2. Define `AvailabilityResult` (frozen) in `core/services/availability.py`. Failing test →
        construct it. Commit.
- [x] 3. Failing test: availability% = `passing ÷ (total − maintenance)` over collapsed verdicts —
        `up` passes; `down`/`degraded` don't; maintenance excluded BOTH sides; gaps excluded (default
        `exclude`). Implement using `collapse` + an injected fake read-repo. Commit. (AC1)
- [x] 4. Failing test: completeness% = `actual ÷ (intervals × distinct_locations)`,
        `intervals = window ÷ interval`, `distinct_locations = COUNT(DISTINCT location)` — a
        3-location signal NEVER exceeds 100%. Implement. Commit. (AC2)
- [x] 5. Failing test: group rollup — availability/completeness = MIN of children; counts SUM;
        children with no data excluded from the min but their absence stays visible. Implement. Commit. (AC3)
- [x] 6. Failing test (per the sprint-6 empty-input working agreement): a window with ZERO
        observations → `availability_pct=None` + zero counts; completeness with a zero denominator →
        `None` (not a divide error). No crash; document. Implement. Commit. (AC6)
- [x] 7. Add the Postgres implementation of the read method in `adapters/persistence/
        observation_repository.py` (mirror `save_new`; injected `Engine`, all SQL here). Failing
        DB-gated test (the `migrated_db` fixture, seeding observations) asserts it reads the right
        window. Implement. Commit. (AC5 persistence)
- [x] 8. Self-review: service is pure (no vendor/HTTP/SQL); derive-on-read (nothing persisted);
        entry points shaped so a short-TTL cache could drop in later but NO cache built (AC4). Tidy
        residue. Commit.
- [ ] 9. **DoD gate** (all four exit 0): `pytest`, `lint-imports` (core stays independent; the new
        read method keeps SQL behind the port), `python scripts/check_fk_direction.py`, `alembic
        upgrade head` (DB-gated via `scripts/dev_db.py`). Forward blast radius: update
        `canonical-types-and-ports.md` (code_refs incl. `core/ports/` — you ADD a port method → update
        + bump `verified_sha`) and `persistence-adapters.md` (code_refs incl. the persistence repos —
        you ADD the read impl → update + bump). CLAUDE.md only if a command/stack changed (none).
        Record evidence in your FINAL MESSAGE (orchestrator writes the board). Commit.

**Reviews (after step 9):** spec reviewer (Opus) against AC1–AC6 verbatim; then code-quality
reviewer (Opus). Working agreements: empty-input behavior defined+tested (AC6); parallel-shape
work shares its assembly; implementer never writes `sprint-current.yaml`; in-memory canonical
fixtures for the pure math (no live services); only the read adapter gets a DB-gated test.

---

## STORY-025 — Enforce the Verdict maintenance↔health invariant (1 pt, light: implementer + DoD)

Spec: Sprint 6 review follow-up. In `backend/src/core/domain/verdict.py`, add a Pydantic
`model_validator(mode="after")` to `Verdict` enforcing: `under_maintenance=True` ⇒ `health is
None`; `under_maintenance=False` ⇒ `health is not None`. Matches `signal.py`'s validate-at-
construction stance.

- [ ] 1. Failing test: constructing a `Verdict` with `under_maintenance=True, health=Health.UP`
        raises; `under_maintenance=False, health=None` raises; BOTH valid shapes still construct;
        `collapse`/`streak` + existing STORY-010 tests pass unchanged. Implement the validator. Commit.
- [ ] 2. DoD gate (all four exit 0). Forward blast radius: re-verify `canonical-types-and-ports.md`
        (the `Verdict` Fact — note the now-enforced invariant) + bump `verified_sha`. Record evidence. Commit.
