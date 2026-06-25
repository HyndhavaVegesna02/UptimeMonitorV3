---
id: STORY-020
title: Named malformed-DQL-row error in the Dynatrace normalizers
type: chore
---

## Context
Follow-up from Sprint 4 review (STORY-008 quality-review minor, non-blocking). The
Dynatrace normalizers + shared assembler subscript required row fields directly
(`row["timestamp"]`, `row["event.id"]`, `row["synthetic_test.id"]`,
`row["synthetic_location.name"]`, and the dispatch key `row["synthetic_test.type"]`), so a
malformed DQL row missing a field raises a bare `KeyError` rather than a named adapter
error like the package's deliberate `UnsupportedMonitorTypeError` / `UnknownVendorOutcomeError`.
Behaviour is fail-loud (not silent corruption), so this is a readability/consistency
chore, not a bug. Code: `backend/src/adapters/inbound/dynatrace/_assembly.py`,
`dispatch.py`, the two `*_normalizer.py`.

## Description
Surface a missing/empty required field as a named `MalformedDqlRowError` (a `ValueError`
subclass, matching the package's existing error style) that identifies the missing field,
instead of a bare `KeyError`. Keep it fail-fast — do not swallow or default.

## Acceptance Criteria (refined — PO-approved 2026-06-25)
- [ ] AC1: Given a DQL row missing any required field (`timestamp`, `event.id`,
      `synthetic_test.id`, `synthetic_test.type`, `synthetic_location.name`), the adapter
      raises `MalformedDqlRowError` naming the missing field — not a bare `KeyError`.
- [ ] AC2: A test exercises each required-field-missing case (parametrized is fine).
- [ ] AC3: `lint-imports` stays green; the error type lives in the dynatrace package (a
      `ValueError` subclass, matching `UnsupportedMonitorTypeError` / `UnknownVendorOutcomeError`);
      the existing 20 STORY-008 tests still pass unchanged. Optional `latency_ms`
      (`request.response_time_ms`) stays optional — its absence is NOT an error.

## Resolved Questions
- Required-field list and error placement confirmed (see AC1): the dispatch key
  `synthetic_test.type` is validated in `dispatch.py`; the remaining fields in
  `_assembly.assemble_observation`. PO-approved at refinement, 2026-06-25.

## History
- 2026-06-25: created from Sprint 4 review (PO asked both STORY-008 minors become chores).
- 2026-06-25: refined for Sprint 5. AC1–AC3 finalized; required-field list fixed; estimate 1.
  Status: ready.
