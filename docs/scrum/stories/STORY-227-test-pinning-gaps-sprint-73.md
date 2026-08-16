---
id: STORY-227
title: Six test-pinning gaps found at sprint-73 review — assertions that pass today for reasons that are not the reason we think
type: chore
points: 5          # RE-PRICED 3 -> 5 at pre-lock verification, 2026-08-16. See "Why 5, not 3".
status: ready
refined: 2026-08-16   # sprint-74 refinement; re-priced at pre-lock verification the same day
sprint: null
---

## Why 5, not 3

Re-priced at pre-lock verification, and **the 3 repeated sprint 73's own worst estimation habit**:
it counted the test edits and priced the wiki at **zero**.

Measured — this story's diff touches `code_refs` of **four `tier: map` / `status: verified`
articles**, every one of which `.scrum/definition-of-done.md:133-136` and A18 force updated or
explicitly re-verified **in-story**:

| Article | Reached via |
| --- | --- |
| `zone-rules.md` | `backend/tests/test_zone_layout.py` (AC1, AC6), `composition/seed_dynamo.py` (AC3) |
| `persistence-adapters.md` | `backend/tests/test_dynamo_seed.py` (AC3), `composition/seed_dynamo.py` |
| `ingest-service-and-pull-loop.md` | `backend/tests/test_pull_loop.py` (AC2) |
| `statuspage-publish.md` | `backend/tests/test_statuspage_adapter.py` (AC5) |

AC3 additionally **mandates** an edit to `persistence-adapters.md`'s own Fact. That work cannot be
split into a follow-up — A18 makes it in-story by rule. Sprint 73 re-priced STORY-155b 5 → 7 for
exactly this reason and its retro called the correction the right call; withholding the same rule
here would be the identical mistake in the opposite direction.

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

> **THE RULE THAT APPLIES TO ALL SIX.** Every strengthened assertion must be **shown RED before it
> goes green**, against the gap it closes — not against a mutation of unrelated code. A test
> strengthened without ever being seen to fail proves only that it compiles. Record, per item, what
> you broke to make it red.

- [ ] **AC1 (the route table pins methods, not just paths) — the highest-value item.**
      `test_zone_layout.py:238`'s `_EXPECTED_ROUTE_TABLE` is a set of **11 path strings**
      (measured at refinement). It must pin the **(method, path)** pairs the app actually serves, so
      a `GET` → `POST` change on a surviving route fails.
      ⚠ **Do not weaken STORY-155b's AC6 while doing this** — the existing test must still prove the
      sample-mode route is absent and no other route changed. Shown-RED: flip one surviving route's
      method and watch it fail naming that route.
- [ ] **AC2 (the AC1-of-155b observation literal pins every field)** —
      `test_pull_loop.py:1080` compares ten `SignalObservation` fields and omits
      `response_status_code`. Add it. ⚠ **This is the test that proves the live ingest path was
      unchanged when `SampleModeIngest` was removed**, so it is the one place a missing field
      matters most. Shown-RED: set a non-`None` `response_status_code` on one expected row.
- [ ] **AC3 (the DynamoDB NULL claim is asserted, or the claim is withdrawn)** —
      `test_dynamo_seed.py` asserts `item.get("group") is None`, which cannot distinguish *written
      as a DynamoDB NULL* from *attribute absent*. Both `seed_dynamo.py`'s comment and
      `persistence-adapters.md`'s Fact claim the NULL form **specifically**.
      Either assert the raw attribute type (so the claim is proven), **or** correct the comment and
      the Fact to say only what is true. ⚠ **A wiki Fact making a claim no test checks is exactly
      what the Facts lint cannot catch** — this is the case that motivated grouping these six.
      ✅ **The prove-it branch IS reachable — verified by probe at pre-lock verification, against the
      local throwaway DynamoDB, so do not default to withdrawing the claim:**
      `'group' in item` returns **True** for the NULL form and **False** for the absent form, on the
      same `resource` Table object the test already uses (the low-level client shows `{'NULL': True}`).
      A one-line change at `backend/tests/test_dynamo_seed.py:178-179` proves it. "Assert the raw
      attribute type" does **not** require a low-level-client rewrite.
      ⚠ **If you take the withdraw branch and edit the comment at `seed_dynamo.py:46-50`, RE-KEY
      `config-layer.md`'s citations to `seed_dynamo.py:56` and `:76` in the same commit.** Both are
      enforced and currently passing; the file is 88 lines, so a line shift leaves them **in range
      and silently wrong** — the "wrong-but-in-range PASSES" hole that `test_citation_gate.py:378-406`
      exists to document. No mechanism catches this.
- [ ] **AC4 (the top-bar test stops depending on an unrelated fixture)** —
      `frontend/src/AppShell.test.tsx:172-174` uses the Approvals badge as its settle barrier, so a
      change to `FIXTURE_PROPOSALS` fails a test about the top bar. Wait on something the test is
      actually about.
      ⚠ **The draft's shown-RED was IMPOSSIBLE and is corrected.** It said "change
      `FIXTURE_PROPOSALS` and confirm the test no longer fails" — but the test builds its expectation
      **from the same constant** (`` `Approvals, ${FIXTURE_PROPOSALS.length} pending` ``,
      `AppShell.test.tsx:172-174`), so adding or removing a proposal moves expectation and render in
      lockstep and the test passes before *and* after. A vacuous "before" makes the "after" vacuous.
      **The only mutation that reds it today is emptying `FIXTURE_PROPOSALS` to `[]`** — that flips
      `hasBadge` false at `Sidebar.tsx:51-54` and the label becomes bare `Approvals`. Use that
      mutation: it must red today and must NOT red after the fix.
- [ ] **AC5 (the duplicated publish test collapses, keeping the part that matters)** —
      `test_statuspage_adapter.py:98-123` duplicates `:36-65` with a strictly weaker payload
      assertion; only the `set(StatusChange.model_fields) == {"component_id", "status"}` pin is new,
      **and that pin is what makes STORY-147's AC4 structural rather than incidental — it must
      survive.** ⚠ The draft guessed "~6 lines"; measured at pre-lock verification the block is
      **26 lines** (`:98-123`), of which only the `model_fields` assertion at `:106` need survive.
      State the actual before/after — and note the pytest count drops **831 → 830**, which AC7 must
      account for.
- [ ] **AC6 (the grep-shaped test name reads for a human)** —
      `test_zone_layout.py:253`'s `test_the_removed_sample_route_is_gone_and_no_other_route_changed`
      is an artifact of STORY-155b's AC5 (zero matches for `sample_mode` in `backend/`). Rename it
      to read naturally. ⚠ **Re-run that grep afterwards** — the original name matched its own
      story's AC and had to be renamed mid-story; do not reintroduce the match.
- [ ] **AC7 (gate, and the count is explained)** — the full nine-command gate exits 0 at the final
      HEAD. AC5 removes assertions and AC1–AC4 strengthen them, so the count may move: state
      before/after and account for any delta. ⚠ *Sprint 73's STORY-155b was marked FAIL by spec
      review for ticking exactly this kind of checkbox without writing the accounting. Write it.*

## Not in scope

Any behaviour change. Every item here is about what is asserted, not about what the code does. If
strengthening an assertion reveals a real defect, that is a separate story and should be filed as
one.

## Open Questions

None. This can be refined and estimated as it stands.
