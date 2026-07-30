# Sprint 64 review — 2026-07-30

**Goal:** start a loop for the first time in this repo's history, against the demo fleet, and make
the run mean something.

**Committed:** 8 points / 4 stories + a 0-point spike. **Delivered:** 8 points / 4 stories + the spike.
**Branch:** `sprint-64` at `3cd494f`, **unmerged**. 31 commits, 30 files, +4362/−616.

**Evidence of record — full 8-command DoD gate, 8/8 GREEN at `bbf3c72`:**

| Command | Result |
| ------- | ------ |
| `pytest` | **666 passed, 0 skipped** |
| import-linter | Analyzed 150 files, 427 dependencies — **8 kept, 0 broken** |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 239 files already formatted |
| `cfn-lint infra/stack.yaml` | silent |
| `npm test` | 51 files, 363 tests passed |
| `npm run build` | built in 502ms |
| `npm run lint` | clean |

`HEAD` (`3cd494f`) differs from the gate commit `bbf3c72` by **only** `.scrum/sprint-current.yaml`
and `docs/scrum/wiki/dev-setup-and-dod.md` — no code delta, so the gate evidence covers the
delivered code. (The spec reviewer independently made this same check against its own review range,
which is the check that makes gate evidence admissible.)

Wiki: `yt_wiki.py` **CLEAN** on sweep / facts / links / integrity. `yt_selftest` 28/28.

---

## The demo

**The loop ran.** `tools/demo_loop_gate/harness.py` launches the **real, unmodified**
`python -m src.composition.run` as an OS subprocess, alongside a real `uvicorn` API subprocess, both
with `CONFIG_DIR=config/demo`, against fresh throwaway DynamoDB tables and an embedded demo engine.
Re-run at `bbf3c72`, **exit 0**, verdict `REALITY GATE 182 SIDE 1: PASS`:

```
components_count                  : 13
signals_count                     : 41
signals_with_zero_rows            : []
signals_with_under_4_locations    : []
drift_warning_count               : 0
healthy_info_count                : 41
approvals                         : 200  []   (is_empty_list true)
loop teardown  : returncode 1 (TerminateProcess, expected on Windows),
                 escalated_to_kill false, reaped_returncode_observed true,
                 startup_marker_observed true, last_signal_ingested_before_terminate true
api teardown   : reaped_returncode_observed true
api_port_free_after_teardown      : true
```

The other two sides, both **exit 0**:

- **Guard** — demo `statuspage_mapping()` `{}`; SAFE `_delegate` chain
  `[StatusWritebackPublisher, LoggingPublisher]` vs UNSAFE
  `[StatusWritebackPublisher, BestEffortPublisher, RecordingPublisher, StatuspagePublisher]`;
  chains **differ**. No network call.
- **Backfill** — empty store **41 drift / 0 healthy**; coverage store **0 drift / 41 healthy**;
  sides **differ**.

**Nothing reached the live Statuspage.** Both subprocesses ran with `CONFIG_DIR=config/demo` (empty
mapping → `LoggingPublisher`) *and* with deliberately fake Statuspage credentials, verified at
source by the orchestrator.

---

## Story 1 — STORY-187, import-provenance helper (1 pt)

**AC1–AC7 met.** Scoped gate 4/4 (617 passed, 0 skipped, +3). Delivered `tools/import_provenance.py`
with `assert_import_root(module, expected_root)`.

**Reality gate PASS, on the real mechanism.** Run from inside an actual `git worktree`, not the
test's simulation: with cwd set to the worktree, `src.composition.vendor_health` still resolved to
the **main tree** — and read `_HEALTH_CHECK_WINDOW = '2h'` from it, the very constant sprint 63's
proof got wrong. Expecting the worktree root raised; expecting the main root returned cleanly. Same
process, same module, same resolved file; only the expected-root argument changed.

**So the helper would have caught sprint 63's false pass — demonstrated, not asserted.** This is the
mechanical rung that A1, its refinement, and A3 each declined to take across two retros.

Verification also corrected the story: the trap is a plain `.pth` `sys.path` append, **not** a
setuptools finder — which made AC3 *easier*, since a `sys.path`-ordering test reproduces the real
mechanism rather than approximating it.

## SPIKE-064 — feasibility (0 pts)

Not a deliverable; it earned its place. It found that **AC3/AC4 were unsatisfiable as specified**
(the five checked-in scenarios cover 6 of 41 signals; 36 signals would have raised drift warnings),
proved the builder route works, and established that **5 cycles suffice** rather than the ~39,000
rows a literal reading of "≥2h of coverage" implied.

