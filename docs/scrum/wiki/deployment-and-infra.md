---
title: Deployment — CloudFormation single-stack + container image (decommissioned 2026-08-13)
tier: reference
verified_sprint: sprint-50
archived_reason: >-
  AWS stack decommissioned by PO decision on 2026-08-13 (STORY-222). This article is now a
  tombstone: it records what was built and why, not a live claim about `infra/stack.yaml` or
  the `Dockerfile` as they stand today. See [[deployment-topology]] for the deployed instance
  and CLAUDE.md's "Deployed topology" section for current status.
# tier: reference (2026-08-13, STORY-222). Converted from tier: map / status: stale after the
# AWS stack was decommissioned. `code_refs` and the `## Facts` header are removed per the
# reference tier's integrity rule (yt_wiki.py check_integrity) -- a tombstone asserts nothing
# about live code, so it carries no code_refs and is never swept. The template's shape below
# is preserved as HISTORY (last read against code at sprint-50, nineteen sprints before this
# conversion) -- not a current claim about `infra/stack.yaml`, which may have drifted since
# and is no longer anchored to this article.
---

## What was built (historical — as of sprint-50, before decommission)

The bullets below describe the CloudFormation template and container image **as they were
last read against code, at sprint-50** — not a current claim. This article is not swept, so
nothing here re-verifies against today's `infra/stack.yaml` or `Dockerfile`.

- **One CloudFormation stack** (`infra/stack.yaml`) declared the whole dev-sized AWS topology,
  linted by `cfn-lint infra/stack.yaml` (a DoD gate since STORY-088). Minimal by design: no NAT,
  no autoscaling, no alarms, no PITR, HTTP-only ALB behind CloudFront's default cert.
- **Network:** a VPC with 2 public subnets across 2 AZs + an Internet Gateway (the ALB's hard
  2-AZ minimum). Three security groups: the ALB SG ingress 80 only from the CloudFront
  origin-facing managed prefix list (a `CloudFrontPrefixListId` **parameter** —
  `infra/stack.yaml` `SourcePrefixListId` — because no CFN intrinsic resolves it); the api SG
  ingress 8000 only from the ALB SG; the loop SG had no ingress.
- **DynamoDB:** the two tables (`infra/stack.yaml:137-156`) both carried `DeletionPolicy: Retain`
  + `UpdateReplacePolicy: Retain`; their key schema (observations pk/sk; control pk/sk + a
  `gsi1` GSI on `gsi1pk`/`gsi1sk`) matched `scripts/create_tables.py:40-88` byte-for-byte.
- **Compute:** one ECR repo; an ECS cluster + execution role (Secrets Manager `GetSecretValue`
  scoped to the two secret ARNs) + one task role scoped to the two table ARNs **and** the GSI
  index ARN (`${ControlTable.Arn}/index/gsi1`, `infra/stack.yaml:253-256`); two 0.25 vCPU /
  0.5 GB task definitions — api ran the image's default CMD with a `/api/v1/health` ALB
  health check; loop overrode the CMD to `python -m src.composition.run` and received the
  four Dynatrace/Statuspage secrets. Two services, desiredCount 1.
- **API health grace (STORY-093 AC2):** `APIService` set `HealthCheckGracePeriodSeconds: 120`
  (`infra/stack.yaml:390`) so the ALB target-group health check (30s interval, unhealthy after
  3 fails ≈ 90s budget, `infra/stack.yaml:365-368`) did not churn the task while the first-boot
  lifespan seed (config read + DynamoDB writes) was still running on a cold task.
- **Loop singleton (double-publish guard):** the loop service set
  `DeploymentConfiguration MinimumHealthyPercent: 0 / MaximumPercent: 100`
  (`infra/stack.yaml:420-422`) so a deploy never ran two loops concurrently. The api service
  kept the rolling default (no `HealthCheckGracePeriodSeconds` on `LoopService` — it had no
  load balancer, so the property was not legal there).
- **Edge:** ALB HTTP:80 → api target group; a private S3 bucket (`DeletionPolicy: Retain`,
  `infra/stack.yaml:427-428`) + Origin Access Control; CloudFront with the default behavior →
  S3 and an ordered `/api/*` behavior → the ALB origin (all methods, caching disabled). A
  CloudFront Function (`RewriteFunction`, `infra/stack.yaml:462-478`) rewrote extensionless
  paths to `/index.html` on the **default behavior only**, never touching `/api/*` responses.
  Two 14-day log groups; two Secrets Manager secrets (names only — values entered in-console).
