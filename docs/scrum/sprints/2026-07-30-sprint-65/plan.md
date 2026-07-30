# Sprint 65 — Plan

**Status:** verified pre-lock; awaiting PO approval.
**Mode:** `external` — the PO implements via an external AI agent building to **this document alone**.
**Points:** 13 across 5 stories.
**Branch:** `sprint-65`, to be branched from `ca5a9c6` (the sprint-65 refinement commit on `sprint-64`).

## Sprint goal

**Make the failure half of the system real.** Today no `DOWN` or `DEGRADED` observation can reach the
pipeline through the real ingest path at all — `map_synthetic_status` raises on every non-`HEALTHY`
code, so the demo engine emits `UP` and absence only, and nothing in this repo may be described as
"the failure path is tested". This sprint closes that in three coupled steps: make a bad row
survivable, land a provisional failure mapping, then drive a real `DOWN` **and a real recovery
publish** through the live loop on the demo fleet. Backend + `tools/` only; **no frontend work**.

## Mode: why `external`, and what it costs

The PO chose `external` for this sprint (2026-07-30). Two standing consequences:

1. **`plan.md` is the entire contract.** External implementers build literally and infer nothing
   (`execution-modes.md §2`), so every story below carries method-level build detail — exact names,
   exact return shapes, exact seams.
2. **Every story gets both reviewers regardless of size** — `yt-spec-reviewer` +
   `yt-quality-reviewer` per story, plus an independent `yt_gate.py` re-run by the orchestrator
   before any story goes `done`. History: external mode ships roughly **one MAJOR per 3-point
   story**, and sprint 47's external delivery self-reported "all nine gates clean" while carrying two
   quality MAJORs and two gate commands that had never run against a DB.

**This is not the sprint-60 situation.** That rejection was UI-specific ("you only implement" for
look-and-feel work). Sprint 65 is backend and `tools/`, judged by tests and exit codes.

**STORY-188 is NOT handed to the external agent.** It edits `.scrum/checklists/`. YourTeam's *What You
Never Do* forbids a subagent writing `.scrum/` state, and an external agent sits further outside than
a subagent. **The orchestrator executes STORY-188 itself.**

## Scope and execution order

| # | Story | Pts | Who | Why here |
| --- | --- | --- | --- | --- |
| 1 | **STORY-188** — normalize checklist encoding | 1 | **orchestrator** | Until it lands, every dispatch reading a checklist carries a corruption risk that **already fired once** during STORY-187. |
| 2 | **STORY-190** — quarantine the bad row, keep the batch | 3 | external | A single unmappable row currently stalls a signal **permanently**. Fix the poison before adding row variety. Changes the `fetch_observations` contract → highest structural risk, so early. |
| 3 | **STORY-177** — provisional failure-code mapping | 3 | external | Lands the mapping on a path that already degrades gracefully. |
| 4 | **STORY-191** — a real `DOWN` and a real recovery publish through the loop | 5 | external | The payoff and the reality gate for 190 + 177. Highest risk → last. |
| 5 | **STORY-185** — un-gate the unsafe side of the publish proof | 1 | external | Independent; gates nothing. Only remaining drop candidate. |

**Cut from scope at verification (PO-approved 2026-07-30):** **STORY-186** and **STORY-189** return to
the backlog as sprint-66 candidates. This was not only a sizing move — it **eliminates both file
collisions** the plan verifier found: STORY-186 AC2/AC4 rewrite the very `test_scenario.py` rejection
tests and `load_scenario_file` validation code that STORY-191 extends, and STORY-189 fights STORY-191
over `demo-engine.md` frontmatter. Dropping them removes two fix-round risks at once.

**Sizing, recorded honestly:** STORY-191 was re-pointed **3 → 5** on the verifier's independent
judgement (it needs scenario vocabulary + validation + tests, four scenario files, a new harness seam,
a row-merge strategy, an event-id namespace, persisted-state assertions across four stores, and a
non-zero-exit artifact shown failing). The sprint stays at **13 points** — the size the PO already
approved — because 186 and 189 came out. Still above the ~9–11 pacing baseline; **the sole remaining
drop candidate is STORY-185.** Never break the 190 → 177 → 191 chain: a partial chain ships a mapping
nothing exercises.

## Verified baseline (precondition)

- Tree clean at `ca5a9c6` apart from this untracked sprint directory.
- Sprint-64 close recorded the full 8-command gate green: **666 passed, 0 skipped**;
  `yt_selftest` **28/28**; `yt_wiki` clean on all four checks.
- `yt_selftest` re-run green this session. Container `uptime_dynamo_8021` up on `127.0.0.1:8021`.

---

## Binding cross-story constraints

