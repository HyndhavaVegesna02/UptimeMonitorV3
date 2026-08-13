---
id: STORY-213
title: test_dynamo_component_repository_list_components_paginates fails intermittently — the message reads as a pagination defect
type: defect
points: 2
status: draft
filed: 2026-08-03
refined: 2026-08-03
sprint: null
---

## Context

Filed from STORY-199's quality review, **with reproduction evidence attached**. It is *not* a defect
in STORY-199's code, and the reviewer proved that before filing: the production loop was
mutation-verified correct and the `ZR-7` guard independently confirms all six compliant call sites.

Observed once, on the first of eleven full-suite runs against committed HEAD, with `REQUIRE_DYNAMO=1`:

```
FAILED backend/tests/test_dynamo_component_repository_list_components_paginates
assert {'comp-page-0', 'comp-page-1'} == {10 ids}
```

— i.e. with `repo._limit = 2`, `list_components` returned **page 1 and stopped**. Did not recur in
10 further full runs (694 passed / 0 skipped each) nor in 25 consecutive targeted runs.

**The reviewer's hypothesis, unconfirmed:** a lost write or an absent `LastEvaluatedKey` from
DynamoDB Local under the `conftest` `clean_dynamo_tables` fixture's ~1,400 delete/recreate table
cycles per run. Related to STORY-179 (the same fixture's known ephemeral-port defect — same fixture,
different symptom).

**Why it is worth a story despite being rare:** the failure message is indistinguishable from
"pagination is broken" — the exact defect sprint 67 had just fixed. At ~1-in-11 it will eventually
fire for someone who then spends a day re-investigating a closed defect. **That cost is the story,
not the flake.**

## Refinement decisions

**1. The deliverable is a self-diagnosing assertion, not a reproduction.** The filed note offered a
choice between hardening the fixture and making the assertion self-diagnosing. Hardening is
speculative — the mechanism is unconfirmed and survived 35 attempts to reproduce. The *stated* cost
is a message that misleads, so fixing the message is the fix. Fixture hardening stays a probe (AC3),
not a promise.

**2. Non-reproduction must not block the story.** An earlier draft of these AC required reproducing
the failure first (agreement A8). That would block this story **by construction** — 35 runs already
failed to reproduce it. A8 governs spikes with a reproducible target; it does not apply here, and
saying so is part of the story.

**3. It is NOT scheduled into sprint 68.** It was briefly placed there as an "enabler" on the theory
that sibling tests polluted a shared table — which the evidence above refutes (pollution yields
*extra* ids; this returned *fewer*). With the mechanism being DynamoDB Local flakiness, it protects
none of sprint 68's work. It is real, it is small, and it waits.

## Acceptance Criteria

- [x] **AC1 — the message distinguishes a flake from a regression at a glance.** On failure the
      assertion reports the observed page count, the ids actually returned, and whether a
      `LastEvaluatedKey` was present when the loop exited. Proven by *forcing* a failure (inject a
      truncated result) and recording the emitted message — not by describing it.
      Landed: `PaginationSpy` (`backend/tests/pagination_diagnostics.py`) wraps the table's
      `query`/`scan` method and renders `.diagnostic()`/`.summary()`.
      `test_dynamo_component_repository_list_components_paginates_diagnostic_message_on_forced_truncation`
      (`backend/tests/test_dynamo_adapters.py`) forces exactly the reviewer's hypothesised shape —
      strips `LastEvaluatedKey` from the first (real) page's response, handed to an UNMODIFIED
      `list_components` — and asserts on the captured `AssertionError` text itself: `"1 page(s) read;
      LastEvaluatedKey present when loop exited=False; ids returned=['comp-page-0', 'comp-page-1'];
      missing=['comp-page-2', ..., 'comp-page-9']; extra=[]"`.
- [x] **AC2 — the test is not weakened. This is the constraint the filed note puts in capitals.**
      It remains one of STORY-199's five AC2 proofs: still full set equality against all ten
      `comp-page-*` ids, and removing `list_components`'s `LastEvaluatedKey` loop must still take it
      RED. Record the mutation, the failure, the restore, and an empty `git diff`.
      Landed: mutation patch `docs/scrum/stories/STORY-213-ac2-mutation-remove-lek-loop.patch`,
      mechanised via `python tools/evidence_check.py mutate <patch> --tests
      backend/tests/test_dynamo_adapters.py::test_dynamo_component_repository_list_components_paginates`
      → `OK: mutation turned RED: [...]`, exit 0, tree restored (`git status --porcelain` empty
      after). The captured failure text on this specific mutation reads `LastEvaluatedKey present
      when loop exited=True` — the OPPOSITE signature from AC1's forced-truncation flake (`=False`),
      because `Limit` is still honored but `ExclusiveStartKey` never advances: the server correctly
      reports more rows exist and the (broken) code never asks for them. This is the empirical basis
      for `PaginationSpy.diagnostic`'s docstring claim that the two LEK values distinguish the two
      failure shapes.
