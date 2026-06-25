---
title: Zone 3 — the ingest service (§8 ordering) + the asyncio pull loop
code_refs: [backend/src/core/services/ingest_service.py, backend/src/composition/pull_loop.py, backend/tests/test_ingest_service.py, backend/tests/test_pull_loop.py]
verified_sha: cca043f
verified_sprint: sprint-5
status: verified          # verified | stale | archived
---

## Facts (verified against code)

STORY-009 closed Zone 3 ingest: the core ingest SERVICE (the crash-safety guarantee) plus the
composition-zone asyncio PULL LOOP that drives it from the Dynatrace adapter (see
[[dynatrace-adapter]]). The ports + canonical types it speaks are in [[canonical-types-and-ports]].

### The ingest service — `IngestService` (`core/services/ingest_service.py`)
- `IngestService(SignalIngestPort)` (`ingest_service.py:43`) is the FIRST populated thing in
  `core/services/`; it owns the dossier §8 ordering so every adapter that feeds the core inherits
  it. It imports ONLY `src.core.*` (ports + domain) — no SQL, no vendor types, no globals.
- Constructed with the four core ports injected (`__init__`, `ingest_service.py:52-63`):
  `observation_repo`, `watermark_repo`, `rejected_repo`, `clock` — so it is fully exercised with
  in-memory fakes (no DB, no Dynatrace) per AC5.
- `ingest_observations(batch) -> IngestResult` (`ingest_service.py:65-110`) runs the §8 order,
  which is significant for AC1 + AC4:
  1. **Validate then quarantine** (`:86-97`): each observation whose `observed_at` is implausibly
     future (`_is_implausibly_future`, `:112-113`: `observed_at > now + FUTURE_TOLERANCE`, against
     the injected `clock.now()`) is written to `rejected_repo.save(signal_key, reason, payload,
     rejected_at)` and EXCLUDED from the persist set; the rest proceeds (no poison pill). Validation
     happens BEFORE dedupe, so a bad row becomes a recorded rejection rather than being deduped away.
  2. **Dedupe + persist** (`:104`): `observation_repo.save_new(valid)` — DB-level
     `ON CONFLICT (source_event_id) DO NOTHING`; its return is the TRUE newly-inserted count, which
     becomes `IngestResult.accepted` (NOT `len(valid)`, so a duplicate is a no-op — AC3).
  3. **Advance watermark accepted-only, after persist** (`:106-108`): to
     `max(observed_at)` over the VALIDATED observations only, and only AFTER `save_new` returns — if
     it raises, the exception propagates and the watermark is left untouched (commit-before-advance,
     AC4). A future-timestamp reject therefore can never leap the cursor (AC2). If nothing is valid,
     the watermark is not advanced (`:101-102`).
- `FUTURE_TOLERANCE = timedelta(minutes=5)` (`ingest_service.py:37`) and
  `FUTURE_TIMESTAMP_REASON` (`:40`) — the §14 T1.3 "year-2099" guard; the 5-min value is a judgment
  call (AC left the number open) to absorb source/process clock skew.
- **Single-signal-batch assumption** (`ingest_service.py:47-49,107`): `signal_key = valid[0].signal_key`
  and one `max(observed_at)` watermark assume one signal per batch — which matches how the Dynatrace
  adapter's `fetch_observations` produces batches (one signal per cycle). Documented, not guarded; a
  latent hazard ONLY if a future ingest path ever feeds a mixed-signal batch (recorded as a
  non-blocking review minor, STORY-009).

### The pull loop — `run_cycle` / `run_periodic` (`composition/pull_loop.py`)
- The loop lives in the composition zone — the one zone allowed to import BOTH `src.core` and
  `src.adapters` (dossier §4). It holds NO domain logic; it only wires three calls per cycle.
- `run_cycle(*, signal_key, native_id, watermark_repo, ingest_port, executor, overlap=DEFAULT_OVERLAP)
  -> IngestResult` (`pull_loop.py:32-57`): `watermark_repo.get(signal_key)` →
  `dynatrace.fetch_observations(watermark=..., overlap=...)` → `ingest_port.ingest_observations(batch)`.
  It is synchronous (none of the three calls is async in this codebase).
- `run_periodic(...)` (`pull_loop.py:60-95`) is the thin asyncio driver:
  `while not stop_event.is_set(): run_cycle(); await asyncio.sleep(interval_seconds)`. Plain
  `asyncio` — NO APScheduler, NO new dependency in `pyproject.toml` (AC5). `stop_event`
  (`asyncio.Event`) makes the loop deterministically stoppable in tests / future graceful shutdown;
  `on_cycle` is an optional hook for observing each `IngestResult` (test progress, later
  logging/metrics). Neither carries domain logic.

### Tests
- `backend/tests/test_ingest_service.py` exercises the real `IngestService` through in-memory fake
  repos + a fixed fake clock (no DB) — covering each AC: future-timestamp quarantine + no poison
  pill (AC1), accepted-only / year-2099 cursor (AC2), true newly-inserted count + duplicate no-op
  (AC3), watermark-not-advanced-on-`save_new`-failure + idempotent replay (AC4).
- `backend/tests/test_pull_loop.py` covers AC5: plain-asyncio (AST-asserts no `apscheduler` import),
  no-domain-logic pass-through, one-cycle-per-tick + stoppable.
- The DB-gated persistence side (the actual `rejected_observations` row write) is covered in
  `backend/tests/test_persistence_adapters.py` — see [[persistence-adapters]].

## Inference (synthesis, not verified)
- The "hand to pipeline (collapse → anti-flap)" step of dossier §8 is deliberately ABSENT here — it
  is Zone 4 (STORY-010), and the ingest service's responsibility ends at advancing the watermark.
  When the pipeline lands, the natural seam is between persist and the existing return.

## History
- sprint-5: created (STORY-009). Documents the ingest service's §8 ordering + the asyncio pull loop
  as built. Verified at cca043f.
