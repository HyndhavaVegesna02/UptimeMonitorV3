---
id: STORY-105
title: Rewrite dashboard — bento grid mission-control page
type: story
---

## Context
UI-rewrite initiative (PO 2026-07-18). Binding brief: docs/scrum/ui-rewrite/design-brief.md.
Depends on STORY-103 foundation + STORY-104 shell.

## Description
Bento dashboard per brief §IA: hero system-status tile (overall state, worst-of, big
type), per-component tiles (status + uptime bar + latency + last-observed RelativeTime,
click-through to drill-down/history), action tiles (pending approvals / maintenance:
neutral at 0, accented >0, whole-tile links), recent-checks feed tile (latest N, relative
times, location short labels). Empty/loading/error states per tile, not per page.

## Acceptance Criteria
- [ ] AC1: bento grid renders hero + component + action + feed tiles from live endpoints; asymmetric layout at ≥1024px, stacks cleanly at 390/768 (no page H-scroll).
- [ ] AC2: hero tile state matches worst-of component status (Vitest + live); action tiles neutral-at-zero/accent->0 with whole-tile link semantics.
- [ ] AC3: feed tile shows latest checks with RelativeTime + location labels, no raw ISO/vendor IDs anywhere on the page.
- [ ] AC4: per-tile loading skeletons (reduced-motion guarded) and error states; one failing fetch never blanks the page.
- [ ] AC5: gates green; live Playwright pass both themes at 390/768/1024/1440.

## History
- 2026-07-18: filed at ui-rewrite refinement (PO-delegated); estimate 3.