- [x] **AC3 — the fixture hypothesis is probed and the result recorded either way.** Examine whether
      `clean_dynamo_tables`'s delete/recreate cycle can race a subsequent write, and whether the
      repository's loop mishandles an absent `LastEvaluatedKey`. **If a concrete defect is found, fix
      it. If not, record the negative result with what was checked.** Non-reproduction is an outcome,
      not a failure of the story.
      **Negative result, recorded (see History for the full evidence):** (1) no race is structurally
      possible — `pytest` runs this suite single-threaded (no xdist configured) and
      `clean_dynamo_tables`/`create_tables()` complete their `table_not_exists`/`table_exists` waiters
      before the fixture yields, so a test body's own writes can never overlap the PREVIOUS test's
      delete/recreate; (2) an empirical 300-iteration write-then-query probe found zero divergence
      between `ConsistentRead=False` (the default the base-table queries use) and `ConsistentRead=True`
      against this container — DynamoDB Local is a single in-memory process with no replica to lag
      behind, so eventual-consistency staleness has no mechanism to manifest here; (3) the three
      GSI-backed call sites (`list_windows`, `list_open`, `is_under_maintenance`) cannot take
      `ConsistentRead=True` at all — real AWS DynamoDB does not support strongly consistent reads on a
      GSI, so this was never an available fix, and `dynamo_maintenance_repository.py`'s own docstring
      already documents that trade-off as PO-accepted (2026-07-14), unrelated to this story; (4) all
      five call sites treat an absent `LastEvaluatedKey` as "no more pages", exactly the documented
      DynamoDB API contract (absence is the ONLY defined "done" signal in the response; there is no
      other field a caller could use to double-check it) — none of the five "mishandles" it, and if
      DynamoDB Local's own engine ever violated that contract, no change on the adapter side could
      detect or correct for it from the response alone; (5) a 200-iteration direct stress of the exact
      delete/recreate + forced-`Limit=2`-pagination cycle (bypassing full-suite overhead to run far
      more iterations than a real suite run allows in one session) reproduced zero truncations. No
      concrete defect found; nothing fixed. Combined with the original 35 non-reproductions (Context),
      that is 47 non-reproductions across two fixture generations (pre- and post-STORY-179) plus 512
      probe iterations targeted directly at the two hypothesised mechanisms.
- [x] **AC4 — the four sibling `_limit`-forcing tests** (`list_windows`, `list_signals`, `list_open`,
      `is_under_maintenance`) get the same diagnostic treatment, or it is stated per test why they do
      not need it. A bare "checked, fine" is not evidence.
      Landed: `test_dynamo_signal_repository_list_signals_paginates`
      (`backend/tests/test_dynamo_adapters.py`),
      `test_dynamo_maintenance_repository_list_windows_paginates`,
      `test_dynamo_maintenance_repository_is_under_maintenance_paginates_past_forced_page_size`
      (`backend/tests/test_dynamo_maintenance_repository.py`), and
      `test_dynamo_proposal_repository_list_open_paginates`
      (`backend/tests/test_dynamo_proposal_repository.py`) all now wrap their table in `PaginationSpy`
      and assert with `.diagnostic()`/`.summary()`. `is_under_maintenance` returns a `bool`, not a set,
      so it uses `.summary()` (page count + LEK presence) with a message spelling out what each LEK
      value would mean, rather than `.diagnostic()`'s id-set rendering.
- [x] **AC5 — no skips.** The gate runs with `REQUIRE_DYNAMO` set (agreement A6); a skipped
      DynamoDB test is a failure, not a pass.
      Confirmed: full gate run with `REQUIRE_DYNAMO=1` in both configurations (see History) —
      `0 skipped` in both.
- [x] **AC6 — cross-referenced with STORY-179**, which owns the same fixture's other known defect, so
      whoever takes 179 sees this evidence.
      `STORY-179-dynamo-local-port-and-readiness.md`'s own "Not in scope" section already points
      forward to this story ("STORY-213's pagination flake — a different symptom, distinct cause"),
      recorded before this story was dispatched. This story's History (below) records that AC3's probe
      ran against the fixture AS STORY-179 LEFT IT (fixed port range, real `ListTables` readiness
      probe) — the pointer this AC asks for. STORY-179 landed and closed in this same sprint, before
      this story was dispatched, so there is no longer a live "whoever takes 179" to hand it to; the
      cross-reference is preserved here for the historical record instead.

## Not in scope

Extracting the shared pagination loop (STORY-214). Changing any adapter's pagination behaviour.
Fixing STORY-179's ephemeral-port defect.

