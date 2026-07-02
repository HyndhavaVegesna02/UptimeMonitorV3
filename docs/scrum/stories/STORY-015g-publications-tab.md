---
id: STORY-015g
title: Publications tab — Statuspage publish history
type: feature
---

## Context
Spec: dossier §17. Zone 7. Split-child of STORY-015; depends on STORY-015a. API:
`GET /api/v1/publications` (STORY-037) — the record of what was actually pushed to the public
Statuspage and when.

## Description
A read-only audit trail in the `changelog-row` pattern: when each status change was published,
for which component, old→new status, and outcome. This is the "what did customers see, and
when" view.

## Acceptance Criteria
- [ ] AC1: Publications render newest-first from `GET /api/v1/publications`: published-at
      (mono), component, old→new status (two badges or a labeled transition), outcome.
- [ ] AC2: Loading/empty ("nothing published yet")/error+retry states tested via MSW.
- [ ] AC3: Follows the established per-tab pattern (page in `tabs/`, hook in `hooks/`); status
      badges follow the non-text-only color rule.

## Open Questions
None.

## History
- 2026-06-29: first version refined; reverted with `521764c`.
- 2026-07-02: re-refined for the Linear-guided direction. Status: ready. Estimate 2.