### C1 — Zone discipline (CLAUDE.md §4), including where the gate cannot see it

Every dependency arrow points inward toward `core`; `core` has no outgoing arrows. The eight
`lint-imports` contracts must pass **unedited** — **no contract may be modified or relaxed for any
story in this sprint.** If a change appears to require editing a contract, stop and raise a blocker.

**The gate is a floor, not a ceiling.** The single most important paragraph in this plan:

> Having an **inbound adapter** import `src.core.ports.rejected_observation_repository` and write
> quarantine rows itself **passes all eight contracts** — verified against `pyproject.toml:38-105`:
> `core-independence` (`:41-42`) has `src.core` as *source* (wrong direction);
> `adapters-independence` (`:53-56`) lists only the three adapter subpackages;
> `adapters-edge-only` (`:83-87`) forbids only `src.api`/`src.composition`. It is still wrong: it
> turns a pure translation layer into an orchestrator holding a persistence dependency. **Do not do
> it.** No mechanical check will stop you.
>
> **The gate catches only half the trap.** Reaching for the *concrete*
> `src.adapters.persistence.dynamo_rejected_observation_repository` instead **does** break
> `adapters-independence` (`pyproject.toml:53-56`). Only the **core-port** route is invisible. So a
> red gate here means you took the concrete route; a green gate does **not** mean you took the right
> one.

Rules that hold beyond the gate:

- An **inbound adapter is a pure translation function** — returns values, persists nothing, holds no
  repository reference. Vendor vocabulary (`code`, `message`, status literals, raw row dicts) never
  leaves `adapters/inbound/dynatrace/`.
- Only **`composition`** may see both sides and decide what happens to an adapter's output.
- A port the core owns must be expressible **in domain types**. If an interface would have to name
  vendor words, it does not belong in `core/ports/`.
- **`tools/` may import `src.*`; `src.*` may never import `tools/`.** A shared constant lives in
  `backend/src/` and `tools/` imports it — never a duplicated literal. (`tools/` is outside
  `root_package = "src"`, so this direction is **ungoverned by the contracts** — prose only.)

### C2 — Evidence rules (working agreements A6, A7 — sprint-64 retro)

- Any reality-gate / proof artifact **ends with an explicit verdict and a non-zero exit on failure**,
  and must be **shown failing on deliberately bad input**. A green-only artifact is not evidence.
- A **polling timeout is a FAILURE**, not partial evidence.
- The board records an artifact's **exit code**. Values read from stdout are not evidence.
- Run `pytest` with **`REQUIRE_DYNAMO=1`** and record **pass/skip counts**. A nonzero skip count is an
  incomplete gate. (`REQUIRE_DYNAMO` makes `conftest.py`'s `dynamo_local` fixture fail instead of
  silently skipping 53 tests. The DoD's `(requires-env: ...)` annotation is **advisory** in
  `yt_gate.py:158-160` and never blocks — **the fixture is the enforcing rung**.)

### C3 — TDD and commit cadence

Strict TDD, **a commit after every green step**, `STORY-NNN:` message prefix, on `sprint-65` only.
That cadence *is* the crash-recovery mechanism. **Never one lump commit.**

### C4 — Environment preconditions

- `DYNAMO_ENDPOINT_URL=http://127.0.0.1:8021`, container `uptime_dynamo_8021`, Docker Desktop running
  (STORY-179 workaround: the fixture's ephemeral port is mapped by Docker but not always routable on
  Windows).
- `REQUIRE_DYNAMO=1` on every gate run.
- Python 3.13.9 in the repo `.venv`; invoke `.venv/Scripts/python.exe` directly on Windows.
- `.venv/Scripts/lint-imports.exe` is **blocked by Windows Application Control** — use the `python -c`
  form.

### C5 — ⚠ Publish safety (binding on STORY-191)

`decide` publishes recoveries with **no human gate** (`core/services/decide.py:122-126` sets
`publish_change` and `action = PUBLISHED_RECOVERY`; `:171-172` calls `self._publisher.publish(...)`).

**Corrected threat model** (the draft of this plan got this wrong; verified against code):

- A **degradation never publishes.** `decide` opens a proposal and publishes nothing
  (`decide.py:128-136`). Degradations wait for human approval.
- A **recovery publishes** only when `severity_rank(proposed) < severity_rank(current)`
  (`decide.py:115-117`). `STATUS_SEVERITY` is `OPERATIONAL 0, DEGRADED 1, PARTIAL_OUTAGE 2,
  MAJOR_OUTAGE 3` (`core/domain/status.py:63-68`).
