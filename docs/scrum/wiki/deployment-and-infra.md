---
title: Deployment â€” CloudFormation single-stack + container image
code_refs: [infra/stack.yaml, Dockerfile, .dockerignore, scripts/create_tables.py]
verified_sha: 7c53685
verified_sprint: sprint-50
status: verified
---

## Facts (verified against code)

- **One CloudFormation stack** (`infra/stack.yaml`) declares the whole dev-sized AWS topology,
  linted by `cfn-lint infra/stack.yaml` (a DoD gate since STORY-088). Minimal by design: no NAT,
  no autoscaling, no alarms, no PITR, HTTP-only ALB behind CloudFront's default cert.
- **Network:** a VPC with 2 public subnets across 2 AZs + an Internet Gateway (the ALB's hard
  2-AZ minimum). Three security groups: the ALB SG ingress 80 only from the CloudFront
  origin-facing managed prefix list (a `CloudFrontPrefixListId` **parameter** â€”
  `infra/stack.yaml` `SourcePrefixListId` â€” because no CFN intrinsic resolves it); the api SG
  ingress 8000 only from the ALB SG; the loop SG has no ingress.
- **DynamoDB:** the two tables (`infra/stack.yaml:137-156`) both carry `DeletionPolicy: Retain`
  + `UpdateReplacePolicy: Retain`; their key schema (observations pk/sk; control pk/sk + a
  `gsi1` GSI on `gsi1pk`/`gsi1sk`) matches `scripts/create_tables.py:40-88` byte-for-byte.
- **Compute:** one ECR repo; an ECS cluster + execution role (Secrets Manager `GetSecretValue`
  scoped to the two secret ARNs) + one task role scoped to the two table ARNs **and** the GSI
  index ARN (`${ControlTable.Arn}/index/gsi1`, `infra/stack.yaml:253-256`); two 0.25 vCPU /
  0.5 GB task definitions â€” api runs the image's default CMD with a `/api/v1/health` ALB
  health check; loop overrides the CMD to `python -m src.composition.run` and receives the
  four Dynatrace/Statuspage secrets. Two services, desiredCount 1.
- **API health grace (STORY-093 AC2):** `APIService` sets `HealthCheckGracePeriodSeconds: 120`
  (`infra/stack.yaml:390`) so the ALB target-group health check (30s interval, unhealthy after
  3 fails â‰ˆ 90s budget, `infra/stack.yaml:365-368`) does not churn the task while the first-boot
  lifespan seed (config read + DynamoDB writes) is still running on a cold task.
- **Loop singleton (double-publish guard):** the loop service sets
  `DeploymentConfiguration MinimumHealthyPercent: 0 / MaximumPercent: 100`
  (`infra/stack.yaml:420-422`) so a deploy never runs two loops concurrently. The api service
  keeps the rolling default (no `HealthCheckGracePeriodSeconds` on `LoopService` â€” it has no
  load balancer, so the property is not legal there).
- **Edge:** ALB HTTP:80 â†’ api target group; a private S3 bucket (`DeletionPolicy: Retain`,
  `infra/stack.yaml:427-428`) + Origin Access Control; CloudFront with the default behavior â†’
  S3 and an ordered `/api/*` behavior â†’ the ALB origin (all methods, caching disabled). A
  CloudFront Function (`RewriteFunction`, `infra/stack.yaml:462-478`) rewrites extensionless
  paths to `/index.html` on the **default behavior only**, never touching `/api/*` responses.
  Two 14-day log groups; two Secrets Manager secrets (names only â€” values entered in-console).
- **Live-deploy fixes (STORY-089, found only by deploying):** the CloudFront function carries
  `AutoPublish: true` (`infra/stack.yaml:466`) â€” distribution `FunctionAssociations` require
  the LIVE stage, and without it stack create fails with "not found or is not published";
  the distribution sets `DefaultRootObject: index.html` (`infra/stack.yaml:485`) â€” the rewrite
  function deliberately skips `/`, so the bare root otherwise 403s at the S3 origin; both
  managed policy IDs are live-verified (`Managed-CachingOptimized`
  `658327ea-f89d-4fab-a63d-7e88639e58f6`, `Managed-AllViewerExceptHostHeader`
  `b689b0a8-53d0-40ab-baf2-68738e2966ac`) â€” the originals were one fabricated ID (404 at
  create) and one ID/comment mismatch (`Managed-AllViewer`).
- **Container image** (`Dockerfile`): a single `python:3.13-slim` image serves **both**
  processes. Default `CMD` runs the API (`uvicorn src.composition.asgi:app`); the loop runs by
  command override (`python -m src.composition.run`) â€” the same override the ECS loop task def
  uses. `.dockerignore` keeps the build context lean (excludes `.venv/`, `frontend/`,
  `backend/tests/`, `.claude/`, `docs/`, `.scrum/`, caches).
- **Cached dependency layer + non-root (STORY-093 AC1):** `Dockerfile` copies only the
  build-config file first, derives the project's `[project] dependencies` list via a stdlib
  `tomllib` one-liner into `requirements.txt`, and installs those + `uvicorn[standard]` â€” all
  BEFORE `COPY backend /app/backend` â€” so a source-only change never invalidates the dependency
  install layer; the final `pip install --no-cache-dir .` (installing the package itself) runs
  after the source copy, riding on the already-installed deps. The dead `ENV PORT=8000` (never
  read â€” `CMD` hard-codes `--port 8000`) is removed. Both processes run as a non-root `app`
  user (`RUN useradd --create-home app` + `USER app`) â€” safe because neither process writes to
  disk (network-only DynamoDB persistence, `.env` load is a container no-op, logs to stderr).

## Inference (synthesis, not verified)
- Deployment is **console-first**: the PO drives the AWS Console against the step-by-step guide
  in `docs/deploy-runbook.md` (stack create â†’ secret entry â†’ the one CLI step: ECR build/push â†’
  frontend build + S3 upload + CloudFront invalidation â†’ verify). CI/CD (GitHub Actions + OIDC)
  is deferred to STORY-090. The live deployment itself is STORY-089.

## History
- sprint-49 (STORY-088 + STORY-092): created. The single-stack template + Dockerfile + console
  runbook landed the AWS deployment surface; `cfn-lint` joined the DoD.
- sprint-50 (STORY-093, review minors): `APIService` gained
  `HealthCheckGracePeriodSeconds: 120`; `Dockerfile` reordered to cache the dependency-install
  layer across source-only changes, dropped the dead `ENV PORT=8000`, and now runs as a
  non-root `app` user. Re-verified against `infra/stack.yaml` line-number drift from the
  1-line insertion.
- sprint-50 (STORY-089, live deployment): three template defects surfaced only by the real
  deploy â€” missing `AutoPublish` on the CloudFront function, a fabricated
  `Managed-CachingOptimized` ID, and no `DefaultRootObject` â€” all fixed and live-verified
  against the deployed stack (`ec09e8a`, `d119cc3`, `c05fc57`). See
  [[deployment-topology]] for the deployed instance itself.
