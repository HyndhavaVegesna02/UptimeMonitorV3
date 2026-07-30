# Sprint 64 plan — the loop actually runs, and the proof can prove which code it ran

**Status:** DRAFT, awaiting PO approval.
**Mode:** `in-process` (standing directive after the sprint-60 external rejection: "you only implement").
**Dates:** 2026-07-30.
**Branch:** `sprint-64`, off `sprint-63` tip `805287f` — see "Branch and baseline".

## Goal

Start a loop for the first time in this repo's history, against the demo fleet, and make the run
mean something. STORY-176 (sprint 63) built the scenario player, the 13-component fleet, the time
base and the publish guard but deliberately launched nothing. This sprint launches it.

Three 1-pointers land first, and their ordering is not cosmetic:

- **STORY-187** gives every later proof in this sprint a way to answer "which code did I just run?".
  Sprint 63's STORY-180 discrimination proof reported 4/4 on *both* sides because the editable
  install resolves `src.*` to the main tree from inside any worktree — a proof that would have argued
  *against* a correct fix. STORY-182's reality gate is the most consequential proof in the
  programme; it should not be the fourth story to rediscover that trap.
- **STORY-183** and **STORY-184** are the two defects whose failure modes *only* bite in a
  long-running loop against a directly-constructed player — i.e. exactly what STORY-182 does. Both
  story files carry the same sequencing recommendation: land with or before STORY-182. Verification
  strengthened this: STORY-182's fleet coverage (B1 below) must construct `SignalScenario` **in
  code**, which is precisely the path STORY-184's invariant guards; and STORY-183's orphan leak is
  real under 41 concurrent signal loops.
- **STORY-182** last, because `decide` publishes recoveries with **no human gate** and the guard must
  be verified against the code that actually runs. A **zero-point day-1 feasibility spike** goes
  *before* story 2 to de-risk it — see "The spike".

**Explicitly out of scope:** STORY-185 and STORY-186 (both `ready`, both PO-deferred at this
refinement — neither gates STORY-182); all frontend work; any failure-path scenario (STORY-177,
still `draft` with 3 open questions); STORY-155 (`sample_mode` removal); STORY-179 (the
`dynamo_local` ephemeral-port defect this sprint works *around*); STORY-178; STORY-173;
STORY-150/151/152/153; STORY-147; STORY-154 (blocked on trial renewal).

## Scope — 8 points, 4 stories + a 0-point spike

| # | Story | Pts | Type | Ceremony |
| - | ----- | --- | ---- | -------- |
| 1 | STORY-187 — an import-provenance helper so a proof can prove WHICH code it ran | 1 | chore | implementer → gate → reality gate |
| — | *Feasibility spike for STORY-182* | 0 | spike | orchestrator, timeboxed, recorded on the board |
| 2 | STORY-183 — bound the demo token cache by RETENTION, not consume-on-first-poll | 1 | defect | implementer → gate → reality gate |
| 3 | STORY-184 — move the scenario interval invariant onto `SignalScenario` itself | 1 | defect | implementer → gate → reality gate |
| 4 | STORY-182 — the real loop run against the demo fleet, and its two-sided gate | **5** | chore | implementer → spec ∥ quality → gate → three-sided reality gate |

### STORY-182 is re-pointed 3 → 5. This is the plan's most consequential change.

It entered planning at 3 (the figure assigned when the old combined STORY-176 was split). The
verifier re-estimated it at **5** against the repo's own yardstick, and the orchestrator agrees:

| Reference | Pts | What it carried |
| --------- | --- | --------------- |
| STORY-148 | 3 | 4 new modules, 23 tests, all in-process, no cross-process orchestration, no live run |
| STORY-176 (part 2a) | 3 | player + YAML loader + validation, 13-component/41-signal fleet authoring, 5 scenarios, guard checks, coverage tests |

STORY-182 additionally carries: the **fleet-wide coverage artifact** that does not exist yet (B1) —
a STORY-176-shaped slice; a **first-in-repo multi-process launch/terminate harness** (every existing
API test uses in-process `TestClient`; the only `subprocess` precedent in the repo is
`scripts/dynamo_local.py` shelling out to Docker); a fresh-table strategy across two processes × two
table names; four asserted preconditions across two processes; evidence over 13 components / 41
signals across four endpoint families; three reality-gate sides, one needing a second throwaway
config dir; and a wiki + `CLAUDE.md` pass. The harness and the gate sides alone fill STORY-148's
entire 3-point envelope.

**It is deliberately NOT split.** Splitting would ship the positive run without its discrimination
proof, which working agreement A1 forbids. The sprint therefore runs at 8 points — still under the
~9–11 baseline, and consistent with the pacing directive.

**If 8 is too much, the only clean lever is the PO trimming AC3's thresholds at lock** (AC are
PO-authoritative; the plan may not quietly narrow them). Deferring STORY-184 is the alternative, but
it is the one 1-pointer STORY-182 structurally needs — see the Goal.

### Why 185 and 186 are not here

Recorded so the omission is a decision, not an oversight. STORY-185 un-gates the unsafe side of the
publish proof from Docker — but sprint 63's out-of-test harness already proved that side with no
Docker at all, so the evidence exists; only the *in-test* proof degrades. STORY-186 is 11 documented
minors of doc/test accuracy. Neither changes what STORY-182 can prove. Both are the first candidates
for sprint 65.

