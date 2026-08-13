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

`_free_tcp_port()` (as it stood at filing time, `scripts/dynamo_local.py:39`) binds
`("127.0.0.1", 0)`, reads the OS-assigned ephemeral port, **closes the socket**, then hands the
bare number to `docker run -p <port>:8000` (`:124`). **Citation note (fix round, 2026-08-13): this
shape no longer exists in the file** — `start_container()` (`scripts/dynamo_local.py::start_container`)
now draws from `_candidate_ports()` and lets `docker run` perform the actual bind; the old
`_free_tcp_port()` function was renamed to `_candidate_port_for_test_injection`
(`scripts/dynamo_local.py::_candidate_port_for_test_injection`) and is now called only from
`resolve_dynamo`'s test-injection branch. See History below for what replaced it.

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
assumed coupling: `_free_tcp_port()` (as it stood at planning time, `:39-45`) and
`unique_container_name()` (`:48-50`) take no shared input and are called independently at
`:123-124`, so this story cannot change the pattern 173's reaper matches on. **Citation note (fix
round, 2026-08-13): those line numbers describe the pre-implementation file.** In the current file,
the equivalent independence holds at the equivalent call site:
`unique_container_name()` (`scripts/dynamo_local.py::unique_container_name`) is called at
`resolve_dynamo`'s `name = unique_container_name()`, and the port draw now lives inside
`start_container()` (`scripts/dynamo_local.py::start_container`) via `_candidate_ports()`
(`scripts/dynamo_local.py::_candidate_ports`) — still no shared input between the two. **The real
coupling runs the other way** — a leaked container from a dead
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
worthless here: `resolve_dynamo` short-circuits at the `env_endpoint` check
(`scripts/dynamo_local.py::resolve_dynamo`, currently `:335-337`; cited `:113-115` at planning
time and re-derived here at the fix round, 2026-08-13, after both the story's own implementation
and its fix round moved the code) and **none** of the functions this story changes is called, so a
URL-set-only run stays green through total breakage.

## Not in scope

Any change to what the tests assert. The DoD command list. STORY-173's container leak (separate
story; see decision 3). STORY-213's pagination flake — a different symptom, distinct cause.

## History

- 2026-08-13: implemented. `_free_tcp_port()` now draws from a fixed, non-ephemeral range
  (`_PORT_RANGE_START`/`_PORT_RANGE_END` = 18000–18099, `scripts/dynamo_local.py`), pinned by
  `test_free_tcp_port_stays_outside_windows_dynamic_range` (renamed at the fix round below to
  `test_candidate_port_for_test_injection_stays_outside_windows_dynamic_range`), shown RED against the pre-fix function
  (measured: port 61867, an OS-assigned ephemeral port, always >= 49152 on this machine — samples
  57634..57643 and 61867 across two separate runs). `start_container()` now requests a port from
  that range, lets `docker run` perform the actual bind, reads the mapping back via `docker port`,
  and verifies it matches (AC2) with a bounded (`_MAX_BIND_ATTEMPTS = 20`), retrying bind-failure
  loop (AC3) — both pinned by mocked-subprocess tests
  (`test_start_container_raises_on_port_mapping_mismatch`,
  `test_start_container_retries_on_bind_failure_then_succeeds`,
  `test_start_container_raises_after_exhausting_retry_budget`). `wait_for_dynamo()` now issues a
  real `ListTables` call via boto3 and additionally checks the response actually carries a
  `TableNames` key (botocore's JSON-protocol parsing turned out to be lenient enough that a bare
  "200 OK" with no DynamoDB body still parses as an empty success — discovered while writing the
  AC4 test, so the probe checks the one key every real response carries, not just call-succeeded).
  Pinned by `test_wait_for_dynamo_rejects_a_non_dynamo_answer`, shown RED against the pre-fix probe
  (measured: a plain TCP listener that accepts and replies with a generic non-DynamoDB HTTP 200
  made the old probe return green in 0.02s). AC6's limitation comment lives at the `_PORT_RANGE_*`
  declaration site in `scripts/dynamo_local.py`.

  **AC7 — re-baselined, honestly.** The story's own discovery evidence above (25s timeout vs
  0.90s fixed-port; 539 tests in 22.46s vs a 241.52s inflated baseline) stands as the ORIGINAL
  measurement of the defect's cost and is not re-derived here — the refinement decision already
  established that reproducing a WinNAT-reserved port on demand is not reliable, and that held
  again today: two direct `resolve_dynamo()` timing probes and two full-suite runs (old code vs
  fixed code, `DYNAMO_ENDPOINT_URL` unset, Docker up) all completed in single-digit-to-80s range
  with NO hang on either side (old: 800 passed + 5 expected new-API failures in 77.29s; fixed: 805
  passed in 79.99s). So this specific rerun shows no wall-clock regression from the fix, and it
  does NOT reproduce the hang either direction — consistent with the defect being real but
  intermittent, not a claim that the fix made things faster today. What IS newly verified: the gate
  env (`DYNAMO_ENDPOINT_URL` set to the manually-started fixed-port container, `REQUIRE_DYNAMO=1`)
  runs the full suite in 49.93s at 805 passed / 0 skipped — consistent with the CORRECTED baseline
  the story argues for, not the inflated one, and the fix removes the failure mode (unowned port
  race + a probe that cannot detect a mapped-but-dead port) that produced the original 241.52s
  regardless of whether any single rerun happens to hit it.

  Quality/spec review returned FAIL/FIX_REQUIRED with 2 CRITICALs, 2 MAJORs, and several MINORs.
  See the fix round entry below.

