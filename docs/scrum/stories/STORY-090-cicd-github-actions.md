---
id: STORY-090
title: CI/CD stage 2 — GitHub Actions pipelines + OIDC deploy role
type: chore
---

## Context
AWS migration epic, stage 2 (PO directive 2026-07-14: "deployment through UI first,
CI/CD later"). Automates what STORY-089's console runbook proved manually. Deliberately
deferred — do not refine to ready until the console deployment is accepted and stable.

Sketch (to be refined then): a GitHub OIDC identity provider + a deploy role trusted by
this repo (no long-lived AWS keys); `backend.yml` (gates → docker build/push tag=sha →
`aws cloudformation deploy --parameter-overrides ImageTag=...` rolling both services,
loop still 0%/100%); `frontend.yml` (the three frontend DoD gates → `aws s3 sync` →
CloudFront invalidation). YourTeam fit: merges to main happen only at sprint review, so
deploy-on-main means deploy-what-the-PO-accepted.

## Description
To be completed at its own refinement after STORY-089 acceptance.

## Acceptance Criteria
- [ ] To be refined (needs: OIDC bootstrap decision — console-created or
      CFN-managed; whether the CI gate job mirrors the full DoD or a scoped subset).

## Open Questions
- OIDC provider/role bootstrap: PO-created in console (one-time) or a second small
  CFN template?
- Does CI run the DynamoDB-Local-backed pytest suite as a service container, and does
  its gate set mirror the DoD exactly?

## History
- 2026-07-14: drafted (deliberately thin) at AWS-migration refinement as the stage-2
  placeholder. Status: draft, unestimated.
