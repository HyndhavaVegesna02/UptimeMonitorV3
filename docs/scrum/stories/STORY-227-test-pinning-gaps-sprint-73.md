---
id: STORY-227
title: Six test-pinning gaps found at sprint-73 review — assertions that pass today for reasons that are not the reason we think
type: chore
points: null
status: draft
refined: null
sprint: null
---

## Where this came from

Filed at the **sprint-73 review** on PO instruction ("file for fixing the minors"). Six
quality-review findings across all three sprint-73 stories, grouped because they are one kind of
problem: **a test that passes, but whose green does not mean what a reader would assume.** None is a
failing test; none blocked acceptance.

Grouped rather than filed as six stories deliberately — the equilibrium directive is explicit that
filing is not free, and sprint 73 took the backlog 14 → 11. Six separate entries would have undone
that.

## The six

### 1. `backend/tests/test_zone_layout.py:238` — the route table pins paths, not methods
`_EXPECTED_ROUTE_TABLE` asserts the set of route **paths**. A change of `GET` → `POST` on a
surviving route would pass. This was adequate for STORY-155b's AC6 (which asked only that the
sample-mode route be gone and no other route change) and the reviewer said so — but the test reads
like a full route-table pin and is not one. **Highest value of the six.**

### 2. `backend/tests/test_pull_loop.py:1080` — the AC1 literal omits one field
STORY-155b's observation-parity literal compares ten `SignalObservation` fields and omits
`response_status_code`. There is none in this harness either way, so nothing is wrong today; it is a
hole in what is otherwise a byte-level pin, and this is the test that proves the live ingest path
was unchanged by the removal.

### 3. `backend/tests/test_dynamo_seed.py` — NULL vs absent is asserted nowhere
`item_without_group.get("group") is None` cannot distinguish "written as a DynamoDB NULL" from
"attribute absent". Both `seed_dynamo.py`'s comment and `persistence-adapters.md`'s Fact **claim the
NULL form specifically** — so a claim is being made that no test checks.

### 4. `frontend/src/AppShell.test.tsx:172-174` — the settle barrier couples unrelated fixtures
The top-bar test waits on the Approvals badge, so a change to `FIXTURE_PROPOSALS` fails a test about
the top bar. Documented in the comment; still a false-failure source.

### 5. `backend/tests/test_statuspage_adapter.py:98-123` — near-duplicate of `:36-65`
Same publisher, same `OPERATIONAL` `StatusChange`, strictly weaker payload assertion. Only the
`StatusChange.model_fields` pin is new — and that pin is the valuable part (it is what makes
STORY-147's AC4 structural rather than incidental). Roughly six lines once the duplication goes.

### 6. `backend/tests/test_zone_layout.py:253` — a test name shaped by a grep
`test_the_removed_sample_route_is_gone_and_no_other_route_changed` is an artifact of STORY-155b's
AC5, which required zero matches for `sample_mode` in `backend/` — the implementer's original name
matched its own grep and had to be renamed mid-story. The name should read for a human, while still
zeroing that grep.

## Why this is worth doing at all

Five of the six are small. The reason to do them together is that **three of them (1, 2, 3) are
tests standing in for claims made elsewhere** — a route-table pin, a "provably unchanged ingest
path", and a wiki Fact about DynamoDB NULLs. The project's whole staleness discipline rests on
tests being the thing that cannot rot; a test that pins less than its name implies is the same
failure as a stale wiki Fact, one layer down.

## Acceptance Criteria

*(To be written at refinement. Each of the six needs the same shape: state what the test currently
proves, what it should prove, and show the strengthened assertion RED against the current
behaviour before it goes green — a strengthened test that was never seen to fail proves nothing.)*

## Not in scope

Any behaviour change. Every item here is about what is asserted, not about what the code does. If
strengthening an assertion reveals a real defect, that is a separate story and should be filed as
one.

## Open Questions

None. This can be refined and estimated as it stands.
