---
title: Deployment — CloudFormation single-stack + container image (decommissioned 2026-08-13)
tier: reference
verified_sprint: sprint-50
archived_reason: >-
  AWS stack decommissioned by PO decision on 2026-08-13 (STORY-222). This article is now a
  tombstone: it records what was built and why, not a live claim about infra/stack.yaml or
  the `Dockerfile` as they stand today. See [[deployment-topology]] for the deployed instance
  and CLAUDE.md's "Deployed topology" section for current status.
# tier: reference (2026-08-13, STORY-222). Converted from tier: map / status: stale after the
# AWS stack was decommissioned. `code_refs` and the `## Facts` header are removed per the
# reference tier's integrity rule (yt_wiki.py check_integrity) -- a tombstone asserts nothing
# about live code, so it carries no code_refs and is never swept. The template's shape below
# is preserved as HISTORY (last read against code at sprint-50, nineteen sprints before this
# conversion) -- not a current claim about infra/stack.yaml, which may have drifted since
# and is no longer anchored to this article.
#
# Fix round (2026-08-13, same story): the ten `file:line` citations below into
# infra/stack.yaml / scripts/create_tables.py were de-lined -- a reference article's
# citations were still checkable-against-HEAD, which is a live-code claim regardless of
# past-tense prose (wiki-protocol.md's tier rules: "the moment a reference article wants to
# cite code, it is a map article and must be one"). What remains is a bare filename mention
# (navigation for a future redeploy), never a line pointer.
#
# `archived_reason` here is deliberately NOT the wiki/archive/ tombstone form
# (wiki-protocol.md:112-118, `status: archived` + `archived_sprint` + `archived_reason`, in
# `wiki/archive/`) -- this article stays in the main wiki dir at `tier: reference`, which is
# its own, separate exemption. The field name is reused only because it is the closest
# existing vocabulary for "why this stopped being a live claim"; `check_integrity`'s
# archive-tombstone loop only walks `wiki/archive/*.md`, so it never reads this field here.
---

## What was built (historical — as of sprint-50, before decommission)

The bullets below describe the CloudFormation template and container image **as they were
last read against code, at sprint-50** — not a current claim. This article is not swept, so
nothing here re-verifies against today's infra/stack.yaml or `Dockerfile`. Where the
original text below named a specific line, it now names the resource or property instead —
stable across drift, unlike a line number.

- **One CloudFormation stack** (infra/stack.yaml) declared the whole dev-sized AWS topology,
  linted by `cfn-lint infra/stack.yaml` (a DoD gate since STORY-088). Minimal by design: no NAT,
  no autoscaling, no alarms, no PITR, HTTP-only ALB behind CloudFront's default cert.
