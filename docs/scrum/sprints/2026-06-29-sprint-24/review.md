# Sprint 24 — Review

**Date:** 2026-06-29
**Goal:** Ship the first real frontend tab — the Dashboard (component statuses) — and establish the per-tab
pattern that 015c–015g copy.

**Committed:** 1 story / 3 pts. **Accepted:** 1 story / 3 pts (100%).

## STORY-015b — Dashboard tab — ACCEPTED (3 pts)

### What shipped
The Dashboard is a real component (`frontend/src/tabs/Dashboard.tsx`) + a data hook
(`frontend/src/hooks/useComponents.ts`) — the **per-tab template**: a hairline `<table>` of component
statuses from `GET /api/v1/components`, the four health badges (icon + label, ink text), loading / empty /
error+retry states, all on `DESIGN-airtable.md` tokens. Extracted cleanly out of `App.tsx`, removing the
shell's `eslint-disable react-hooks/set-state-in-effect`.

### Acceptance criteria — all MET
- **AC1** each component rendered with its status using the shell health tokens (up→success, down→
  signature-coral, degraded→signature-mustard, maintenance→info); status by icon+label, never color alone.
- **AC2** data via the typed `/api/v1/components` client; loading + empty + error states; MSW-backed tests
  drive success (badge mapping via accessible text), empty (`[]`), and a real 500→retry recovery.
- **AC3** a11y/responsive: real `<table>`/`<th scope>`, keyboard order, viewport handling at 375px (the
  table wrapper scrolls, not the page).

### Evidence
- **Frontend gate green** on the clean committed tree `cef0f82`: typecheck 0 · lint 0 · **test 19 passed**
  (4 shell + 15 dashboard) · build 0.
- **Backend untouched** — frontend-only commits, byte-identical to the verified `ad7d8f2`.
- **Spec: PASS + Quality: APPROVE — zero blocking (both Opus, first-pass).** Verified the hook owns its
  effect (the `eslint-disable` smell is gone, not relocated), sub-components are module-scope, the table is
  real, the CSS is token-only, and the tests genuinely drive behavior (status→badge via text, real
  500→reset→recovery, unknown-status guard).
- **Review fixes applied inline (PO-authorized, `cef0f82`):** the two real a11y items + cheap cleanups so
  they don't propagate into 5 more tabs — degraded-badge label → `--colors-ink` (≥4.5:1) with health color
  moved to the icon; `role="status"`→`role="img"` on static badges; dropped redundant `mountedRef`; removed
  a dead `<tr>` key + moved ErrorPanel tint into `.dashboard-error`; added a behavioral Refresh-click test
  (→19 tests). Gate re-run green.
- **Wiki compile pass** (`4e8ecfd`): `frontend-zone.md` updated (Dashboard tab + per-tab pattern + the
  resolved `eslint-disable` + the badge-contrast note), 3 new files added to `code_refs`, re-stamped to
  `cef0f82`. Sweep: 0 stale / 0 broken links.

### Follow-up filed
- **STORY-041 — Frontend pattern hardening** (2 pts, `ready`): extract shared `StatusBadge`/
  `LoadingSkeleton`/`ErrorPanel`; data-drive `getStatusBadge`; tokenize the shell `.health-badge--*`
  `rgba()`; fix off-grid `10px` button paddings. Land with/before the 2nd tab (015c) to avoid 6× drift.

## Outcome
Branch `sprint-24` (5 commits from `sprint-24-start` @ `cd015ab`) accepted and merged to `main`. Velocity:
3 committed / 3 accepted. The Dashboard tab is live and the per-tab pattern is set for 015c–015g.
