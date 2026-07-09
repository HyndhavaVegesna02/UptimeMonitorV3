---
id: STORY-076
title: One home for read-window policy — _shared/windowing.py consumed by availability + history
type: chore
---

## Context
From the 2026-07-10 API restructure proposal (§3.4 G3, §10 Phase 3). The read-window defaulting
policy (`_DEFAULT_WINDOW_HOURS = 24`; `until` defaults to now, `since` defaults to `until − 24h`)
exists twice: `api/v1/availability/service.py::_resolve_window` (which also computes the window
label) and inlined in `api/v1/history/service.py` (lines ~43–53). The duplication is
contract-FORCED: `api-feature-independence` forbids history importing from availability, and core
is the wrong home for HTTP default policy. If one copy's default ever changes, the dashboard and
history quietly disagree about what "recent" means, with no test catching it. Availability's own
docstring claims window defaulting "has ONE home" — currently false across features.

## Description
Add `backend/src/api/v1/_shared/windowing.py` as the single home for the defaulting policy; both
features consume it; both private copies are deleted. Pure consolidation — behavior identical.

## Acceptance Criteria
- [ ] `backend/src/api/v1/_shared/windowing.py` exposes the window-defaulting policy (the 24h
      constant + a `resolve_window(since, until, now)`-shaped function) with semantics IDENTICAL
      to today's: `until` missing → `now`; `since` missing → `until − 24h`; explicit values pass
      through. Docstring cites proposal §3.4 G3. Feature-specific concerns (availability's window
      LABEL, each feature's syntactic validation) stay feature-local — only the defaulting policy
      moves.
- [ ] `availability/service.py` and `history/service.py` both consume it; NO private copy of the
      defaulting logic remains in either (the duplicated constant + defaulting expressions are
      deleted, not shadowed).
- [ ] `windowing.py` has direct unit tests covering: both defaults applied, one-sided defaults,
      explicit pass-through — plus the empty/degenerate case per the standing empty-input
      agreement (both `None` with a fixed `now` → the exact 24h window ending at `now`).
- [ ] **Frozen behavior:** all existing endpoint tests pass UNMODIFIED (window semantics are
      observable through them).
- [ ] Backend six-gate DoD green (lint-imports still 8 kept, 0 broken — `_shared` already fenced);
      wiki blast radius resolved via the mechanical sweep.

## Open Questions
None.

## References
- Proposal: `docs/superpowers/specs/2026-07-10-api-restructure-design.md` §3.4 (G3), §6.2, §10 Phase 3
- Depends on: STORY-075 (the `_shared` package + its contract must exist).

## History
- 2026-07-10: filed + refined from the accepted API restructure proposal (Phase 3). Status: ready (2 pts).
