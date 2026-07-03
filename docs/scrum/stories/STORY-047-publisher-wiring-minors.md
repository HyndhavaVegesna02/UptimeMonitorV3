---
id: STORY-047
title: Chore — publisher-wiring minors from the STORY-045 quality review
type: chore
---

## Context / how it surfaced
Filed at the Sprint 29 review (2026-07-03): the PO accepted STORY-045 with a follow-up chore for
the two non-blocking quality-review minors (Opus quality reviewer, 0 Critical / 0 Major — these
were the only notes):

1. `composition/app.py::create_app` injected-fakes path: a test that injects `component_repo` but
   omits `publication_repo` (or vice versa) silently gets a bare `LoggingPublisher` with NO status
   write-back, even though a `component_repo` is present. Production is unaffected (the real path
   always constructs both repos and always gets the full `StatusWritebackPublisher` chain), but the
   test-surface behavior is surprising: a fake-injected app can exercise approve and see no
   write-back without any signal as to why.
2. `composition/publish_helper.py`: the pre-existing `publish_best_effort` free function and the
   `BestEffortPublisher` class that wraps it are both live seams (predates STORY-045). One
   canonical best-effort seam is cleaner.

## Acceptance Criteria
- [ ] AC1: in `create_app`, whenever a `component_repo` is available (injected or real), the wired
      publisher performs status write-back — injecting `component_repo` without `publication_repo`
      yields `StatusWritebackPublisher(LoggingPublisher())`, not a bare `LoggingPublisher`. Tested
      for the partial-injection combinations. Production wiring unchanged (still the full chain).
- [ ] AC2: `publish_best_effort` has exactly one production consumer
      (`BestEffortPublisher.publish`) or is folded into the class — grep-verifiable; no behavior
      change; existing publish_helper tests stay green (rewritten only if a signature they cover
      moves, per the 2026-06-29 contract-change agreement).
- [ ] AC3: all six backend DoD gates stay green; wiki blast radius resolved
      (`statuspage-publish.md`, `api-five-file-convention.md` as applicable).

## Open Questions
None — both changes are mechanical; AC1's shape (write-back whenever component_repo exists) was
implied by the reviewer's note.

## History
- 2026-07-03: filed from the Sprint 29 review (PO verdict: accept + follow-up chore). Estimate 1.
  Status: ready.