- **Network:** a VPC with 2 public subnets across 2 AZs + an Internet Gateway (the ALB's hard
  2-AZ minimum). Three security groups: the ALB SG ingress 80 only from the CloudFront
  origin-facing managed prefix list (a `CloudFrontPrefixListId` **parameter** —
  infra/stack.yaml's `SourcePrefixListId` — because no CFN intrinsic resolves it); the api SG
  ingress 8000 only from the ALB SG; the loop SG had no ingress.
- **DynamoDB:** the two tables (infra/stack.yaml's `ObservationsTable` and `ControlTable`
  resources) both carried `DeletionPolicy: Retain` + `UpdateReplacePolicy: Retain`; their key
  schema (observations pk/sk; control pk/sk + a `gsi1` GSI on `gsi1pk`/`gsi1sk`) matched
  scripts/create_tables.py byte-for-byte.
- **Compute:** one ECR repo; an ECS cluster + execution role (Secrets Manager `GetSecretValue`
  scoped to the two secret ARNs) + one task role scoped to the two table ARNs **and** the GSI
  index ARN (`${ControlTable.Arn}/index/gsi1`, the `ECSTaskRole` policy's `DynamoDBAccessPolicy`
  in infra/stack.yaml); two 0.25 vCPU / 0.5 GB task definitions — api ran the image's default
  CMD with a `/api/v1/health` ALB health check; loop overrode the CMD to
  `python -m src.composition.run` and received the four Dynatrace/Statuspage secrets. Two
  services, desiredCount 1.
- **API health grace (STORY-093 AC2):** `APIService`'s `HealthCheckGracePeriodSeconds: 120`
  property (infra/stack.yaml) so the ALB target-group health check (`APITargetGroup`'s
  30s interval, unhealthy after 3 fails ≈ 90s budget) did not churn the task while the
  first-boot lifespan seed (config read + DynamoDB writes) was still running on a cold task.
- **Loop singleton (double-publish guard):** `LoopService`'s
  `DeploymentConfiguration MinimumHealthyPercent: 0 / MaximumPercent: 100` (infra/stack.yaml)
  so a deploy never ran two loops concurrently. The api service kept the rolling default (no
  `HealthCheckGracePeriodSeconds` on `LoopService` — it had no load balancer, so the property
  was not legal there).
- **Edge:** ALB HTTP:80 → api target group; a private S3 bucket (`FrontendBucket`,
  infra/stack.yaml, `DeletionPolicy: Retain`) + Origin Access Control; CloudFront with the
  default behavior → S3 and an ordered `/api/*` behavior → the ALB origin (all methods, caching
  disabled). A CloudFront Function (`RewriteFunction`, infra/stack.yaml) rewrote extensionless
  paths to `/index.html` on the **default behavior only**, never touching `/api/*` responses.
  Two 14-day log groups; two Secrets Manager secrets (names only — values entered in-console).
- **Live-deploy fixes (STORY-089, found only by deploying):** `RewriteFunction`'s
  `AutoPublish: true` property (infra/stack.yaml) — distribution `FunctionAssociations`
  require the LIVE stage, and without it stack create failed with "not found or is not
  published"; `CloudFrontDistribution`'s `DefaultRootObject: index.html` property
  (infra/stack.yaml) — the rewrite function deliberately skipped `/`, so the bare root
  otherwise 403s at the S3 origin; both managed policy IDs were live-verified
  (`Managed-CachingOptimized` `658327ea-f89d-4fab-a63d-7e88639e58f6`,
  `Managed-AllViewerExceptHostHeader` `b689b0a8-53d0-40ab-baf2-68738e2966ac`) — the originals
  were one fabricated ID (404 at create) and one ID/comment mismatch (`Managed-AllViewer`).
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
  non-root `app` user. Re-verified against infra/stack.yaml line-number drift from the
  1-line insertion.
- sprint-50 (STORY-089, live deployment): three template defects surfaced only by the real
  deploy — missing `AutoPublish` on the CloudFront function, a fabricated
  `Managed-CachingOptimized` ID, and no `DefaultRootObject` — all fixed and live-verified
  against the deployed stack (`ec09e8a`, `d119cc3`, `c05fc57`). See
  [[deployment-topology]] for the deployed instance itself.
- sprint-71 (STORY-222, 2026-08-13): the AWS stack was decommissioned by PO decision. Converted
  this article from `tier: map` / `status: stale` to `tier: reference` — a tombstone. `code_refs`
  and the `## Facts` heading are removed (renamed to "What was built"); the content is
  unchanged in substance, only reframed as history. infra/stack.yaml and the `Dockerfile`
  remain in the repo (cfn-lint still runs them in the DoD gate) as the redeploy procedure, not
  as evidence of anything currently running.
- sprint-71 (STORY-222 fix round, same day): review found the tier: reference classification
  false in substance — the ten `file:line` citations into infra/stack.yaml and
  scripts/create_tables.py were still checkable against HEAD, and the citation-gate ratchet
  (`backend/tests/test_citation_gate.py`) exempts `tier: reference` from enforcement (AC6), so a
  citation drifting 5,000 lines past EOF would have stayed green here and only gone red if this
  article were `tier: map`. Stripped every `:LINE`/`:LINE-LINE` suffix; a line number that
  carried real meaning was replaced with the CloudFormation resource or property name it
  pointed at (stable, self-describing, and immune to line drift). The bare filenames remain as
  redeploy navigation, not as a checkable claim.
