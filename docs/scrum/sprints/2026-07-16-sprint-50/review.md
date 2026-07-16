# Sprint 50 Review — Deploy for real

**Goal:** Harden the container image and stack (STORY-093), then execute the live console
deployment and verify the deployed system end-to-end (STORY-089).
**Outcome: both stories Done.** The system is LIVE at
**https://d3ukiib1iqmbxb.cloudfront.net** (us-east-1, stack `uptime-monitor`).
Full 8-command DoD gate GREEN on final HEAD `89925c9` (pytest 522, import-linter 8/8,
ruff ×2, cfn-lint, npm test 363 / build / lint).

## STORY-093 — sprint-49 review minors (2 pts) — DONE

| AC | Evidence |
|----|----------|
| AC1 container hardening | Non-root `USER app` (verified `whoami` in container); dead `ENV PORT` removed; dep layer split via tomllib-derived requirements — 2nd build after source-only touch shows dependency layer **CACHED** |
| AC2 ECS health grace | `HealthCheckGracePeriodSeconds: 120` on `APIService`; cfn-lint green |
| AC3 test hygiene | Zero-assertion test now asserts real call shapes (mutation-tested); new no-Postgres guard meta-test (522nd test); `monkeypatch.setenv` swap |
| AC4 gates | Full 8-command gate green (at 0f7546f per-story, re-proven at 89925c9 close) |

Commit cadence: 8 TDD steps, cf875ff..b2d0cfa. Bonus fold-in: the deploy-runbook branch
prerequisite updated off stale `sprint-49` (plan-verifier GAP 1).

## STORY-089 — live console deployment + e2e verification (3 pts) — DONE

Demo = the live system itself: **https://d3ukiib1iqmbxb.cloudfront.net**

| AC | Evidence |
|----|----------|
| AC1 stack up | `CREATE_COMPLETE`; image in ECR; API task `healthy` in target group; loop exactly 1 RUNNING task |
| AC2 frontend | PO click-through: all six tabs render over HTTPS; probes: `/`→200, `/approvals`→200 HTML (rewrite fn LIVE), `/api/*` same-origin 200s, no CORS |
| AC3 live loop | Watermark advanced `21:42:42Z → 21:44:42Z`; `/history` returns real per-minute Grail observations (2 locations); `/availability` computes 69/69 verdicts |
| AC4 mutation | Sample-mode toggled from the deployed UI: two `PUT /api/v1/sample-mode 200` in CloudWatch + `CONFIG/SAMPLE_MODE` item verified in DynamoDB, left `false` |
| AC5 secrets | Leak sweep over all sprint commits: only dummy test fixtures; values only in Secrets Manager |
| AC6 docs | CLAUDE.md deployed-topology section; new `deployment-topology.md` wiki article; board evidence recorded |

**Three template defects found ONLY by deploying live** (the exact class sprint-49's
deferred-to-089 reality gate predicted), each fixed on-branch and verified by redeploy:
1. `AutoPublish: true` missing on the CloudFront function (ec09e8a)
2. Fabricated `Managed-CachingOptimized` policy ID + ID/comment mismatch on the
   origin-request policy — both re-derived live from the account (d119cc3)
3. No `DefaultRootObject` — bare `/` 403'd (c05fc57, in-place stack update)

**PO org-policy interrupt** (mid-story, logged): company AWS rules — us-east-1 only,
nightly 22:00 IST reaper. Encoded into the runbook; stack tagged `c7n-keep=true` +
`username=Hyndhava` (propagates to all resources). Saved to memory for future sprints.

## Decisions needed from the PO

1. **Verdict per story** (accept / reject): STORY-093, STORY-089.
2. **Keep the stack running or tear down?** It's reaper-protected and costs real money
   ~24/7 (2 Fargate tasks + ALB + CloudFront). Options: keep live; or delete the stack
   (tables/bucket/ECR persist via Retain — full cleanup needs those deleted manually too).
   Org rules say clean up when the learning activity completes — your call on timing.

## Deferred / follow-up candidates
- Browser-automation MCP (Playwright) tooling gap: AC2/AC4 UI verification needed PO
  hands; an MCP would let the orchestrator drive it (raise at retro — tooling moment).
- `/api/v1/history` appears to ignore its `limit` query param (returned full window with
  `limit=2`) — worth a defect story.
- STORY-090 (CI/CD) is now unblocked per the PO's "UI first, CI/CD later" directive.
