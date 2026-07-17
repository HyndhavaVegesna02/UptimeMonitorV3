---
id: STORY-100
title: Approvals decision support — evidence-first proposal cards + consequence-aware confirm
type: story
---

## Context
ui-redesign exploration 2026-07-17 (journal finding #4, decision D5): the approval card
shows only a raw signal slug, a transition pair, and a raw timestamp. The operator is
asked to publish a public status change with no evidence — no component name, no
affected locations, no duration, no route to the underlying checks. "Metrics without
context" is the top observability-dashboard anti-pattern (logz.io #1).

## Description
Evidence-first proposal card, built ONLY from data already exposed by existing endpoints
(component list, check history, availability — no API changes):
- Friendly component name (slug stays as secondary text).
- "Proposed Xm ago" (STORY-098 formatter) + "observing signals since" context when
  derivable from history.
- Affected locations: latest result per location for the proposal's signal from the
  existing history endpoint (status + latency + relative time).
- "View checks" link → Check History pre-filtered to the component/signal (URL params;
  Check History already supports filter state — wire params to it if not yet URL-driven,
  display-layer only).
- Confirm step states the consequence: "Publishes '<component>: <to-status>' to the
  public status page." Approve keeps primary styling; the consequence line is explicit.

## Acceptance Criteria
- [ ] AC1: proposal card shows friendly component name, transition, relative proposed
      time, and per-location latest results (each with status badge, latency, relative time).
- [ ] AC2: "View checks" navigates to Check History with the relevant filter applied
      (deep-linkable URL).
- [ ] AC3: the approve confirm step names the component and target status and states that
      it publishes to the public status page; reject confirm unchanged in behavior.
- [ ] AC4: queue with multiple proposals renders each card independently (MSW test);
      loading/error states for the evidence fetch degrade gracefully (card still
      actionable if history fetch fails).
- [ ] AC5: no new backend endpoints or params consumed beyond what exists today;
      Vitest green.

## History
- 2026-07-17: filed + refined during ui-redesign refinement (PO-delegated); estimate 3.
