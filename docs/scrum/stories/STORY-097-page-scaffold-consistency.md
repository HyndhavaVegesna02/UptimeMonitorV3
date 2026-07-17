---
id: STORY-097
title: Consistent page scaffold — shared PageHeader, container widths, designed empty states
type: story
---

## Context
ui-redesign exploration 2026-07-17 (journal findings #10, #11): Dashboard/Approvals/
Maintenance render the h1 outside the content card while Check History/Publications put
the title inside it; container max-widths differ per tab; empty states range from designed
(Approvals: icon + title + body) to bare text (Maintenance, Publications); Publications
shows "Showing the latest 50 publications" above "Nothing published yet".

## Description
One scaffold for all six tabs: a shared `PageHeader` (h1 + subtitle, outside the card,
with a slot for page-level actions like the Availability range switcher) and one content
container width policy; adopt the existing `EmptyState` primitive everywhere with
per-page icon/title/body/action; Publications' count subtitle only renders when there
are publications.

## Acceptance Criteria
- [ ] AC1: all six tabs render h1 + subtitle via the shared PageHeader, outside the card;
      exactly one h1 per page; heading levels sequential.
- [ ] AC2: content container width is consistent across tabs (one token, one policy —
      wide data pages may opt into full width via an explicit prop, not divergence).
- [ ] AC3: Approvals, Maintenance list, Publications, and Check History (filtered-to-zero)
      all use the designed EmptyState with a helpful body line; Publications no longer
      claims "latest 50" when empty.
- [ ] AC4: Availability's legend + range switcher live in the PageHeader actions slot
      (visual position may shift only within the header row).
- [ ] AC5: Vitest: PageHeader renders title/subtitle/actions; per-page tests updated;
      suite green.

## History
- 2026-07-17: filed + refined during ui-redesign refinement (PO-delegated); estimate 2.
