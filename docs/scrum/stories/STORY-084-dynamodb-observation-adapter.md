---
id: STORY-084
title: DynamoDB observation adapter — idempotent ingest transaction + half-open window query
type: chore
---

## Context
AWS migration epic (see STORY-082 Context). The highest-stakes adapter: it carries the
ingest idempotency the whole pipeline relies on and the single read
(`in_window`) that feeds `core/queries/availability.py` — the availability math itself
is pure Python and does not change.

Postgres semantics being ported (from `observation_repository.py`):
- `save_new`: `ON CONFLICT (source_event_id) DO NOTHING ... RETURNING` — uniqueness on
  `source_event_id` ALONE; return value is the true count of newly inserted rows.
- `in_window`: half-open `[since, until)` on `(signal_key, observed_at)`.

Approved DynamoDB port: per observation, one `TransactWriteItems` writing the data item
(`SIG#<key>` / `<observed_at>#<event_id>`) and a dedupe marker (`EVT#<event_id>` /
`DEDUPE`) with `attribute_not_exists`; a cancelled transaction = duplicate = not
counted. `in_window` = Query `pk = SIG#<key> AND sk BETWEEN :since AND :until` with
bare-ISO bounds (yields exactly the half-open interval: `since` sorts before
`since#<id>`, and `until#<id>` sorts after bare `until`), looping on
`LastEvaluatedKey`.

## Description
Implement `DynamoObservationRepository` satisfying `ObservationRepository` with exact
behavioral parity, proven against `dynamo_local`.

## Acceptance Criteria
- [ ] AC1 (idempotency): re-ingesting a batch containing an already-stored
      `source_event_id` inserts nothing for it and the returned count excludes it —
      including the cross-attribute case (same `source_event_id`, different
      `observed_at`) that a same-partition key collision would NOT catch.
- [ ] AC2 (count semantics): `save_new` returns the number of observations actually
      newly persisted; empty batch short-circuits to 0 without any DynamoDB call.
- [ ] AC3 (half-open window): boundary tests prove an observation at exactly `since` is
      included and one at exactly `until` is excluded.
- [ ] AC4 (pagination): `in_window` returns the complete result set across multiple
      Query pages (exercised by forcing paged responses, e.g. Query `Limit`), never
      just the first page.
- [ ] AC5 (round-trip fidelity): all `SignalObservation` fields survive a
      save→read round-trip — `observed_at` tz-aware UTC, `source` Provenance map,
      nullable `latency_ms`/`response_status_code`/`raw_ref` absent-vs-set handled.
- [ ] AC6 (availability parity): `AvailabilityCalculator.compute` over a canonical
      multi-location fixture set produces an identical `AvailabilityResult`
      (availability%, completeness%, all five counts) whether the observations were
      served by the Postgres adapter or the DynamoDB adapter.
- [ ] AC7 (boundaries + gates): import-linter contracts pass; six backend gates green;
      not yet wired into composition.

## Open Questions
None.

## History
- 2026-07-14: drafted at AWS-migration refinement. Status: draft, 5 points proposed.
- 2026-07-14: PO approved AC + estimate ("approve all") → ready.
