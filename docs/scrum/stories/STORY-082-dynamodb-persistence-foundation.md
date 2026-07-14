---
id: STORY-082
title: DynamoDB persistence foundation — table bootstrap, DynamoDB Local test fixture, settings/composition seam
type: chore
---

## Context
First story of the AWS migration epic (PO decisions 2026-07-14, superseding STORY-017's
Railway/Vercel/Neon topology): the backend migrates entirely from Postgres to DynamoDB;
deployment target is S3+CloudFront / ECS Fargate+ALB / DynamoDB via one CloudFormation
template, deployed console-first (CI/CD is a later stage, STORY-090).

**Approved design (2026-07-14 plan):** two on-demand tables —
- `uptime-observations`: `pk=SIG#<signal_key>` / `sk=<observed_at ISO-UTC>#<source_event_id>`
  data items plus `pk=EVT#<source_event_id>` / `sk=DEDUPE` idempotency markers. No GSI.
- `uptime-control`: generic `pk`/`sk` single-table (TOPOLOGY partition, WATERMARK#,
  PROPOSAL# + COMPONENT#<id>/OPEN_PROPOSAL slot, PUBLICATION partition, MAINTWIN#,
  REJECTED#, CONFIG/SAMPLE_MODE, COUNTER items) with one sparse GSI (`gsi1pk`/`gsi1sk`).

**Approved decisions binding on the epic:** counter-based int IDs (core domain types
unchanged); maintenance-check eventual-consistency delta accepted; fresh-start cutover
(no Neon history migration); DoD amendment (retire `alembic upgrade head` +
`check_fk_direction.py`; adopt DynamoDB-Local-backed pytest + `cfn-lint infra/`) is
PO-approved but takes effect only at the cutover story (STORY-087) — the Postgres gates
keep holding until then.

This story builds the seam only: no port adapter yet. Postgres stays fully wired.
Honors the 2026-06-23 "pure core, mockable edges" agreement: adapter-zone tests use a
throwaway local DB (amazon/dynamodb-local), never live AWS.

## Description
Add `scripts/create_tables.py` (idempotent bootstrap of both tables + GSI1), a
session-scoped `dynamo_local` pytest fixture mirroring the `migrated_db` ladder, the
settings fields for region/table names/endpoint override, and a composition-level
boto3 resource factory for adapters to consume. Adds `boto3` as a runtime dependency
(an uncommitted STORY-017 Phase-0 spike had added it; that spike was stashed at the
2026-07-14 clean-up, so this story adds it on clean history).

## Acceptance Criteria
- [ ] AC1 (bootstrap script): `python scripts/create_tables.py` creates
      `uptime-observations` and `uptime-control` with the approved key schemas + GSI1,
      honoring `DYNAMO_ENDPOINT_URL` (local) or real AWS otherwise; a second run against
      existing tables exits 0 without error or modification (idempotent).
- [ ] AC2 (test fixture): a session-scoped `dynamo_local` fixture in
      `backend/tests/conftest.py` follows the `migrated_db` ladder — reuse an
      env-supplied `DYNAMO_ENDPOINT_URL` if set (bootstrapping tables to current), else
      spawn a throwaway `amazon/dynamodb-local` Docker container on a free port (torn
      down in a finalizer even on test failure), else skip DynamoDB-gated tests cleanly.
- [ ] AC3 (settings): `composition/settings.py` gains `aws_region`, the two table names,
      and an optional endpoint override, read from env with sane defaults; existing
      `DATABASE_URL` loading is untouched (parallel seam, not a replacement yet).
- [ ] AC4 (resource factory): a composition-layer factory yields a configured boto3
      DynamoDB resource; nothing outside `adapters/persistence/` + `composition/`
      imports boto3.
- [ ] AC5 (boundaries): all 8 import-linter contracts still pass; the six backend DoD
      gates (Postgres-era) stay green.

## Open Questions
None — design fixed by the PO-accepted 2026-07-14 plan.

## History
- 2026-07-14: drafted at AWS-migration refinement (PO accepted plan + decisions in
  session cc-refine-aws-migration-20260714-0300). Status: draft, 5 points proposed.
- 2026-07-14: PO approved AC + estimate ("approve all") → ready.
