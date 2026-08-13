---
title: Deployed topology — the live AWS instance (STORY-089), decommissioned 2026-08-13
tier: reference
verified_sprint: sprint-50
archived_reason: >-
  AWS stack decommissioned by PO decision on 2026-08-13 (STORY-222). This article already
  carried no code_refs and no Facts (tier: reference since 2026-08-12); the decommission
  closes the "unverified since 2026-07-29" question this article's own Superseded note left
  open -- the stack is not merely unverified now, it does not exist.
# tier: reference (2026-08-12) — and this article is why the tier exists. Everything below
# is an OBSERVATION of a running deployment on a given day, not a claim about code: no
# `git diff` over any code_ref can confirm or refute "the ALB target group was healthy",
# so the staleness machinery never had purchase on it. Carrying `status: verified` was the
# misleading part — it read as "checked against the repo" when nothing in the repo was ever
# checked. Reference articles declare no code_refs and no Facts, so this one cannot claim
# more than it knows. The live-state question belongs to the two `aws`/`curl` commands
# below and to CLAUDE.md's "Deployed topology" section, which carries the current status.
#
# `archived_reason` here is deliberately NOT the wiki/archive/ tombstone form
# (wiki-protocol.md:112-118, `status: archived` + `archived_sprint` + `archived_reason`, in
# `wiki/archive/`) -- this article stays in the main wiki dir at `tier: reference`, its own,
# separate exemption. `check_integrity`'s archive-tombstone loop only walks
# `wiki/archive/*.md`, so it never reads this field here; it is reused purely as the closest
# existing vocabulary for "why this stopped being a live claim".
---

## Observed 2026-07-17 — the deployment as it was that day, NOT a current claim

> **DECOMMISSIONED 2026-08-13 by PO decision (STORY-222).** The stack described below no
> longer exists — it was torn down, not merely unverified. A re-check on 2026-07-29 had
> already got **503** from `/api/v1/health` with expired AWS credentials, cause never
> confirmed (CloudFront answered, so the origin was unhealthy; the likeliest cause was the
> 22:00 IST reaper stopping ECS tasks that lost their `c7n-keep=true` tag) — see CLAUDE.md's
> "Deployed topology" section for the current status. **Treat every "healthy"/"1 task"
> statement below as true on 2026-07-17 and gone since 2026-08-13.** The Verify commands
> below (including the `curl` against `d3ukiib1iqmbxb.cloudfront.net`) describe **this now-gone
> instance**, not a domain a redeploy will get — CloudFormation assigns CloudFront distributions
> a fresh domain on every stack create, so a future redeploy's real verify command will hard-code
> a different hostname than the one preserved here.

- **Stack:** CloudFormation stack `uptime-monitor` in **us-east-1**, account `065317679010`,
  created from `infra/stack.yaml` via the console runbook (`docs/deploy-runbook.md`);
  reached `CREATE_COMPLETE` on the third attempt (see History) + one in-place update
  (`DefaultRootObject`). Stack-level tags `c7n-keep=true` + `username=Hyndhava` propagate to
  all taggable resources (org nightly-reaper protection — see the company account rules in
  the runbook Prerequisites).
- **Public URL:** `https://d3ukiib1iqmbxb.cloudfront.net` — SPA from the private S3 bucket
  `uptime-monitor-frontend-065317679010`, `/api/*` proxied same-origin to the ALB
  (`uptime-monitor-alb-2022040732.us-east-1.elb.amazonaws.com`, HTTP:80, reachable only from
  the CloudFront origin-facing prefix list).
- **Services** (cluster `uptime-monitor-cluster`, Fargate, image
  `065317679010.dkr.ecr.us-east-1.amazonaws.com/uptime-monitor-repo:latest`):
  `uptime-monitor-api` (1 task, healthy in target group `uptime-monitor-api-tg`) and
  `uptime-monitor-loop` (exactly 1 task — singleton by DeploymentConfiguration). Logs:
  `/ecs/uptime-monitor-api`, `/ecs/uptime-monitor-loop` (14-day retention).
- **Data:** tables `uptime-monitor-observations` + `uptime-monitor-control`
  (`DeletionPolicy: Retain`). Live-verified flows: boot seed populated components from
  `config/apps`; the loop ingests real Grail observations (~2/min from 2 synthetic
  locations); watermark `WATERMARK#http-check`/`META` advances every cycle
  (observed `21:42:42Z → 21:44:42Z`); sample-mode round-trip (UI toggle → two
  `PUT /api/v1/sample-mode 200` in the api CloudWatch log → `CONFIG`/`SAMPLE_MODE`
  item flip, left `enabled: false`).
- **Secrets:** values live ONLY in Secrets Manager `uptime-monitor-dynatrace-secrets`
  (`DYNATRACE_ENV_URL`, `DYNATRACE_API_TOKEN`) and `uptime-monitor-statuspage-secrets`
  (`STATUSPAGE_PAGE_ID`, `STATUSPAGE_API_KEY`) — JSON keys must match those exact names
  (ECS resolves per-key via `ValueFrom '<arn>:<KEY>::'`; a missing key blocks loop task
  launch with `ResourceInitializationError`). Plain env vars injected by the task defs:
  `AWS_REGION`, `DYNAMO_OBSERVATIONS_TABLE`, `DYNAMO_CONTROL_TABLE`.
- **Verify commands (as run against THIS now-decommissioned instance — CLI, region
  us-east-1):** `aws cloudformation describe-stacks --stack-name uptime-monitor`
  (status/outputs); `aws ecs describe-services --cluster uptime-monitor-cluster --services
  uptime-monitor-api uptime-monitor-loop`; `aws dynamodb get-item --table-name
  uptime-monitor-control --key '{"pk":{"S":"WATERMARK#http-check"},"sk":{"S":"META"}}'`;
  `curl https://d3ukiib1iqmbxb.cloudfront.net/api/v1/health` (expect 200 — that hostname died
  with this stack; a redeploy gets a new CloudFront domain from its own `describe-stacks`
  output, not this one).

## Inference (synthesis, not verified)
- Redeploy of code = push a new image to ECR + force new deployment on the two services
  (runbook Step 3.5); redeploy of frontend = `npm run build` + `aws s3 sync frontend/dist
  s3://uptime-monitor-frontend-065317679010 --delete` + CloudFront invalidation `/*`.
  Template changes go through `aws cloudformation update-stack` (as the
  `DefaultRootObject` fix did) — no delete/recreate needed for in-place-updatable
  properties.
- ECS task-launch retry backoff after failed secret resolution is slow; a
  `--force-new-deployment` resets it immediately (used during the initial deploy).

## History
- sprint-50 (STORY-089): created at the first live deployment. Attempt 1 failed on the
  unpublished CloudFront function, attempt 2 on the fabricated cache-policy ID (each
  rollback leaving Retain leftovers — tables + bucket — that must be deleted before
  retrying, since the fresh create cannot claim their names); attempt 3 succeeded, then
  one update added `DefaultRootObject`. Full defect detail in [[deployment-and-infra]].
- sprint-71 (STORY-222, 2026-08-13): the AWS stack described above was decommissioned by
  PO decision. This article was already `tier: reference` with no code_refs/Facts, so no
  tier conversion was needed — only the framing changed, from "unverified since 2026-07-29"
  to "gone since 2026-08-13". See [[deployment-and-infra]] (converted to a tombstone in the
  same story) and CLAUDE.md's "Deployed topology" section for the current status.
