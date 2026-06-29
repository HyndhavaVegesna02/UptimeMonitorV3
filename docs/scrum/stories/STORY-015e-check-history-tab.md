---
id: STORY-015e
title: Check History tab — per-signal observation history
type: feature
---

## Context
Spec: dossier §17. Zone 7. Depends on STORY-015a (shell). Shows the recent observation history for a
selected signal (location, health, latency, timestamp) — the raw checks behind the status.

## Acceptance Criteria
- [ ] AC1: A signal selector + a history table/list from `GET /api/v1/history?signal_key=…` (most-recent
      first): location, health, latency (ms), observed_at (locale-aware time).
- [ ] AC2: Loading/empty/error states; large lists virtualized or paged if needed (`virtualize-lists`);
      MSW-backed Vitest tests cover success/empty/error.
- [ ] AC3: Table is sortable with `aria-sort` where applicable (`sortable-table`); a11y + responsive floor met.

## Skills to use
`ui-ux-pro-max` (data tables, virtualization), `vercel-react-best-practices`, `design-taste-frontend`.

## History
- 2026-06-29: created as a per-tab split-child of STORY-015. 3 pts. Status: ready.
