# Sprint 53 Retro — 2026-07-17

## What happened worth learning from
1. **Two agent crashes, two clean recoveries, zero rework.** The session-limit kill (first
   STORY-099 dispatch) died pre-write; the mid-stream API error (STORY-102) died with 5
   green commits + 1 uncommitted scrap. Both recoveries were mechanical: last green commit
   is truth, discard scraps, resume (via transcript) or re-dispatch. The per-green-step
   commit cadence is the crash-recovery mechanism and it paid for itself twice today.
2. **The retro-52 amendments held.** A1 (no live-DB endpoint in gate shells) was followed by
   every dispatch and no stack wipe recurred; A2 (:focus-visible ≠ programmatic focus) was
   needed AGAIN this sprint — the rail-tooltip check first read "hidden" under .focus() and
   passed under a real keyboard Tab, exactly the false-alarm class A2 documents; A3 (wiki
   ownership with the implementer) produced properly rewritten sample-mode.md Facts rather
   than blind re-stamps.
3. **Deliberate over-commit (6 vs velocity 5) worked** because the three stories were
   independent display-layer work — but it consumed the whole day including a session-limit
   window. Not a pattern to repeat without that independence property.
4. **Story briefs citing "current state you are fixing" (live-verified observations) kept
   implementers from re-exploring** — dispatches went straight to TDD. Keep doing this.

## Amendments
- **A1 (sprint-53) — Crash-recovery protocol is working as designed; no new rule.** Recorded
  as a confirmation data point for the existing cadence rules, not a new agreement. (Rung:
  none — evidence only.)
- **A2 (sprint-53) — Over-commit guard:** exceeding the velocity reference requires the plan
  to state WHY the stories are independent enough to drop one at review without waste; done
  this sprint, now the explicit bar. (Rung: prose — planning practice, recorded here.)

## Tooling friction
Session limit killed a dispatch mid-flight (external constraint, not process). The Playwright
MCP browser is shared with the operator's desktop Chrome — harmless so far (worked in a
dedicated tab), but noted for awareness.
