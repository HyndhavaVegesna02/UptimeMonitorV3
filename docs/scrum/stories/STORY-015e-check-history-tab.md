---
id: STORY-015e
title: Check History tab — per-signal observation history
type: feature
---

## Context
Spec: dossier §17. Zone 7. Split-child of STORY-015; depends on STORY-015a. API:
`GET /api/v1/history` (STORY-014c) — raw per-signal observations (the ingest ledger view).

## Description
A dense, chronological list of check observations — the reference's `changelog-row` pattern is
the natural fit: hairline-separated rows with timestamp (mono), signal/component, health
StatusBadge, latency (mono, ms), and location. Filterable by component/signal and time window.

## Acceptance Criteria
- [ ] AC1: The tab fetches `GET /api/v1/history` (tz-aware window params) and renders
      observations newest-first: timestamp, signal/component, status badge, latency, location.
- [ ] AC2: A component/signal filter and a window selector drive refetches; MSW tests assert
      the sent query params.
- [ ] AC3: Machine values (timestamps, latency) render in the mono token; status follows the
      non-text-only color rule (badge = dot + label).
- [ ] AC4: Loading/empty ("no observations in this window")/error+retry states tested.

## Open Questions
None.

## History
- 2026-06-29: first version refined; reverted with `521764c`.
- 2026-07-02: re-refined for the Linear-guided direction. Status: ready. Estimate 3.
