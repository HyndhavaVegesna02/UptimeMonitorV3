# Sprint 25 — Retro

**Date:** 2026-07-02
**Sprint:** STORY-015a (5 pts committed / 5 accepted). Frontend zone, second attempt — the shell,
guided by `DESIGN-linear.app.md`, dark + light themes.

## What went well
- **Cleanest frontend execution.** Both Opus reviewers passed first-pass (spec PASS all 7 AC /
  quality APPROVE, 0 Critical, 0 Major); zero fix loops; all nine DoD gates green at `08d91e7`.
- **Commit-after-green cadence finally held (7 commits).** The reverted sprint-23/24 retros flagged
  single-commit landings THREE times as "inherent to external implementation — can't enforce."
  Moving implementation in-process on a Sonnet 5 subagent (PO directive 2026-07-02) fixed it the
  first time out: TDD steps landed as individual commits, so crash-recovery granularity is back.
- **"Guide, not copy" worked.** The plan's design brief (token values, accent discipline, health
  palette, type scale) gave the implementer enough to make sound creative choices without a
  verbatim-mirror mandate — the airtight token layer, flash-free dual theme, and race-safe fetch
  hook all came back clean.
- **Start-clean on agreements was validated.** The PO chose not to re-adopt the two reverted
  sprint-23/24 amendments (scaffold-pruning, non-text-only health color); their content was baked
  into story AC (AC1, AC6) instead — and both were satisfied cleanly. The lessons survived as AC
  without needing to be standing agreements.
- **Wiki stayed honest:** mechanical sweep flagged 4 articles (3 on the one-line pyproject
  `frontend` ruff-exclude, 1 real update); new `frontend-zone.md` added; 0 stale / 0 broken across 12.

## What caused friction
- **Dead work at lock: the external-implementer prompt.** The 2026-06-28 agreement mandates emitting
  a copy-paste external-implementer prompt as a standard deliverable at EVERY lock. I did — a full
  self-contained Antigravity/Gemini prompt. The PO's very next message ("you only implement with
  Sonnet 5") moved implementation in-process, obsoleting that prompt entirely. The deliverable was
  waste the moment it was produced.
- **Environmental (not amendable): both Opus reviewers died on a session limit mid-review** on the
  first dispatch, producing no findings, and had to be re-dispatched after the reset. Because the
  mechanical gate ran in parallel (not gated behind the reviewers), the re-dispatch was cheap — but
  it cost a wait. Also a Docker `dev_db up` readiness timeout on one gate re-run, cleared by a
  down+up retry. Both environmental; no process change fixes them.

## Amendment proposed — DECLINED by PO (2026-07-02)
1. **Retire the 2026-06-28 "emit external-implementer prompt at lock" deliverable.** Implementation
   is in-process on a Sonnet 5 subagent as of the 2026-07-02 directive, so the working agreements
   now reach the implementer through the *subagent brief* the orchestrator constructs at dispatch —
   not through a copy-paste external prompt. Emitting that prompt at lock is now dead work (this
   sprint proved it: one was emitted and immediately obsoleted).
   **PO declined** (2026-07-02) — the 2026-06-28 external-prompt-at-lock agreement stands as
   written; not re-proposed without new evidence. (Practically: with implementation in-process, the
   external prompt is a low-cost redundant deliverable rather than a blocker.)

## Carry-forward (backlog, not amendments)
- **STORY-041** (chore, 2 pts, ready): the six quality-review minors — client error-wrapping on a
  malformed 2xx body, shared `cx()` helper, modular MSW handlers, catch-all route — land with/before
  the 2nd tab (015c) so the template is hardened before it's copied six times.
- `statusMapping.ts` is provisional pending STORY-015b's real Dashboard (its unknown/partial/major
  branches aren't yet unit-tested).

## Process metrics
- Reviewer rejections: 0 (both first-pass). Fix loops: 0. Hotfixes: 0. Blocked: 0.
- Estimate accuracy: 5 pts, single story, no overrun.
- Velocity: 5/5. Recorded last-3 entries (20, 21, 22, 25) = 5, 5, 3, 5 → next-sprint mean 4.33.
  (Sprints 23/24 were reverted in `521764c`; velocity.json has no entries for them, so the
  last-3-entries mean is unaffected by the numbering gap.)
