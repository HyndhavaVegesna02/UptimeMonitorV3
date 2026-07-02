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
the natural fit: hairline-separated rows with timestamp (mono), health StatusBadge, latency
(mono, ms), and location.

**API contract (audit-verified 2026-07-02, per the tab-AC-vs-DTO agreement):**
`GET /api/v1/history` requires exactly ONE `signal_key` (no component filter, no multi-signal
query) plus optional tz-aware `since`/`until` (naive → 422); returns `ObservationDTO`
`{signal_key, observed_at, health, location, latency_ms}` newest-first. There is NO pagination —
`in_window` is unbounded, so a 30-day window at production cadence can return tens of thousands
of rows. The tab therefore selects a SIGNAL (enumerated via STORY-044's topology endpoint —
dependency) and defaults to a modest window (24h), with larger windows a deliberate choice.
Depends on STORY-015a (shell) and STORY-044 (signal enumeration).

## Acceptance Criteria (field-level detail re-verified against the real endpoints at planning)
- [ ] AC1: The tab picks a signal from the STORY-044 enumeration and fetches
      `GET /api/v1/history?signal_key=…` with tz-aware window params, rendering observations
      newest-first: timestamp (mono), status badge, latency (mono), location.
- [ ] AC2: A signal selector and a window selector (default 24h) drive refetches; MSW tests assert
      the exact query params sent (signal_key + tz-aware since/until).
- [ ] AC3: Machine values (timestamps, latency) render in the mono token; status follows the
      non-text-only color rule (badge = dot + label).
- [ ] AC4: Loading/empty ("no observations in this window")/error+retry states tested. Large-window
      volume is acknowledged in the story plan (render strategy or a follow-up pagination story —
      not silently ignored).

## Open Questions
None.

## History
- 2026-06-29: first version refined; reverted with `521764c`.
- 2026-07-02: re-refined for the Linear-guided direction. Status: ready. Estimate 3.
- 2026-07-02 (audit): AC reconciled to the real `/history` contract — dropped the nonexistent
  component filter; single required `signal_key` (via STORY-044 enumeration — now a dependency);
  noted the unbounded-window volume risk. Status: ready, blocked-by STORY-044.
