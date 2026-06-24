# Sprint 1 — Review

**Goal:** Zone 1 complete — the canonical vocabulary and the core's owned interfaces
exist, so every later zone has vendor-neutral types and ports to build against.

**Committed:** 6 pts (STORY-004 + STORY-005) · **Branch:** `sprint-1` ·
**Baseline at lock:** all four DoD commands green on `main`.

**Result: both stories Done, full pipeline green. Nothing merged to main yet — awaiting
your accept/reject per story.**

---

## STORY-004 — Canonical SignalObservation type (3 pts)

**What was built:** three frozen Pydantic v2 types in `backend/src/core/domain/signal.py`
(exported via `__init__.py`):
- `Health(str, Enum)` — closed enum `up`/`down`/`degraded`
- `Provenance` — frozen `{system, native_id, native_kind}`; sole home of vendor ids
- `SignalObservation` — the canonical spine, all §5 fields, with a validator rejecting
  naive/non-UTC `observed_at`

Tests: `backend/tests/test_signal_observation.py` (16).

| AC | Verdict | Evidence |
|----|---------|----------|
| AC1 frozen + all §5 fields | MET | `test_signal_observation_constructs_from_valid_fields`, `..._is_frozen` |
| AC2 closed health enum | MET | `test_health_has_exactly_up_down_degraded`, `..._rejects_unknown_health` |
| AC3 UTC `observed_at`, reject naive | MET | `..._rejects_naive_observed_at`, `..._accepts_tz_aware_utc` |
| AC4 vendor id only in `source` | MET | `test_vendor_id_appears_only_inside_source`, `..._field_names_are_vendor_neutral` |
| AC5 round-trip + invalid rejected | MET | `..._round_trips_via_model_dump`, `..._requires_signal_key/_source` |
| AC6 `lint-imports` 0 | MET | gate green, 3 contracts kept |

**Spec review:** PASS (6/6 MET; UTC-offset strictness endorsed vs §5).
**Quality review:** APPROVE (0 critical/major; 2 minors recorded as story notes).
**Decision of note:** `observed_at` rejects any non-zero UTC offset (`+02:00` too), not just
naive — strict reading of §5 "UTC run time". Reviewers endorsed; flagged for your awareness.

## STORY-005 — The core ports (3 pts)

**What was built:** five port ABCs in `backend/src/core/ports/` + three supporting domain
types in `backend/src/core/domain/status.py` (`ComponentStatus`, `StatusChange`,
`IngestResult`). Fakes for every port in `backend/tests/fakes.py`.

| AC | Verdict | Evidence |
|----|---------|----------|
| AC1 five ports as ABCs, canonical signatures | MET | `*_is_abstract_and_cannot_be_instantiated` tests; signatures match exactly |
| AC2 a fake per port, under `tests/`, exercised | MET | 5 fakes in `tests/fakes.py`, each used in `test_core_ports.py` |
| AC3 `ClockPort.now()` tz-aware UTC, injectable | MET | `test_fake_clock_returns_injected_fixed_tz_aware_utc_time` |
| AC4 watermark `get` None unset, advance→get | MET | `..._get_returns_none_when_unset`, `..._advance_then_get_round_trips` |
| AC5 `lint-imports` 0, ports→domain not services | MET | gate green; `core-internal-layering` now bites, KEPT |

**Spec review:** PASS (5/5 MET; ports map 1:1 to dossier §6).
**Quality review:** APPROVE (0 critical/major; 3 minors recorded as story notes).
**Scoping:** richer repository query methods deliberately deferred to Zone 2/4 consumers.

---

## DoD evidence (recorded per story in `sprint-current.yaml`)

Both stories passed the full four-command gate (exit 0): `pytest`, `lint-imports`,
`alembic upgrade head`, `check_fk_direction.py`. Final state on the branch:
`pytest` → **45 passed**; `lint-imports` → **3 contracts kept, 0 broken**;
`alembic upgrade head` → baseline applied; FK-check → **0 FKs, 0 violations**.

## Demo

Pure-core zone, no UI/endpoint yet. Demo is the live test + boundary gate (run at review).

## Wiki compile pass (blocking — done)
- **Created** `canonical-types-and-ports.md` — Zone 1 types + ports catalogued with
  `file:line` Facts, verified at the branch tip.
- **Rehabilitated** `architecture-boundary.md` — re-verified (Facts still hold), `verified_sha`
  bumped, noted the layering contract now bites; cross-linked to the new article.
- **Link-lint:** all `[[links]]` resolve. No articles stale ≥3 sprints.

## Notes carried forward (non-blocking, in story files)
- STORY-004: UTC-offset validator permissive on tz *name*; vendor-id test is flat-shape only.
- STORY-005: `from fakes import` bare style; `RecordingStatusPublisher` naming; defensive
  `NotImplementedError` after `@abstractmethod`.