## Branch and baseline

**Branch `sprint-64` off `sprint-63` tip `805287f` — NOT off main.** Same reasoning as sprint 63
branching off 62: the PO accepts each sprint but keeps it unmerged (standing "don't merge with
main"), so `main` (`517fc38`) contains none of STORY-146's config shape, STORY-148's engine, or
STORY-176's player and fleet — and STORY-182 `depends_on` all three. `main` and
`debug/ingest-stall-sample-mode` are two different branches; both are ancestors of HEAD, so
branching here loses nothing.

**Baseline verified at `805287f`, 2026-07-30: full 8-command gate GREEN.** `pytest` 561 passed / 53
skipped; import-linter `Contracts: 8 kept, 0 broken`; `ruff check` clean; `ruff format --check` 222
files; `cfn-lint` silent; `npm test` 51 files / 363 tests; `npm run build` built; `npm run lint`
clean. Independently re-confirmed by `yt-plan-verifier`: `614 passed in 26.46s`, 0 skips.

`805287f` is the refinement commit; the only changes since sprint 63's evidence-of-record HEAD
`05245fd` are `.scrum/` and `docs/` markdown and YAML — no file under `backend/`, `tools/`, or
`frontend/`, so the code baseline is unmoved.

### The 53 skips are a finding, not noise — read this before trusting any gate this sprint

That baseline `pytest` run reported **561 passed, 53 skipped**, where sprint 63's final gate at
`05245fd` reported **614 passed**. Not a regression: Docker Desktop was not running, so
`backend/tests/conftest.py`'s session-scoped `dynamo_local` fixture skipped every DynamoDB-gated
test. **The gate still exited 0.** A green `pytest` therefore does not by itself mean the persistence
floor ran.

The orchestrator started Docker Desktop and the fixed-port container and re-ran:
`DYNAMO_ENDPOINT_URL=http://127.0.0.1:8021 pytest` → **614 passed, 0 skipped**. Floor restored.

**Standing precondition for every gate record this sprint:** `DYNAMO_ENDPOINT_URL=http://127.0.0.1:8021`,
container `uptime_dynamo_8021` (the STORY-179 ephemeral-port workaround), Docker Desktop running.
Record the pass/skip **counts** as `env_note` on each gate record — **a nonzero skip count on a
backend gate is an incomplete gate, not a pass.**

## The spike — zero points, timeboxed, before story 2

Pre-lock verification found two blockers (B1, B5) that were each ~20 minutes of reading away, and
would have landed on day 4 with the sprint's budget spent. The spike exists so the remaining
unknown-unknowns surface on day 1. It produces findings on the board, not code:

1. **Fleet-wide row coverage** for all 41 native monitor ids × 4 locations — confirm the chosen
   artifact from B1 actually makes `check_vendor_id_health` quiet and `/history` non-empty for every
   signal.
2. **Loop start/stop on Windows** — `run.py:218` never returns; confirm the external-termination
   route works and that writes are durable at kill time.
3. **The two-process env matrix** — `CONFIG_DIR`, `DYNAMO_ENDPOINT_URL`,
   `DYNAMO_OBSERVATIONS_TABLE`, `DYNAMO_CONTROL_TABLE` on both the loop and the API process.

If the spike finds STORY-182 infeasible as specified, it is Blocked with the exact question rather
than attempted — and the sprint still delivers three green stories.

## Verified contracts (re-verified at `805287f`; every row checked twice — orchestrator, then verifier)

**Three corrections to the story text, and one correction to the orchestrator's own first pass.**
The orchestrator initially "corrected" `expand_scenario`'s docstring citation to `:156-159`; the
verifier showed the **story's `:158-160` was right** (`:160` carries the "never after (AC2f: never in
the future)" clause). That correction is withdrawn. Recorded because a plan that silently corrects a
correct address is the same defect class the plan is meant to catch.

### The publish exposure — the safety-critical chain

| Claim | Address at `805287f` | Verified |
| ----- | -------------------- | -------- |
| `decide` publishes a recovery with no human gate | `core/services/decide.py:119` sets `publish_change = None`; `:122-126` fills it on `proposed_is_better` with `action = PUBLISHED_RECOVERY` | ✅ (`:122-126`, not `:121-126`) |
| …and publishes it unconditionally at the end | `decide.py:171-172` — `if publish_change is not None: self._publisher.publish(publish_change)` | ✅ |
| The guard is config-only: no mapping → no live publisher | `composition/publish_helper.py:211` — `if statuspage_page_id and statuspage_api_token and component_mapping:` | ✅ |
| **`build_publisher` returns the SAME top-level type on both sides** | `publish_helper.py:234` returns `StatusWritebackPublisher` **outside** the `if`/`else` | ⚠️ **new — see reality gate side 2** |
| The layers store `_delegate`, not `delegate` | `publish_helper.py:51`, `:96`, `:169` | ✅ |
| `CONFIG_DIR` governs the loop's config | `composition/settings.py:32` — `os.environ.get("CONFIG_DIR", "config/apps")` | ✅ |
| `CONFIG_DIR` governs the API's config too (separate process) | `composition/app.py:137-138` — `cfg_dir = config_dir or settings.config_dir`; `config_dir` param at `:50` defaults `None`, and the documented recipe passes nothing | ✅ |

