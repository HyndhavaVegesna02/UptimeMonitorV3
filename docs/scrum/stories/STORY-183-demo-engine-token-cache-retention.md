---
id: STORY-183
title: Demo engine — bound the token cache by RETENTION, not by consume-on-first-poll
type: defect
---

## Context

STORY-180 AC4 bounded `_DemoHTTPServer.results` by changing the poll handler from
`results.get(token)` to `results.pop(token, None)` (`tools/demo_engine/server.py:124`). That closed
the common path and its test proves it — but it is a **partial** bound, and it narrowed the wire
protocol as a side effect. Both were found by the orchestrator while verifying STORY-180 against
its AC7 ("no wire-contract change"), and recorded on the sprint-63 board under
`story_gates[STORY-180].ac4_risk_check` rather than fixed there: STORY-180 was already Done and
gated, sprint scope was frozen, and its AC4 test now pins *consume* semantics, so a different bound
needs its own AC rather than a quiet test edit.

**Neither problem is a defect in production code.** `tools/demo_engine/` never ships — it cannot
enter the production image (dossier §4; the package lives outside `backend/src/` on purpose).
The cost lands on the demo run, which is the only substitute for vendor data since the Dynatrace
trial expired.

### Problem 1 — the bound does not hold for an abandoned token

A token is written at `server.py:104` (immediately before the 202 response) and removed only by a
successful poll at `:124`. Any query that is executed but never polled therefore leaks its entry
**for the process lifetime** — the exact failure mode AC4 exists to prevent.

That path is reachable, not hypothetical:

- `grail_executor.py:110-111` raises `GrailQueryError` if the poll request itself fails, so the
  token is orphaned and nothing ever collects it.
- `composition/pull_loop.py:200-207` logs the failed cycle with a traceback and the loop continues
  to the next cycle — so the process keeps running, keeping the orphan alive.
- This server has a demonstrated history of transient socket faults on Windows: the body-drain
  comment at `server.py:75-80` documents an intermittent `ConnectionResetError`/`httpx.ReadError`
  reproduced live against the 401 branch. A read timeout on the poll leg produces exactly the
  orphan above.

One orphan per faulted cycle is a slow leak, and it is unbounded in time.

### Problem 2 — a repeat poll now 404s, which the real vendor does not do

Real Grail retains a completed result and serves it to a repeat poll of the same
`request-token` within a retention window. This engine now answers the second poll with
`404 unknown request token` (`:125-127`). Nothing in this repo re-polls today —
`grail_executor.py:100-137` returns at the first `state == "SUCCEEDED"` (`:127-128`) and the engine
resolves every query synchronously, so AC7 holds and STORY-180 is not in doubt — but the demo
engine's entire purpose is wire fidelity, and this is a divergence a future consumer (or a manual
`curl` while debugging STORY-182's run) would meet as a puzzling 404.

### Why one change fixes both

A **retention-based** bound is what the vendor itself does: keep a completed result for N minutes,
then evict it whether or not it was polled. That bounds the abandoned-token path Problem 1 leaves
open, and restores the repeat-poll fidelity Problem 2 lost — a strict improvement on both axes over
consume-on-read.

## Description

Replace the consume-on-first-poll bound with a retention bound on `_DemoHTTPServer.results`:
entries carry their insertion instant and are evicted once older than a module-level retention
constant (a FIFO cap is an acceptable alternative if simpler, but retention is the closer analogue
of the vendor's behaviour). A repeat poll inside the retention window returns the same records; a
poll after eviction returns the existing `404 unknown request token`.

Follow the demo engine's existing conventions: `tools/` only, no file under `backend/src/` changes,
and the retention constant is declared once with its reason stated at the literal.

## Acceptance Criteria

- [ ] **AC1 (the abandoned-token leak is bounded)** — an entry that is never polled is evicted once
      it passes the retention window. A test proves it with an injected clock or an explicitly
      small retention value — **not** by sleeping in real time.
- [ ] **AC2 (repeat poll inside retention is served, restoring vendor fidelity)** — polling the same
      `request-token` twice inside the retention window returns the SAME records both times, with
      `state: "SUCCEEDED"` and HTTP 200 each time. This is the assertion that would have failed
      before this story, and it replaces STORY-180's `test_results_cache_is_evicted_after_being_polled`,
      whose contract is the opposite. **That replacement is stated in the story evidence** so the
      change is never mistaken for a silently weakened test.
- [ ] **AC3 (eviction after retention still 404s)** — a poll of a token evicted by retention returns
      `404 {"error": "unknown request token"}`, unchanged from today.
- [ ] **AC4 (the bound is asserted, not asserted-about)** — a test drives N executes without polling
      and asserts `len(server.results)` stays bounded, so the fix cannot regress to unbounded growth
      while staying green.
- [ ] **AC5 (no wire-contract change)** — STORY-148's proven contract does not move: the seven row
      fields, the nanosecond scale conversion, both query grammars, the async execute/poll protocol,
      and the `Api-Token ` scheme-prefix check are unchanged in behaviour. Auth is still checked
      BEFORE the cache is touched (`server.py:112` before `:124`), so an unauthenticated poll can
      never affect cache state.
- [ ] **AC6 (still zero production code)** — `git diff` for this story touches no file under
      `backend/src/`.
- [ ] **AC7** — the DoD gate commands the diff can affect exit 0.

## Open Questions

None. The retention-vs-FIFO choice is an implementation decision, deliberately left to the
implementer by AC1's wording; retention is the recommendation because it also satisfies AC2.

## History

- 2026-07-29: filed by the orchestrator while verifying STORY-180's AC4 against AC7 during sprint
  63. Recorded on the board (`story_gates[STORY-180].ac4_risk_check`) and NOT fixed in-story: the
  story was already gated and sprint scope was frozen. Estimated 1 point — the change is small and
  the tests are the substance. **Sequencing recommendation: land it with or before STORY-182**
  (sprint 64), whose long-running loop run is the first time either problem can actually bite.
