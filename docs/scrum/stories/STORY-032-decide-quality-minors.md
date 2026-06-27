---
id: STORY-032
title: decide.py quality minors — DRY, import style, opened.id guard, trailing blanks
type: chore
---

## Context
Follow-up from Sprint 10 review (STORY-024 quality review, Opus — the non-blocking MINOR findings;
the blocking MAJOR, missing docstrings, was fixed inline during the sprint at commit `ed87055`).
Cosmetic / robustness tidy-ups in `backend/src/core/services/decide.py` only — no behaviour change.

## Acceptance Criteria (refined — PO-approved 2026-06-27)
- [ ] AC1: The two degradation branches in `decide` (no-open-proposal vs supersede) no longer
      duplicate the `StatusProposal(...)` construction + `create_open` + None-check verbatim — the
      common assembly is factored into one small local helper, with only the success action
      (`PROPOSED` vs `SUPERSEDED`) differing.
- [ ] AC2: `opened.id` (typed `int | None`) is guarded before being passed to `resolve(proposal_id:
      int, ...)` — an `assert`/explicit check with a clear message, consistent with the codebase's
      fail-loud ethos (a `get_open` result is always persisted, so this documents the contract).
- [ ] AC3: Import style matches the peer core services (import the severity helpers from the same
      source as the other domain symbols; sort imports); trailing blank lines at EOF removed (also in
      `test_decide.py` and the extra blank in `core/domain/__init__.py` introduced this sprint).
- [ ] AC4: Behaviour unchanged — all existing `test_decide.py` tests pass unchanged; `pytest` +
      `lint-imports` green. (Optionally add `from __future__ import annotations` to match
      `ingest_service.py`, at the implementer's discretion.)

## Resolved Questions
- None. Bounded cosmetic/robustness change to `decide.py` (+ two trailing-blank cleanups). No logic
  change, no new tests required beyond keeping the suite green.

## History
- 2026-06-27: created from Sprint 10 review (PO accepted STORY-024 + asked the quality minors become a
  follow-up chore). Status: ready — no open questions. Estimate: 1.
