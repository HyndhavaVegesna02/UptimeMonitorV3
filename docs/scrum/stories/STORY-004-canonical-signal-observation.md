---
id: STORY-004
title: Canonical SignalObservation type
type: feature
---

## Context
Spec: dossier §5 (Canonical signal) + §6 (vocabulary rule P3). Zone 1. The spine of
the whole system — the vendor-neutral form of one synthetic monitor execution from one
location. Vendor identifiers live ONLY in provenance.

## Description
Define the frozen, validated `SignalObservation` canonical type in `src/core/domain/`:
`signal_key` (stable name you choose, never a vendor id), `observed_at` (UTC),
`health` (closed enum: `up` / `down` / `degraded`), `source_event_id` (idempotency
key), `source` provenance `{system, native_id, native_kind}`, `location`, optional
`latency_ms`, optional `raw_ref`. Every field must make sense to a reader who has never
heard of Dynatrace.

**Implementation decision (refinement):** Pydantic v2 frozen model
(`model_config = ConfigDict(frozen=True)`). Pydantic is already a core dependency and is
NOT forbidden by the `core-independence` import contract (which forbids
`src.adapters`/`sqlalchemy`/`httpx`). It gives closed-enum validation, UTC enforcement,
and serialize→reconstruct round-trip natively. `Provenance` (frozen: `system`,
`native_id`, `native_kind`) and `Health` (str enum) are defined alongside in
`core/domain`.

## Acceptance Criteria
- [ ] AC1: `SignalObservation` lives in `src/core/domain/`, is frozen (mutating a field
      raises), and constructs from valid §5 fields: `signal_key:str`,
      `observed_at:datetime`, `health:Health`, `source_event_id:str`,
      `source:Provenance`, `location:str`, `latency_ms:int|None`, `raw_ref:str|None`.
      `Provenance` and `Health` are defined alongside.
- [ ] AC2: `health` is a closed enum — exactly `up`/`down`/`degraded`; any other value
      raises at construction.
- [ ] AC3: `observed_at` must be tz-aware UTC; a naive datetime is rejected (not silently
      coerced) so bad upstream data surfaces.
- [ ] AC4: The vendor identifier appears ONLY inside `source` (`native_id`); a test
      asserts no field outside `source` carries a vendor id, and every field name reads
      vendor-neutrally.
- [ ] AC5: Round-trip (`construct → model_dump → reconstruct`) yields an equal object;
      invalid inputs (bad enum, naive datetime, missing required field) raise
      `ValidationError`.
- [ ] AC6: `lint-imports` exits 0 (`core/domain` imports nothing outward; no vendor type).
- [ ] Every AC carries at least one test (DoD standing rule).

## Open Questions
- None — resolved at refinement (2026-06-24): library = Pydantic v2 frozen model;
  estimate = 3; naive datetime is rejected, not coerced.

## Review notes (Sprint 1 — non-blocking minors from quality review)
- `signal.py` `_require_utc` validator accepts any zero-offset tzinfo (e.g. a tz literally
  named "GMT"), not strictly `timezone.utc`. Correct per §5 ("UTC run time" = the instant,
  offset-zero); recorded only so the choice is on record. No change needed.
- `test_vendor_id_appears_only_inside_source` stringifies `model_dump()` values and checks
  substring absence — solid for the current flat shape; would need recursion if a future
  nested non-source field were added. Out of scope for this story.

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §5/§6. Status: draft.
- 2026-06-24: refined for Sprint 1 — AC finalized, library decision (Pydantic v2 frozen
  model) recorded, open questions resolved. Status: ready.
- 2026-06-24: implemented (commits abeb448..30c46e7), spec review PASS (6/6 AC MET),
  quality review APPROVE (0 critical/major). Full DoD gate green. Status: done (board).
