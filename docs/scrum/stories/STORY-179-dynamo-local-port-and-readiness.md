---
id: STORY-179
title: dynamo_local picks an ephemeral port Docker maps but Windows won't route, and the readiness probe cannot detect it
type: defect
points: 3
status: ready
filed: 2026-07-29
refined: 2026-08-13
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

## Refinement decisions — settled 2026-08-13 at sprint-71 planning

**1. Allocation strategy: a fixed non-ephemeral range with retry, AND `docker port` read-back.**
Neither alone is sufficient, and the reason matters. `docker port` read-back removes the *race*
(Docker owns the bind, so there is no unowned gap) but **not** the WinNAT problem — Docker would
still select from the dynamic range on Windows. A fixed low range fixes the *range* problem but
keeps a smaller race. Take both: request from a fixed range, let Docker bind it, read the mapping
back and verify it matches, retry on bind failure. **Decision 2 is the backstop for whatever still
slips through**, which is why that half is the load-bearing one.

**2. Shown-RED: prove the probe defect with a non-DynamoDB listener, NOT by reproducing WinNAT.**
This is the key refinement finding. Reproducing a WinNAT-reserved port on demand is not reliably
achievable, and an AC that depends on it would block the story by construction. But the probe
defect does not need it: point `wait_for_dynamo` at **any** plain TCP listener that accepts and
never answers DynamoDB. The current probe returns green (it returns on any response); the fixed
probe must fail fast. That is deterministic, machine-independent, and tests the actual defect.
For the allocation half, prove the **property** rather than the failure: assert the chosen port is
outside the Windows dynamic range (`< 49152`), which reds against the current `_free_tcp_port()`.

**3. STORY-173 stays a separate story and is NOT in this sprint.** Plan verification refuted the
assumed coupling: `_free_tcp_port()` (`:39-45`) and `unique_container_name()` (`:48-50`) take no
shared input and are called independently at `:123-124`, so this story cannot change the pattern
173's reaper matches on. **The real coupling runs the other way** — a leaked container from a dead
PID permanently holds a slot in the fixed range this story introduces. That is a known, accepted
limitation of shipping 179 without 173, and AC6 records it rather than hiding it.

**4. Re-baseline the recorded suite duration** — AC7.

## Acceptance criteria

**AC1 — the allocated port is outside the Windows dynamic range.** Port selection draws from a
fixed non-ephemeral range and never returns a port ≥ 49152. Pinned by a test that **is shown RED
against the current `_free_tcp_port()`** (which returns OS-assigned ephemeral ports).

**AC2 — the mapping is verified, not assumed.** After `docker run`, the actual published port is
read back (`docker port`) and compared with the requested one; a mismatch is an error naming both.

**AC3 — bind failure retries rather than dies.** A port already in use causes a retry within the
range, bounded, with the exhaustion case raising a message naming the range and the attempts.

**AC4 — `wait_for_dynamo` proves the service ANSWERS, not merely that it accepts.** It issues a
real DynamoDB `ListTables` call. Pinned by a test that stands up a plain TCP listener which accepts
and never answers: the current probe returns green against it, the new one must fail. **Shown RED
by running the new test against the old probe.**

**AC5 — a mapped-but-dead port fails fast with a diagnosis.** On timeout the error states that the
port was mapped but did not answer, and names the port — the sentence that would have saved the
hour this defect cost. Not a bare `TimeoutError`.

**AC6 — the interaction with STORY-173 is recorded in the code, not just here.** A comment at the
allocation site states that a leaked container from a dead PID holds its slot in the fixed range
until STORY-173 lands. This is a known limitation being shipped deliberately.

**AC7 — the suite duration is re-baselined and the inflation stated.** The story records the
measured before/after wall-clock and says plainly that earlier recorded timings were inflated by
absorbed timeouts (evidence above: 241.52s vs 22.46s), so the change does not read as a regression.

**AC8 — the DoD gate is green in BOTH configurations.** With `DYNAMO_ENDPOINT_URL` set (the gate
env) **and** with it unset and Docker available. Plan verification proved the first alone is
worthless here: `resolve_dynamo` short-circuits at `dynamo_local.py:113-115` and **none** of the
functions this story changes is called, so a URL-set-only run stays green through total breakage.

## Not in scope

Any change to what the tests assert. The DoD command list. STORY-173's container leak (separate
story; see decision 3). STORY-213's pagination flake — a different symptom, distinct cause.