**Risk note (fix round, 2026-08-14):** the committed mutation patch
(`docs/scrum/stories/STORY-213-ac2-mutation-remove-lek-loop.patch`) is a textual diff against
`list_components` as it exists today; it will silently stop applying if that method is ever rewritten
(e.g. by extracting the shared pagination loop). **STORY-214, the story that would have done exactly
that, was archived by PO decision on 2026-08-13** as accepted duplication, so this is a recorded
dependent risk, not an active one — a future reader reviving that refactor should know the patch
needs regenerating.

## History

- 2026-08-13: **Flake re-measured BEFORE any implementation, per this story's own dispatch brief** —
  the 1-in-11 rate was measured before STORY-179 rewrote `clean_dynamo_tables`'s container lifecycle
  (fixed port range, `docker port` read-back, a real `ListTables` readiness probe), and that fix
  landed earlier in this same sprint. Ran the full suite (`python -m pytest`, `REQUIRE_DYNAMO=1`) 12
  times in config 2 (`DYNAMO_ENDPOINT_URL` unset, Docker up — the configuration the original failure
  was observed in): **809 passed / 0 skipped every time, 0-in-12.** Config 1
  (`DYNAMO_ENDPOINT_URL=http://127.0.0.1:8021`) also ran clean: **809 passed / 0 skipped in 51.95s.**
  The rate may have genuinely dropped since STORY-179, but per this story's own refinement decision 2
  ("non-reproduction must not block the story"), this changed nothing about the deliverable — AC1/AC2/
  AC4 land regardless of whether the flake still fires.
- 2026-08-13: implemented AC1 — `backend/tests/pagination_diagnostics.py::PaginationSpy` (pure-Python
  unit tests in `backend/tests/test_pagination_diagnostics.py`, no DynamoDB required), then wired into
  `test_dynamo_component_repository_list_components_paginates`
  (`backend/tests/test_dynamo_adapters.py`) and proven by forced truncation in the sibling test
  `..._diagnostic_message_on_forced_truncation` in the same file, which strips `LastEvaluatedKey` from
  the real first page's response (an UNMODIFIED `list_components` is exercised; only the raw response
  it receives is tampered with one frame below it) and asserts on the captured `AssertionError` text.
  Sanity-checked the proof mechanism itself by temporarily disabling the truncation and confirming the
  meta-test's own self-check correctly fails (`"the forced truncation did not reproduce a failure"`).
- 2026-08-13: implemented AC2 — mutation patch
  `docs/scrum/stories/STORY-213-ac2-mutation-remove-lek-loop.patch` removes `list_components`'s
  `while True` / `LastEvaluatedKey` loop, still honoring `Limit`. Mechanised via
  `python tools/evidence_check.py mutate <patch> --tests
  backend/tests/test_dynamo_adapters.py::test_dynamo_component_repository_list_components_paginates
  --repo-root C:/Hyn/uptime_monitor_v3` → `OK: mutation turned RED`, exit 0, restore confirmed (`git
  status --porcelain` empty, `git diff` empty). The captured failure text under this mutation reads
  `LastEvaluatedKey present when loop exited=True` — discovered this is the OPPOSITE signature from
  AC1's forced-truncation flake (`=False`), and corrected `PaginationSpy.diagnostic`'s docstring (which
  had the two mappings backwards in the first draft) against this measured evidence rather than
  leaving the more comfortable but wrong description in place.
- 2026-08-13: implemented AC4 — `list_signals` got the same treatment alongside AC1 (same file,
  same commit); `list_windows` and `is_under_maintenance`
  (`backend/tests/test_dynamo_maintenance_repository.py`) and `list_open`
  (`backend/tests/test_dynamo_proposal_repository.py`) followed. `PaginationSpy.diagnostic`'s type
  hint widened from `Iterable[str]` to `Iterable[Any]` for `list_open` (`StatusProposal.id` is
  `int | None`, not `str`).
- 2026-08-13: AC3 probe — see the AC3 entry above for the negative result. Additionally ran two
  scratch (non-committed) empirical probes against the fixed-port gate container: (1) 300 iterations of
  rapid write-then-query comparing `ConsistentRead=False` vs `=True` on the same key range — 0
  divergences; (2) 200 iterations of the exact `clean_dynamo_tables` delete/recreate cycle followed by
  a forced-`Limit=2` `list_components` call — 0 truncations. Both scripts ran from the session
  scratchpad, never committed (their only purpose was to generate the counts recorded above).
- 2026-08-13: both DoD gate configurations green — see report for full pasted output. `docker ps -a`
  confirmed no `uptime_dynamo_pytest_*` residue at the end of the session (one bash-tool timeout mid a
  batch of full-suite runs left two such containers running; both were `docker rm -f`'d before the
  next batch).
