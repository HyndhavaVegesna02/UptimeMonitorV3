---
id: STORY-026
title: Per-component skew flag (Tier-2)
type: feature
---

## Context
Spec: dossier §11 (skew, surfaced) + Tier-2 item 7 / T2.7 (multi-watermark). Zone 4. Split from
STORY-011 (the availability calculator) at refinement — skew is a cross-signal watermark peer
comparison, distinct from the two-grain availability/completeness math. Depends on **STORY-011**
(the availability calculator) and on reading watermarks across a component's feeding signals.

## Description
Surface the per-component **skew flag**: a feeding signal lagging its peers by more than its own
interval. Because the availability engine already reads watermarks, it surfaces this alongside
completeness — related but distinct (completeness can be low for other reasons). The flag appears
both on the dashboard and as an annotation on any proposal born during skew. Pure / compute-only,
consistent with the rest of the calculator (derive-on-read, persists nothing).

## Acceptance Criteria (draft — confirm at refinement)
- [ ] AC1: Given a component's feeding signals and their watermarks, the skew flag is set when any
      feeding signal lags its peers by more than its own `interval`. Unit-tested with in-memory
      fixtures.
- [ ] AC2: Skew rides alongside completeness but is a DISTINCT signal (not derived from the
      completeness %). Tested that the two can diverge.
- [ ] AC3: Pure / provider-blind — watermarks read through a port; `lint-imports` green; no live
      services in tests. `interval` is an injected input (no per-app config dependency).

## Open Questions
- How are a component's "feeding signals" (its peers) determined? That is the component→signals
  topology, which is seeded config (§7) and does not exist yet — does this story take the peer set
  as an injected input (staying pure, deferring topology), or does it need a topology precursor?
- Where does the flag surface in the result shape — an added field on `AvailabilityResult`, or a
  separate per-component result? Confirm against the dashboard need (Zone 7) at refinement.

## History
- 2026-06-25: created by splitting the skew flag out of STORY-011 at refinement (Tier-2, cross-
  signal). Status: draft — two open questions (peer-set source, result shape) to resolve before a
  sprint. Proposed estimate: 3.