- Every component is seeded **`OPERATIONAL`** (`composition/seed_dynamo.py:49`), and the **only**
  writer of component status is `StatusWritebackPublisher.publish` (`publish_helper.py:179`),
  reachable from `ApprovalService.approve` (`core/services/approval.py:69`) or `decide`'s own recovery
  branch.
- **Therefore a `DOWN`-then-`UP` observation ladder cannot publish anything** — from a seeded
  `OPERATIONAL` baseline the proposal path yields `PROPOSED` then at most `OBSOLETED`
  (`decide.py:157-169`). STORY-191 reaches the publish path by **pre-setting a component's stored
  status to a worse-than-`OPERATIONAL` value** (a real, reachable state: a previously-approved
  degradation), so an all-`UP` ladder proposes `OPERATIONAL` and trips the recovery branch. This also
  means a **static, past-anchored store and a single cycle are sufficient** — no live row injection.

**The guard is config-only.** `config/demo/` declares no `statuspage_component_id` on any component
(verified: 3 fleet files + 5 scenarios, **zero** occurrences; the only one in `config/` is
`config/apps/httpcheck.yaml:8` → `xdnywbx77npw`). So `Config.statuspage_mapping()`
(`composition/config.py:554-564`) returns `{}`, and `build_publisher`'s guard at
`publish_helper.py:211` falls through to the `else` at `:230-231`, yielding
`StatusWritebackPublisher(LoggingPublisher(), component_repo)` — **even with real credentials
present**, which the repo-root `.env` does supply from any launch directory because
`run.py:179`'s `load_dotenv()` walks up from the source file, not CWD.

**`CONFIG_DIR=config/demo` on BOTH processes, or neither is guarded:**

- the loop — `composition/run.py::main` → `build_live_loop`, reading `settings.config_dir` (default
  `config/apps`, `settings.py:32`; used at `run.py:183`);
