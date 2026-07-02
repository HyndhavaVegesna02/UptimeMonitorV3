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
A read-only audit trail in the `changelog-row` pattern: when each status change was published and
for which component. This is the "what did customers see, and when" view.

**API contract (audit-verified 2026-07-02, per the tab-AC-vs-DTO agreement):**
`PublicationDTO` = `{id, component_id, status, published_at, proposal_id}` — a SINGLE published
status; there is NO from-status, so an "old→new" transition cannot be rendered from this endpoint
(the earlier draft promised one). `list_recent` returns at most the repository's most-recent 50
(no pagination) — the tab shows "the latest 50 publications", stated in the UI copy or header.
`proposal_id` links a publication to its originating proposal (render as mono id; no proposal
lookup endpoint by id exists — no drill-through yet).

## Acceptance Criteria
- [ ] AC1: Publications render newest-first from `GET /api/v1/publications`: published-at (mono),
      component_id, the published status (single StatusBadge), and proposal_id (mono).
- [ ] AC2: Loading/empty ("nothing published yet")/error+retry states tested via MSW.
- [ ] AC3: Follows the established per-tab pattern (page + feature hook via shared `useFetch` +
      per-feature MSW module); status badges follow the non-text-only color rule; the 50-item cap
      is visible to the operator, not silent.

## Open Questions
None.

## History
- 2026-06-29: first version refined; reverted with `521764c`.
- 2026-07-02: re-refined for the Linear-guided direction. Status: ready. Estimate 2.
- 2026-07-02 (audit): AC reconciled to the real `PublicationDTO` — dropped the impossible old→new
  transition (single status field only); surfaced the 50-item `list_recent` cap. Status: ready.
