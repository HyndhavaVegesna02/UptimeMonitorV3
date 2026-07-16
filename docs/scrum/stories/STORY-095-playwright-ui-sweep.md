---
id: STORY-095
title: Playwright UI sweep — thorough browser verification of the deployed dashboard
type: chore
---

## Context
PO directive 2026-07-17: "use playwright to thoroughly check the UI." The sprint-50
retro landed the Playwright MCP (`.mcp.json`) but it loads at session start — this
sprint drives Playwright directly (Node, headless Chromium) against the LIVE deployed
system (`https://d3ukiib1iqmbxb.cloudfront.net`, kept running per the sprint-50 review
decision). Until now, UI verification has been PO-manual click-throughs; this story is
the first orchestrator-driven, evidence-producing browser pass.

## Acceptance Criteria
- [ ] AC1 (six tabs render): Playwright loads each of the six tabs on the deployed URL;
      each renders its real content state (data table/cards/timeline or a legitimate
      empty state) — no error boundary, no blank shell, no unhandled console error.
      Direct-URL deep loads (e.g. `/approvals`) also render (CloudFront rewrite-fn path).
- [ ] AC2 (console + network hygiene): zero unexpected console errors and zero failed
      `/api/*` requests across the sweep (a 4xx that the UI intentionally triggers and
      handles is documented, not a failure).
- [ ] AC3 (mutation round-trips via the browser): sample-mode toggled ON → UI reflects
      it AND the control-table item flips → toggled OFF → verified clean. A maintenance
      window scheduled via the form → appears in the list → deleted → gone (leaves the
      live system clean).
- [ ] AC4 (theme + viewport spot checks): dark and light themes both render on the
      Dashboard; one narrow-viewport (mobile-ish) render sanity check.
- [ ] AC5 (evidence): screenshots per tab + a findings log recorded under the sprint
      folder; any defect found is filed as a backlog story (finding defects does NOT
      fail this story — that's its purpose).

## Open Questions
None.

## History
- 2026-07-17: drafted from the PO directive at sprint-51 planning. Estimate 2
  (script + sweep + evidence; no production code).
