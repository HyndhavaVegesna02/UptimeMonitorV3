# Sprint 37 — Retrospective

**Delivered:** STORY-052 (1) + STORY-046 (2) = **3/3 points accepted.** 12th consecutive
clean sprint (every committed story accepted). Console-free sprint by design — STORY-017
(deploy) stayed parked on `sprint-35`.

## What went well
- **Both stories single-dispatch, zero fix loops**, first-pass clean at review.
- **Crash recovery held under a real process interruption.** The STORY-052 implementer
  (Sonnet 5) committed all seven TDD steps, then the process exited before its final
  report. Because of the commit-after-every-green-step cadence, nothing was lost: the
  orchestrator verified the crash-recovery invariants (coherent committed work, clean tree,
  no leaked artifacts — 2026-06-25 agreement) and reconstructed the DoD evidence by
  re-running all nine gates itself (verification-before-completion). The methodology
  behaved exactly as designed — the interruption cost only a gate re-run, not the work.
- **The consumer-DTO planning check paid off:** `MaintenanceWindowDTO` fields were verified
  against the wire before lock, so STORY-046's overlay hit no mid-sprint contract surprise.

## What dragged
- **A flaky canonical gate.** `npm test` false-red (exit 1) on a PRE-EXISTING, unrelated
  test — `CheckHistoryPage`'s 1500-row 1000-cap render timing out at Vitest's 5000ms default
  under file-parallelism CPU contention. It passed in isolation (3.6s) and single-threaded
  (230), and had passed green during STORY-052's own run minutes earlier. The 2026-07-02
  contention agreement was written narrowly for *concurrent DB runs* and did not literally
  cover a *single* invocation starving itself, so the correct handling relied on judgment.

## Process observations (no amendment needed — existing agreements covered them)
- The multi-session/branch state was briefly tangled (a stray checkout put the tree on the
  parked `sprint-35` right after `sprint-37` locked). Resolved by re-orienting on actual git
  state and confirming intent with the PO rather than guessing — the "verify before acting"
  discipline. No rule change; worth noting the value of a standup-style re-orient after any
  process restart.
- The interrupted-implementer recovery is fully covered by the 2026-06-25 crash-recovery +
  verification-before-completion agreements. No new rule.

## Amendments (PO-approved)
1. **2026-07-06 — A DoD-gate red caused by resource contention (not the code under test) is
   an INVALID signal — prove it, re-run isolated for the valid result, file a story to make
   the gate deterministic.** Generalizes the 2026-07-02 DB-concurrency agreement to ANY
   contention (CPU/IO/test-runner parallelism), with a MANDATORY proof step (empty diff for
   the failing unit since the sprint cut + passes isolated/serialized) so a GENUINE red can
   never be waved off as "just contention." Full text in `working-agreements.md`. Motivated
   by the `npm test` false-red above; the concrete fix is tracked as STORY-054.

## Follow-ups filed
- **STORY-054** (defect, draft) — make the frontend DoD gate deterministic (raise the
  CheckHistoryPage render-cap test timeout / reduce its fixture / pin Vitest parallelism).
- **STORY-053** (draft) — failure-shim proxy, refined to a separate proxy service; stays
  console-gated, belongs with the deploy work.
- **STORY-017** (parked) — deployment live tail, unmerged on `sprint-35`.

## Velocity
Recorded: sprint 37 committed 3 / accepted 3. Recent recorded trend (33,34,36,37) =
5,5,6,3 — the 3 is a deliberate console-free under-commit, not a capacity signal; the
ready pool was thin because the two larger candidates (017, 053) are console-gated.
