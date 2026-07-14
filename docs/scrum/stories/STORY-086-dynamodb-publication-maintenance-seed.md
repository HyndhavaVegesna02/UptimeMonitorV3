---
id: STORY-086
title: DynamoDB adapters — publications, maintenance windows, rejected observations + seed rewrite
type: chore
---

## Context
AWS migration epic (see STORY-082 Context). Completes the adapter set and ports the
boot-time topology seed. Postgres semantics being ported:
- `publications.list_recent`: `ORDER BY published_at DESC LIMIT n` with a correlated
  subquery deriving `author` from the first approved `approval_events.actor`
  (STORY-066). DynamoDB port: single `PUBLICATION` time-ordered partition, Query
  descending; author read from the `approved_actor` denormalized by STORY-085,
  via BatchGetItem on the distinct proposal METAs (`proposal_id=None` → author=None).
- `maintenance_windows`: counter IDs; `MAINTWIN#<id>`/`META` + `gsi1pk=MAINT`,
  `gsi1sk=<starts_at>#<id>` for the ordered listing; `is_under_maintenance` = GSI query
  (`gsi1sk <= at`, filter `ends_at > :at AND component_id`). **PO-accepted delta
  (2026-07-14):** the GSI is eventually consistent — a window created seconds earlier
  may be missed for one pull cycle; windows are scheduled ahead of time, accepted.
- `rejected_observations`: append-only quarantine, no port reads it —
  `REJECTED#<signal_key|UNKNOWN>` / `<rejected_at>#<uuid>`.
- `composition/seed.py`: the only multi-statement transaction in the codebase becomes
  plain idempotent PutItems on the TOPOLOGY partition (atomicity dropped deliberately:
  the seed is idempotent and re-runs at every boot of both processes — double-seeding
  stays safe, per STORY-017's D3 finding).

## Description
Implement `DynamoPublicationRepository`, `DynamoMaintenanceRepository`,
`DynamoRejectedObservationRepository`; rewrite `seed_topology` for DynamoDB. Proven
against `dynamo_local`.

## Acceptance Criteria
- [ ] AC1 (publications): `record` assigns counter int ids and persists every attempt
      (succeeded AND failed outcomes); `list_recent(limit)` returns newest-first capped
      at limit; `author` equals the approving actor for publications with a
      proposal_id and None for proposal-less ones — parity with the Postgres correlated
      subquery proven on the same fixture script as STORY-066's reality gate.
- [ ] AC2 (maintenance): `create` assigns counter ids; `list_windows` returns all
      windows ordered by starts_at ascending; `is_under_maintenance` honors
      `starts_at <= at < ends_at` boundary semantics (inclusive start, exclusive end,
      tested at both instants); `delete` removes the window and raises
      `MaintenanceWindowNotFoundError` on a missing id.
- [ ] AC3 (rejected): `save` persists reason + full payload map; unknown/absent
      signal_key never fails the quarantine write.
- [ ] AC4 (seed): `seed_topology` upserts apps/components/signals from `config/apps`
      idempotently — running it twice yields identical state; a changed config value
      (e.g. a signal name) is reflected on re-seed; component `status` is NOT reset by
      re-seeding (parity with the Postgres upsert's column set).
- [ ] AC5 (consistency delta recorded): the maintenance eventual-consistency behavior
      is documented in the adapter docstring and the wiki article created/updated for
      the persistence zone.
- [ ] AC6 (boundaries + gates): import-linter contracts pass; six backend gates green;
      not yet wired into composition.

## Open Questions
None.

## History
- 2026-07-14: drafted at AWS-migration refinement. Status: draft, 5 points proposed.
- 2026-07-14: PO approved AC + estimate ("approve all") → ready.
