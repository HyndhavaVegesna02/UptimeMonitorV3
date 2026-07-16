# Sprint 51 Plan — history `limit` + first orchestrator-driven UI sweep

- **Sprint goal:** Add the server-side `limit` cap to the history endpoint (STORY-094)
  and run the first thorough, evidence-producing Playwright verification of the live
  deployed dashboard (STORY-095).
- **Mode:** `in-process`.
- **Stories & order:**
  1. **STORY-094** (2 pts) — history `limit` param. First: it's the code change; an
     early blocker leaves time for the sweep.
  2. **STORY-095** (2 pts) — Playwright UI sweep of the deployed system (no production
     code; runs against the live stack as currently deployed — independent of 094,
     whose fix reaches the live stack only after PO acceptance + image redeploy).
- **Plan-verifier: SKIPPED** (token economy, PO-approved 2026-07-15). Reason: not
  contract-sensitive — STORY-094 is a one-zone additive param on an existing endpoint
  against existing DTOs (no cross-component consumption, no units/scale logic, no new
  vendor path); STORY-095 writes no production code (verification sweep over the
  already-live UI). Recorded here for PO visibility at approval.
- **Tooling:** Playwright MCP (.mcp.json, landed at sprint-50 retro) loads only at
  session START — unavailable mid-session. This sprint drives Playwright directly:
  `npm i -D playwright` scoped to a throwaway `tools/ui-sweep/` (or npx), headless
  Chromium against `https://d3ukiib1iqmbxb.cloudfront.net`. Same engine the MCP wraps;
  from next session the MCP takes over this role interactively.

---

## STORY-094 — history `limit` param (2 pts)

### Verified contracts / constraints (from refinement recon, cited)

- `backend/src/api/v1/history/controller.py:19-27` declares `signal_key`/`since`/`until`
  only; FastAPI ignores unknown query params (probe `limit=2` was a no-op).
- `service.py:46` sorts most-recent-first AFTER `in_window`; the cap slices this sorted
  list (`[:limit]`) — the repository port `in_window` signature is NOT changed (no port
  churn; the DynamoDB query already bounds by window).
- `validation.py` is the existing edge-422 seam (STORY-052 convention) — limit
  validation (int ≥ 1) goes there; FastAPI's own type coercion handles non-int as 422
  natively via `Query(None, ge=1)` — prefer the declarative `ge=1` form, and add the
  explicit validation-seam test either way.
- Frontend does NOT adopt limit (AC3 is comment reconciliation only):
  `frontend/src/api/client.ts:210-217` "NO pagination ... always requests the full
  in-window result" must gain a note that the server now ACCEPTS an optional cap the
  client deliberately does not use; same for the `CheckHistoryPage.tsx:53` render-cap
  comment.
- Five-file API convention (STORY-014): the param touches controller + validation +
  service; models.py (DTO) unchanged; the zone-layout meta-test must stay green.

### Steps

- [x] 1. Failing test first (`backend/tests/test_history_endpoint.py` pattern): with 5
  seeded observations, `limit=2` returns exactly the 2 newest; `limit` larger than the
  result set returns all; run — red (param not declared). Commit after green via step 2.
- [x] 2. Declare `limit: int | None = Query(None, ge=1, ...)` in the controller; thread
  through the service (`sorted_obs[:limit]` when limit is not None). See step-1 tests
  pass. Commit.
- [x] 3. Edge tests: absent limit → identical full-window behavior (existing tests
  untouched and green); `limit=0` and `limit=-1` → 422; `limit=abc` → 422. Commit.
- [x] 4. AC3 docs: reconcile the two frontend comments (client.ts, CheckHistoryPage.tsx)
  — server cap exists, client render-cap stays authoritative. Commit.
- [ ] 5. Story gate: `yt_gate.py --only` pytest + ruff (diff = backend api/tests +
  frontend comments; comments don't affect npm gates but run `npm run lint` if
  CheckHistoryPage.tsx line-wrap changes). Wiki blast radius check. Board update.

### Reality gate (094)
Consumer/API story ⇒ live render-vs-wire spot check: run the LOCAL stack (DynamoDB Local
+ uvicorn), curl `/api/v1/history?...&limit=2` → exactly 2 newest rows; absent limit →
full window. (The LIVE stack still runs the pre-fix image; live verification of this fix
happens at the post-acceptance redeploy — never ship-on-promise, so the story's live
evidence is the local stack, stated explicitly.)

---

## STORY-095 — Playwright UI sweep of the deployed dashboard (2 pts)

### Constraints

- Target: `https://d3ukiib1iqmbxb.cloudfront.net` (LIVE — leave it clean: every mutation
  reversed; sweep is read-mostly).
- Playwright driven directly (headless Chromium); screenshots + findings log to
  `docs/scrum/sprints/2026-07-17-sprint-51/ui-sweep/`.
- Console errors and failed `/api/*` responses collected per page via Playwright
  `console`/`response` events.
- The six tabs (nav routes from `frontend/src/nav/tabs.ts`): Dashboard, Approvals,
  Availability, Check History, Maintenance, Publications.

### Steps

- [ ] 1. Scaffold `tools/ui-sweep/` (gitignored node_modules): playwright dep +
  chromium install + sweep script skeleton (console/network capture harness). Commit.
- [ ] 2. AC1/AC2 sweep: for each tab — SPA-nav load AND direct-URL deep load; assert
  rendered content state; screenshot; collect console errors + failed API calls. Commit
  script + evidence.
- [ ] 3. AC3 mutations via the browser: sample-mode ON → UI + control-table verify →
  OFF → verify clean. Maintenance window schedule → visible in list → delete → gone.
  Screenshots each step. Commit evidence.
- [ ] 4. AC4: dark/light theme renders on Dashboard; one 390px-wide viewport check.
  Commit evidence.
- [ ] 5. AC5: findings log (`ui-sweep/findings.md`) — every anomaly either explained or
  filed as a backlog story. Story gate (`--only` ruff format if any .py touched — else
  note no gate-relevant diff; the full close gate covers it). Board update.

### Reality gate (095)
The story IS a live reality gate by construction (real browser, real deployed system).

### Sprint close
Full 8-command gate on final HEAD + wiki compile pass (yt_wiki.py exit 0) before review.
