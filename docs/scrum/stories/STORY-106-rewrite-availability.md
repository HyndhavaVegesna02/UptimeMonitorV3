---
id: STORY-106
title: Rewrite availability — windowed uptime vs completeness, new skin
type: story
---

## Context
UI-rewrite initiative (PO 2026-07-18). Binding brief: docs/scrum/ui-rewrite/design-brief.md.
Depends on STORY-103 foundation + STORY-104 shell.

## Description
Availability page on new tokens: PageHeader-equivalent (one h1), 24h/7d/30d switcher,
per-component rows (or tiles) with availability % + bar and data-completeness ('N% of
expected checks received' — unambiguous label carried from redesign), signal drill-down.

## Acceptance Criteria
- [ ] AC1: window switcher works (live); one h1; new skin only.
- [ ] AC2: completeness label unambiguous (received-share phrasing); legend explains down vs missing.
- [ ] AC3: drill-down to signal rows preserved; gates green; live pass both themes.

## History
- 2026-07-18: filed at ui-rewrite refinement (PO-delegated); estimate 2.
