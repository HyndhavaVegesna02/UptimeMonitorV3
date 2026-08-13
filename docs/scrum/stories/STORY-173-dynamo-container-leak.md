---
id: STORY-173
title: A killed pytest run leaks its DynamoDB Local container and stalls the next run
type: defect
points: null
status: draft
filed: 2026-07-28
sprint: null
---

## Context

Observed 2026-07-28 during the sprint-62 baseline gate, **twice**. Re-confirmed 2026-07-29 while
root-causing STORY-179, where two leaked containers needed a manual `docker rm -f`.

**Re-verified 2026-08-13 at the equilibrium refinement pass: `backend/tests/conftest.py` contains
no reaping logic of any kind** — a grep for `reap`, `orphan`, `getpid` and container removal
patterns returns nothing.

## Reproduction

1. Start `python .claude/skills/yourteam/scripts/yt_gate.py`.
2. Kill it mid-`pytest` — e.g. a 10-minute tool timeout, or Ctrl-C.
3. The session-scoped `dynamo_local` fixture leaves its container running
   (`uptime_dynamo_pytest_<pid>_<hash>`, observed still `Up` 20 minutes after its owning python
   process was gone).
4. The **next** gate run stalls in pytest — four python processes at ~0% CPU for 20 minutes, no
   progress — and only recovers after `docker rm -f` on the orphans.

## Why it matters more than it looks

The symptom is not "a stray container". The symptom is **the next run hangs with no diagnosis**,
and the cause is invisible unless you happen to run `docker ps -a` and recognise the name pattern.
An engineer who does not already know this defect will read a 20-minute stall as a broken test
suite.

It is the same family as STORY-080 (dev_db CLI port collision, sprint-44 gate contention): the test
harness leaving state behind that poisons the next invocation.

## Fix direction (SCRIPT rung, per the enforcement ladder — this is a retro routing call already made)

**The fixture should reap containers matching its own name pattern whose owning PID is dead, at
session start.** That is a script-level fix, not a prose warning in a runbook.

Sketch of the shape, to be settled at refinement:

- The container name already encodes the owning PID (`uptime_dynamo_pytest_<pid>_<hash>`), so
  liveness is checkable without extra bookkeeping.
- Reap at **session start**, not at teardown — teardown is exactly what does not run when the
  process is killed.
- Reap only containers matching the fixture's own pattern. **Never** `docker rm -f` broadly; a
  developer's unrelated containers are not this fixture's business.

## Refinement should settle

1. **PID liveness across platforms.** The check must work on Windows, where this was observed.
   Decide whether to test the PID directly or to use a container label plus an age bound.
2. **Reap-at-start vs. reap-at-start-and-atexit.** `atexit` helps for clean exits and does nothing
   for `SIGKILL`; start-time reaping covers both but only on the *next* run.
3. **Whether it lands with STORY-179.** Same fixture, same "the container harness is not
   trustworthy" root. The backlog notes they are likely one story's work together — but they are
   *separate defects* and the shown-RED for each must be separate, whichever way it is packaged.
4. **How to prove it red.** Killing a real pytest run mid-flight is awkward to automate; a
   plausible proof is to create a container matching the pattern with a dead PID embedded and show
   the fixture reaps it at session start, plus a control showing it does NOT reap a live-PID one.
   That control is the half that matters — a reaper that removes too much is worse than none.

## Not in scope

STORY-179's port-allocation and readiness-probe defects (same fixture, different failures — decide
packaging at planning, not by widening this story). Any change to what the tests assert.