- **Live-deploy fixes (STORY-089, found only by deploying):** the CloudFront function carried
  `AutoPublish: true` (`infra/stack.yaml:466`) — distribution `FunctionAssociations` require
  the LIVE stage, and without it stack create failed with "not found or is not published";
  the distribution set `DefaultRootObject: index.html` (`infra/stack.yaml:485`) — the rewrite
  function deliberately skipped `/`, so the bare root otherwise 403s at the S3 origin; both
  managed policy IDs were live-verified (`Managed-CachingOptimized`
  `658327ea-f89d-4fab-a63d-7e88639e58f6`, `Managed-AllViewerExceptHostHeader`
  `b689b0a8-53d0-40ab-baf2-68738e2966ac`) — the originals were one fabricated ID (404 at
  create) and one ID/comment mismatch (`Managed-AllViewer`).
- **Container image** (`Dockerfile`): a single `python:3.13-slim` image served **both**
  processes. Default `CMD` ran the API (`uvicorn src.composition.asgi:app`); the loop ran by
  command override (`python -m src.composition.run`) — the same override the ECS loop task def
  used. `.dockerignore` kept the build context lean (excludes `.venv/`, `frontend/`,
  `backend/tests/`, `.claude/`, `docs/`, `.scrum/`, caches).
- **Cached dependency layer + non-root (STORY-093 AC1):** `Dockerfile` copied only the
  build-config file first, derived the project's `[project] dependencies` list via a stdlib
  `tomllib` one-liner into `requirements.txt`, and installed those + `uvicorn[standard]` — all
  BEFORE `COPY backend /app/backend` — so a source-only change never invalidated the dependency
  install layer; the final `pip install --no-cache-dir .` (installing the package itself) ran
  after the source copy, riding on the already-installed deps. The dead `ENV PORT=8000` (never
  read — `CMD` hard-codes `--port 8000`) was removed. Both processes ran as a non-root `app`
  user (`RUN useradd --create-home app` + `USER app`) — safe because neither process wrote to
  disk (network-only DynamoDB persistence, `.env` load is a container no-op, logs to stderr).

## Inference (synthesis, not verified)
- Deployment was **console-first**: the PO drove the AWS Console against the step-by-step guide
  in `docs/deploy-runbook.md` (stack create → secret entry → the one CLI step: ECR build/push →
  frontend build + S3 upload + CloudFront invalidation → verify). CI/CD (GitHub Actions + OIDC)
  was deferred to STORY-090, which stays archived on the "no live stack" fact (STORY-222). The
  live deployment itself was STORY-089.

## History
- sprint-49 (STORY-088 + STORY-092): created. The single-stack template + Dockerfile + console
  runbook landed the AWS deployment surface; `cfn-lint` joined the DoD.
- sprint-50 (STORY-093, review minors): `APIService` gained
  `HealthCheckGracePeriodSeconds: 120`; `Dockerfile` reordered to cache the dependency-install
  layer across source-only changes, dropped the dead `ENV PORT=8000`, and now runs as a
  non-root `app` user. Re-verified against `infra/stack.yaml` line-number drift from the
  1-line insertion.
- sprint-50 (STORY-089, live deployment): three template defects surfaced only by the real
  deploy — missing `AutoPublish` on the CloudFront function, a fabricated
  `Managed-CachingOptimized` ID, and no `DefaultRootObject` — all fixed and live-verified
  against the deployed stack (`ec09e8a`, `d119cc3`, `c05fc57`). See
  [[deployment-topology]] for the deployed instance itself.
- sprint-71 (STORY-222, 2026-08-13): the AWS stack was decommissioned by PO decision. Converted
  this article from `tier: map` / `status: stale` to `tier: reference` — a tombstone. `code_refs`
  and the `## Facts` heading are removed (renamed to "What was built"); the content is
  unchanged in substance, only reframed as history. `infra/stack.yaml` and the `Dockerfile`
  remain in the repo (cfn-lint still runs them in the DoD gate) as the redeploy procedure, not
  as evidence of anything currently running.