It also caught **itself** producing a false negative: reading locations from `dt.synthetic.location.id`
(mirroring the monitor-id field) instead of `dt.entity.synthetic_location` reported
"AC3 REACHABLE: False" while the rows were entirely correct. That trap went into STORY-182's brief.

## Story 2 — STORY-183, retention-bound the token cache (1 pt)

**AC1–AC7 met.** Scoped gate 4/4 (621 passed, 0 skipped, net +4).

**Reality gate PASS**, two-sided over real HTTP with the real unmodified `make_grail_executor`
exercised on both sides. One value changed — the retention passed to the constructor:

| | tiny (1s) | large (1h) |
| --- | --- | --- |
| repeat poll inside window served | True | True |
| poll after advancing past window | **404** | **200** |
| cache length after 5 executes | **1** | **6** |

Two independent axes of difference. How it could have agreed and didn't: if retention were copied
from the module constant at construction, monkeypatching would no-op and both sides would behave
identically — so the harness reads the **instance's** effective retention back and asserts it took
effect before reporting. And under the old consume-on-poll bound, "repeat poll served" would read
False on **both** sides while cache length couldn't have differed at all.

AC2-vs-AC5 was settled on documented evidence, not judgement: the replaced test's own docstring
attributes it to STORY-180, and AC5's enumerated wire contract never included eviction semantics.

## Story 3 — STORY-184, interval invariant on the type (1 pt)

**AC1–AC7 met.** Scoped gate 4/4 (628 passed, 0 skipped, +7).

**Reality gate PASS** via main-tree patch-and-restore. At the parent commit,
`SignalScenario(interval_seconds=-30, cycles=[["L1"],["L1"]])` constructed happily and produced
`['2026-07-30T12:00:30Z', '2026-07-30T12:00:00Z']` for `end_time=12:00:00Z` — **a row 30 seconds in
the future**, which `ingest_service` would have quarantined silently while `run.py` discarded the
rejected count. The AC5 pinning test **failed** there and **passes** at head; restore left
`git diff` empty; no DoD gate was run while patched.

**AC3's tripwire held** — the test file diff has no removal lines at all, so all seven loader
rejection tests are byte-identical. But that evidence is weaker than it looks, so all five interval
shapes were driven through the loader by hand. Two unpinned behavioural changes surfaced that no
test caught (both benign, both filed): the rejection message lost its `(STORY-176 AC2f)` citation,
and **error precedence flipped** — a file with both a bad interval and bad cycles now reports the
cycles error. Both strengthen the already-filed STORY-186 finding (g).

## Story 4 — STORY-182, the real loop run and its three-sided gate (5 pts)

**AC1–AC7 met, after one fix round.** Re-pointed 3 → 5 at planning; the estimate held.

**Round 1: spec FAIL, quality FIX_REQUIRED (4 majors).** The central defect: `harness.py` **reported
rather than enforced** — assertions only for AC1, `__main__` exited 0 regardless, and a polling
timeout set a flag and *continued*. A rerun with a dead monitor id would have printed the bad number
and passed. AC5's wording is explicit that the endpoint be *asserted* empty.

Two findings corrected the orchestrator directly:

- **The API subprocess carried the real `.env` Statuspage credentials.** `asgi.py:37` loads the
  file; `app.py:169-183` calls `load_statuspage_secrets()` and feeds `build_publisher`. The code
  comment justifying the omission named `load_live_secrets` — a real function, wrong path. No live
  gap (the empty mapping still forced `LoggingPublisher`), but two of `build_publisher`'s three
  guards were satisfied on the only publish-capable process, and `CLAUDE.md` had been given a
  **false** claim about it.
- **`gone_by_pid` was tautological** — `poll()` after `wait()` reads a cached returncode and can
  never be False, while the docstring claimed "gone BY PID" and the README claimed "OS-level PID
  verification". The orchestrator had repeated that datum to the PO as evidence.

**All four majors and three minors fixed.** Then the check that actually closes a
"this-cannot-fail" defect: every new assertion was fed good **and** bad evidence directly —
**13/13 discrimination cases correct**. AC3 raises on a zero-row signal, an under-4-location signal,
11 components, 39 signals; AC4 on 1 drift warning and on 40 healthy lines; AC5 when a proposal
appears; the timeout path on both a missed startup marker and a missed ingest poll.