- the API's **approve trigger** — `composition/app.py:137` (`cfg_dir = config_dir or
  settings.config_dir`), and `asgi.py` calls `create_app()` with **no** `config_dir`. It genuinely
  consumes Statuspage secrets at `app.py:169-183`.

Demo component ids are **disjoint** from `config/apps`'s (13 demo ids `api-gateway`…`catalog-service`
vs `http-check`), because `StatuspagePublisher` keys on the canonical component id
(`adapters/outbound/statuspage/__init__.py:41-46`).

Fake vendor credentials on both subprocesses are **defence in depth, never the guard**.
Fail-safe bonus: if `config/demo` fails to load, `app.py:147` sets `seed_config = None` and
`:171-175` yields `mapping = {}` → `LoggingPublisher`. Failure to load degrades **safe**.

---

## Verified API contracts

Every signature below was read from the tree at `ca5a9c6` and independently re-verified by
`yt-plan-verifier`. Build against these, not memory.

### `RejectedObservationRepository` — `backend/src/core/ports/rejected_observation_repository.py:19-26`

```python
def save(self, *, signal_key: str | None, reason: str, payload: dict, rejected_at: datetime) -> None
```

Its docstring (`:31-32`) already states the intent STORY-190 needs: *"Rejection is never a poison
pill — the caller persists this and moves on to the rest of the batch."* Written for validation
rejects; fits normalization rejects **unchanged**. `payload` is an opaque `dict`, so a raw vendor row
carries no vendor shape into `core`. **No new port and no new domain type are required.**

### `dispatch` — `backend/src/adapters/inbound/dynatrace/dispatch.py`

`_NORMALIZERS` `:44-46` · `UnsupportedMonitorTypeError` `:49` · `normalize_row` `:56` ·
`normalize_rows` `:73` · the defect comprehension `:80` · `MalformedDqlRowError` re-export `:29-31`.

Three exceptions can escape per row: `UnknownVendorStatusError` (`health_mapping.py:50`),
`UnsupportedMonitorTypeError` (`dispatch.py:49`), `MalformedDqlRowError`.

### `adapter` — `.../adapter.py`

`DEFAULT_OVERLAP` `:21` · `fetch_observations(*, signal_key, native_id, watermark, executor, overlap)
-> list[SignalObservation]` `:24-44`.

### `health_mapping` — `.../health_mapping.py`

`_OUTCOME_TO_HEALTH` `:23-27` · `UnknownVendorOutcomeError` `:30` · `map_execution_outcome` `:34` ·
`UnknownVendorStatusError` `:50` · `map_synthetic_status` `:54`, healthy OR-rule `:65-66`, raise
`:68-70`.

**`Health.DOWN` and `Health.DEGRADED` already exist** and are already mapped by `_OUTCOME_TO_HEALTH`.
STORY-177 therefore needs **no `core/` change at all**.

### `pull_loop` — `backend/src/composition/pull_loop.py`

`run_cycle` returns `IngestResult | tuple[IngestResult, DecideAction]` (`:82`).
Body: `watermark_repo.get` `:101` → `fetch_observations` `:102-108` → `ingest_observations` `:109`.
Orchestration comment `:111`, `orch_params` `:112-119`, guard `if all(...)` **`:120`**.
`run_periodic` **`:137-219`**; its `on_cycle` is typed against that same union (`:147-150`); it builds
the `run_cycle` call at **`:186-199`** and catches/logs/continues at `:200-207` (by design, STORY-050).

### `ingest_service` — `backend/src/core/services/ingest_service.py`

`FUTURE_TOLERANCE` `:37` · `self._watermark_repo.advance(...)` **`:139`** — verified by exhaustive
grep to be the **only** `advance()` call in `backend/src/` and `tools/`.

### `query` — `.../query.py`

`build_dql_query` adds **only a lower bound** (`timestamp >= toTimestamp(since)`, `:91-99`) — **no
upper bound, no limit** — and `sort timestamp asc` (`:102`).

### `decide` / `status` / `seed`

`decide.py:115-117` rank comparison · `:122-126` recovery branch · `:128-136` degradation opens a
proposal and publishes nothing · `:157-169` `OBSOLETED` · `:171-172` the publish call.
`core/domain/status.py:63-68` `STATUS_SEVERITY`. `composition/seed_dynamo.py:49` seeds `OPERATIONAL`.

### `publish_helper` — `backend/src/composition/publish_helper.py`

Guard `:211` · credentialed chain `:212-227` (`RecordingPublisher` writes a `publications` row on
**every** attempt, per STORY-072) · safe fallback `:230-231` (`LoggingPublisher`, **no**
`RecordingPublisher`) · `StatusWritebackPublisher.publish` `:179` (the only component-status writer).

### `scenario` — `tools/demo_engine/scenario.py`

`SignalScenario(signal_key, monitor_id, interval_seconds, cycles: list[list[str]])` with
`__post_init__` rejecting non-`int`/non-positive `interval_seconds` (STORY-184) ·
`InvalidScenarioError` · `load_scenario_file` (per-cycle validation currently requires `list[str]`) ·
`expand_scenario(scenario, *, end_time)` — **past-anchored**, `cycles[-1]` at `end_time`, event ids
`f"{signal_key}-{seq}"`.

### `rows` — `tools/demo_engine/rows.py:52-63`

`build_row(..., status_code=STATUS_CODE_HEALTHY, status_message=STATUS_MESSAGE_HEALTHY, ...)` —
**`status_code`/`status_message` are already parameters (`:59-60`), so the row builder needs NO
change.**

### `tools/demo_engine/assumed_failure_codes.py`

`ASSUMED_DOWN_CODE = "1"` `:33` · `ASSUMED_DOWN_MESSAGE = "UNHEALTHY"` `:34`. **There is no DEGRADED
pair.** Docstring claims at `:16-18` and `:31-32` — and also `:11-14`, `:20-22`, plus
`tools/demo_engine/README.md:22` — become **false** when STORY-177 lands.

### Anti-flap thresholds — **units matter**

All three demo fleets declare `thresholds: {major: 5, partial: 3, degraded: 2, recovery: 2}`
(`config/demo/fleet-core.yaml:38`, `fleet-edge.yaml:39`, `fleet-platform.yaml:39`). These are
**consecutive-CYCLE counts**, not seconds and not percentages — `anti_flap` compares them against
`streak_.length` (`core/services/pipeline.py:219-239`), and `streak` reads **backward from the newest
cycle** (`:113-124`). `_collapse_health` (`:85-98`) maps both "all degraded" and "a mix" to
`Health.DEGRADED`. Window bound: `orchestrate.py:98` computes
`since = until − (max_threshold + 2) × interval` — a **7-cycle window** for these fleets, so a ladder
longer than 7 cycles loses its head.

### Harness — `tools/demo_loop_gate/harness.py`

`run_positive_side(*, api_port=API_PORT, loop_wait_seconds=90.0) -> dict` **`:335-339`** — **takes no
store or scenario parameter**; `:419` hardcodes `build_fleet_row_store(cfg, end_time=run_start)`; one
cycle per signal then terminate `:352-356`. `_assert_ac3_ingest` `:279-295` asserts
`signals_with_zero_rows == []` **and** `signals_with_under_4_locations == []` across all 41 signals;
`_assert_ac4_vendor_health` `:298-310` asserts zero drift warnings; `_wait_for_last_signal` polls for
`distinct_locations >= 4` (`:187`). The `UP`-only→no-publish mechanism is already documented at
`:828-832`. `guard_reality_gate.py` is already correctly shaped: `main() -> bool`,
`sys.exit(0 if main() else 1)` at `:132`, with both a safe and a deliberately-unsafe side — but it
runs **in the harness process** (`:83-128`) and never observes the subprocess.

### Dedupe — `backend/src/adapters/persistence/dynamo_observation_repository.py:57-61, 68-79`

`save_new` writes `pk=EVT#<source_event_id>, sk=DEDUPE` under `attribute_not_exists(pk)`. **Identical
event ids are silently dropped as duplicates, with no error.**

