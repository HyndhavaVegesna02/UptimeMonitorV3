---
id: STORY-180
title: Demo-engine polish — the eight non-blocking minors from STORY-148's quality review
type: chore
---

## Context

`yt-quality-reviewer` raised nine minors on STORY-148 (2026-07-29). One (a malformed JSON body
escaping as a stdlib traceback) was fixed in-story because it landed in the same function as a
MAJOR. The other **eight** were deliberately deferred: none blocks the wire contract, and letting
a story absorb its own review nits is how a 3-pointer becomes a 6.

They are scheduled **with STORY-176** on purpose. STORY-176 turns the demo engine from a
test-scoped object into a long-running process driving a real loop, which is what makes (1) and
(5) stop being theoretical. Doing both in one sprint also avoids touching `tools/demo_engine/`
twice in consecutive sprints.

Two of the eight are the same class of defect this sprint series keeps finding: a **docstring
that claims more than its code delivers** (6), and a **test that bypasses the producer it claims
to verify** (2). Those two are worth more than the tidying.

## Description

Fix the eight minors below. Each is small; the value is in doing them together while the engine
is already open, and in the two that are real correctness-of-documentation defects.

### The eight

1. **The vendor-health window is hardcoded AND the query's own clause is discarded.**
   `tools/demo_engine/store.py:22` pins `VENDOR_HEALTH_WINDOW = timedelta(hours=2)` while
   `query_grammar.parse_query` throws away the `from:now()-2h` clause it parsed. If
   `composition/vendor_health.py`'s `_HEALTH_CHECK_WINDOW` ever changes, the demo diverges
   **silently** in the one dimension it hardcodes. Either parse the window out of the query
   string, or assert it equals the constant. The existing comment defends the literal but says
   nothing about the discarded clause.
2. **A fidelity test that bypasses the producer.**
   `backend/tests/demo_engine/test_watermark_precision.py:19-26` hand-builds the ingest query
   string. Only the 9-digit case *needs* a literal (the real `build_dql_query` cannot emit one);
   the 0- and 6-digit cases are reachable through the real builder (`microsecond=0` /
   `microsecond=746000`) and should use it.
3. **A test that exercises no product code.** `test_watermark_precision.py:63-70` asserts only a
   stdlib string-ordering fact. Honestly named, but it is a comment wearing a test's clothes —
   fold it into the docstring it belongs in.
4. **A test name that overstates.** `test_assumed_failure_codes.py:29-40` is named
   `..._produces_a_structurally_valid_row` but asserts only that the two status values echo their
   inputs. Rename to what it checks (or check what it is named).
5. **An unevicted token cache.** `tools/demo_engine/server.py:47` — `_DemoHTTPServer.results`
   grows one entry per query for the process lifetime. Irrelevant to tests; a slow leak in
   STORY-176's long-running demo.
6. **A docstring claiming more than the code.** `tools/demo_engine/rows.py:36-37` calls
   `("0", "HEALTHY")` "The ONLY (code, message) pair `map_synthetic_status` accepts".
   `health_mapping.py:65` is an `or`, so **either half alone suffices**. Correct the docstring to
   the code's actual contract.
7. **Wasted clock read.** `store.py:57-61` computes `datetime.now(timezone.utc)` on every call
   including ingest queries, where `instant` is then unused.
8. **`sys.path[0]` insertion for `tools/`.** `backend/tests/conftest.py:30` inserts `tools/` at
   the FRONT of `sys.path`, ahead of stdlib, for every backend test. Zero collision risk today
   (`tools/` holds only `demo_engine/` and the hyphenated, unimportable `ui-sweep/`) and it
   matches the existing `scripts/` precedent — so this is a **"safer default" note, not a bug**.
   Append would be preferable if `tools/` ever gains a generic module name.

## Acceptance Criteria

- [ ] **AC1 (minor 6 — the docstring drift, and it must be checked against the code)** —
      `rows.py`'s claim about `map_synthetic_status` matches what `health_mapping.py` actually
      does. The AC is satisfied by reading the `or` and stating its real semantics, not by
      rewording the sentence to sound softer.
- [ ] **AC2 (minor 1 — the window can no longer diverge silently)** — Either the engine parses
      the window from the query, or a test fails if `store.py`'s constant and
      `vendor_health.py`'s `_HEALTH_CHECK_WINDOW` disagree. A comment alone does not satisfy this
      AC: the point is that a future change to the composition constant cannot pass green.
- [ ] **AC3 (minor 2 — the real producer drives the reachable cases)** — The 0- and 6-digit
      watermark cases go through the real `build_dql_query`. The 9-digit case keeps its literal,
      with the reason (the real builder cannot emit 9 digits) stated at the literal.
- [ ] **AC4 (minor 5 — bounded token cache)** — `_DemoHTTPServer.results` no longer grows without
      bound, with a test proving the bound (e.g. an entry is evicted after being polled, or the
      cache is capped). "It doesn't matter in tests" is the reason it was deferred, not a reason
      to skip the fix now that STORY-176 makes the process long-lived.
- [ ] **AC5 (minors 3, 4, 7 — the tidying)** — The stdlib-only test is folded into a docstring;
      the overstated test name matches its assertions; the unused clock read is gone from the
      ingest path. Test COUNT may drop by one from (3); that drop is stated in the story
      evidence so it is never mistaken for a lost test.
- [ ] **AC6 (minor 8 — decided explicitly, either way)** — `conftest.py`'s `tools/` insertion is
      either moved to append or deliberately left at the front, and the choice is recorded with
      its reason in the file. What is NOT acceptable is leaving it undocumented after a reviewer
      flagged it — a reader must be able to tell the current state is chosen, not inherited.
- [ ] **AC7 (no wire-contract change)** — STORY-148's proven contract does not move: the seven
      required row fields, the nanosecond scale conversion, both query grammars, the async HTTP
      protocol, and the auth scheme-prefix check are unchanged in behaviour. Every STORY-148 test
      that asserts them still passes, and none is edited except as AC3/AC5 require.
- [ ] **AC8 (still zero production code)** — `git diff` for this story touches no file under
      `backend/src/`. STORY-148's AC9 rule holds: the demo engine adapts to production, never the
      reverse.
- [ ] **AC9** — All eight DoD gate commands exit 0.

## Open Questions

None. Minor 8 is a deliberate either-way decision (AC6), not an open question.

## History

- 2026-07-29: filed at STORY-148's close as the routed remainder of its quality review (eight of
  nine minors; the ninth was fixed in-story). Estimated 2 points.
- 2026-07-29: refined and pulled into sprint 63 on PO instruction, alongside STORY-176 — whose
  long-running engine is what makes minors 1 and 5 matter — bringing the sprint to 8 points.
