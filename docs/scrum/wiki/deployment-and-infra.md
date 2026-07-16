---
title: Deployment — CloudFormation single-stack + container image
code_refs: [infra/stack.yaml, Dockerfile, .dockerignore, scripts/create_tables.py]
verified_sha: 96f456f
verified_sprint: sprint-49
status: verified
---

## Facts (verified against code)

- **One CloudFormation stack** (`infra/stack.yaml`) declares the whole dev-sized AWS topology,
  linted by `cfn-lint infra/stack.yaml` (a DoD gate since STORY-088). Minimal by design: no NAT,
  no autoscaling, no alarms, no PITR, HTTP-only ALB behind CloudFront's default cert.
- **Network:** a VPC with 2 public subnets across 2 AZs + an Internet Gateway (the ALB's hard
  2-AZ minimum). Three security groups: the ALB SG ingress 80 only from the CloudFront
  origin-facing managed prefix list (a `CloudFrontPrefixListId` **parameter** —
  `infra/stack.yaml` `SourcePrefixListId` — because no CFN intrinsic resolves it); the api SG
  ingress 8000 only from the ALB SG; the loop SG has no ingress.
- **DynamoDB:** the two tables (`infra/stack.yaml:137-156`) both carry `DeletionPolicy: Retain`
  + `UpdateReplacePolicy: Retain`; their key schema (observations pk/sk; control pk/sk + a
  `gsi1` GSI on `gsi1pk`/`gsi1sk`) matches `scripts/create_tables.py:40-88` byte-for-byte.
- **Compute:** one ECR repo; an ECS cluster + execution role (Secrets Manager `GetSecretValue`
  scoped to the two secret ARNs) + one task role scoped to the two table ARNs **and** the GSI
  index ARN (`${ControlTable.Arn}/index/gsi1`, `infra/stack.yaml:253-256`); two 0.25 vCPU /
  0.5 GB task definitions — api runs the image's default CMD with a `/api/v1/health` ALB
  health check; loop overrides the CMD to `python -m src.composition.run` and receives the
  four Dynatrace/Statuspage secrets. Two services, desiredCount 1.
- **Loop singleton (double-publish guard):** the loop service sets
  `DeploymentConfiguration MinimumHealthyPercent: 0 / MaximumPercent: 100`
  (`infra/stack.yaml:419-421`) so a deploy never runs two loops concurrently. The api service
  keeps the rolling default.
- **Edge:** ALB HTTP:80 → api target group; a private S3 bucket (`DeletionPolicy: Retain`,
  `infra/stack.yaml:426-427`) + Origin Access Control; CloudFront with the default behavior →
  S3 and an ordered `/api/*` behavior → the ALB origin (all methods, caching disabled). A
  CloudFront Function rewrites extensionless paths to `/index.html` on the **default behavior
  only** (`infra/stack.yaml:498-500`), never touching `/api/*` responses. Two 14-day log
  groups; two Secrets Manager secrets (names only — values entered in-console).
- **Container image** (`Dockerfile`): a single `python:3.13-slim` image serves **both**
  processes. Default `CMD` runs the API (`uvicorn src.composition.asgi:app`); the loop runs by
  command override (`python -m src.composition.run`) — the same override the ECS loop task def
  uses. `.dockerignore` keeps the build context lean (excludes `.venv/`, `frontend/`,
  `backend/tests/`, `.claude/`, `docs/`, `.scrum/`, caches).

## Inference (synthesis, not verified)
- Deployment is **console-first**: the PO drives the AWS Console against the step-by-step guide
  in `docs/deploy-runbook.md` (stack create → secret entry → the one CLI step: ECR build/push →
  frontend build + S3 upload + CloudFront invalidation → verify). CI/CD (GitHub Actions + OIDC)
  is deferred to STORY-090. The live deployment itself is STORY-089.

## History
- sprint-49 (STORY-088 + STORY-092): created. The single-stack template + Dockerfile + console
  runbook landed the AWS deployment surface; `cfn-lint` joined the DoD.