### Existing call sites that must keep working (STORY-190 AC7) — verified complete

`backend/tests/test_dynatrace_adapter.py:169,193,247,255,297`;
`backend/tests/demo_engine/test_via_grail_executor.py:47,87`;
`backend/tests/demo_engine/test_scenario_coverage.py:55`; plus the one production caller
`adapter.py:44`. (`normalize_row` singular at `test_dynatrace_adapter.py:271,284,313` is untouched by
STORY-190.)

---

## Per-story build contract

### Story 1 — STORY-188 (1 pt, **orchestrator**)

Measured state at `ca5a9c6`, independently reproduced by the verifier:

| File | Invalid UTF-8 bytes | Existing `U+FFFD` |
| --- | --- | --- |
| `implementer.md` | 0 | 3 |
| `plan-verification.md` | 2 — `0x97` @ 3492, 3640 | 2 |
| `quality-review.md` | 3 — `0x97` @ 2833, 2883, 3007 | 3 |
| `spec-review.md` | 0 | 0 |

All 13 sites are one character: `0x97` is cp1252 EM DASH and every `U+FFFD` is a destroyed em-dash.
All 13 become `U+2014`. Templates under `.claude/skills/yourteam/templates/checklists/` are **clean**
(verified), so the corruption is post-generation. `yt_selftest` is **28/28 green with the corruption
present**, so parity is not byte-comparing this content — AC4 asserts that rather than assuming it.
No backend DoD command reads `.scrum/` (verified), which is why AC6 adds the missing mechanical rung.
**Land AC6's guard in `yt_selftest`, not in `backend/tests/`** — a backend test reading `.scrum/`
would create a new repo-layout coupling, and the skill rung must stay **project-generic** (PO
directive 2026-07-13). Until this lands, edit those files byte-safely (latin-1 read/write).

### Story 2 — STORY-190 (3 pts, external)

Build exactly this. **Names are prescribed; do not invent alternatives.**

1. In `dispatch.py`, a frozen dataclass **`RowNormalizationFailure`** with exactly two fields:
   `row: dict` (the raw vendor row) and `reason: str` (the caught exception's `str()`, which already
   names the offending code / `event.type` / field). **Adapter-local — not in `core/domain/`.**
2. In `dispatch.py`, a frozen dataclass **`NormalizationOutcome`** with exactly two fields:
   `observations: list[SignalObservation]` and `failures: list[RowNormalizationFailure]`.
3. In `dispatch.py`, a new function **`normalize_rows_lenient(rows, *, signal_key) ->
   NormalizationOutcome`**, catching exactly `UnknownVendorStatusError`,
   `UnsupportedMonitorTypeError` and `MalformedDqlRowError` per row. Observations keep **input
   order**. **Leave `normalize_rows` itself byte-for-byte unchanged and strict** — it is the fail-loud
   unit and all 9 call sites above must pass unmodified (AC7).
4. `fetch_observations` uses the lenient path and returns **`NormalizationOutcome`** (the same type,
   not a bare tuple). This is the intended contract change.
5. **`run_cycle` AND `run_periodic` both gain a keyword-only `rejected_repo:
   RejectedObservationRepository | None = None`.** `build_live_loop` calls **`run_periodic`**
   (`run.py:137-150`), *never* `run_cycle` — so `run_periodic` must accept it and pass it through at
   its `run_cycle` call site (`pull_loop.py:186-199`). Adding it only to `run_cycle` wires nothing
   and production quarantines nothing.
6. `run_cycle` ingests `outcome.observations` exactly as today, so **`run_cycle`'s return type and
   `on_cycle`'s type (`pull_loop.py:82`, `:147-150`) are UNCHANGED** — do not widen them. For each
   failure it calls `rejected_repo.save(signal_key=..., reason=..., payload=failure.row,
   rejected_at=<clock now>)` and logs at **WARNING** naming `signal_key` and `reason`. When
   `rejected_repo is None`, still log at WARNING — **never silently drop**.
7. `rejected_repo` already exists at the composition root (it is passed to `IngestService`); thread it
   from there through `build_live_loop` → `run_periodic` → `run_cycle`.

