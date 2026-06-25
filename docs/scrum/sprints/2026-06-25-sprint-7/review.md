# Sprint 7 — Review

**Goal:** Zone 4's calculator lands — a pure, derive-on-read availability engine computes two-grain
availability% + location-aware completeness% (and a min-of-children group rollup) from canonical
observations, persisting nothing; plus the Verdict maintenance-invariant guard.

**Branch:** `sprint-7` (commits `a601a4b..22c4e16`) · **Committed:** 6 pts · **Done:** 6 pts
**Capacity:** ~6 (velocity 8/6/6/6/5/6/6, last-3 mean).

---

## STORY-011 — Availability calculator: two-grain math + group rollup (5 pts) — ✅ DONE

**Pipeline:** implementer (Sonnet) → spec review **PASS** (Opus) → quality review (Opus): 1 CRITICAL
→ **fix loop 1** (fresh Sonnet) → re-review **APPROVE** (Opus) → DoD gate green.

Built (pure core, `core/services/availability.py`):
- **`AvailabilityResult`** (the §11 frozen shape) + **`AvailabilityCalculator.compute`** —
  availability% = `passing ÷ (total − maintenance)` over collapsed verdicts (gaps/maintenance
  excluded); completeness% = `actual ÷ (intervals × distinct_locations)` (location-aware, never
  >100%). `interval`/`window`/`maintenance`/`computed_at` all injected — no config, no clock read.
- **`rollup_group`** — min-of-children percentages, summed counts, no-data children excluded from
  the min but their absence stays visible.
- **`ObservationRepository.in_window`** read port + its Postgres impl (all SQL behind the port).
  Service unit-tested with in-memory fakes; the read adapter has a DB-gated test.

### AC checklist (spec reviewer verified each MET)
- AC1 availability formula over collapsed verdicts ✅ · AC2 location-aware completeness (3-loc never
  >100%) ✅ · AC3 min-of-children rollup ✅ · AC4 derive-on-read, no cache ✅ · AC5 pure, SQL behind
  the port, injected interval/window ✅ · AC6 empty/degenerate input → None, no crash ✅

**Fix loop:** quality review caught a CRITICAL — cycle bucketing used FLOOR `expected_cycles`, but
`in_window` returns partial-tail observations that bucketed one past, making `gap_verdicts` go
**negative** and completeness exceed 100% on non-divisible windows (e.g. a rolling "last 24h from
now"). Fix loop 1 switched to integer CEILING `expected_cycles` (preserving divisible-window
behavior) + a non-divisible-window regression test; re-review APPROVE.

### Non-blocking minor recorded (note)
- A test helper imports `AvailabilityCalculator` lazily while importing siblings at module top —
  cosmetic, no functional impact.

---

## STORY-025 — Enforce the Verdict maintenance↔health invariant (1 pt) — ✅ DONE

A Pydantic `model_validator(mode="after")` on `Verdict` now rejects incoherent shapes at
construction (`under_maintenance=True` ⇒ `health is None`; `False` ⇒ a set `health`), matching
`signal.py`'s validate-at-construction stance. Light pipeline.

**Note:** one existing STORY-010 test (`test_verdict_health_defaults_to_none`) asserted the
*now-invalid* shape succeeds — it contradicted the very invariant this story enforces, so the
implementer correctly replaced it with a raises-test. A legitimate, flagged exception to "existing
tests pass unchanged."

---

## DoD evidence (orchestrator-verified)
| Command | Result |
|---|---|
| `pytest` | 191 passed (162 baseline + 24 availability/ports + 1 fix-loop + 4 net Verdict-invariant) |
| `lint-imports` | 3 kept, 0 broken |
| `check_fk_direction.py` | 10 FKs, 0 violations |
| `alembic upgrade head` | no-op (read-only SELECT added; no migration) |

## Demo
- Availability calculator: `pytest backend/tests/test_availability.py` (incl. the 3-location 100%
  case + the non-divisible-window regression).
- Verdict invariant: `pytest backend/tests/test_verdict.py`.
- Pure-math tested with in-memory fakes; only the `in_window` read adapter uses a throwaway DB.

## Wiki
Compile pass done (blocks review): EXTRACTED a new `core-pipeline-and-availability.md` (the
collapse/streak + availability Facts had grown into a catch-all whose code_refs didn't even list
`pipeline.py` — those Facts were uncovered by the staleness check); `canonical-types-and-ports.md`
re-scoped to vocabulary + ports; `ingest-service-and-pull-loop.md` rehabilitated. No stale articles;
links lint clean.

## Carried into Sprint 8
- STORY-024 (anti-flap + decide, 5, draft) — still needs the per-app config mechanism resolved.
- STORY-026 (skew flag, 3, draft) — two open questions (peer-set source, result shape).

## PO verdict
- [x] STORY-011 — **ACCEPTED** (2026-06-25). 5 pts. Merged to main.
- [x] STORY-025 — **ACCEPTED** (2026-06-25). 1 pt. Merged to main.
- PO directed a follow-up from the minor: **STORY-027** (hoist the lazy `AvailabilityCalculator`
  import in `test_availability.py`) added to the backlog as `ready`.