**What review confirmed as genuinely good:** the quality reviewer ran its own A4 mutation probe —
five independent mutations of the coverage builder, **every one turned tests RED** — so the
computational core is pinned, not shape-asserted. And A3 holds on both discrimination proofs,
including correctly **discarding** a length-1 `_delegate` chain as a harness defect.

---

## Blocked

None.

## Filed, not fixed (candidates for refinement)

1. **Encoding landmine, pre-existing.** `.scrum/checklists/quality-review.md` is not valid UTF-8
   (3 raw cp1252 `0x97` bytes) and `.scrum/checklists/implementer.md` carries 3 real `U+FFFD`. Any
   tool round-tripping either file corrupts text nobody edited — it happened during STORY-187 and
   was caught only by a pre-commit `git diff` read.
2. **STORY-184's two unpinned behavioural changes** (message text, error precedence) — strengthens
   STORY-186 finding (g).
3. **Four throwaway `story182-*` DynamoDB table pairs** left in the long-lived local container.
   Harmless (in-memory, uniquely suffixed) but untidy.
4. **`demo-engine.md`'s "the run itself is not wired up"** is now stale in *content* though the
   mechanical sweep does not flag it — its `code_refs` do not yet include `tools/demo_loop_gate/*`.
5. **Two docstrings that contradict their code**, noted and deliberately not fixed (out of scope):
   `vendor_health.py:86` claims a healthy id "logs nothing" while `:126-133` logs INFO; and
   `api/v1/availability/models.py` misdescribes `rollup.distinct_locations`, which is hardcoded 0.

## Process notes carried to the retro

- Both reviewers died mid-read on a session limit with no verdict, and were relaunched. Recorded per
  A5 rather than quietly retried.
- The orchestrator introduced **two citation errors while correcting citations** (a withdrawn
  `scenario.py` "correction", and eight wrong line numbers in a wiki update). Both caught by
  re-reading each address against the file — the only defence that has worked.
- The spike's timing figure did not transfer from a no-I/O stand-in to the real system, and was
  reported in the same sentence as a claim that did.
- **A green `pytest` silently skipped the entire persistence floor** with Docker down (561 passed /
  53 skipped vs 614 / 0 at the same commit) and the gate still recorded PASS.

---

## PO verdict — 2026-07-30

**ALL FOUR STORIES ACCEPTED.** Velocity **8/8** (`velocity.json` sprint 64: committed 8, accepted 8).

| Story | Pts | Verdict |
| ----- | --- | ------- |
| STORY-187 — import-provenance helper | 1 | ACCEPTED |
| STORY-183 — retention-bound token cache | 1 | ACCEPTED |
| STORY-184 — interval invariant on the type | 1 | ACCEPTED |
| STORY-182 — the real loop run + three-sided gate | 5 | ACCEPTED (after one fix round) |

**Branch: `sprint-64` stays UNMERGED at `3cd494f`**, per the standing "don't merge with main"
instruction, re-confirmed by the PO at this review. Accepted is not landed. Sprint 65 branches off
`sprint-64`, exactly as 64 branched off 63 and 63 off 62 — `main` (`517fc38`) still lacks STORY-146's
config shape, STORY-148's engine, STORY-176's player and now STORY-182's harness.

### Follow-ups filed from this review

- **STORY-188** — normalize the `.scrum/checklists` encoding. The corruption risk already fired once
  during STORY-187 and was caught only by a pre-commit `git diff` read. These two files are read by
  every implementer and reviewer dispatch.
- **STORY-189** — three doc/wiki gaps left deliberately: `demo-engine.md`'s `code_refs` omit
  `tools/demo_loop_gate/*` (so content-staleness is invisible to the mechanical sweep), and two
  docstrings that claim more than their code does (`vendor_health.py:86`,
  `api/v1/availability/models.py`).
- **STORY-186 REINFORCED**, not re-filed: finding (g) now carries sprint 64's evidence that the seven
  loader rejection tests passed byte-identical across two real behavioural changes, and gains a
  precedence case.

Still `ready` and unscheduled: **STORY-185** (un-gate the unsafe side of the publish proof from
Docker) and **STORY-186** (the demo-engine doc/test hygiene batch).

### Note on the throwaway tables

Four `story182-observations-*` / `story182-control-*` pairs remain in the long-lived local
`uptime_dynamo_8021` container from repeated harness runs. In-memory and uniquely suffixed, so they
cannot collide; not worth a story. They vanish when the container restarts.
