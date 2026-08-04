---
title: Zone 3 â€” the ingest service (Â§8 ordering) + the asyncio pull loop
code_refs: [backend/src/core/services/ingest_service.py, backend/src/composition/pull_loop.py, backend/src/composition/run.py, backend/src/composition/sample_mode.py, backend/src/composition/vendor_health.py, backend/tests/test_ingest_service.py, backend/tests/test_pull_loop.py, backend/tests/test_run_live_loop.py, backend/tests/test_vendor_health.py, backend/tests/test_dynamo_rejected_observation_repository.py]
verified_sha: bfa5f77
verified_sprint: sprint-68
status: verified
# Re-verified 2026-07-30 (sprint-65, STORY-190). NEW section added on partial-batch resilience.
# The key correction: the defect was never 'a lost batch' -- it was a PERMANENTLY STALLED SIGNAL,
# because the raise happened before the watermark advance and the next cycle re-read the same
# window. Records where each piece lives (adapter pure, composition decides) and the zone trap the
# eight contracts cannot catch.
# Re-verified 2026-07-30 (sprint-65 quality-review round). NEW Fact: rejected_at falls back to
# SystemClock() rather than an inline datetime.now(), keeping the quarantine timestamp injectable.
---

## Facts (verified against code)

STORY-009 closed Zone 3 ingest: the core ingest SERVICE (the crash-safety guarantee) plus the
composition-zone asyncio PULL LOOP that drives it from the Dynatrace adapter (see
[[dynatrace-adapter]]). The ports + canonical types it speaks are in [[canonical-types-and-ports]].

### The ingest service â€” `IngestService` (`core/services/ingest_service.py`)
- `IngestService(SignalIngestPort)` (`ingest_service.py::IngestService`) is the FIRST populated thing in
  `core/services/`; it owns the dossier Â§8 ordering so every adapter that feeds the core inherits
  it. It imports ONLY `src.core.*` (ports + domain) â€” no SQL, no vendor types, no globals.
- Constructed with the four core ports injected (`ingest_service.py::IngestService.__init__`):
  `observation_repo`, `watermark_repo`, `rejected_repo`, `clock` â€” so it is fully exercised with
  in-memory fakes (no DB, no Dynatrace) per AC5.
- `ingest_observations(batch) -> IngestResult` (`ingest_service.py::IngestService.ingest_observations`) runs the Â§8 order,
  which is significant for AC1 + AC4:
  1. **Validate then quarantine** (`ingest_service.py::IngestService.ingest_observations`): each observation whose `observed_at` is implausibly
     future (`ingest_service.py::IngestService._is_implausibly_future`: `observed_at > now + FUTURE_TOLERANCE`, against
     the injected `clock.now()`) is written to `rejected_repo.save(signal_key, reason, payload,
     rejected_at)` and EXCLUDED from the persist set; the rest proceeds (no poison pill). Validation
     happens BEFORE dedupe, so a bad row becomes a recorded rejection rather than being deduped away.
  2. **Dedupe + persist** (`ingest_service.py::IngestService.ingest_observations`): `observation_repo.save_new(valid)` â€” an
     idempotent insert, never a duplicate on replay (the DynamoDB adapter's `EVT#.../DEDUPE` marker
     item, `dynamo_observation_repository.py:58-62` â€” corrected STORY-181, sprint-63; the comment had
     said "ON CONFLICT DO NOTHING" SQL that never ran here); its return is the TRUE newly-inserted
     count, which becomes `IngestResult.accepted` (NOT `len(valid)`, so a duplicate is a no-op â€” AC3).
  3. **Advance watermark accepted-only, after persist** (`ingest_service.py::IngestService.ingest_observations`): to
     `max(observed_at)` over the VALIDATED observations only, and only AFTER `save_new` returns â€” if
     it raises, the exception propagates and the watermark is left untouched (commit-before-advance,
     AC4). A future-timestamp reject therefore can never leap the cursor (AC2). If nothing is valid,
     the watermark is not advanced (`ingest_service.py::IngestService.ingest_observations`).
- `FUTURE_TOLERANCE = timedelta(minutes=5)` (`ingest_service.py::FUTURE_TOLERANCE`) and
  `FUTURE_TIMESTAMP_REASON` (`ingest_service.py::FUTURE_TIMESTAMP_REASON`) â€” the Â§14 T1.3 "year-2099" guard; the 5-min value is a judgment
  call (AC left the number open) to absorb source/process clock skew.
