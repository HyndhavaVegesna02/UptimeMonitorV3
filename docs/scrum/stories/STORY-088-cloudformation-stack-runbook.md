---
id: STORY-088
title: CloudFormation single-stack template + console deployment runbook
type: chore
---

## Context
AWS migration epic (see STORY-082 Context). PO decisions 2026-07-14: minimal topology
(no NAT, no autoscaling, no alarms, no PITR, HTTP-only ALB behind CloudFront's default
cert), **console-first deployment** — the PO drives the AWS Console against an exact
step-by-step runbook the team prepares (same modality as superseded STORY-017's
decision 1); CI/CD is deferred to STORY-090.

Approved resource set (one `infra/stack.yaml`): VPC with 2 public subnets (2 AZs — the
ALB's hard minimum) + IGW; SGs (ALB ← CloudFront origin-facing managed prefix list;
API 8000 ← ALB SG only; loop no ingress); the two DynamoDB tables
(`DeletionPolicy: Retain`); one ECR repo (the existing Dockerfile serves both processes
via CMD override); ECS cluster + execution role + one shared task role scoped to the
two table ARNs/GSI; two task definitions (0.25 vCPU / 0.5 GB — api: uvicorn :8000
with `/api/v1/health` healthcheck; loop: `python -m src.composition.run` with the two
Secrets Manager secrets injected); two services desiredCount=1 — the loop service
pinned to `minimumHealthyPercent=0 / maximumPercent=100` so deploys never run two
loops concurrently (double Statuspage publish guard); ALB HTTP:80 → api target group;
private S3 bucket + OAC; CloudFront — default behavior → S3, ordered behavior
`/api/*` → ALB origin (all methods, caching disabled; keeps `client.ts::API_BASE_URL
= '/api'` unchanged and CORS deferred), plus a CloudFront Function rewriting
extensionless paths to `/index.html` on the default behavior only (never touching
`/api/*` error bodies); two log groups (14-day retention); two Secrets Manager secrets
(names only — values entered by the PO in-console, never in the repo).

## Description
Author `infra/stack.yaml` and `docs/deploy-runbook.md` (exact console steps + the full
env-var/secret NAME table per service). `cfn-lint` joins the DoD gate set from this
story onward (second half of the 2026-07-14 DoD amendment).

## Acceptance Criteria
- [ ] AC1 (template): `infra/stack.yaml` declares the approved resource set above;
      parameters for image tag and desired counts; outputs for the CloudFront domain,
      ALB DNS, ECR URI, and table names.
- [ ] AC2 (lint gate): `cfn-lint infra/` exits 0 and is added to
      `.scrum/definition-of-done.md` (+ CLAUDE.md commands table) in this story.
- [ ] AC3 (loop singleton): the loop service's deployment configuration is
      `minimumHealthyPercent: 0, maximumPercent: 100` with desiredCount 1 — asserted in
      the template and called out in the runbook.
- [ ] AC4 (secrets hygiene): no secret VALUE at any commit; the template references
      Secrets Manager ARNs; the runbook lists every env var and secret NAME per
      service and where the PO enters each value.
- [ ] AC5 (runbook): `docs/deploy-runbook.md` walks the PO end-to-end through the
      console — stack upload/create, secret value entry, ECR login + image
      build/push (the one CLI-only step, commands given verbatim), frontend
      `npm run build` + S3 upload + CloudFront invalidation, and the verification
      checklist (six tabs render, `/api/*` round-trips, watermark advances) — with no
      step assuming prior AWS knowledge.
- [ ] AC6 (gates): full amended gate set green (pytest incl. DynamoDB-Local suite,
      import-linter, ruff check, ruff format, cfn-lint).

## Open Questions
None.

## History
- 2026-07-14: drafted at AWS-migration refinement. Status: draft, 5 points proposed.
- 2026-07-14: PO approved AC + estimate ("approve all") → ready.
