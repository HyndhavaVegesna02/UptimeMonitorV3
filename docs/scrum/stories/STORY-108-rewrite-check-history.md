---
id: STORY-108
title: Rewrite check history — dense operator table
type: story
---

## Context
UI-rewrite initiative (PO 2026-07-18). Binding brief: docs/scrum/ui-rewrite/design-brief.md.
Depends on STORY-103 foundation + STORY-104 shell.

## Description
Check History on new tokens: filters (search/result/location/window) + URL-param seed
(?signal=), dense JetBrains-Mono table with RelativeTime + location labels, latency
threshold tint (named tokens), sticky header in table container, results summary line
('N checks · M down', aria-live polite), designed zero-result + unfiltered empty states.

## Acceptance Criteria
- [ ] AC1: filters + URL seed work (live); table dense skin, no raw ISO/IDs.
- [ ] AC2: latency tints via tokens (computed-style live check); sticky header; summary line accurate + aria-live.
- [ ] AC3: 390px: table scrolls only inside its container; gates green; live pass both themes.

## History
- 2026-07-18: filed at ui-rewrite refinement (PO-delegated); estimate 2.
