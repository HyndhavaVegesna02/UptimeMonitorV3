# Sprint 27 — Review

**Date:** 2026-07-02
**Goal:** the Approvals tab (the human approval gate) + the shared `useFetch<T>`.
**Committed / delivered:** STORY-015c (5) = 5 pts. Done.
**Branch:** `sprint-27` (tag `sprint-27-start` @ `7938f2a`). Commits `8b874c6..50bf57b`.
**Mode:** in-process — Sonnet 5 implementer at high effort; Opus spec + quality reviewers.

## STORY-015c — Approvals tab (5 pts) — ACCEPTED PENDING PO VERDICT
The product's reason to exist: a degradation reaches the public Statuspage only after a human
approves it here. Lists open proposals (`GET /api/v1/approvals`) and performs approve/reject
(`POST /api/v1/decisions/{id}`) with a confirmation step and full failure handling. Also lands the
shared `useFetch<T>` (015c is the 2nd fetch hook — the parallel-shape agreement discharged).

### AC checklist (spec reviewer — all MET)
- **AC1** — renders `component_id`, the `from_status → to_status` transition (StatusBadges; null
  `from_status` → "New"), `proposed_at` (mono); empty state "nothing pending approval"; via
  `useApprovals`→shared `useFetch`; semantic accessible table. MET.
- **AC2** — approve & reject each POST `{action, actor: getActor(), notes?}`; confirmation gates the
  POST (no POST on first click); success refreshes; both paths + the exact POSTed body asserted via
  MSW. MET.
- **AC3** — 409 → inline "already resolved" + refresh; 404 → "no longer exists" + refresh; any other
  → `ErrorState` + retry. All three MSW-driven, distinct outcomes. MET.
- **AC4** — loading/empty/error+retry via shell primitives; buttons keyboard-operable (≥40px,
  accent focus); confirm dismissable (Cancel fires no POST). Tested. MET.
- **AC5** — shared `useFetch<T>` (`lib/useFetch.ts`) is the sole effect body; `useComponents` +
  `useApprovals` are thin wrappers; `useComponents` tests unchanged+green; generic has its own test.
  MET.

### Planning note (the new amendment's first application)
015c's AC were reconciled to the verified contracts before lock: `ProposalDTO` has **no
reason/evidence field** (dropped from the draft AC) and the decision POST **requires `actor`** —
supplied as a fixed placeholder behind a single swappable `getActor()` seam (auth deferred to
STORY-017), per PO decision.

### DoD evidence — all gates green at `50bf57b` (clean committed tree)
Frontend: npm test 96 passed / 18 files; build exit 0; lint exit 0. Backend: lint-imports 5/0; ruff
check + format clean; pytest 426 (frontend-only diff). DB pair unaffected (no schema change).

### Reviews
- **Spec (Opus): PASS** — all 5 AC MET, each traced to a driving test.
- **Quality (Opus): APPROVE** — 0 Critical, 0 Major. Mutate path sound (no double-submit — confirm
  control unmounts on submit; no stale closure; list reconciles after every resolved decision);
  `useFetch` cancelled-guard + retry intact after extraction; uniform `ApiError` contract. One
  minor (getJson/postJson tail duplication) folded in inline → shared `readOkJson` (`50bf57b`).

## Follow-ups captured (not blocking)
- The two real tabs now set the template (read = thin `useFetch(getX)`; mutating = local
  confirm/submit machine + `ApiError.status` branching) — captured in `frontend-zone.md` for
  015d–015g. No new chore needed.
- `notes` (optional decision field) intentionally not surfaced — candidate backlog item if an
  operator-notes UI is wanted later.

## Wiki compile pass (blocking; complete)
`frontend-zone.md` updated for 015c (shared `useFetch<T>`; `postJson`/`readOkJson` uniform error
contract; actor seam; `ProposalDTO`/decision types; approvals handler/hook/page; read + mutate
per-tab patterns). `code_refs` extended. Mechanical sweep: 0 stale / 0 broken links across 12
articles.

## Process metrics
- Reviewer rejections: 0 (both first-pass). Fix loops: 0. Hotfixes: 0. Blocked: 0.
- Estimate accuracy: 5 pts, no overrun. Commit cadence held (6 TDD commits + 1 review-nit fix).
- Velocity (if accepted): 5/5.
