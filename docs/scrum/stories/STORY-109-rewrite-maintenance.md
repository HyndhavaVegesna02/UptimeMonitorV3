---
id: STORY-109
title: Rewrite maintenance — schedule form + windows list on new skin
type: story
---

## Context
UI-rewrite initiative (PO 2026-07-18). Binding brief: docs/scrum/ui-rewrite/design-brief.md.
Depends on STORY-103 foundation + STORY-104 shell.

## Description
Maintenance on new tokens: form with inline validation (noValidate, required Title/
Component/Start/End, end-after-start, aria-describedby errors, focus-first-invalid),
success/delete polite toasts, windows list with WYSIWYG local time + tz label (raw UTC
tooltip), Upcoming/Active chips, delete confirm, designed empty state.

## Acceptance Criteria
- [ ] AC1: validation contract (Vitest + live empty-submit); no native bubbles.
- [ ] AC2: create/delete round-trip with toasts (live probe, cleaned up); WYSIWYG local display + UTC tooltip.
- [ ] AC3: gates green; live pass both themes.

## History
- 2026-07-18: filed at ui-rewrite refinement (PO-delegated); estimate 2.
