---
id: STORY-026
title: Per-component skew flag (Tier-2)
type: feature
---

## Context
Spec: dossier §11 (skew, surfaced) + Tier-2 item 7 / T2.7 (multi-watermark). Zone 4. Split from
STORY-011 (the availability calculator) at refinement — skew is a cross-signal watermark peer
comparison, distinct from the two-grain availability/completeness math. PURE / compute-only,
consistent with the rest of the calculator (derive-on-read, persists nothing). Reads watermarks —
but, per the established Zone 4 pattern (STORY-010 injected `maintenance`, STORY-011 injected
`interval`/`window`), the **peer set and their watermarks are INJECTED inputs**, so no topology
loading or DB access lives in this pure function.

## Description
In `core/services/` (e.g. `availability.py` or a sibling): a pure `skew` function. Given a
component's feeding signals — each with its current watermark and its own `interval` — the skew
flag is SET for any feeding signal that lags its peers (the most-recent peer watermark) by MORE than
its own `interval`. Returns a SEPARATE per-component skew result (NOT a field bolted onto
`AvailabilityResult` — skew rides alongside completeness but is a distinct signal, since completeness
can be low for other reasons). The result names which signals are lagging (so the dashboard /
proposal annotation can show them).

## Acceptance Criteria (refined — PO-approved 2026-06-25)
- [ ] AC1: Given a component's feeding signals (each: `signal_key`, watermark, `interval`), a signal
      lagging the most-recent peer watermark by MORE than its own `interval` is flagged as skewed;
      one within its interval is not. Unit-tested with in-memory fixtures.
- [ ] AC2: Skew is a SEPARATE result from `AvailabilityResult` (its own type), not derived from the
      completeness %. A test shows the two can diverge (full completeness yet a skewed feeder, and
      vice versa).
- [ ] AC3: Pure / provider-blind — peer set + watermarks + intervals are INJECTED (no topology
      load, no DB, no vendor/HTTP/SQL); `lint-imports` green; tests need no live services.
- [ ] AC4: Boundary + degenerate inputs are defined and tested (sprint-6 + sprint-7 agreements):
      a signal lagging by EXACTLY its interval (not skewed) vs just over (skewed); an empty peer set
      and a single-signal component (no peers → no skew); a signal with no watermark yet. No crash.

## Resolved Questions
- Peer-set source: **INJECTED** (the feeding signals + their watermarks + intervals are passed in);
  the component→signals topology (seeded config, §7) is NOT loaded here — deferred, consistent with
  the Zone 4 injection pattern. (PO-approved at refinement, 2026-06-25.)
- Result shape: a **separate per-component skew result type** (names the lagging signals), NOT a
  field on `AvailabilityResult`. (PO-approved 2026-06-25.)

## History
- 2026-06-25: created by splitting the skew flag out of STORY-011 at refinement (Tier-2, cross-
  signal). Status: draft.
- 2026-06-25 (sprint-8 refinement): open questions resolved (injected peers; separate result type);
  AC1–AC4 finalized; estimate held at 3. Status: ready.
