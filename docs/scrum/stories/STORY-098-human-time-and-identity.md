---
id: STORY-098
title: Human time & identity — relative timestamps, local-time display, friendly location names
type: story
---

## Context
ui-redesign exploration 2026-07-17 (journal findings #5, #6): raw ISO-8601 UTC
timestamps with microseconds are shown verbatim on every surface (dashboard drill-down,
check history, approvals "Proposed …", publications); the maintenance form takes local
time input but displays the created window as raw UTC; raw vendor location IDs
(`SYNTHETIC_LOCATION-0000000000000047`) dominate two tables.

## Description
One shared time formatter module (journal D3): relative time ("4m ago" / "in 2h") for
recency-oriented surfaces, absolute local time for scheduling surfaces (maintenance
windows), and the full ISO-UTC string always available in the `title`/tooltip and in a
`<time dateTime=…>` attribute. Tabular figures for table alignment. One shared location
formatter: strip the vendor prefix to a short display form ("Location …0047" style),
full raw ID in the tooltip. Display-layer only — DTOs, API calls, and stored data unchanged.

## Acceptance Criteria
- [ ] AC1: no rendered surface shows microseconds or a bare ISO-8601 UTC string as its
      primary text (raw stays available via tooltip/`title` + `<time dateTime>`).
- [ ] AC2: check history, dashboard signals ("last observed"), approvals ("proposed"),
      and publications show relative time that updates at least once a minute.
- [ ] AC3: maintenance windows display start–end in the operator's local timezone with
      an explicit timezone label; the raw UTC range is in the tooltip.
- [ ] AC4: location cells show the short display form with the raw ID as tooltip; the
      Location filter dropdown remains keyed by raw ID (behavior unchanged).
- [ ] AC5: formatter unit tests (relative boundaries: <1m, minutes, hours, days; future
      times; invalid input) + updated page tests; suite green.

## History
- 2026-07-17: filed + refined during ui-redesign refinement (PO-delegated); estimate 2.
