---
id: STORY-015c
title: Approvals tab — pending proposals list + approve/reject
type: feature
---

## Context
Spec: dossier §17 (the approval gate is the product's reason to exist — a degradation reaches
the public Statuspage only after a human approves it here). Zone 7. Split-child of STORY-015;
depends on STORY-015a. API: `GET /api/v1/approvals` (STORY-014b) +
`POST /api/v1/decisions/{proposal_id}` (STORY-014). The only mutating tab besides Maintenance.

## Description
Lists open status proposals (component, proposed status, evidence/reason, opened-at) and lets
the operator approve or reject each. A decision is deliberate: the action asks for confirmation
before POSTing. After a decision the list refreshes. A lost race (proposal already resolved by
a concurrent decision — the API's 409) is surfaced as an inline explanation and the row
refreshes, never a crash or a silent no-op.

## Acceptance Criteria
- [ ] AC1: Open proposals render from `GET /api/v1/approvals`: component, proposed status
      (StatusBadge), reason/evidence, opened-at (mono). Empty state: "nothing pending approval".
- [ ] AC2: Approve and Reject actions POST `/api/v1/decisions/{proposal_id}` with the decision;
      a confirmation step precedes the POST; success removes/refreshes the entry. MSW tests
      drive both decisions end to end.
- [ ] AC3: A 409 (proposal no longer open — lost race) shows an inline "already resolved"
      message and refreshes the list; an unexpected error shows the shell error state with
      retry. Both tested.
- [ ] AC4: Loading/empty/error states + keyboard operability of the action buttons (≥40px
      targets, visible focus) — tested.

## Open Questions
None.

## History
- 2026-06-29: first version refined (never implemented — revert `521764c` hit first).
- 2026-07-02: re-refined for the Linear-guided direction. Status: ready. Estimate 5 (mutating
  tab, confirmation flow, race handling).
