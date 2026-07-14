---
id: STORY-089
title: Live console deployment + end-to-end verification (PO-driven)
type: chore
---

## Context
AWS migration epic (see STORY-082 Context). The PO executes STORY-088's runbook in the
AWS Console; console actions are sanctioned PO-interaction points during the sprint,
not blockers (modality carried over from superseded STORY-017). Fresh-start cutover
per the 2026-07-14 decision: no Neon data migrates — topology seeds from `config/apps`
at boot, observations regenerate from Dynatrace, watermarks establish on the first
cycle; proposal/publication history starts empty.

## Description
Deploy the stack for real and verify the deployed system end-to-end, recording
evidence. Produce the deployed-topology documentation.

## Acceptance Criteria
- [ ] AC1 (stack up): the CloudFormation stack reaches CREATE_COMPLETE from the
      console; the image is pushed to ECR; both ECS services reach steady state
      RUNNING (api healthy in the target group, loop running exactly one task).
- [ ] AC2 (frontend): the built SPA is in S3; the CloudFront URL renders all six tabs
      over HTTPS from the deployed API through the `/api/*` behavior (no CORS errors —
      same-origin by design).
- [ ] AC3 (live loop): the loop ingests real Grail observations into
      `uptime-observations` — the watermark advances across at least two cycles;
      availability and history endpoints return real data for the seeded signal.
- [ ] AC4 (mutation round-trip): one write path exercised live from the deployed UI
      (sample-mode toggle or maintenance schedule + delete) and verified in DynamoDB.
- [ ] AC5 (secrets hygiene): Dynatrace/Statuspage values exist only in Secrets Manager;
      no secret value in the repo at any commit of the sprint.
- [ ] AC6 (docs): CLAUDE.md gains the deployed-topology section (stack, services, env
      var/secret names, verify commands); a `deployment-topology` wiki article is
      created with `code_refs` to `infra/stack.yaml`, the Dockerfile, and the runbook;
      evidence recorded in the sprint board.

## Open Questions
None.

## History
- 2026-07-14: drafted at AWS-migration refinement. Status: draft, 3 points proposed
  (PO-interactive; live-credential/account gated like the old Integration+Deployment
  block).
- 2026-07-14: PO approved AC + estimate ("approve all") → ready.
