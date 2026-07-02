---
id: STORY-044
title: Availability & topology API — component→signals enumeration + component-rollup availability + real per-signal intervals
type: feature
---

## Context
Enabler for the two-grain Availability tab (STORY-015d) and the Check History tab (STORY-015e),
from the PO's 2026-07-02 clarifications + the full-codebase audit:
- A component CAN have multiple signals (the mapping lives in `config/apps/*.yaml` and is seeded
  into the DB by `composition/seed.py`), and the dashboard must show availability at BOTH grains —
  the component rollup AND each signal.
- Today NO endpoint enumerates signals or the component→signal mapping, so a frontend cannot know
  what `signal_key` to pass `/availability` or `/history` (both REQUIRE it).
- The core already computes the rollup: `core/services/availability.py::rollup_group(children)` —
  availability%/completeness% = MIN across children, counts SUM ("a group is only as available as
  its worst child", dossier §11/AC3) — but it is not exposed via any endpoint.
- **Audit finding folded in (H2):** `api/v1/availability/controller.py:37` defaults
  `interval_seconds` to 60 with a comment promising "STORY-040 will supply per-signal config" —
  STORY-040 closed (sprint 18) without doing it, and the real config (`httpcheck.yaml`) says 120.
  A default-interval call computes `expected_cycles` 2× too high → completeness% roughly HALVED.
  The interval must come from the signal's own config server-side, not from a client guess.

## Description
Backend-only. Expose the topology the frontend needs and the component-grain availability, and
make per-signal intervals authoritative server-side:
1. **Signals/topology enumeration** — the frontend can list components WITH their signals
   (per signal: `signal_key`, `name`, `interval_seconds`, `component_id`). Shape decided at
   refinement of the endpoint (extend `/components` vs a new feature module) — either way the
   five-file convention + api-feature-independence contract hold.
2. **Component-rollup availability** — an endpoint computes per-signal `AvailabilityResult`s for
   ALL of a component's signals (each with ITS OWN configured interval) and rolls them up via the
   existing `rollup_group`; returns the rollup plus the per-signal children (so 015d renders both
   grains from one call).
3. **Interval correctness** — per-signal availability uses the signal's configured
   `interval_seconds` (from the seeded topology) by default; the misleading stopgap default/comment
   is retired or corrected.

## Acceptance Criteria
- [ ] AC1: an endpoint returns every component with its signals — `signal_key`, signal `name`,
      `interval_seconds`, `component_id` — sourced from the seeded topology (NOT re-read from
      config files at request time). Empty topology → 200 + empty. Tested (DB-gated, seeded via the
      shared harness).
- [ ] AC2: an endpoint returns component-grain availability for a component id over a tz-aware
      window: the `rollup_group` result PLUS the per-signal child results, each child computed with
      that signal's configured interval. Naive datetimes → 422 (2026-06-28 agreement). Unknown
      component id → 404. No-data window → the calculator's None-percentage degenerate handling
      surfaces as null, not 500. Tested incl. a multi-signal component fixture proving MIN/SUM
      rollup and per-child intervals.
- [ ] AC3: per-signal `/availability` no longer silently mis-computes: when `interval_seconds` is
      not supplied by the caller, the signal's configured interval is used (the 60s stopgap default
      + the stale "STORY-040 will supply" comment are gone). An explicit caller-supplied interval
      still wins (back-compat). Tested: default path uses 120 for `http-check` (completeness no
      longer halved).
- [ ] AC4: five-file shape test for any new feature module (2026-06-28 agreement); all six backend
      gates green; wiki blast radius resolved (`api-five-file-convention`,
      `core-pipeline-and-availability`, `frontend-zone` untouched).

## Open Questions
None blocking — endpoint shape (extend vs new module) is a plan-level decision, made at sprint
planning against the five-file convention.

## History
- 2026-07-02: refined from the PO's multi-signal clarifications + audit finding H2. Unblocks
  STORY-015d and STORY-015e (both need signal enumeration). Estimate 5. Status: ready.