### Ingest, seed and the false-pass traps behind STORY-182's ACs

| Claim | Address at `805287f` | Verified |
| ----- | -------------------- | -------- |
| `/topology` is seed-derived — passes with zero ingest | `api/v1/topology/service.py:29` docstring: *"sourced from the seeded topology"* | ✅ |
| `/components` likewise | `api/v1/components/service.py:21` — `list_components()` | ✅ |
| The dedupe marker is permanent | `adapters/persistence/dynamo_observation_repository.py:58-61` — `pk=f"EVT#{...source_event_id}"`, `sk="DEDUPE"` | ✅ |
| **Component status survives a reused CONTROL table** | `composition/seed_dynamo.py:44` — `#s = if_not_exists(#s, :default)` | ⚠️ **new — see AC2/AC1(e)** |
| **Watermarks live in the control table, dedupe in observations** | `run.py:78-80` wires `DynamoWatermarkRepository` to `settings.dynamo_control_table` | ⚠️ **new** |
| Unset `DYNAMO_ENDPOINT_URL` → real AWS with real credentials | `composition/dynamo.py:21-24` — the dummy `test`/`test` credentials are set **only inside** `if settings.dynamo_endpoint_url:` | ✅ (story said `:19-27`) |
| Default table names differ from the deployed ones | `settings.py:34-37` — `uptime-observations`/`uptime-control` vs deployed `uptime-monitor-*` | ✅ |
| A leftover sample-mode flag forces every observation DOWN | `composition/sample_mode.py:61-72` | ✅ |
| Components are seeded `OPERATIONAL` | `composition/seed_dynamo.py:49` — `":default": ComponentStatus.OPERATIONAL.value` | ✅ |
| The vendor-health probe runs at startup, before the loops are built | `composition/run.py:197` | ✅ (story AC4 said `:196`) |
| `.env` is loaded by walking up from the source file, not CWD | `composition/run.py:179` — `load_dotenv()`, rationale `:172-178` | ✅ |
| A future row is silently quarantined and its count discarded | `ingest_service.py:37` `FUTURE_TOLERANCE = 5min`; `:121` writes to `_rejected_repo`; `run.py` passes no `on_cycle` | ✅ |
| **`availability_pct` / `completeness_pct` are 0–1 FRACTIONS, not percentages** | `core/queries/availability.py:261` (`passing_verdicts / denominator`), `:266-267` (`len(observations) / completeness_denominator`) | ⚠️ **new — the `_pct` trap the checklist names** |
| **…over a default 24h window**, so a minutes-long run yields `completeness_pct ≈ 0.002` | `api/v1/availability/controller.py:31-33` — window defaults to `until − 24h` | ⚠️ **new** |
| **`rollup.distinct_locations` is HARDCODED 0** | `availability.py:334`, deliberate, documented `:306-311` | ⚠️ **new — asserting `>=4` there can never pass; asserting `== 0` passes vacuously forever** |
| `check_vendor_id_health` needs ≥1 row in the trailing **2h window** | `composition/vendor_health.py:37` (`_HEALTH_CHECK_WINDOW = "2h"`), `:50` (`from:now()-2h`), `:113` (`if count == 0`) | ⚠️ **new — not "2h of coverage"** |
| …and the healthy branch is **NOT silent** | `vendor_health.py:126-133` logs INFO per healthy signal; `run.py:163` sets `basicConfig(level=INFO)`. (Its own docstring at `:86` says "logs nothing" — the docstring is wrong; write the gate against the code) | ⚠️ **new** |
| An unseeded monitor id returns `[]` rather than erroring | `tools/demo_engine/store.py:59-72` filters `self._rows` by `dt.synthetic.monitor.id` | ⚠️ **new — the B1 mechanism** |
| The loop never returns and takes no stop signal | `run.py:218` `await asyncio.gather(*loops)` over 41 `run_periodic` coroutines; `build_live_loop` (`run.py:140-150`) passes no `stop_event`/`on_cycle`, though `run_periodic` accepts both (`pull_loop.py:146-150`) | ⚠️ **new** |
| The first cycle fires before the first sleep | `pull_loop.py:160` docstring | ✅ |
| Writes are commit-first | `decide.py:108-111` | ✅ |
| `distinct_locations` **is** real on the per-signal children | `api/v1/availability` per-signal DTO; `/history` `ObservationDTO.location` at `api/v1/history/models.py:30` | ✅ |

### The demo engine, for STORY-183 and STORY-184

