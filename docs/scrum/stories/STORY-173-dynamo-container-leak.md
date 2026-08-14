---
id: STORY-173
title: A killed pytest run leaks its DynamoDB Local container and stalls the next run
type: defect
points: 2
status: ready
refined: 2026-08-14   # sprint-72 planning; placement decided on measurement below. LOCKED into sprint 72 by the PO on 2026-08-14.
filed: 2026-07-28
sprint: 72   # story 3 of 4
---

## Context

Observed 2026-07-28 during the sprint-62 baseline gate, **twice**. Re-confirmed 2026-07-29 while
root-causing STORY-179, where two leaked containers needed a manual `docker rm -f`.

**Re-verified 2026-08-14 (sprint-72 planning): `scripts/dynamo_local.py` and
`backend/tests/conftest.py` still contain no reaping logic of any kind** — a grep for `reap`,
`orphan`, `getpid`-based liveness and container-removal patterns returns only the normal-exit
`stop_container` teardown (`conftest.py:95`, `dynamo_local.py:314-316`). STORY-179 rewrote the port
allocation and readiness probe in this file and did **not** touch the leak.

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
suite. Same family as STORY-080 (dev_db CLI port collision): the harness leaving state behind that
poisons the next invocation.

## The code, measured at sprint-72 planning (2026-08-14)

- The name carries its owner: `unique_container_name()` →
  `f"{prefix}_{os.getpid()}_{uuid.uuid4().hex[:8]}"`, prefix `uptime_dynamo_pytest`
  (`scripts/dynamo_local.py:95-97`). Liveness is therefore checkable with no extra bookkeeping.
- Normal-exit teardown already exists and is not the problem (`stop_container`,
  `dynamo_local.py:314-316`; called from `conftest.py:95`). It is exactly what does not run on a
  kill.

### *** The placement trap, and the decision ***

`resolve_dynamo` (`dynamo_local.py:319-362`) resolves in three steps, and **step 1 returns before
any container code**:

```
1. DYNAMO_ENDPOINT_URL set  -> return DynamoPlan(source="env")      # dynamo_local.py:335-337
2. docker available         -> spawn a container
3. otherwise                -> skip
```