**AC2 and AC3 are the teeth.** AC2 requires proving the **watermark advanced** across two consecutive
cycles — "good rows survived" does **not** satisfy it, because the permanent stall is the defect.
AC3 requires the stall **reproduced failing** on the pre-fix state (C2/A7).

### Story 3 — STORY-177 (3 pts, external)

Unconditional provisional mapping with loud provenance. **No env var, no config surface, no injected
policy.**

- **One named constant** in `health_mapping.py`: a `dict[tuple[str, str], Health]` mapping the exact
  `(code, message)` tuple to `Health`, seeded with **exactly two** entries:
  `("1", "UNHEALTHY") -> Health.DOWN` (reusing the existing assumed pair) and
  `("2", "DEGRADED") -> Health.DEGRADED` (**new** — no DEGRADED pair exists anywhere today, so this
  is a fresh, explicitly-labelled assumption). Comment it UNVERIFIED and name STORY-154 as its
  replacement.
- **Matching rule and order, both load-bearing:** keep the existing healthy OR-rule **first and
  unchanged** (`code == "0" or message == "HEALTHY"` → `Health.UP`, `:65-66`) — it is pinned by
  `backend/tests/test_dynatrace_adapter.py:100`, which asserts
  `map_synthetic_status(code="123", message="HEALTHY") is Health.UP`. Only *after* it fails, look up
  the **exact `(code, message)` tuple** in the provisional dict. Tuple-exact, **never code-only**.
- Every provisional hit logs at **WARNING** naming code, message, and provisional/unverified status
  pending STORY-154. A `HEALTHY` row logs **no** such warning.
- A pair outside both rules still raises `UnknownVendorStatusError` naming the real code and message
  (AC3) — the property the fail-loud design protects, and why no gate is needed.

**Named deliverables that this story makes false and must fix:**

- `tools/demo_engine/assumed_failure_codes.py` — must **import** the constant from
  `src.adapters.inbound.dynatrace.health_mapping` rather than redeclaring literals (C1); docstring
  claims at `:11-14`, `:16-18`, `:20-22`, `:31-32` all rewritten.
- **`backend/tests/demo_engine/test_assumed_failure_codes.py:45-56`** —
  `test_assumed_failure_code_is_rejected_by_the_real_unmodified_health_mapping` asserts
  `pytest.raises(UnknownVendorStatusError)` on the ASSUMED pair and **will fail** when this story
  lands. **Invert it deliberately** (assert it now maps to `Health.DOWN` and warns) and rewrite its
  module docstring `:1-14`. This is expected work, not a regression to route around.
- `tools/demo_engine/README.md:22`.
- `health_mapping.py`'s module docstring (`:8-12`) and `map_synthetic_status`'s (`:55-63`) — state the
  current reasoning **and why the old one was superseded** (trial expired 2026-07-28; the deferred
  live verification cannot happen), so a future reader does not read this as a regression.

**Zone check:** the diff must touch **no file under `backend/src/core/`** (AC7).

### Story 4 — STORY-191 (5 pts, external) — read C5 first

**Scenario vocabulary.** Extend `SignalScenario.cycles` so a cycle entry is **either** the current
`list[str]` (all named locations `UP` — unchanged) **or** a `dict[str, str]` of location id →
`"up"` / `"down"` / `"degraded"`. `down`/`degraded` rows carry STORY-177's constant, **imported**, never
a literal. A malformed outcome raises `InvalidScenarioError` naming file, signal key and cycle index,
matching the existing convention.

**Backward compatibility is an AC.** The five checked-in `config/demo/scenarios/*.yaml`
(`clean-fleet`, `dark-location`, `dark-monitor`, `late-return`, `staggered-intervals`) must load and
expand byte-identically. **There are 9 rejection-test functions / 11 collected cases** in
`backend/tests/demo_engine/test_scenario.py` at `:334, 351, 374, 388, 403, 417, 438, 453, 467`
(`test_load_scenario_file_missing_required_field_raises` is parametrized ×3) — **all 11 must pass
unmodified.** (Earlier drafts and STORY-186 say "seven"; that number is wrong.)

**Four scenarios in `config/demo/scenarios/`:**

1. **A `DOWN` ladder** — enough consecutive `down` cycles to cross a *named* threshold. Be explicit:
   to reach `MAJOR_OUTAGE` needs `major: 5` consecutive cycles; `degraded: 2` also "crosses a
   threshold". Keep the ladder **≤ 7 cycles** (`orchestrate.py:98`).
2. **A partial-breadth case** — `down` at some locations, `up` at others, same cycle. **Note:**
   `_collapse_health` (`pipeline.py:85-98`) maps both this and the all-`degraded` case to
   `Health.DEGRADED`, so their `Verdict`s are **identical**. The distinguishing evidence is
   per-location `SignalObservation.health` — assert on that, not the verdict.