| Claim | Address at `805287f` | Verified |
| ----- | -------------------- | -------- |
| A token is written immediately before the 202 | `tools/demo_engine/server.py:103-105` | ✅ |
| Auth is checked BEFORE the cache is touched (AC5) | `server.py:112` returns early; the `pop` is at `:124` | ✅ |
| The poll consumes the token | `server.py:124` — `self.server.results.pop(token, None)` | ✅ |
| A repeat poll 404s | `server.py:125-127` | ✅ |
| **The cache attribute is `_DemoHTTPServer.results`, reached from tests as `server._httpd.results`** | `server.py:48`; `backend/tests/demo_engine/test_server.py:106` | ⚠️ **new — AC4 and the story both write `server.results`** |
| **The server is threading, and the cache is a bare dict** | `server.py:37` extends `ThreadingHTTPServer` | ⚠️ **new — a sweep iterating live risks `RuntimeError: dictionary changed size during iteration`** |
| Consume semantics belong to STORY-180, **not** STORY-148's wire contract | `test_server.py:92-96` docstring attributes the test to "STORY-180 AC4 (minor 5)"; `server.py:117-123` comment likewise | ✅ **— this is what makes STORY-183 AC2 a correction, not an AC5 violation** |
| The orphan path is reachable: a failed poll raises and abandons the token | `grail_executor.py:111` | ✅ |
| …and the loop survives it, keeping the orphan alive | `pull_loop.py:200-207` | ✅ |
| Nothing re-polls today, so STORY-180 AC7 genuinely held | `grail_executor.py:127` returns at the first `SUCCEEDED` | ✅ |
| `expand_scenario`'s docstring claims "never after `end_time`" with no precondition | `tools/demo_engine/scenario.py:158-160` | ✅ **the story was right; the orchestrator's `:156-159` is withdrawn** |
| **The editable install is a plain `.pth` `sys.path` append, NOT a setuptools MetaPathFinder** | `.venv/Lib/site-packages/__editable__.uptime_monitor_v3-0.1.0.pth` contains exactly `C:\Hyn\uptime_monitor_v3\backend`; `pyproject.toml:23` `package-dir = {"" = "backend"}` | ⚠️ **new — the story and the first plan draft both said "finder". This makes STORY-187 AC3 EASIER: a `sys.path`-ordering test reproduces the real mechanism exactly rather than approximating it** |
| **Provenance is split-brain under pytest from a worktree** | `demo_engine.*` → the **worktree** (`backend/tests/conftest.py:37-39` inserts `.../tools` at `sys.path[0]`); `src.*` and `tests.*` → the **main tree** via the `.pth` | ⚠️ **new — a single "is this module under cwd?" check gives a false green for 183/184 and a false red for 182** |

## Story 1 — STORY-187, an import-provenance helper (1 pt)

`docs/scrum/stories/STORY-187-import-provenance-helper-for-proofs.md` — AC1–AC7 verbatim in the
brief. First because stories 2–4 all owe a discrimination proof and this is the tool that keeps one
honest.

### Steps

1. RED: a test asserting the helper raises a **named** error, with both the expected root and the
   actual resolved path in the message, when a module resolves outside the expected root (AC2).
2. GREEN: the helper in `tools/` — resolve the module, report `__file__` and the root, raise when it
   falls outside. Usable from a bare `python -c` one-liner (AC4 forces this; a `pytest`-only fixture
   does not satisfy it).
3. RED→GREEN: the editable-install regression test (AC3). **The mechanism is a `.pth` `sys.path`
   append, not a setuptools finder** — so build a second root containing a same-named module, append
   the "wrong" root to `sys.path` the way the `.pth` does, set `expected_root` to the other, and
   **first assert that a plain `import` really resolved to the wrong root** so the trap is live in the
   test rather than simulated only in the helper's arithmetic. Label it in the docstring as a `.pth`
   `sys.path`-entry reproduction (AC3 permits a labelled simulation and forbids an unlabelled one;
   here the label is nearly literal).
4. Provenance-report test (AC1).
5. Update `.scrum/checklists/implementer.md` (the A1-refinement line) and A3's lines in
   `implementer.md` + `quality-review.md` to name the helper, **keeping the manual `__file__` print
   as the documented fallback** (AC5 — the prose rung is not deleted).
6. Confirm AC6 mechanically: `git diff` touches nothing under `backend/src/`, and nothing under
   `backend/src/` imports the helper.
7. Record the actual one-liner invocation and its output in the story evidence (AC4).

### Reality gate (187) — the proof-checker gets checked, on the real mechanism

**The first draft of this gate was rejected in verification:** "a module inside the root passes, one
outside raises" is satisfiable with any stdlib module as the negative side, which proves
`Path.is_relative_to` works — not that the trap is caught. Since every other gate this sprint
delegates its provenance check to this helper, a weak gate here propagates.

The negative side must reproduce the `.pth` mechanism as in step 3, and must assert the plain import
resolved to the wrong root **before** the helper is consulted. Both sides recorded, and the verdict
states how they differed (A3).

## Story 2 — STORY-183, retention-bound the token cache (1 pt)

`docs/scrum/stories/STORY-183-demo-engine-token-cache-retention.md` — AC1–AC7.

**AC2 vs AC5 is settled, not open:** replacing STORY-180's
`test_results_cache_is_evicted_after_being_polled` is the correction AC2 mandates, **not** a wire
contract change AC5 forbids. Evidence: that test's own docstring attributes it to "STORY-180 AC4
(minor 5)" (`test_server.py:92-96`) and the `pop` comment attributes the consume semantics to
STORY-180 (`server.py:117-123`); AC5's enumerated contract (seven row fields, ns scale, both
grammars, async execute/poll, `Api-Token ` prefix) does not include cache-eviction semantics. The
replacement must keep asserting the **bound**, which AC4 does.

### Steps

1. RED: AC2's assertion — poll the same `request-token` twice inside the retention window, expect
   HTTP 200 + `state: "SUCCEEDED"` + identical records both times. **This is the assertion that
   fails before the change.**
