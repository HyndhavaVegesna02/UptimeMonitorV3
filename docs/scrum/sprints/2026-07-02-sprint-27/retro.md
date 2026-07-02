# Sprint 27 — Retro

**Date:** 2026-07-02
**Sprint:** STORY-015c (5 pts committed / 5 accepted). The Approvals tab — the human approval gate,
the first MUTATING frontend tab — plus the shared `useFetch<T>`.

## What went well
- **Third clean sprint in a row.** Both Opus reviewers first-pass (spec PASS all 5 AC / quality
  APPROVE 0 Critical, 0 Major), zero fix loops, zero blocks. Only one client-dedup nit, folded
  inline. Commit cadence held (6 TDD commits + 1 nit fix).
- **Last sprint's amendment paid off on its FIRST use.** The 2026-07-02 "verify tab-AC fields vs
  the backend DTO at planning" agreement caught, before any code, that `ProposalDTO` has no
  `reason/evidence` field and that the decision POST requires an `actor` — trimmed the impossible
  field and wired `actor` as a swappable seam at planning. Exactly the mid-sprint block / wrong-build
  it exists to prevent. The amendment is validated, not just theoretical.
- **The first mutating tab landed clean.** Approve/reject is the app's highest-risk frontend surface
  (a real write, TOCTOU-prone). It went in first-pass with a sound state machine: double-submit
  guarded by UNMOUNTING the confirm control, `ApiError.status` branching for 409/404/generic, and a
  list refresh after every resolved decision. The quality reviewer specifically probed the race
  surface and found nothing.
- **Shared `useFetch<T>` landed at the right moment.** The parallel-shape trigger the Sprint-26
  retro flagged was discharged proactively — planned into 015c rather than discovered as drift.
  `useComponents` + `useApprovals` are now thin wrappers over one effect body; the read + mutate
  per-tab templates are documented in `frontend-zone.md` for 015d–015g.

## What we learned
- **The process is well-tuned; no new amendment this sprint.** Three consecutive clean sprints under
  in-process Sonnet 5 implementation + Opus review, with the accumulated agreements (tests-drive-real
  -behavior, contract-change-rewrites-tests, parallel-shape, mutate-failure-paths, tab-AC-vs-DTO)
  visibly shaping a first-pass result. Forcing an amendment where nothing broke would be noise —
  none proposed.

## Carry-forward (next-planning, not amendments)
- **015d (Availability) + 015e (Check History) send time-window query params** (`since`/`until`).
  The backend enforces tz-AWARE datetimes and 422s naive ones (working agreement 2026-06-28). At
  those stories' planning, verify (per the tab-AC-vs-DTO agreement) the exact query-param contract
  and ensure the frontend sends tz-aware ISO timestamps — a latent frontend↔backend integration
  risk if the tab sends a bare date.
- `notes` (optional decision field) intentionally not surfaced in 015c — candidate backlog item if
  an operator-notes UI is later wanted.

## Process metrics
- Reviewer rejections: 0 (both first-pass). Fix loops: 0. Hotfixes: 0. Blocked: 0.
- Estimate accuracy: 5 pts, single story, no overrun.
- Velocity: 5/5. Recorded last-3 entries (25, 26, 27) = 5, 5, 5 → next-sprint mean 5.0.
- Frontend progress: 3 of 6 tabs done (shell + Dashboard + Approvals); 015d–015g remain
  (Availability 3, Check History 3, Maintenance 3, Publications 2).
