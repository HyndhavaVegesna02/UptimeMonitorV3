---
id: STORY-179
title: dynamo_local picks an ephemeral port Docker maps but Windows won't route, and the readiness probe cannot detect it
type: defect
points: null
status: draft
filed: 2026-07-29
sprint: null
---

## Context

Two defects in `scripts/dynamo_local.py`, root-caused 2026-07-29 while running STORY-146's gate.
Together they cost ~1h of sprint time and made a healthy test suite look hung.

**Re-verified live 2026-08-13 at the equilibrium refinement pass — both are still present, in the
same functions, unchanged.**

They are filed as one story because they are the same failure end-to-end: the first breaks the
container, the second guarantees nobody finds out.

## Defect 1 — port allocation is racy and Windows-hostile

`_free_tcp_port()` (`scripts/dynamo_local.py:39`) binds `("127.0.0.1", 0)`, reads the OS-assigned
ephemeral port, **closes the socket**, then hands the bare number to `docker run -p <port>:8000`
(`:124`).

Two problems compound:

1. **The port is unowned between close and bind.** Anything may take it in the gap.
2. **On Windows it lands in the dynamic range** (observed: 49177; range 49152–65535), where WinNAT
   hands out and reserves ports. Docker then creates a mapping that **`docker ps` displays but that
   never routes**: container `Up`, logs clean, every request hangs forever.

## Defect 2 — the readiness probe cannot detect defect 1

`wait_for_dynamo()` does a bare `GET /` over `http.client` and **returns on ANY response**:

```python
conn = http.client.HTTPConnection("127.0.0.1", port, timeout=1.0)
conn.request("GET", "/")
res = conn.getresponse()
res.read()
return
```

Docker's port proxy **accepts the TCP connect**, so the probe goes green and every real DynamoDB
call then blocks. A check that proves *connectability* but not that the service *answers* is a
check that green-lights a broken container.

This is the load-bearing half. Defect 1 is a bad-luck bug; defect 2 is what turns it into an hour.

## Evidence (measured, not theorised)

- `boto3.list_tables()` against the fixture's own container **timed out at 25s**.
- A standalone container on **fixed port 8021** answered in **0.90s**.
- With `DYNAMO_ENDPOINT_URL` pointed at the fixed port, pytest ran **539 tests in 22.46s** — against
  a **241.52s "green" baseline that was silently absorbing these timeouts test-by-test**.

**The suite is ~11× faster than the recorded numbers claim.** Every duration in the sprint records
taken before this is discovered is inflated by absorbed timeouts.

## Why this is tier-1 for equilibrium

The point of the mechanical floor is that you can stop watching it. Both halves of this defect
attack that directly: the container lies about being healthy, and the probe built to catch that
lies too. It is the same class as a gate that exits 0 having run nothing.

## Fix direction (SCRIPT rung, per the enforcement ladder)

1. **Allocate from a fixed non-ephemeral range with retry-on-bind-failure**, or let Docker choose
   and **read the port back from `docker port`** rather than pre-selecting one.
2. **Make `wait_for_dynamo` do a real `ListTables` call** rather than `GET /`.
3. **Fail fast with a clear message when a mapped port does not answer** — the diagnosis, not just
   the timeout.

## Refinement should settle

1. **Which allocation strategy**, and whether `docker port` read-back removes the race entirely
   (it does not remove the WinNAT range problem — a fixed low range does).
2. **How to prove the fix.** The natural shown-RED is to force a WinNAT-range port and show the
   new probe fails fast where the old one returned green. Verify that is reproducible on this
   machine before committing to it as the proof.
3. **Whether to take STORY-173 in the same story.** Same fixture, same "the container harness is
   not trustworthy" root, and the backlog already notes they are likely one story's work together.
   Deciding this is a planning question, not an implementation one.
4. **Re-baseline the recorded suite duration** once fixed, and say plainly in the story that
   earlier timings were inflated — otherwise the improvement reads as a regression in test count.

## Not in scope

Any change to what the tests assert. The DoD command list. STORY-213's pagination flake (a
different symptom in the same fixture, but a distinct cause).