3. **A `degraded` case.**
4. **A poison-row case** — a status code still unmapped after STORY-177, proving STORY-190 at loop
   scale. **The poison row must be an EXTRA row alongside four good locations**, never a location's
   only row: a quarantined row is never persisted, so otherwise the signal shows 3 of 4 locations,
   `_assert_ac3_ingest`'s `signals_with_under_4_locations` (`harness.py:287-290`) fails and
   `_wait_for_last_signal`'s `>= 4` poll (`:187`) times out — which C2 calls a **FAILURE**.

**Harness integration.**

- Add a keyword-only seam to `run_positive_side` (`harness.py:335-339`) accepting extra scenarios,
  and **MERGE** their rows into `build_fleet_row_store(cfg, end_time=run_start)` (`:419`) — **never
  substitute.** `_assert_ac3_ingest` (`:279-295`) requires all 41 signals × 4 locations and
  `_assert_ac4_vendor_health` (`:298-310`) requires zero drift, so the fleet-wide store must survive.
- **Prescribe a distinct event-id namespace** for failure-scenario rows (e.g. prefix `fail-`).
  `expand_scenario` emits `f"{signal_key}-{seq}"`, so overlapping the fleet store produces identical
  ids and `save_new`'s `EVT#` dedupe (`dynamo_observation_repository.py:57-61`) **silently drops the
  second set with no error.**

**The recovery/publish proof (AC6) — the mechanism, spelled out.**

1. Before the recovery cycle, **write one demo component's stored status to `MAJOR_OUTAGE`** via the
   component repository (a real, reachable state — a previously-approved degradation).
2. Run an **all-`UP`** ladder for that component's signal. `anti_flap` proposes `OPERATIONAL`
   (rank 0 < rank 3), so `decide.py:115-126` sets `publish_change`, returns
   `DecideAction.PUBLISHED_RECOVERY`, and `:171-172` calls `publish()`. **This works with the static
   past-anchored store and one cycle per signal** — no live row injection.
3. **Two-sided persisted evidence, no logs, no stdout:**
   - **The publish fired:** that component's status in the control table changed `MAJOR_OUTAGE` →
     `OPERATIONAL`. `StatusWritebackPublisher.publish` (`publish_helper.py:179`) is the only
     component-status writer and **is** in the safe chain (`:230-231`), so this change is proof the
     recovery publish executed.
   - **Nothing left the process:** the **publications table is empty**. `RecordingPublisher`
     (`:212-227`) writes a `publications` row on *every* attempt and is present **only** in the
     credentialed+mapping chain — absent from the `LoggingPublisher` fallback. An empty publications
     table with a `PUBLISHED_RECOVERY` having occurred is exactly the discriminator.
4. Additionally run `guard_reality_gate.py` and record its **exit code** (C2). Note it reconstructs
   the chain **in-process** (`:83-128`) and never observes the subprocess — it corroborates step 3, it
   does not replace it.

Assert everything from **persisted state**, never parsed log text. The artifact ends with an explicit
verdict, exits **non-zero on failure**, and is **shown failing on deliberately bad input** (C2/A7).

### Story 5 — STORY-185 (1 pt, external)

Build to the story file's AC.

---

## The DoD gate — 8 commands, all must exit 0

`.scrum/definition-of-done.md` is authoritative; runner
`python .claude/skills/yourteam/scripts/yt_gate.py`.

**Backend (5)**, from the repo root: `pytest` (with `REQUIRE_DYNAMO=1`; record pass/skip counts) ·
`python -c "from importlinter.cli import lint_imports_command; lint_imports_command()"` (expect
`Contracts: 8 kept, 0 broken.`) · `ruff check .` · `ruff format --check .` ·
`cfn-lint infra/stack.yaml`.

**Frontend (3)**, from `frontend/`: `npm test`, `npm run build`, `npm run lint` — regression-only.

Mid-sprint gates MAY be `--only`-scoped. The **full 8-command gate on the final HEAD is mandatory and
is the evidence of record.** Known defect: `yt_gate.py` exits 0 when `--only` matches nothing
(STORY-178, unscheduled) — confirm a scoped run actually ran the commands it claims.

---

## Delivery contract (stated at handoff, verified on return)

1. **Commit per story, not one lump**, `STORY-NNN:` messages on `sprint-65`, TDD cadence. If work
   returns as one uncommitted tree, the orchestrator commits it per story **before** reviewing.
2. **A self-reported gate result is never trusted.** The orchestrator's own `yt_gate.py` run on the
   final HEAD is the only record that counts.
