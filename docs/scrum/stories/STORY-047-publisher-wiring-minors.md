---
id: STORY-047
title: Chore — quality-review minors (STORY-045 publisher wiring + STORY-044 availability DTO)
type: chore
---

## Context / how it surfaced
Filed at the Sprint 29 review (2026-07-03): the PO accepted STORY-045 with a follow-up chore for
the two non-blocking quality-review minors (Opus quality reviewer, 0 Critical / 0 Major — these
were the only notes). At the Sprint 30 review (2026-07-03) the PO accepted STORY-044 and folded
its two quality minors into this same chore (items 3–4 below).

1. `composition/app.py::create_app` injected-fakes path: a test that injects `component_repo` but
   omits `publication_repo` (or vice versa) silently gets a bare `LoggingPublisher` with NO status
   write-back, even though a `component_repo` is present. Production is unaffected (the real path
   always constructs both repos and always gets the full `StatusWritebackPublisher` chain), but the
   test-surface behavior is surprising: a fake-injected app can exercise approve and see no
   write-back without any signal as to why.
2. `composition/publish_helper.py`: the pre-existing `publish_best_effort` free function and the
   `BestEffortPublisher` class that wraps it are both live seams (predates STORY-045). One
   canonical best-effort seam is cleaner.

3. (from STORY-044, sprint 30) `api/v1/availability/service.py::get_component_availability`
   constructs each `SignalAvailabilityDTO` by spelling out all nine `AvailabilityDTO` fields
   inline instead of reusing the `_to_dto` helper — field-list duplication that would drift if
   `AvailabilityDTO` gains a field.

4. (from STORY-044, sprint 30) same function: `children_signals` is iterated twice (null-interval
   guard, then compute). The reviewer judged this INTENTIONAL fail-fast-before-any-compute and
   clear as written — recorded here because the PO folded both minors in; no behavior change is
   wanted, simplify only if it falls out of the AC4 refactor naturally.

5. (from STORY-048, sprint 31) `backend/tests/fakes.py::FakeSampleModeRepository` uses bare
   `dict` type hints (`store: dict | None`, `self._store: dict`) where the peer fakes
   parametrize (e.g. `dict[int, StatusProposal]`) — cosmetic consistency fix
   (`dict[bool, bool]` keyed by the single-row id, or whatever shape the store actually holds).
   NOTE this fake is part of the TEMPORARY sample-mode feature (see
   `docs/scrum/wiki/sample-mode.md` REMOVAL inventory) — if removal happens first, this item
   dies with it. The sprint-31 quality review's other minor (wiki `verified_sha` pinned at the
   last code commit instead of the wiki commit) needs NO chore: the sweep is clean and the pins
   refresh naturally on the next touch.

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
- [ ] AC4: `get_component_availability` builds each child `SignalAvailabilityDTO` via the shared
      `_to_dto` helper (no nine-field inline duplication); existing rollup-endpoint tests stay
      green (behavior identical). The double iteration (item 4) needs no change unless the
      refactor removes it for free.
- [ ] AC5: `FakeSampleModeRepository`'s store hints are parametrized like the peer fakes (item
      5); suite stays green; skip (and tick as N/A) if sample-mode removal landed first.

## Open Questions
None — all changes are mechanical; AC1's shape (write-back whenever component_repo exists) was
implied by the reviewer's note.

## History
- 2026-07-03: filed from the Sprint 29 review (PO verdict: accept + follow-up chore). Estimate 1.
  Status: ready.
- 2026-07-03: Sprint 30 review — PO accepted STORY-044 and folded its two quality minors in
  (items 3–4, AC4). Estimate stays 1 (all items are small mechanical edits in two files).
- 2026-07-03: Sprint 31 review — STORY-048 accepted; its one actionable cosmetic minor folded in
  (item 5, AC5); the verified_sha-pin minor recorded as no-action. Estimate stays 1.