**The gate environment sets `DYNAMO_ENDPOINT_URL`** (a fixed-port container, per `CLAUDE.md` and
STORY-179's workaround). So a reaper placed after that short-circuit **would never run in the
configuration the gate actually uses** — which is STORY-179's AC8 trap verbatim: with the URL set,
none of the changed code executes, and the run stays green through total breakage.

**Decision: reap BEFORE the step-1 short-circuit.** A container leaked by a previous killed run is
leaked regardless of how *this* run obtains its endpoint, so the reap is not conditional on the
plan. It must be guarded by `docker_available()` and must never raise (AC4) — a developer with no
Docker who sets `DYNAMO_ENDPOINT_URL` at a remote endpoint must be unaffected.

## Acceptance Criteria

- [x] **AC1 (dead-PID containers are reaped at session start)** — a container matching the
      fixture's own pattern whose embedded PID is no longer alive is removed before the run
      proceeds. Shown RED against current code.
- [x] **AC2 (*** the control, and it is the half that matters ***: it never reaps too much)** — a
      reaper that removes too much is worse than none. Three negatives, each with its own test:
      (a) a pattern-matching container whose PID is **alive** is NOT removed; (b) a container that
      does not match the pattern is NEVER removed — named explicitly because the gate's own
      long-lived container is `uptime_dynamo_8021`, outside the pattern, and destroying it would
      break the gate mid-run; (c) no broad `docker rm -f` and no wildcard prune appears in the
      diff. AC2(a) and AC2(b) are shown RED against a naive prefix-only reaper.
- [x] **AC3 (it runs in BOTH configurations)** — the reap executes with `DYNAMO_ENDPOINT_URL` set
      **and** unset. Proven by a test that calls `resolve_dynamo` with an injected reaper and
      asserts it was invoked in both cases. This AC exists because the gate only ever runs the
      first of those two.
      **The injection seam must be added and named**: `resolve_dynamo` today is
      `resolve_dynamo(*, env, docker_available, spawn_container)`
      (`scripts/dynamo_local.py:319-323`) and has **no reaper parameter**. Follow the existing
      convention of the three it already has — a keyword-only `Callable | None = None` that falls
      back to the module-level implementation when omitted, so production callers are unchanged
      and only tests inject. State the parameter name, its default and its contract in the
      docstring.
- [x] **AC4 (it degrades to a no-op, never a failure)** — Docker absent, `docker` slow or erroring,
      or a container that refuses removal must leave the run proceeding normally with at most a
      note. Proven by injecting a failing/absent docker callable. The reaper must not add a
      material delay to a Docker-less run — record the measured cost when Docker is present.
- [x] **AC5 (PID liveness is decided on Windows, and undetermined means DO NOT reap)** — the
      liveness check is specified and tested on Windows, where the defect was observed. If
      liveness cannot be determined for a given container, the conservative branch is taken: it is
      **left alone**. A named test covers the undetermined case. If an age bound is used instead of
      or alongside PID liveness, the bound is justified and tested at both edges.
      **Two Windows traps, both measured at pre-lock verification (2026-08-14) on throwaway
      processes — do not re-derive them, and do not assume the POSIX shapes:**
      1. `os.kill(pid, 0)` does **not** terminate the process (`signal 9` does), and on a dead or
         nonexistent PID it raises a bare **`OSError` with `winerror == 87`, NOT
         `ProcessLookupError`**. A reaper catching only `ProcessLookupError` therefore **raises**,
         violating AC4. Branch on `winerror`, and test it.
      2. A still-open process handle makes a **dead** PID read as **alive**. That is a reason to
         keep the conservative branch, and an argument for pairing liveness with an age bound
         against PID recycling.
- [x] **AC6 (the story leaks nothing itself)** — `docker ps -a` verified before and after the
      story's own test runs; no container matching either pattern survives. Normal-exit teardown
      still removes the fixture's container (existing behaviour unbroken).
- [x] **AC7 (gate)** — the DoD commands the diff can affect exit 0 at the story's final HEAD, with
      pass/skip counts recorded, and the run repeated in **both** `DYNAMO_ENDPOINT_URL`
      configurations for the reasons in AC3. Run the wiki sweep after the last commit and take
      what it returns; do **not** pre-declare a blast radius. For information only:
      `scripts/dynamo_local.py` is in **no** article's `code_refs`, while
      `backend/tests/conftest.py` is a `code_ref` of `demo-engine.md` and `persistence-adapters.md`
      (both `verified`, `tier: map`). Choose placement on engineering grounds and record which
      files were touched.

## Open Questions

None. The filing's four questions are settled above: placement is before the env short-circuit
(measured trap); reap-at-start only, since `atexit` does nothing for the kill case that defines
this defect; packaging is standalone (STORY-179 has landed, and its shown-REDs were separate as
the filing required); and the proof shape is AC1 + AC2's three negatives, which is the "create a
dead-PID container and a live-PID control" sketch made explicit.

## Not in scope

STORY-179's port-allocation and readiness-probe work (landed sprint 71). Any change to what the
tests assert. Reaping containers this fixture did not create.

## History

- 2026-07-28: filed after two occurrences during the sprint-62 baseline gate.
- 2026-08-13: re-verified at the equilibrium refinement pass — still no reaping logic.
- 2026-08-14: **refined at sprint-72 planning, estimated 2.** The placement question is settled by
  measurement rather than preference: `resolve_dynamo` returns at `dynamo_local.py:335-337` when
  `DYNAMO_ENDPOINT_URL` is set, which is the gate's own configuration, so a reaper placed after it
  would be dead code exactly where it is needed — STORY-179's AC8 lesson applied forward. The
  estimate sits at 2 because the reap itself is small and the weight is in AC2's three negatives.
- 2026-08-15: **Implemented.** `reap_dead_pytest_containers(*, docker_available, list_containers,
  pid_is_alive, remove_container)` and `_pid_is_alive(pid)` land in `scripts/dynamo_local.py`.
  `resolve_dynamo` gains a `reap` keyword-only param (default `reap_dead_pytest_containers`),
  called unconditionally as its first action — before the `DYNAMO_ENDPOINT_URL` short-circuit
  (AC3, proven invoked in both configurations). Matching is a full-string regex
  (`_PYTEST_CONTAINER_NAME_RE`) against `unique_container_name()`'s exact shape, never a
  prefix/substring — AC2(b)'s guard against touching `uptime_dynamo_8021`. A container is removed
  only when `pid_is_alive` returns `False`; `True` or `None` (undetermined) leaves it alone (AC5).
  The whole function is wrapped so Docker absence/errors and a refused removal degrade to a no-op,
  never a raise (AC4); measured cost against a real Docker daemon (this machine): **~0.1s** for a
  single `docker ps -a --filter` round trip.
  **AC1 was shown RED against current code first** (`AttributeError: module 'dynamo_local' has no
  attribute 'reap_dead_pytest_containers'`) before any production code existed.
  **AC2(a)/(b) were shown RED against a naive prefix-only reaper**, defined only inside the test
  module (never shipped): it removed BOTH a live-PID container and the gate's own
  `uptime_dynamo_8021`, which the real implementation's exact-match + confirmed-dead-only design
  does not.
  **AC4 and AC5 were each mutation-proofed**: the try/except scaffolding was stripped
  (3/5 AC4 tests went RED), and the Windows `winerror == 87` branch was reduced to a POSIX-only
  `except ProcessLookupError` (3/6 AC5 tests went RED); both mutations were reverted with `git diff`
  verified empty before committing the real implementation.
  **AC5's Windows facts were independently re-confirmed, and one nuance was added beyond the
  brief**: a dead/never-existed PID reliably raises `OSError(winerror=87)`, but a PID whose
  process WAS spawned and waited on by the SAME process doing the liveness check still reads
  alive after exit (`tasklist` confirms it is gone from the OS process table; `os.kill` raises
  nothing) — an artifact of that process's own retained handle, not of the reap's real code path
  (the reaper never holds a handle to the PID it is checking; a PID checked from an unrelated
  process correctly reads dead). Both shapes are pinned as separate named tests rather than only
  cited.
  **AC6 end-to-end**: a genuine container was spawned by a separate helper process and left
  running (no mock), then removed by the real `reap_dead_pytest_containers()` from this process —
  the story's own reproduction, reproduced and fixed against real Docker, not stand-ins.
  `docker ps -a` carried no `uptime_dynamo_pytest_*` container before or after any test run in
  this story, and the gate's own `uptime_dynamo_8021` stayed `Up` throughout.
  The stale STORY-179 comment at `dynamo_local.py:41-61` (which named STORY-173 as "NOT in this
  sprint" and described the leaked-port-slot exposure as a standing limitation) was updated to
  state the reaper narrows — but, by AC5's own conservative design, does not zero out — that
  exposure.
