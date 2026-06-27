---
id: STORY-027
title: Hoist the lazy AvailabilityCalculator import in test_availability.py
type: chore
---

## Context
Follow-up from Sprint 7 review (STORY-011 quality-review minor, non-blocking, readability only).
In `backend/tests/test_availability.py`, a test helper imports `AvailabilityCalculator` lazily
(inside the helper function body) while its siblings `AvailabilityResult` / `rollup_group` are
imported at module top. Cosmetic inconsistency, no functional impact — purely a tidy-up.

## Acceptance Criteria (refined — PO-approved 2026-06-25)
- [x] AC1: `AvailabilityCalculator` is imported at module top in `backend/tests/test_availability.py`,
      alongside `AvailabilityResult` / `rollup_group`; the in-function lazy import is removed.
- [x] AC2: No behaviour change — all existing availability tests pass unchanged; `lint-imports`
      stays green. (Test-only change; nothing under `src/` is touched.)

## Resolved Questions
- None. Cosmetic test-import tidy-up.

## History
- 2026-06-25: created from Sprint 7 review (PO asked the lazy-import minor become a follow-up).
  Status: ready — test-only, no open questions. Estimate: 1 (near-trivial).
