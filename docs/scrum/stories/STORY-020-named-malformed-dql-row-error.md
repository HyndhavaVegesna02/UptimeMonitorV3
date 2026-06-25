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

## Acceptance Criteria (draft — confirm at refinement)
- [ ] AC1: Given a DQL row missing any required field, the adapter raises
      `MalformedDqlRowError` naming the missing field — not a bare `KeyError`.
- [ ] AC2: A test exercises each required-field-missing case (or a parametrized equivalent).
- [ ] AC3: `lint-imports` stays green; the error type lives in the dynatrace package; the
      existing 20 STORY-008 tests still pass unchanged.

## Open Questions
- None expected; confirm the exact field list + error placement at refinement.

## History
- 2026-06-25: created from Sprint 4 review (PO asked both STORY-008 minors become chores).
  Status: draft — refine + estimate before a sprint. Proposed estimate: 1.
