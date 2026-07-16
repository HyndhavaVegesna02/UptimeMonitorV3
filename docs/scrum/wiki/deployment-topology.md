---
title: Deployed topology â€” the live AWS instance (STORY-089)
code_refs: [infra/stack.yaml, Dockerfile, docs/deploy-runbook.md]
verified_sha: 7c53685
verified_sprint: sprint-50
status: verified
---

## Facts (verified live against the deployed stack, 2026-07-17)

- **Stack:** CloudFormation stack `uptime-monitor` in **us-east-1**, account `065317679010`,
  created from `infra/stack.yaml` via the console runbook (`docs/deploy-runbook.md`);
  reached `CREATE_COMPLETE` on the third attempt (see History) + one in-place update
  (`DefaultRootObject`). Stack-level tags `c7n-keep=true` + `username=Hyndhava` propagate to
  all taggable resources (org nightly-reaper protection â€” see the company account rules in
  the runbook Prerequisites).
- **Public URL:** `https://d3ukiib1iqmbxb.cloudfront.net` â€” SPA from the private S3 bucket
  `uptime-monitor-frontend-065317679010`, `/api/*` proxied same-origin to the ALB
  (`uptime-monitor-alb-2022040732.us-east-1.elb.amazonaws.com`, HTTP:80, reachable only from
  the CloudFront origin-facing prefix list).
- **Services** (cluster `uptime-monitor-cluster`, Fargate, image
  `065317679010.dkr.ecr.us-east-1.amazonaws.com/uptime-monitor-repo:latest`):
  `uptime-monitor-api` (1 task, healthy in target group `uptime-monitor-api-tg`) and
  `uptime-monitor-loop` (exactly 1 task â€” singleton by DeploymentConfiguration). Logs:
  `/ecs/uptime-monitor-api`, `/ecs/uptime-monitor-loop` (14-day retention).
- **Data:** tables `uptime-monitor-observations` + `uptime-monitor-control`
  (`DeletionPolicy: Retain`). Live-verified flows: boot seed populated components from
  `config/apps`; the loop ingests real Grail observations (~2/min from 2 synthetic
  locations); watermark `WATERMARK#http-check`/`META` advances every cycle
  (observed `21:42:42Z â†’ 21:44:42Z`); sample-mode round-trip (UI toggle â†’ two
  `PUT /api/v1/sample-mode 200` in the api CloudWatch log â†’ `CONFIG`/`SAMPLE_MODE`
  item flip, left `enabled: false`).
- **Secrets:** values live ONLY in Secrets Manager `uptime-monitor-dynatrace-secrets`
  (`DYNATRACE_ENV_URL`, `DYNATRACE_API_TOKEN`) and `uptime-monitor-statuspage-secrets`
  (`STATUSPAGE_PAGE_ID`, `STATUSPAGE_API_KEY`) â€” JSON keys must match those exact names
  (ECS resolves per-key via `ValueFrom '<arn>:<KEY>::'`; a missing key blocks loop task
  launch with `ResourceInitializationError`). Plain env vars injected by the task defs:
  `AWS_REGION`, `DYNAMO_OBSERVATIONS_TABLE`, `DYNAMO_CONTROL_TABLE`.
- **Verify commands** (CLI, region us-east-1):
  `aws cloudformation describe-stacks --stack-name uptime-monitor` (status/outputs);
  `aws ecs describe-services --cluster uptime-monitor-cluster --services uptime-monitor-api uptime-monitor-loop`;
  `aws dynamodb get-item --table-name uptime-monitor-control --key '{"pk":{"S":"WATERMARK#http-check"},"sk":{"S":"META"}}'`;
  `curl https://d3ukiib1iqmbxb.cloudfront.net/api/v1/health` (expect 200).

## Inference (synthesis, not verified)
- Redeploy of code = push a new image to ECR + force new deployment on the two services
  (runbook Step 3.5); redeploy of frontend = `npm run build` + `aws s3 sync frontend/dist
  s3://uptime-monitor-frontend-065317679010 --delete` + CloudFront invalidation `/*`.
  Template changes go through `aws cloudformation update-stack` (as the
  `DefaultRootObject` fix did) â€” no delete/recreate needed for in-place-updatable
  properties.
- ECS task-launch retry backoff after failed secret resolution is slow; a
  `--force-new-deployment` resets it immediately (used during the initial deploy).

## History
- sprint-50 (STORY-089): created at the first live deployment. Attempt 1 failed on the
  unpublished CloudFront function, attempt 2 on the fabricated cache-policy ID (each
  rollback leaving Retain leftovers â€” tables + bucket â€” that must be deleted before
  retrying, since the fresh create cannot claim their names); attempt 3 succeeded, then
  one update added `DefaultRootObject`. Full defect detail in [[deployment-and-infra]].
