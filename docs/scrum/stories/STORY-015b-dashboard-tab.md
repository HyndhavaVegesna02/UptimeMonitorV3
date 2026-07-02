---
id: STORY-015b
title: Dashboard tab — live component health at a glance
type: feature
---

## Context
Spec: dossier §17. Zone 7. Split-child of STORY-015; depends on STORY-015a (shell). The first
real tab — it consumes `GET /api/v1/components` (STORY-014b) and establishes the per-tab
pattern (page component in `tabs/`, data hook in `hooks/`, shell primitives for badges/panels)
that 015c–015g copy.

## Description
The operator's landing view: every monitored component with its current health, at a glance.
Each component row/card shows name, health StatusBadge (dot/icon + label — never color alone),
and last-observed timestamp (mono). Health tokens from the shell drive the badge; an unknown
status value renders a neutral "unknown" badge rather than crashing.

## Acceptance Criteria
- [ ] AC1: The Dashboard tab fetches `GET /api/v1/components` via the shell's `apiClient` and
      renders one entry per component: name, status badge (icon/dot + label), last-observed
      timestamp. A semantic table (or list with proper roles) — keyboard/reader accessible.
- [ ] AC2: Loading, empty ("no components configured"), and error+retry states render using the
      shell's state components; MSW-backed tests drive all three plus the success path.
- [ ] AC3: Status→badge mapping is tested via accessible text (UP/DOWN/DEGRADED/MAINTENANCE),
      including the unknown-status guard.
- [ ] AC4: The per-tab pattern is established and documented (page in `tabs/`, hook in
      `hooks/`, e.g. `useComponents`) for the remaining tabs to copy; no `eslint-disable` to
      paper over effect misuse.

## Open Questions
None.

## History
- 2026-06-29: first version accepted (sprint 24), then reverted with `521764c`.
- 2026-07-02: re-refined for the Linear-guided direction. Status: ready. Estimate 3.