- 2026-08-13, fix round: **CRITICAL 1** — `wait_for_dynamo`'s boto3 client had no
  `botocore.config.Config`, so a single `list_tables()` call was bounded only by botocore's
  defaults (60s connect, 60s read, up to 10 legacy retries), letting one call overrun
  `timeout_seconds` by up to two orders of magnitude (measured before the fix: a silent
  accept-never-answer peer took 626.24s against a 3.0s budget; a closed port took 46.41s). Fixed
  by passing `Config(connect_timeout=1.0, read_timeout=1.0, retries={"max_attempts": 1})`
  (measured after: silent peer 4.85s, closed port 4.85s). Also tightened
  `test_wait_for_dynamo_rejects_a_non_dynamo_answer`'s assertion from `elapsed < 10.0` (pinned
  nothing) to `elapsed < timeout_seconds + 3.0`, shown RED against the pre-fix client (3 of 8 runs
  failed, 14–28s) and green after (6/6 runs, ~3.7–4.1s).

  **CRITICAL 2** — `test_start_container_retries_on_bind_failure_then_succeeds` asserted only
  `isinstance(port, int)` (vacuous by construction) and pinned nothing about the actual port
  source. Replaced it with an assertion that every requested `-p` port and the returned port fall
  inside the fixed range. Proved the pin meaningful by mutating `start_container()` to draw from
  OS-assigned ephemeral ports (defect 1 verbatim) in a scratch edit: suite went RED (1 failed —
  "requested port 50073 outside the fixed range 18000-18099"); reverted, green again.

  **MAJOR 1** — the timeout message claimed "the port is mapped, not dead-on-arrival"
  unconditionally, even against a port nothing was ever listening on (measured: a closed port
  raises `ConnectTimeoutError`, never a connection). `wait_for_dynamo` now tracks whether any
  attempt actually established a connection and words the two cases separately; the
  never-connected case states plainly that "nothing is listening" cannot be ruled out. New test
  `test_wait_for_dynamo_does_not_claim_mapped_when_nothing_ever_listened`, shown RED against the
  old unconditional message.

  **MAJOR 2** — `start_container`'s retry loop retried every non-zero `docker run` exit, so a
  daemon-down/image-pull/disk failure was retried `_MAX_BIND_ATTEMPTS` times and then reported as a
  false "could not bind ... to any port in the fixed range" diagnosis. Added `_is_bind_failure`
  (matches "already allocated" / "bind for") so only bind conflicts retry; anything else re-raises
  immediately with Docker's own output. New test
  `test_start_container_reraises_non_bind_docker_failure_immediately`, shown RED against the old
  catch-all retry.

  **MINORs** — `_docker_port_mapping`'s `int(port_str)` now raises a contextual `RuntimeError`
  instead of a bare `ValueError` on malformed `docker port` output, and `start_container` now stops
  the container on that failure path too (previously only the mismatch branch cleaned up); two new
  tests. `_MAX_BIND_ATTEMPTS = 20` and the STORY-173 leak-quantification comment now carry a stated
  reason instead of an unrecorded claim. The port-range clear-check now records the exact `netsh
  interface ipv4 show excludedportrange protocol=tcp` command and this run's output (exclusions
  only at 50000-50059 and 52680-53228). `_free_tcp_port()` renamed to
  `_candidate_port_for_test_injection` (it never verified freeness; its only remaining caller is
  `resolve_dynamo`'s test-injection branch). The `monkeypatch.setattr(dynamo_local.subprocess,
  "run", ...)` pattern (which mutated the real stdlib `subprocess` module in place) was replaced
  with rebinding the module-level name `dynamo_local.subprocess` to a narrow `SimpleNamespace`, in
  all six occurrences. This story's own stale citations above (AC8, Context, decision 3) were
  re-derived against the current file.

  Full `test_dynamo_local.py` suite green throughout (14 passed, 2 Docker-gated deselected in this
  quick pass; see gate runs below for the Docker-inclusive count). `docker ps -a` shows no
  `uptime_dynamo_pytest_*` residue after this round.
