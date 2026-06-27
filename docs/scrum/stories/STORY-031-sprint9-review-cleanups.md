---
id: STORY-031
title: Sprint 9 review cleanups — test/fixture/style nits
type: chore
---

## Context
Follow-up from Sprint 9 review (non-blocking quality-review minors on STORY-012 + STORY-013).
Bundles a few cosmetic test/style tidy-ups; no behaviour change.

## Acceptance Criteria (refined — PO-approved 2026-06-26)
- [x] AC1: Remove the leftover import-smoke test `test_publisher_can_be_imported` in
      `backend/tests/test_statuspage_adapter.py` (it only asserts `is not None`; real tests now cover
      the adapter).
- [x] AC2: Resolve the unused `backend/tests/fixtures/statuspage/component_degraded.json` — EITHER
      delete it, OR add a `publish()` test that exercises the `DEGRADED → degraded_performance` path
      end-to-end and asserts against it (prefer exercising it, so the degraded mapping is covered
      through the publish path, not just the unit mapping test).
- [x] AC3: Tidy the style nits flagged in review: add the missing blank line between
      `FakeProposalRepository` methods in `backend/tests/fakes.py`; hoist the mid-module
      `import json` / `from pathlib import Path` to the top of `test_statuspage_adapter.py`.
- [x] AC4: `pytest`, `lint-imports` green; no behaviour change to production code.

## Resolved Questions
- None. Cosmetic/test-only cleanups.

## History
- 2026-06-26: created from Sprint 9 review (PO asked for a follow-up bundling the non-blocking
  minors). Status: ready — test/style only, no open questions. Estimate: 1.
