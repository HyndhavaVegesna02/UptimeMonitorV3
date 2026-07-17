# Sprint 51 Review — history `limit` + first orchestrator-driven UI sweep

**Goal:** Add the server-side `limit` cap to the history endpoint (STORY-094) and run
the first thorough Playwright verification of the live deployed dashboard (STORY-095).
**Outcome: both stories Done.** Full 8-command gate GREEN on final HEAD `3cdf09d`
(pytest 529, import-linter 8/8, ruff ×2, cfn-lint, npm 363/build/lint).

## STORY-094 — history `limit` param (2 pts) — DONE

Reframed at refinement: `limit` never existed (FastAPI silently ignored it; the frontend
never sends it) — implemented as an additive optional newest-first cap.

| AC | Evidence |
|----|----------|
| AC1 limit=N → N newest | 7 new tests incl. one against the real DynamoDB-Local repository path; local-stack curl: limit=2 → exactly the 2 newest of 5 seeded |
| AC2 absent → unchanged; bad → 422 | Existing tests untouched & green; limit=0/-1/abc → 422 (declarative `Query(ge=1)`); local curl 422 confirmed |
| AC3 frontend comments reconciled | client.ts + CheckHistoryPage.tsx docs-only diff; render-cap stays authoritative |
| AC4 gate | Scoped gate green at 7f352b8; full close gate green at 3cdf09d |

**Note:** the LIVE stack still runs the pre-fix image (by design — never deploy
unaccepted code). On acceptance I push the new image + force redeploy (~3 min) and
verify `limit` live.

## STORY-095 — Playwright UI sweep of the deployed dashboard (2 pts) — DONE

All five ACs PASS against `https://d3ukiib1iqmbxb.cloudfront.net` (real headless
Chromium). Evidence: `ui-sweep/` in this folder (per-tab PNGs both load modes, theme +
390px shots, mutation step shots, `findings.md`).

- Six tabs render via BOTH deep-load (CloudFront rewrite path) and SPA nav.
- Zero console errors, zero failed `/api/*` across 20+ page loads.
- Mutations round-tripped and reversed: sample-mode ON→OFF (UI + control-table verified
  both ways); maintenance window created via the form, listed, deleted, gone.
- Light/dark both render (system-pref emulation AND the in-app toggle).
- Live system confirmed left clean at session end.

**Findings:** 3 anomalies — 2 EXPLAINED (screenshot thumbnail ambiguity; a harness race,
fixed in the harness), 1 **CANDIDATE-STORY**: below ~768px the sidebar keeps full
desktop width and squeezes content (390×844 spot check). Proposed as a new backlog
story (mobile/narrow-viewport breakpoint).

## Decisions needed from the PO
1. Verdict per story: STORY-094, STORY-095.
2. On STORY-094 acceptance: redeploy the live stack now (image push + force new
   deployment) so `limit` is live?
3. File the responsive-sidebar candidate as a backlog story?
