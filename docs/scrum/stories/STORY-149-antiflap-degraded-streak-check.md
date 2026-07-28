---
id: STORY-149
title: Anti-flap — require a streak for DEGRADED, symmetric with the DOWN ladder
type: defect
---

## Context

`anti_flap` proposes `degraded` for a `DEGRADED` streak of **any length, with no length check
at all** (`backend/src/core/services/pipeline.py:226-227`):

```python
if streak_.health is Health.DEGRADED:
    return _propose(ComponentStatus.DEGRADED)
```

The `DOWN` branch immediately above it requires `length >= thresholds.degraded` before
proposing anything, and returns an unpublishable internal warning for a streak of exactly 1
(`pipeline.py:215-224`). `DEGRADED` has no such damping.

**Repro (why this matters as locations grow).** `_collapse_health` returns `DEGRADED` for
**any** disagreement between a cycle's per-location observations (`pipeline.py:84-97`) — it
returns `DOWN` only when *every* location is down. So:

- With **one** location (today's live topology) a mix is impossible: one observation is either
  `up` or `down`, so `DEGRADED` only arises if the vendor itself reports it. The unguarded path
  is effectively dead code in production.
- With **3–7** locations, a mix is the normal consequence of any single location hiccuping
  **once** — and each such cycle proposes a public status change with **zero anti-flap
  damping**. One blip moving a public status page is precisely what anti-flap exists to prevent.

Given the PO's confirmation that many more components (and their locations) are coming, this
becomes live the moment a second location exists.

This is **Phase 1** of the agreed fix. Phase 2 — the breadth-ceiling model (D1/D2), which also
addresses the `major_outage` severity ceiling and the `degraded` semantic conflation — is a
separate, larger story and is NOT in this sprint. Phase 1 is deliberately scoped to the four
lines that close the damping hole with no modelling debate.

## Description

Make the `DEGRADED` branch of `anti_flap` symmetric with the `DOWN` ladder: require the streak
to reach `thresholds.degraded` before proposing, and return the existing internal-warning
outcome for a streak of exactly 1.

`thresholds.degraded` already means "how many consecutive bad cycles before we call it
degraded" (`AntiFlapThresholds`, `pipeline.py:146-147`), so no new config is needed.

## Acceptance Criteria

- [ ] **AC1** — A `DEGRADED` streak with `length >= thresholds.degraded` proposes
      `ComponentStatus.DEGRADED` (unchanged outcome for the sustained case).
- [ ] **AC2** — A `DEGRADED` streak with `length == 1` returns the **internal-warning** outcome
      (`proposed_status is None`, `internal_warning is True`) — logged, never published —
      exactly as the `DOWN` branch does for a single failure (`pipeline.py:222-223`).
- [ ] **AC3** — A `DEGRADED` streak with a length above 1 but below `thresholds.degraded`
      proposes **nothing** (`proposed_status is None`, `internal_warning is False`). Covers the
      case reachable when `thresholds.degraded > 2`.
- [ ] **AC4 (regression — proves the defect is gone)** — A test asserts the OLD behaviour no
      longer holds: a `DEGRADED` streak of 1 previously proposed `degraded`, and now does not.
      This test must fail if the fix is reverted.
- [ ] **AC5 (no collateral change)** — Every existing `anti_flap` test for the `DOWN` and `UP`
      branches passes **untouched** — no assertion is edited, weakened, or deleted. The
      `DOWN` ladder (`major`/`partial`/`degraded`/warning) and the `UP` recovery threshold are
      byte-identical in the diff.
- [ ] **AC6** — All five backend DoD gate commands exit 0.

## Open Questions

None.

## History

- 2026-07-28: drafted as Phase 1 (P1) of the anti-flap/breadth work agreed with the PO. Phase 2
  (breadth sets a severity ceiling, duration climbs to it; minority-unreachable caps at
  `partial_outage`) is recorded as D1/D2 in
  `docs/scrum/sprints/2026-07-28-sprint-62/decisions-and-future-work.md` and is explicitly out
  of this sprint. Note that on the live HTTP path today no vendor mapping produces `DOWN` or
  `DEGRADED` at all (`health_mapping.py:65-70`), so this fix is verified against fixtures and
  demo-engine scenarios rather than live vendor failures.