3. **Reviewers get each story's own commit range.**
4. **Never merge to main.** Re-confirmed by the PO at the sprint-64 review; `sprint-65` stays unmerged.
5. **Do not touch `.scrum/`.** The orchestrator is its sole writer; STORY-188 is orchestrator-executed.

## Plan verification

One `yt-plan-verifier` pass ran pre-lock (contract-sensitive on every count: a vendor adapter path, an
adapter→composition contract change, three live OS processes, a safety-critical publish guard with
real credentials on disk, and `external` mode making this document the full contract).

**Verdict: GAPS — 16 blocking, all folded into this document before the PO saw it.** The three most
consequential:

- **The draft's threat model was wrong.** It claimed sprint 65 was the first time the publish path
  could fire, via a `DOWN`→`UP` recovery. Verified impossible: components seed `OPERATIONAL` and a
  degradation never changes stored status, so that ladder yields `PROPOSED` then `OBSOLETED` and
  publishes nothing. C5 is rewritten and STORY-191's mechanism replaced with the pre-set-status route
  (PO-approved), which also removed the need for live row injection.
- **`build_live_loop` calls `run_periodic`, not `run_cycle`** — the draft's threading instruction
  would have wired nothing in production.
- **Undefined names and return shapes** throughout STORY-190/177 (the failure dataclass, the lenient
  function, the DEGRADED pair, the matching rule) — every one now prescribed, because a literalist
  implementer would otherwise coin-flip each.

Also fixed: 4 citation drifts (`run.py:179`, `pull_loop.py:137-219`, the orchestration guard at
`:120`, 8 not 9 files in `tools/demo_loop_gate/`); `gap_verdicts` not `missing_cycles`; 11 rejection
cases not 7; the event-id dedupe collision; the poison-row assertion conflict; the un-named harness
seam; the missing threshold units; `test_assumed_failure_codes.py` as a named deliverable; C1
sharpened to note the gate catches the concrete-persistence variant; STORY-185's frontmatter.

**Independently confirmed:** the STORY-190 stall claim survived four refutation angles and was
strengthened (`advance()` is the only watermark writer in the tree; `build_dql_query` has no upper
bound; the demo store never evicts; `sort timestamp asc` means the *earliest* bad row aborts,
discarding already-normalized earlier rows). C1's trap verified against all eight contracts. Every
safety-critical C5 citation exact. STORY-188's byte measurements reproduced exactly.

## Deliberate omissions

- **STORY-186** and **STORY-189** cut at verification — see Scope. Both are sprint-66 candidates.
  STORY-189's own file carries a correction: the field is **`gap_verdicts`**, not `missing_cycles`, and
  `demo-engine.md` does not mention `tools/demo_loop_gate/` **anywhere** (grep count 0) — its Facts
  still claim no demo loop has been started, which sprint 64 falsified. So that story is a **Fact
  rewrite**, not a `code_refs` addition plus a `verified_sha` re-stamp.
- **STORY-154** (the real vendor codes) stays blocked on trial renewal; STORY-177 precedes it and 154
  replaces its constant's **contents**.
- **STORY-152** (`completeness` uses expected, not observed, locations) out of scope.
- **STORY-150 / STORY-151** become verifiable after this sprint but are not in it.
- **STORY-155** (remove `sample_mode`) untouched — the unconditional approach adds no config surface.
- **STORY-178** (`--only` false green) and **STORY-179** (dynamo port) unscheduled; 179's workaround
  is C4.
- **No frontend work.**
- **PO reminder, carried forward:** the PO wants a sprint dedicated purely to **auditing**
  boundary/code-discipline issues — the class C1 describes, where the import direction is legal but
  the design is wrong. **Raise at sprint-66 planning.**

## Risks

| Risk | Mitigation |
| --- | --- |
| **C1's trap is invisible to the gate** and external agents build literally | C1 names the wrong implementation explicitly and notes a green gate does not mean the right route was taken; `yt-quality-reviewer` gets the boundary question as a named check on STORY-190 |
| **The recovery publish genuinely fires in STORY-191** | Two-sided persisted proof (status changed **and** publications empty), `guard_reality_gate.py` exit code recorded, `CONFIG_DIR` on both processes, fake creds as defence in depth, and a fail-safe load path |
| 13 points is above the pacing baseline | Sole drop candidate: STORY-185. Never break 190→177→191 |
| External mode ships ~1 MAJOR per 3-pt story | Both reviewers on every story, independent gate re-run, STORY-191 last so its fix round blocks nothing |
| STORY-177 red-gates an existing test | `test_assumed_failure_codes.py:45-56` named as a deliberate inversion, not a regression |
| Event-id collision silently drops rows | A distinct `fail-` namespace is prescribed |
| STORY-186/189 would have fought STORY-191 over the same files | Both cut from scope |