- **Single-signal-batch assumption â€” now ENFORCED, not just documented** (STORY-022,
  `ingest_service.py::MixedSignalBatchError` and `ingest_service.py::IngestService.ingest_observations`): `signal_key = valid[0].signal_key` and one `max(observed_at)`
  watermark still assume one signal per batch â€” which matches how the Dynatrace adapter's
  `fetch_observations` produces batches (one signal per cycle) â€” but the assumption is now GUARDED
  up front instead of trusted silently. `ingest_observations` collects the distinct `signal_key`s
  across the WHOLE input batch immediately after the empty-batch early return, and BEFORE any
  validation, persistence, or watermark work; if more than one distinct key is present it raises
  `MixedSignalBatchError` (a `ValueError` subclass defined in this same core module, `ingest_service.py::MixedSignalBatchError`),
  naming the offending keys (sorted, deduped, on `.signal_keys`). A single-signal batch and an
  empty batch behave exactly as before (STORY-009 unchanged). This closes the Sprint 5 review minor:
  a future mixed-signal batch (a push webhook batching several monitors, or a future "ingest
  everything newer" path) now fails loud instead of silently over-advancing one signal's watermark
  using another signal's timestamps.
 
### Partial-batch resilience (STORY-190, sprint 65) — one bad row costs only itself

- **The defect this closed was NOT "a lost batch" — it was a PERMANENTLY STALLED SIGNAL.**
  `normalize_rows` (`dispatch.py::normalize_rows`) is a bare list comprehension, so one unnormalizable
  row aborted the whole list. That runs inside `fetch_observations`, which `run_cycle` calls BEFORE
  `ingest_port.ingest_observations` — so `IngestService`'s watermark advance was never reached.
  `run_periodic` caught the exception, logged at ERROR and continued (by design, STORY-050), and the
  next cycle re-read the SAME unadvanced watermark and re-queried the SAME window, still containing
  the same bad row. The signal therefore never advanced again while the loop looked alive.
- Three properties made it unrecoverable rather than self-healing, all verified: the advance in
  `IngestService.ingest_observations` is the ONLY watermark writer in `backend/src/` and `tools/`;
  `build_dql_query` (`query.py::build_dql_query`) adds only a LOWER time bound, no upper bound and no
  limit, so the poison row stays in-window indefinitely; and `sort timestamp asc` means the EARLIEST
  bad row aborts, discarding already-normalized earlier rows too.
- **The fix, and where each piece lives.** The adapter stays a PURE translation function — it returns
  `NormalizationOutcome` (observations + failures) and persists nothing (see [[dynatrace-adapter]]).
  `run_cycle` ingests `outcome.observations` as before, and for each failure logs at WARNING and
  calls `rejected_repo.save(signal_key=..., reason=..., payload=<raw row>, rejected_at=...)`. The
  watermark then advances on the good rows, so the signal moves past the bad one.
- **No new port and no new domain type were needed.** `RejectedObservationRepository.save` already
  took `signal_key` / `reason` / `payload: dict` / `rejected_at`, and its docstring already said
  "Rejection is never a poison pill — the caller persists this and moves on to the rest of the
  batch." It was written for validation rejects and fits normalization rejects unchanged; the raw row
  goes in as an opaque `dict`, so no vendor shape reaches `core`.
- **`rejected_repo` is threaded to BOTH `run_cycle` AND `run_periodic`**, because `build_live_loop`
  (`run.py`) calls `run_periodic`, never `run_cycle`. Wiring only `run_cycle` would quarantine
  nothing in production while every test passed.
- **`rejected_at` is injected, not read from the wall clock.** `clock` is one of the six OPTIONAL
  orchestration extras, so the ingest-only call shape can arrive without one; `run_cycle` then falls
  back to `SystemClock()` rather than calling `datetime.now(...)` inline. An inline call would have
  been the ONLY direct wall-clock read in `backend/src/` outside `adapters/system_clock.py` and would
  make the quarantine timestamp untestable.
- **Zone note worth keeping:** having the inbound adapter write quarantine rows itself would pass all
  eight `lint-imports` contracts (adapters may import core, and the port lives in `core/ports/`)
  while turning a translation layer into an orchestrator. Only `composition` decides what happens to
  an adapter's output. The gate does catch the CONCRETE `adapters.persistence.*` variant — only the
  core-port route is invisible to it.

### The pull loop â€” `run_cycle` / `run_periodic` (`composition/pull_loop.py`)
- The loop lives in the composition zone â€” the one zone allowed to import BOTH `src.core` and
  `src.adapters` (dossier Â§4). It holds NO domain logic; it only wires three calls per cycle.
- `run_cycle(*, signal_key, native_id, watermark_repo, ingest_port, executor, overlap=DEFAULT_OVERLAP, ...) -> IngestResult | tuple[IngestResult, DecideAction]` (`pull_loop.py::run_cycle`): `watermark_repo.get(signal_key)` â†’
  `dynatrace.fetch_observations(watermark=..., overlap=...)` â†’ `ingest_port.ingest_observations(batch)`. When optional orchestration parameters are passed (config, observation_repo, maintenance_repo, component_repo, decide_service, clock), it calls `orchestrate_signal` after ingest and returns a tuple of `(IngestResult, DecideAction)` (STORY-016a).
  It is synchronous (none of the calls are async in this codebase).
- `run_periodic(...)` (`pull_loop.py::run_periodic`) is the thin asyncio driver:
  `while not stop_event.is_set(): run_cycle(); await asyncio.sleep(interval_seconds)`. Plain
  `asyncio` â€” NO APScheduler. `stop_event`
  (`asyncio.Event`) makes the loop deterministically stoppable in tests / future graceful shutdown;
  `on_cycle` is an optional hook for observing each cycle result. Neither carries domain logic.
- **Orchestration threading (STORY-016 T4):** `run_periodic` accepts the same six optional
  orchestration extras as `run_cycle` (`config`, `observation_repo`, `maintenance_repo`,
  `component_repo`, `decide_service`, `clock`) and passes them straight through, so the LIVE loop runs
  the pipeline after ingest (all-or-none guard preserved). `on_cycle`'s type widens to
  `IngestResult | tuple[IngestResult, DecideAction]` accordingly.
- **Per-cycle failure resilience (STORY-050, dossier Â§8, log-only per PO decision):** `run_periodic`
  now wraps the `run_cycle` call in `try/except Exception` (`pull_loop.py::run_periodic`) â€” a cycle
  that raises (e.g. `GrailQueryError` from a network timeout, per the STORY-050 incident) no longer
  crashes the process. The `except` catches `Exception`, deliberately NOT `BaseException`: in Python
  3.13 `asyncio.CancelledError` (like `KeyboardInterrupt`/`SystemExit`) is a `BaseException` subclass,
  so it is not swallowed and still propagates to stop the loop. Each `run_periodic` call owns ONE
  in-memory `consecutive_failures` counter for its one signal: on a caught exception the counter
  increments and `logger.exception` logs at ERROR with the signal_key, the cause, and the running
  count (`"Cycle failed for signal_key=%r (consecutive_failures=%d): %s"`); a success resets the
  counter to zero. `on_cycle` is skipped on a failed cycle (there is no result to hand it) â€” the
  success path is otherwise unchanged. The post-cycle `stop_event` re-check (STORY-023) now runs
  after a FAILED cycle too, so a stop requested mid-failure still takes effect without waiting one
  more `interval_seconds`. The loop NEVER exits on cycle failures, however many happen in a row
  (AC3 â€” an accepted trade-off: a persistent failure, e.g. a mis-rotated token, is visible only in
  logs). Startup failures (`MissingLiveSecretError`, bad config) are unaffected: they run in
  `composition/run.py::main` BEFORE any `run_periodic` call exists, so they still fail fast (AC2).

### The live driver â€” `build_live_loop` / `main` (`composition/run.py`, STORY-016 T5)
- `build_live_loop(*, settings, secrets, config, engine, clock) -> list[Coroutine]`
  (`run.py::build_live_loop`) is the production assembly: it mirrors `create_app`'s Postgres repo
  wiring on one `engine`, builds the Dynatrace Grail executor (see [[dynatrace-adapter]]) and the
  publisher, constructs `DecideService(proposal_repo, publisher=...)`, and returns one
  `run_periodic(...)` coroutine per configured signal (with the six orchestration extras threaded).
- **Publisher selection (STORY-016b, reshaped by STORY-045):** `build_live_loop` no longer assembles
  the chain inline â€” it calls the shared `composition/publish_helper.py::build_publisher`
  (`run.py::build_live_loop`, STORY-045 D2; see [[statuspage-publish]] for the full chain Facts),
  passing `secrets.statuspage_page_id`/`statuspage_api_token` + `config.statuspage_mapping()`. With
  Statuspage configured (both secrets AND a non-empty mapping) the chain is
  `StatusWritebackPublisher(BestEffortPublisher(RecordingPublisher(StatuspagePublisher)))`; otherwise
  `StatusWritebackPublisher(LoggingPublisher())` â€” still **Dynatrace-only** externally (the PO can
  verify ingestâ†’pipelineâ†’proposal internally without Statuspage creds) and still writing NO
  publication rows on the no-op path, but the `components.status` write-back now applies on BOTH
  paths (the local no-creds dev stack sees the Dashboard change).
- `main()` (`run.py::main`, entrypoint `python -m src.composition.run`) loads settings + live secrets
  + config, seeds topology once, `asyncio.gather`s the loops, and disposes the engine in a `finally`
  on EVERY exit path (resource-lifecycle agreement; proven by `test_main_resource_lifecycle_failure_during_seeding`).
  **STORY-043 (`.env` loading, defect fix):** the VERY FIRST line of `main()` is now
  `load_dotenv()` (`run.py::main`), BEFORE `load_settings()`/`load_live_secrets()` run â€” it loads a
  gitignored repo-root `.env` into `os.environ` so the documented local recipe (CLAUDE.md "Run the
  app locally") can supply `DYNATRACE_*`/`STATUSPAGE_*` secrets from that file instead of
  requiring them to be exported into the shell first (before this story, NOTHING loaded `.env` â€”
  `load_settings`/`load_live_secrets` only ever read `os.environ` directly, so the documented recipe
  crashed with `MissingLiveSecretError`). `composition/asgi.py` gets the same treatment at module
  scope, before `create_app()`. `load_dotenv()`'s default `override=False` semantics mean an
  already-exported env var always wins over `.env` â€” production (AWS ECS Fargate, which sets real
  env vars and ships no `.env` file, is unaffected; corrected STORY-181 sprint-63 â€” the comment
  used to say "Railway") â€” and the call lives ONLY at these two process
  entrypoints, never inside `load_settings`/`load_live_secrets` themselves, so DB-gated/unit tests
  that call those functions directly with explicit `monkeypatch` env are untouched (AC4; STORY-050's
  fail-fast-before-any-loop test stays green with `load_dotenv` patched in
  `backend/tests/test_run_live_loop.py`). See [[dev-setup-and-dod]] for the full correction of the
  CLAUDE.md/wiki claims this fixed.
- **Vendor-id drift probe at startup (STORY-070, `composition/vendor_health.py`):** `main()` now
  runs `check_vendor_id_health(config=..., executor=make_grail_executor(...))` (`run.py::main`) ONCE
  at startup, BEFORE `build_live_loop`/`run_periodic` are built. `check_vendor_id_health`
  (`vendor_health.py::check_vendor_id_health`) iterates every configured signal and runs a bounded
  DQL count (`adapters/inbound/dynatrace/query.py::build_vendor_health_dql` â€” a cheap
  `fetch dt.synthetic.events, from:now()-2h | filter monitor.id == <native_id> | summarize count()`
  existence probe, distinct from the ingest fetch in [[dynatrace-adapter]]; relocated into that
  adapter module from `composition/vendor_health.py` at STORY-204, ZR-8 finding 2 â€” query-
  construction logic lives in exactly one adapter) through the SAME injected `Executor` seam the
  pull loop uses; a 0-row/0-count result (`vendor_health.py::_extract_count`) logs a PROMINENT
  WARNING naming the `native_id` + `signal_key`, a healthy id logs only INFO. This is a **loud
  WARNING, NOT fail-fast** (PO-decided, sprint-41) **for the EXECUTOR only**: each signal's
  `executor(query)` call is wrapped in `try/except Exception` that logs a WARNING and `continue`s,
  so an executor error for one signal never stops the others and never propagates to `main()` â€”
  that probe cannot take down the loop it protects. It IS fail-fast for a misconfigured
  `native_id`: `build_vendor_health_dql` raises `InvalidNativeIdError` for a DQL-breaking character
  BEFORE the executor is ever called, and that call sits outside the try/except, so it DOES
  propagate out of `check_vendor_id_health` and `main()` identically to the ingest path's
  `build_dql_query` (STORY-204 AC1) â€” before STORY-204 this same builder validated nothing and
  would have silently built a malformed query instead. It closes the Sprint 38
  silent-no-data-pipeline gap (a monitor id recreated in Dynatrace, hotfix `79bfbb3`; see the
  2026-07-08 retro working agreement). Uses its own `make_grail_executor` instance (a cheap
  closure, no network until invoked) so it never depends on `build_live_loop` having run.
- **STORY-048 sample-mode seam (temporary â€” see [[sample-mode]]):** `build_live_loop` step 2's
  `ingest_port` is now `composition/sample_mode.py::SampleModeIngest(delegate=IngestService(...),
  sample_mode_repo=PostgresSampleModeRepository(engine))` instead of a bare `IngestService` â€” a
  composition-layer decorator that forces every observation to `Health.DOWN` (+ a `raw_ref`
  marker) while a persisted flag is ON, and passes the batch through byte-identically while OFF.
  `IngestService` and `run_periodic`/`run_cycle` (`composition/pull_loop.py`) themselves are
  UNCHANGED â€” the decorator wraps the ingest port from the outside, at the one seam
  `build_live_loop` already owned. This is a TEMPORARY, removable feature; see [[sample-mode]] for
  its full Facts and the removal inventory.

### Tests
- `backend/tests/test_ingest_service.py` exercises the real `IngestService` through in-memory fake
  repos + a fixed fake clock (no DB) â€” covering each AC: future-timestamp quarantine + no poison
  pill (AC1), accepted-only / year-2099 cursor (AC2), true newly-inserted count + duplicate no-op
  (AC3), watermark-not-advanced-on-`save_new`-failure + idempotent replay (AC4).
- STORY-022 adds `test_mixed_signal_batch_raises_named_error_naming_the_keys_before_any_repo_call`:
  a batch spanning two distinct `signal_key`s raises `MixedSignalBatchError` naming both keys, and
  asserts zero calls reached `save_new`, `watermark_repo.advance`, or `rejected_repo.save` â€” proving
  the guard runs up front, before any work.
- `backend/tests/test_pull_loop.py` covers AC5: plain-asyncio (AST-asserts no `apscheduler` import),
  no-domain-logic pass-through, one-cycle-per-tick + stoppable; plus STORY-016 the orchestration-
  threading path (`run_periodic` with all six extras yields a `(IngestResult, DecideAction)` tuple to
  `on_cycle`). STORY-050 adds: a fake executor that fails once then succeeds proves the SECOND
  cycle's ingest still ran and the failure is logged at ERROR with the signal_key (AC1); a scripted
  fail/fail/succeed/fail sequence proves the per-signal consecutive-failure count logged is
  1, 2, (reset), 1 and all four cycles run â€” the loop never exits on failure (AC3); a dedicated
  cancellation test proves `asyncio.CancelledError` still stops the loop (it is a `BaseException`,
  not caught by the new `except Exception`); a dedicated stop_event test proves a stop requested
  during a FAILING cycle still takes effect immediately (extends STORY-023 to the failure path).
  `backend/tests/test_run_live_loop.py` adds `test_main_fails_fast_on_missing_secrets_before_any_loop_starts`,
  pinning AC2: a `MissingLiveSecretError` from `load_live_secrets()` still terminates `main()` before
  `sa.create_engine`, `seed_topology`, or `build_live_loop` ever run.
- `backend/tests/test_run_live_loop.py` (STORY-016, rewritten by STORY-045 per the 2026-06-29
  contract-change agreement) builds the REAL chain via `build_live_loop` (only `run_periodic`
  patched) and asserts the `StatusWritebackâ†’BestEffortâ†’Recordingâ†’Statuspage` nesting + the six
  extras on each call (including that the SAME `component_repo` instance threads into both
  `run_periodic` and the writeback publisher), plus `main()` engine-dispose on success AND on a
  seeding failure. STORY-048 (the sanctioned AC7b exception, temporary feature â€” see
  [[sample-mode]]) additionally asserts `ingest_port` is a `SampleModeIngest` wrapping the REAL
  `IngestService` wired to the real repos, and that the SAME `ingest_port` instance threads into
  every per-signal `run_periodic` call.
- `backend/tests/test_vendor_health.py` (STORY-070) exercises `check_vendor_id_health` with FAKE
  executors (no live Dynatrace): a 0-rows and a `[{"count()":0}]` result each assert exactly one
  WARNING record naming the monitor id; a `[{"count()":2882}]` result asserts NO warning; a raising
  executor asserts the error is caught+logged and does NOT propagate, and that one signal's probe
  error does not block the others; an empty config is a no-op (executor never called).
  `backend/tests/test_run_live_loop.py` adds `test_main_probes_vendor_id_health_before_loops_start`,
  which pins the wiring WITHOUT patching it away â€” it passes the REAL `make_grail_executor` closure,
  asserts the executor is callable and the real loaded `config` is threaded, and asserts ordering
  (`check_vendor_id_health` runs before `build_live_loop`) via an attached manager mock.
- The DB-gated persistence side (the actual rejected-observation write) is covered by the
  DynamoDB adapter tests (`backend/tests/test_dynamo_rejected_observation_repository.py`,
  STORY-086) since the DynamoDB cutover (STORY-087) â€” see [[persistence-adapters]]. (The former
  Postgres `test_persistence_adapters.py` regression retired with the relational layer.)

## Inference (synthesis, not verified)
- The "hand to pipeline (collapse â†’ anti-flap)" step of dossier Â§8 is deliberately ABSENT here â€” it
  is Zone 4 (STORY-010), and the ingest service's responsibility ends at advancing the watermark.
  When the pipeline lands, the natural seam is between persist and the existing return.

## History
- sprint-5: created (STORY-009). Documents the ingest service's Â§8 ordering + the asyncio pull loop
  as built. Verified at cca043f.
- sprint-6: re-verified (STORY-022). The single-signal-batch assumption Fact is updated from
  "documented, not guarded; a latent hazard" to ENFORCED â€” `MixedSignalBatchError` now guards the
  whole batch up front. Verified at 49bc707.
- sprint-6: re-verified (STORY-023). Comment-only â€” `run_periodic`'s post-cycle `stop_event`
  re-check now carries an explanatory comment; no Fact changed. Verified at 9e5b329.
- sprint-7: re-verified (STORY-011 incidental). `test_ingest_service.py`'s local
  `DedupingObservationRepository` fake gained an `in_window` `NotImplementedError` stub (just to
  satisfy the `ObservationRepository` ABC after STORY-011 added the read method) â€” a fixture-
  compliance stub, no behavior change; the ingest-service/pull-loop Facts are unchanged.
  Verified at 98bebe9.
- sprint-20: updated (STORY-016). `run_periodic` now threads the six orchestration extras through to
  `run_cycle` (live loop runs the pipeline after ingest); added the live driver `composition/run.py`
  (`build_live_loop` + `main`) that assembles the full chain and runs one loop per signal.
  Verified at d9c2a77.
- sprint-21: updated (STORY-016b). `build_live_loop` now selects the Statuspage chain vs a no-op
  `LoggingPublisher` based on whether Statuspage is configured (Dynatrace-only internal verification);
  the failing-row pull_loop tests mock the vendor-mapping edge (production is fail-loud). Verified at 213034b.
- sprint-22: re-verified (STORY-016c). No pull-loop source change; `test_pull_loop.py` rows were flipped
  from `event.type: http_step_execution` to `http_monitor_execution` (the canonical row the live loop now
  ingests â€” see [[dynatrace-adapter]]). Verified at ed19084.
- sprint-29: updated (STORY-045). `build_live_loop`'s inline publisher assembly moved into the shared
  `publish_helper.py::build_publisher` (consumed by BOTH composition roots); the chain gains
  `StatusWritebackPublisher` outermost (components.status write-back on both the creds and no-creds
  paths); `test_run_live_loop.py` assembly tests rewritten for the new nesting. Ingest service +
  pull loop themselves unchanged. verified_sha â†’ 7cabee7.
- sprint-31 (STORY-048, a TEMPORARY feature â€” see [[sample-mode]]): `build_live_loop` step 2's
  `ingest_port` is now wrapped in `composition/sample_mode.py::SampleModeIngest` (the on-demand
  outage simulator) â€” the ONE marked seam line in `run.py`. `test_run_live_loop.py`'s assembly
  assertions were UPDATED (the AC7b-sanctioned exception) to assert the real
  `SampleModeIngestâ†’IngestService` nesting; `IngestService`, `pull_loop.py`, and the pre-existing
  BEHAVIOR tests (`test_ingest_service.py`, `test_pull_loop.py`) are UNCHANGED and pass unmodified.
  verified_sha â†’ 0ea652e.
- sprint-36 (STORY-043, defect): `main()` (`composition/run.py`) and `composition/asgi.py` (module
  scope) now call `dotenv.load_dotenv()` as their very first action, before
  `load_settings`/`load_live_secrets`/`create_app()` â€” the "Facts" section above documents the
  before/after correction in full. `python-dotenv` added to `[project.dependencies]`
  (`pyproject.toml`) as a runtime dependency. `load_settings`/`load_live_secrets` themselves are
  UNCHANGED (still read only `os.environ`, per AC4) â€” the loading is entrypoint-only. verified_sha
  â†’ 6a33edb.
- sprint-36 (STORY-050, defect): `run_periodic` now catches `Exception` (not `BaseException`) around
  each `run_cycle` call, logs a failure at ERROR with the signal_key + cause + a per-signal
  consecutive-failure count, skips `on_cycle` on failure, resets the counter on success, and NEVER
  exits on cycle failures (LOG-ONLY per PO decision) â€” the loop rides out the transient Grail/network
  errors that used to crash the whole process. `on_cycle`'s type and `run_cycle` itself are
  UNCHANGED. `test_run_live_loop.py` gains one test pinning that AC2's startup fail-fast (missing
  secrets) is untouched by this change. verified_sha â†’ 80df0c2.
- sprint-41 (STORY-070, feature): `main()` (`composition/run.py`) now runs `check_vendor_id_health`
  (new module `composition/vendor_health.py`) ONCE at startup before `build_live_loop`, logging a loud
  WARNING for any configured monitor `native_id` that returns 0 executions in a bounded 2h DQL count
  probe â€” the drift-detection the Sprint 38 silent-no-data incident motivated (loud, NOT fail-fast;
  PO-decided). `code_refs` += `vendor_health.py` + `test_vendor_health.py`; the ingest service, pull
  loop, and the existing `build_live_loop` publisher/sample-mode wiring are all UNCHANGED. verified_sha
  â†’ 4d3fd7a.
- sprint-44 (STORY-079, Facts-coverage cleanup): `yt_wiki.py facts` flagged two uncovered
  citations: `pyproject.toml` (cited to prove no new dependency, e.g. APScheduler, was added for
  the pull loop) and `backend/tests/test_persistence_adapters.py` (cited as covering the DB-gated
  persistence side of the rejected-observations write). Both added to `code_refs` â€” genuinely
  defining for the "plain asyncio, no new dep" and "rejected-row persistence" claims this article
  makes. Also normalized this article's `status:` frontmatter line, which carried the same trailing
  `# verified | stale | archived` inline comment the STORY-064 fix corrected on
  [[canonical-types-and-ports]]/[[dynatrace-adapter]] â€” `yt_wiki.py`'s parser reads it as part of
  the value, so the sweep was silently skipping this article too. No Fact text changed. verified_sha
  â†’ 678ff0d.
- sprint-44 (STORY-079 fix loop, quality review MAJOR): `pyproject.toml` was over-broad in
  `code_refs` â€” it is touched by every dependency change anywhere in the repo, while the
  plain-asyncio contract is already pinned by `pull_loop.py` itself. Removed `pyproject.toml`
  from `code_refs`. The Facts-section clause "NO new dependency in `pyproject.toml` (AC5)" was a
  point-in-time record of STORY-009's AC5, not a living contract this article continuously
  verifies â€” moved out of Facts: STORY-009 AC5 was satisfied at the time (no new dependency, e.g.
  APScheduler, was added for the pull loop). The living Fact ("Plain `asyncio` â€” NO APScheduler")
  stays in place, unedited. `verified_sha` re-stamped to `adc002a`.
- sprint-45 (STORY-065/STORY-066): re-verified, no changes to Ingest or Pull Loop. verified_sha -> f6f589fd4dcb6e3a2a565453c43b0fb95d7e5787.

- 2026-07-13 (sprint-45 gate closure): re-stale was ruff-format-only (48fba51 line-wrapped a delete stmt + trimmed trailing blank lines in maintenance_repository.py / fakes.py / test_persistence_adapters.py) â€” behavior and Facts unchanged. Re-verified; verified_sha -> 010a21b.
- sprint-50 (STORY-093, test hygiene): `test_run_live_loop.py::test_main_resource_lifecycle_success`
  gained real assertions (`mock_make_dynamo_resource`/`mock_seed_topology_dynamo`/`mock_build_loop`
  called with the expected shape) â€” the test previously ended at `asyncio.run(main())` with none.
  `run.py`, `pull_loop.py`, `ingest_service.py`, and `sample_mode.py` are all UNCHANGED. No Fact
  changed. verified_sha -> a8700f5.
- sprint-62 (STORY-146): RE-VERIFIED, no content change. `test_pull_loop.py`, `test_run_live_loop.py` and `test_vendor_health.py` changed only in how they construct `AppConfig`. The source files this article is about — `pull_loop.py`, `run.py`, `vendor_health.py`, `ingest_service.py` — are untouched by the story (AC7 requires it; verified by an empty `git diff` over those paths). verified_sha -> d004da7.
- sprint-63 (STORY-181): the sweep flagged `run.py`, `ingest_service.py`. Two Facts above directly
  quoted comments this story retired: the dedupe-and-persist step now describes the real
  `EVT#.../DEDUPE` marker-item mechanism instead of "ON CONFLICT DO NOTHING" SQL that never ran
  here, and the STORY-043 `.env`-loading Fact drops `DATABASE_URL` (retired) and corrects
  "production (Railway...)" to "production (AWS ECS Fargate...)" (STORY-089). No ordering, DoD
  command, or test behaviour changed. verified_sha -> b272c32.
- sprint-68 (STORY-204): the vendor-id drift probe Fact rewritten. `build_vendor_health_query`
  relocated from `composition/vendor_health.py` into
  `backend/src/adapters/inbound/dynatrace/query.py` as `build_vendor_health_dql` (ZR-8 finding 2,
  see [[zone-rules]]), sharing `query.py`'s `_reject_dql_breaking_native_id` with `build_dql_query`
  instead of validating nothing. **This Fact's own "never propagates to `main()`" claim was only
  ever true for the executor** — the query-BUILD call was always outside the
  `try/except Exception` block, so it was vacuously true pre-fix only because the old builder never
  raised anything; post-fix it CAN raise `InvalidNativeIdError` for a misconfigured `native_id`,
  and that now correctly propagates, matching the ingest path (STORY-204 AC1). Corrected to state
  both halves explicitly: NOT fail-fast for the executor, IS fail-fast for a misconfigured
  `native_id`. `check_vendor_id_health`/`_extract_count` themselves, `run.py::main`'s call site, and
  every other Fact in this section are unchanged — proven by the ordering/wiring tests in
  `test_run_live_loop.py`/`test_pull_loop.py` passing unmodified. verified_sha -> c815ebe.
- sprint-68 (STORY-204 fix round): the sweep flagged `run.py`, `vendor_health.py`,
  `test_vendor_health.py`. `run.py`'s call-site comment (`main()`) was expanded to state the
  blast-radius asymmetry explicitly (ingest degrades one signal via `run_periodic`, the probe
  aborts `main()` entirely) — this article's own Fact above already stated that asymmetry
  correctly (it was one of two reviewers' independent findings that ONLY `run.py`'s comment and
  `vendor_health.py`'s docstring had regressed to a false "never raises"/"propagates identically"
  claim; this article's Fact was not one of them). `vendor_health.py`'s docstring gained the same
  disclosure; `test_vendor_health.py`'s breaking-char test dropped an unused `caplog` fixture and
  a `with caplog.at_level(...)` wrapper that asserted nothing about logs — the Facts above
  (`test_vendor_health.py (STORY-070) exercises ... WARNING record ... does NOT propagate`) never
  cited that wrapper. No Fact in this article changed. verified_sha -> bfa5f77.
