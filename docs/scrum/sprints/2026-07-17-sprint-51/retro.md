# Sprint 51 Retro

## Data
- Velocity 4/4 (both stories accepted first-pass; zero reviewer loops — both 2-pt, no
  reviewer tier; PO verdicts clean).
- Estimates exact. No blockers, no hotfixes, no effort-cap trips.
- Wiki: 0 stale at close; 3 articles re-verified in-sprint; re-stamped at merge.
- First orchestrator-driven UI verification in project history (STORY-095): 6 tabs ×
  2 load modes, 0 console errors, 0 failed API calls, mutations reversed cleanly —
  replaced the PO-manual click-through entirely.
- Post-acceptance live redeploy: image push OK; SSO token expired before the two
  update-service calls (blocked on PO refresh); resumed from the failed step;
  `limit` verified live through CloudFront (limit=2 → 2 newest; limit=0 → 422).

## What went well
- Refinement recon flipped STORY-094 from "defect" to the true story (param never
  existed) BEFORE planning — no mid-sprint surprise.
- The prefetched Chromium cache + the sweep harness made STORY-095 start instantly;
  the harness (tools/ui-sweep/sweep.mjs) is now reusable project tooling.
- The sprint-50 HealthCheckGracePeriodSeconds fix proved itself: zero task churn
  through the live rollout.

## What dragged
- STORY-094's reality-gate uvicorn survived a wrapper-job kill (needed taskkill + netstat
  verify) → amendment 1.
- SSO expiry mid-redeploy cost a blocked handoff → amendment 2.
- (Minor, orchestrator tooling) PS 5.1 utf8 BOM bit the wiki re-stamp once more before
  the BOM-safe method was used; no amendment — the safe pattern is now established in
  session history and the lint catches it mechanically.

## Amendments (PO-approved 2026-07-17, both landed)
1. **Checklist rung** — implementer.md: spawned servers/containers end with OS-level
   teardown VERIFICATION (PID gone + port freed), wrapper-job kill is not evidence.
2. **Prose rung** — working-agreements.md: verify credential freshness before
   multi-step live-cloud sequences; on mid-sequence expiry resume from the failed
   step, never restart.

## Carry-forward
- Playwright MCP (.mcp.json) loads from the NEXT session — interactive browser
  verification becomes first-class then; the sweep harness remains for scripted passes.
- Backlog next: STORY-090 (CI/CD, draft), STORY-096 (sidebar breakpoint, draft),
  STORY-081 (incident-id, draft) — all need refinement.