2. GREEN: entries carry their insertion instant; eviction is by retention against an **injectable**
   clock (AC1 forbids real-time sleeping). Retention constant declared once with its reason at the
   literal. Eviction is **lazy**, and the sweep takes a `threading.Lock` or iterates a
   `list(self.results.items())` snapshot — `_DemoHTTPServer` extends `ThreadingHTTPServer`
   (`server.py:37`) over a bare dict, and STORY-182 will drive 41 concurrent signal loops through it.
3. Replace STORY-180's consume-semantics test and **state the replacement in the story evidence**
   (AC2's explicit requirement) so it is never read as a silently weakened test.
4. AC1: an entry never polled is evicted once past the window (injected clock / tiny retention).
5. AC3: a poll after eviction still returns `404 {"error": "unknown request token"}`.
6. AC4: drive N executes with **the injected clock advanced past retention between executes**, and
   assert the cache length stays **strictly below N** (ideally 1). With a stopped clock and lazy
   eviction, `len(...) <= N` passes while the leak is fully intact — a green gate with the AC unmet.
   Note the attribute: the cache is `server._httpd.results` (`server.py:48`,
   `test_server.py:106`) — **not** `server.results` as AC4's text and the first plan draft both
   wrote.
7. AC5: re-run STORY-148's wire-contract tests unchanged. Confirm auth still precedes any cache touch
   (`server.py:112` before `:124`).
8. AC6: `git diff` touches no file under `backend/src/`.

### Reality gate (183) — an eviction proof that cannot silently no-op

Two-sided with **differing sides**: tiny retention → the unpolled entry is gone and the length is
bounded; large retention → the same sequence keeps the entry and a repeat poll returns 200 with
identical records.

**Two traps closed after verification.** (i) If the implementation copies retention at server
construction, monkeypatching the module constant afterwards has no effect and **both sides behave
identically** — the sprint-63 `_delegate` shape again. The harness therefore prints the *server
instance's effective retention* before reporting either side, and prefers advancing the injected
clock over patching the constant. (ii) Provenance is checked for **`demo_engine.server`
specifically** — under pytest from a worktree that module resolves to the worktree while `src.*`
resolves to the main tree, so a generic check would give a false green here.

## Story 3 — STORY-184, the interval invariant on the type (1 pt)

`docs/scrum/stories/STORY-184-scenario-interval-invariant-on-the-type.md` — AC1–AC7.

### Steps

1. RED: AC5's pinning test — `SignalScenario(..., interval_seconds=-30, cycles=[["L1"], ["L1"]])`
   then `expand_scenario` must now raise instead of yielding a row at `end_time + 30s`. Confirmed
   reproducible at HEAD by the verifier: it currently returns
   `['2026-07-30T12:00:30.000000000Z', '2026-07-30T12:00:00.000000000Z']` for a 12:00:00Z `end_time`.
   Note `interval_seconds=0` produces two rows both at `12:00:00Z` — **duplicate timestamps, not a
   future row** — so AC5's future-row pinning is the `-30` case only; AC1 covers `0` at the type level.
2. GREEN: the sign/type invariant on the frozen type — `__post_init__` on the existing frozen
   dataclass, or the pydantic `frozen=True` + `model_validator(mode="after")` shape the domain
   already uses. Implementer's call; **state which and why**. Precedent for this exact field:
   `composition/config.py:34-51` and `core/domain/topology.py:50-55`.
3. `load_scenario_file` catches and re-raises as `InvalidScenarioError` so its path- and
   signal-key-prefixed messages survive.
4. AC1: direct construction rejects `-30` and `0`; a valid positive value constructs fine — both the
   rejected and the valid shape, per `implementer.md:32`.
5. AC2: rejects `"30"`, `30.5`, and `True` — a `bool` **is** an `int` subclass and must be rejected;
   this case is currently unpinned even at the loader.
6. AC3: **the seven existing loader rejection tests pass unmodified.** If any needs editing, the
   loader's contract has changed and that is called out, not absorbed.
7. AC4: make `expand_scenario`'s docstring claim (`scenario.py:158-160`) true — either leave it
   unconditional because it is now enforced, or state the one remaining caller-side caveat (a caller
   may still pass a future `end_time`; the guarantee is "at or before `end_time`", not "at or before
   now"). No site may claim more than the code enforces.
8. AC6/AC7: no `backend/src/` file changes; the test count moves only by this story's additions.

### Reality gate (184) — the future row, before and after

The step-1 pinning test is run at the story's parent commit (where it must **fail**, producing the
`12:00:30Z` row) and at the story head (where it must raise). Per A1's approved route, the before
side is taken by patching and restoring in the **main** tree — which also avoids the worktree
split-brain entirely. **The revert is `git checkout -- tools/demo_engine/scenario.py`, and no DoD
gate may be run while the tree is patched.** `git diff` must be confirmed empty afterwards.
Provenance is checked for **`demo_engine.scenario`**.

## Story 4 — STORY-182, the real loop run and its three-sided gate (5 pts)

`docs/scrum/stories/STORY-182-demo-loop-run-and-gate.md` — AC1–AC7 verbatim. 5-pointer ceremony:
implementer, then **spec ∥ quality reviewers concurrently**, then the scoped gate, then the
three-sided reality gate.

**Nothing in this story may modify `backend/src/`** (AC6). The system runs *unmodified*; that is the
entire point — and it is also why the loop must be terminated externally.

### B1 — AC3 and AC4 are unsatisfiable with the existing scenarios. This is scoped work, not a step.

Measured by the verifier:

```
clean-fleet.yaml           signals=1  components=1  locations=4
dark-location.yaml         signals=1  components=1  locations=3
dark-monitor.yaml          signals=1  components=1  locations=0
late-return.yaml           signals=1  components=1  locations=2
staggered-intervals.yaml   signals=2  components=1  locations=2

UNION of all five:         signals=6  components=5
FLEET declares:            signals=41 components=13   ->  35 signals with ZERO coverage
```

An unseeded monitor id returns `[]` (`store.py:59-72`), so those 35 signals ingest nothing and
`/history` is empty for them. AC4 is worse: `check_vendor_id_health` iterates **every** signal in the
loaded config (`vendor_health.py:96-97`) and warns on `count == 0` (`:113`) — 35 `VENDOR-ID DRIFT
SUSPECTED` warnings. The five existing scenarios are deliberately *partial* (a dark location, a dark
monitor, a late return); none reaches the thresholds, and their union does not either.

**A fleet-wide coverage artifact is therefore in scope and must be named in the implementation:**
`UP` cycles across all 4 declared locations for all 41 native monitor ids, with ≥1 row per signal
inside the trailing 2h window. Either a checked-in `config/demo/scenarios/whole-fleet.yaml` or a
harness builder that constructs `SignalScenario`s from the loaded demo config — **implementer's
call, stated with its reason.** The builder route is why STORY-184 must land first: it constructs
`SignalScenario` in code, which is exactly the path the type invariant guards.

### Preconditions, asserted and recorded before the loop starts (AC1)

Each is an assertion with its value recorded in the evidence — not an assumption:

- (a) `CONFIG_DIR` → `config/demo` on **both** the loop and the API process. The API loads its own
  config (`app.py:137-138`) and defaults to `config/apps` (`settings.py:32`), which declares a
  **real** `statuspage_component_id` (`config/apps/httpcheck.yaml:8`).
- (b) `DYNAMO_ENDPOINT_URL` → `http://127.0.0.1:8021` and the table names are the demo ones, on
  **both** processes — never unset, never `uptime-monitor-*`. Unset, `dynamo.py:21-24` omits the
  dummy credentials and boto3 targets real AWS us-east-1 with the operator's real credentials.
- (c) `GET /api/v1/sample-mode` → `{"enabled": false}`. An ON flag forces **every** observation DOWN
  (`sample_mode.py:61-72`).
- (d) STORY-176's publish-guard checks re-run green **at this story's HEAD**.
- (e) **NEW (B4):** `GET /api/v1/components` shows every component `status == "operational"` before
  the loop starts, values recorded. `seed_dynamo.py:44` seeds status with
  `#s = if_not_exists(#s, :default)`, so on a reused control table a non-`OPERATIONAL` status
  **persists** — and then with UP-only observations `severity_rank(proposed) < severity_rank(current)`
  makes `proposed_is_better` true, `decide.py:122-126` fills `publish_change`, and `:171-172`
  **calls `publish()`**. AC5's recorded rationale would be false on the safety-critical path.

### Process topology and loop lifecycle — declared, because AC1(a) is ambiguous

Both a real `uvicorn` subprocess and an in-process `create_app()` + `TestClient` are defensible
readings of "the API process", and they verify **different** things about `CONFIG_DIR`. The
implementer declares which and why; the plan requires the choice to be stated and its consequence
for AC1(a) acknowledged. A `uvicorn` subprocess is the reading that actually exercises the
two-process `CONFIG_DIR` trap AC1(a) exists for, and is preferred absent a stated reason otherwise.

The loop: `run.py:218` awaits `gather` over 41 `run_periodic` coroutines with **no `stop_event`**
(`run.py:140-150`), and AC6 forbids editing `backend/src/` — so it must be killed externally. The
evidence must state the launch command, the run duration and **why that duration suffices** (the
first cycle fires before the first sleep, `pull_loop.py:160`, so one cycle per signal completes
early), the exact termination call, and what makes writes durable at kill time (commit-first,
`decide.py:108-111`).

### Steps

1. Build the run harness under `tools/` (not `backend/src/`): the B1 coverage artifact, the demo
   engine, the declared process topology, and assertion + recording of every AC1 precondition
   including (e).
2. **Fresh observations *and* control tables** (AC2 + B4), created via `scripts/create_tables.py`
   with `DYNAMO_OBSERVATIONS_TABLE` / `DYNAMO_CONTROL_TABLE` set **identically on both processes** —
   each process runs its own `load_settings()`, so this is the same two-process trap as `CONFIG_DIR`.
   Control matters as much as observations: watermarks live there (`run.py:78-80`) and component
   status survives there (B4). State in the evidence which strategy was used and why; if the
   `observed_at >= run-start` alternative is taken instead, it must additionally cover the stale
   watermark and the persisted status.
3. Run the loop; capture the startup `check_vendor_id_health` output (`run.py:197`). AC4 requires
   **no** dead ids across the ≥40 demo signals — i.e. zero `VENDOR-ID DRIFT SUSPECTED` warnings, and
   (per the code, not its docstring) **one `Vendor-id health OK` INFO line per healthy signal**.
4. AC3, the ingest proof, from **observation-derived** endpoints — with the unit traps closed:
   - `GET /api/v1/history?signal_key=…` — count distinct `location` values over the returned
     `ObservationDTO`s (`api/v1/history/models.py:30`) for the **≥4 locations** proof, or use the
     per-signal `signals[].distinct_locations`.
   - **Do NOT assert locations off `rollup.distinct_locations` — it is hardcoded 0**
     (`availability.py:334`). Asserting `>= 4` there can never pass; asserting `== 0` passes
     vacuously forever.
   - `availability_pct` / `completeness_pct` are **0–1 fractions over a default 24h window**
     (`availability.py:261,266-267`; `controller.py:31-33`), so a minutes-long run yields
     `completeness_pct ≈ 0.002`. Any assertion must either pass an explicit narrow window or assert
     an exact expected fraction — **never** "high completeness", which fails, and never a loose
     bound, which passes vacuously.
   - `/components` and `/topology` are recorded and **explicitly labelled seed-derived: they pass
     with zero ingest and are not the proof.**
5. AC5: assert `GET /api/v1/approvals` returns a well-formed **empty** result, and record why it
   must — with only `UP` observations and every component `OPERATIONAL` (asserted at AC1(e), not
   assumed from `seed_dynamo.py:49`), `proposed_status == current_status`, so `decide` takes neither
   branch and `publish_change` stays `None` (`decide.py:119-126`). **Record the consequence
   explicitly:** `publish` is never called, so any "no Statuspage POST was attempted" log line is
   **vacuous** and proves nothing about the guard. The guard's evidence is the `_delegate`-chain
   assertion below, never this silence.
6. AC6: verify mechanically from the commit range that no file under `backend/src/` is modified.
7. Update the wiki (`demo-engine.md` at minimum) and `CLAUDE.md`'s demo-engine section — this story
   makes CLAUDE.md's "No demo loop is started yet" false.

### Reality gate (182) — three sides, and each pair must differ

1. **Positive** — the full run as AC3/AC4 describe, on fresh observations *and* control tables.

2. **Discriminating on the guard.** **The first draft of this side could not come back negative, and
   the verifier proved it:**

   ```
   SAFE   top-level type : StatusWritebackPublisher
   UNSAFE top-level type : StatusWritebackPublisher      <- same; the type assertion is useless
   SAFE   _delegate chain: [StatusWritebackPublisher, LoggingPublisher]
   UNSAFE _delegate chain: [StatusWritebackPublisher, BestEffortPublisher, RecordingPublisher, StatuspagePublisher]
   SAFE   .delegate chain: [StatusWritebackPublisher]    <- the sprint-63 trap, length 1
   UNSAFE .delegate chain: [StatusWritebackPublisher]    <- identical, and falsely looks safe
   ```

   `build_publisher` returns `StatusWritebackPublisher` in **both** branches
   (`publish_helper.py:234`, outside the `if`/`else`). So: against a throwaway config that *does*
   declare a `statuspage_component_id` (a fake vendor id), assert the **full `_delegate` chain of
   type names** equals `[StatusWritebackPublisher, LoggingPublisher]` on the safe side and
   `[StatusWritebackPublisher, BestEffortPublisher, RecordingPublisher, StatuspagePublisher]` on the
   unsafe side; assert the two chains **differ**; and **treat a chain of length 1 on either side as a
   harness defect (the wrong attribute was walked) whose result is DISCARDED, not reported.**
   **Make no network call.**

3. **Discriminating on backfill.** Restated after verification — the first draft was wrong in both
   directions. The code needs **≥1 row inside the trailing 2h window**, not "≥2h of coverage"
   (`vendor_health.py:37,50`; `store.py:74-82`), and the healthy branch is **not silent** — it logs
   INFO per signal (`:126-133`, with `run.py:163` at INFO level). So: an engine with **zero** rows in
   the trailing 2h → one `VENDOR-ID DRIFT SUSPECTED` warning **per signal (41)**; an engine with ≥1
   row per signal in the window → **zero** drift warnings and one `Vendor-id health OK` INFO per
   signal. **Assert both counts on both sides.**

All three sides print module provenance via STORY-187's helper before reporting anything, naming
**`src.composition.run` and `src.composition.publish_helper`** specifically (not a generic
under-cwd check, which would give a false red here — `src.*` resolves to the main tree via the
`.pth`). The recorded verdict must state, per A3, **how each pair differed**.

## Safety — read before dispatching story 4

This is **the first time a loop is started in this repo.** `decide` publishes recoveries with no
human gate. The guard is config-only and needs `CONFIG_DIR` on **both** the loop and the API
process. `config/demo/` declares no `statuspage_component_id` on any component, and its component ids
are deliberately **disjoint** from `config/apps`'s because `StatuspagePublisher` keys on the
canonical component id (`adapters/outbound/statuspage/__init__.py:41-46`) — a collision would PATCH
the real public page even with an empty mapping elsewhere. Real Statuspage credentials **are**
present: the repo-root `.env` supplies them from any launch directory, because `load_dotenv()` walks
up from the source file, not CWD (`run.py:179`). And per B4, a reused control table can make `decide`
call `publish()` even under UP-only observations.

## Tooling notes (known friction, not blockers)

- **STORY-179** (`dynamo_local`'s ephemeral host port is not always routable on Windows) — worked
  around all sprint with the fixed-port container `uptime_dynamo_8021` and an explicit
  `DYNAMO_ENDPOINT_URL`. Not fixed here.
- **The silent 53 skips** — see "Branch and baseline". Every backend gate record carries its
  pass/skip counts; a nonzero skip count is an incomplete gate.
- **Two docstrings that contradict their code**, both noted so gates are written against the code and
  neither is fixed here (out of scope, candidates for STORY-186's successor):
  `vendor_health.py:86` claims a healthy id "logs nothing" while `:126-133` logs INFO; and
  `api/v1/availability/models.py` describes `rollup` as "MIN of non-None percentages, SUM of counts",
  which misdescribes `distinct_locations` — it is neither, it is hardcoded 0.
- **STORY-178** (ANSI escapes in the gate fragment) — cosmetic, still open, not in scope.
- Tooling is frozen at lock, like scope. No new MCP servers or scripts mid-sprint.

## Wiki blast radius (expected)

`yt_wiki.py` at `805287f`: **sweep CLEAN, facts CLEAN, links CLEAN, integrity CLEAN.** Two advisory
`code_refs` amplifier notes (`composition/run.py` in 4 articles, `pyproject.toml` in 5) — advisory
only, but note that any touch of `run.py` quarantines four articles at once. STORY-182 modifies no
`backend/src/` file, so this should not trigger.

Expected to need updating at the sprint-end compile pass:

- `demo-engine.md` — stories 2, 3 and 4 all change what it describes; STORY-182 makes its "the run
  itself is not wired up" statement false.
- `dev-setup-and-dod.md` — the 53-skip finding belongs here as a Fact with its pinning evidence.
- `ingest-service-and-pull-loop.md` / `statuspage-publish.md` — re-verify only, if untouched.
- `CLAUDE.md` — the demo-engine section's "No demo loop is started yet (STORY-182, sprint 64)"
  becomes false in story 4.

Per working agreement A2, any behavioural Fact added must cite the test that pins it. Strong
candidates from this plan's verification: the `_pct` fraction semantics, the hardcoded
`rollup.distinct_locations`, and the `.pth` provenance mechanism.

## Plan verification — `yt-plan-verifier`, verdict GAPS, all 8 blocking findings folded in

Dispatched pre-lock: the sprint is contract-sensitive on every count that matters — STORY-182
consumes another component's output across a vendor adapter path, runs three live processes, and its
guard is safety-critical with real credentials on disk. **Verdict GAPS: 8 blocking, 11 advisory.**
Every blocking finding is folded into the sections above; the two that would have wrecked the sprint:

| # | Finding | Where it landed |
| - | ------- | --------------- |
| B1 | AC3/AC4 unsatisfiable — the five scenarios cover 6 of 41 signals; 35 ingest nothing and each warns | New scoped artifact, story 4 "B1" |
| B2 | **Reality gate side 2 could not come back negative** — `build_publisher` returns the same top-level type on both sides (`publish_helper.py:234`); proven with a probe | Side 2 rewritten to a `_delegate`-chain equality + difference assertion, with length-1 discarded |
| B3 | STORY-182 is 5 points, not 3, and hides B1's authoring plus a first-in-repo process harness | Re-pointed; sprint 8 pts; explicitly not split (A1 forbids shipping the run without its proof) |
| B4 | AC5's rationale and the no-publish property need a fresh **control** table, not just observations | New AC1(e) precondition + step 2 rewritten |
| B5 | The loop never returns, takes no `stop_event`, and AC6 forbids editing `backend/src/`; "the API process" is ambiguous | New "Process topology and loop lifecycle" section |
| B6 | `_pct` fields are 0–1 fractions over a 24h window; `rollup.distinct_locations` is hardcoded 0 | Contract table + step 4 rewritten with an explicit prohibition |
| B7 | Gate side 3 wrong in both directions — needs ≥1 row in a 2h window, and the healthy branch logs INFO rather than being silent | Side 3 restated as two asserted counts per side |
| B8 | STORY-187's gate differed for a reason unrelated to the trap (any stdlib module satisfies it) | Gate rewritten to reproduce the `.pth` mechanism and assert the import really went wrong |

Advisories folded in: A1 (citation corrections — including **withdrawing the orchestrator's own
wrong "correction"** of `scenario.py:158-160`, and `decide.py:122-126`), A2 (AC4's vacuous bound),
A3 (the no-op constant patch), A4 (`server._httpd.results`), A5 (the threading sweep), A6 (the `.pth`
mechanism, which makes AC3 *easier*), A7 (per-gate module naming under the split-brain), A8 (two
lying docstrings, noted not fixed), A9 (the named revert command), A10 (the fresh-table env matrix),
A11 (**the day-1 spike** — ordering kept, risk posture changed).

Verification also **confirmed** four things, worth recording so they are not re-litigated: the
baseline (`614 passed`, 0 skips); STORY-184's before-side defect reproduces exactly as stated;
STORY-183's AC2-vs-AC5 tension resolves in AC2's favour on documented evidence; and the
187 → 183 → 184 → 182 order is right on dependencies.
