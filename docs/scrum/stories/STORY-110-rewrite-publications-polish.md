---
id: STORY-110
title: Rewrite publications + initiative polish sweep
type: story
---

## Context
UI-rewrite initiative (PO 2026-07-18). Binding brief: docs/scrum/ui-rewrite/design-brief.md.
Depends on STORY-103 foundation + STORY-104 shell.

## Description
Publications on new tokens (timeline/list, outcome + author when present, RelativeTime,
count subtitle only when populated, designed empty state). THEN the initiative polish
sweep on ui-rewrite HEAD: full six-tab x {390,768,1024,1440} x {light,dark} Playwright
matrix, keyboard-only walkthrough, console/network zero-error audit, contrast spot checks,
journal wrap-up + PO presentation package (before/after screenshots).

## Acceptance Criteria
- [ ] AC1: publications page per description (MSW-populated Vitest + live empty state).
- [ ] AC2: polish matrix executed with evidence (screenshots + findings; blockers fixed in-story, nits filed).
- [ ] AC3: full 8-command gate green on final HEAD; presentation package ready for PO review.

## History
- 2026-07-18: filed at ui-rewrite refinement (PO-delegated); estimate 3.
