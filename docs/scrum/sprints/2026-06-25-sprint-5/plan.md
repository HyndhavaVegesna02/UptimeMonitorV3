# Sprint 5 — Plan

**Goal:** Zone 3 ingest closes — the core ingest service + an asyncio pull loop pull from the
Dynatrace adapter, validate-then-quarantine, dedupe on `source_event_id`, and advance the
per-signal watermark over accepted observations only, committing before advancing so a crash
mid-loop loses nothing.

**Branch:** `sprint-5` · **Start tag:** `sprint-5-start` · **Started:** 2026-06-25
**Capacity:** ~6 (velocity 8/6/6/6/5, last-3 mean) · **Committed:** 6 (STORY-009 = 5, STORY-020 = 1)

**Order:** STORY-009 first (high-risk centerpiece), then STORY-020 (1-pt mop-up).
**Model assignment (PO rule, mandatory):** implementer → Sonnet; reviewers → Opus.

Substrate already in place: `SignalIngestPort.ingest_observations(batch) -> IngestResult`
(`core/ports/signal_ingest.py`); `ObservationRepository.save_new(batch) -> int` (dedupes via
`ON CONFLICT DO NOTHING`, returns newly-inserted count); `WatermarkRepository.get/advance`;
`ClockPort` (`core/ports/clock.py`); `IngestResult{accepted, rejected}` (`core/domain/status.py`).
`core/services/` is EMPTY. There is NO rejected-observations port/adapter yet — STORY-009 adds it.
The `rejected_observations` spine table exists (cols: `signal_key` nullable, `reason`, `payload`
jsonb, `rejected_at`; no FK — see `migrations/versions/3a8254bcfe59_spine_schema.py`).

---

## STORY-009 — Pull loop + watermarks + validation gate (5 pts, full pipeline)

Spec: dossier §8 (ingest ordering) · §6 (ports) · §14 T1.3 (validation gate). Two pieces:
the **core ingest service** (pure, fake-tested) and the **asyncio pull loop** (composition).
§8 ordering: validate → dedupe → persist → advance watermark (accepted-only) → [hand to
pipeline: Zone 4, OUT OF SCOPE] → commit → sleep.

TDD steps (commit after every green step; stage only files you touched — never `git add -A`):

- [x] 1. Create `backend/src/core/services/__init__.py` + the ingest-service module skeleton.
        Add a `RejectedObservationRepository` port under `core/ports/` (a quarantine sink:
        `save(*, signal_key, reason, payload, rejected_at)` in domain terms) and export it from
        `core/ports/__init__.py`. Failing test: the service class is a `SignalIngestPort`. `pytest`
        + `lint-imports` green. Commit.
- [x] 2. Ingest service constructor takes the four core ports (observation repo, watermark repo,
        rejected repo, clock) injected — no globals. Failing test (in-memory fakes): a batch of all
        VALID observations → service calls `save_new`, returns `IngestResult(accepted=<save_new
        return>, rejected=0)`, and advances the watermark to `max(observed_at)`. Implement the happy
        path. Commit. (AC3 happy path)
- [x] 3. Failing test: an observation with an implausibly-FUTURE `observed_at` (the "year-2099"
        case, judged against the injected `ClockPort.now()` + a tolerance) is QUARANTINED to the
        rejected repo (with reason + payload), is NOT passed to `save_new`, and the rest of the batch
        still proceeds (no poison pill). `IngestResult.rejected` counts it. Order is validate-THEN-
        dedupe. Implement the validation gate. Commit. (AC1)
- [x] 4. Failing test: the watermark advances to `max(observed_at)` over ACCEPTED observations
        ONLY — the future-timestamp reject from step 3 cannot leap the cursor. Implement accepted-only
        advance. Commit. (AC2)
- [x] 5. Failing test: a duplicate `source_event_id` makes `save_new` return fewer than
        `len(valid)`; `IngestResult.accepted` reflects the TRUE newly-inserted count returned by
        `save_new` (not `len(valid)`). Re-ingesting the same batch is a no-op (idempotent). Implement.
        Commit. (AC3)
- [x] 6. Failing test: commit-before-advance ordering at the service level — if `save_new` raises,
        the watermark is NOT advanced and nothing counts as accepted (a half-applied cycle never moves
        the cursor). Plus an idempotent-replay test proving overlap + dedupe + accepted-only-advance
        together lose nothing and double-count nothing across a re-run. Implement the ordering /
        unit-of-work boundary. Commit. (AC4)
- [x] 7. Add `PostgresRejectedObservationRepository` under `backend/src/adapters/persistence/`,
        mirroring `PostgresObservationRepository` (injected `Engine`, no global). Failing DB-gated
        test (use the `migrated_db` fixture from `backend/tests/conftest.py`): `save(...)` writes a
        row into `rejected_observations` with the reason + payload jsonb. Implement. Commit. (AC1
        persistence)
- [x] 8. Add the asyncio pull loop in `backend/src/composition/`. Failing test: a single-cycle
        coroutine, given a signal + an injected adapter `Executor` (fake) + the ingest port + clock,
        runs ONE cycle — `WatermarkRepository.get(signal_key)` → `dynatrace.fetch_observations(...)`
        (watermark + overlap) → `SignalIngestPort.ingest_observations(batch)`. Assert it holds NO
        domain logic (only calls the port + adapter) and is a plain `asyncio` task (NO new dependency
        in `pyproject.toml`). Implement the single-cycle function + the periodic asyncio wrapper. Commit.
        (AC5)
- [x] 9. Self-review the whole diff: `core/services/` imports only `core`; `composition/` may import
        both sides; the loop has no business logic; no SQL above persistence. Tidy any TDD residue. Commit.
- [ ] 10. **DoD gate** (all four exit 0): `pytest`, `lint-imports` (the new service is core — must
        import only core; the loop is composition), `python scripts/check_fk_direction.py`,
        `alembic upgrade head` (DB-gated via `scripts/dev_db.py up`/`down`). Forward blast radius:
        `canonical-types-and-ports.md` (code_refs incl. `core/ports/` — you ADD a port → update its
        Facts + bump `verified_sha`) and `persistence-adapters.md` (code_refs incl. the persistence
        repos — you ADD the rejected-obs adapter → update + bump). `dynatrace-adapter.md`: re-verify
        only if your diff touches the adapter dir (it shouldn't — the loop only consumes
        `fetch_observations`). CLAUDE.md: update only if a command/stack changed (none expected). Record
        evidence in `sprint-current.yaml`. Commit.

**Reviews (after step 10):** spec reviewer (Opus) against AC1–AC5 verbatim; then code-quality
reviewer (Opus). Per the new working agreement: parallel-shape work must share its assembly; and
the orchestrator (not the implementer) records DoD evidence into `sprint-current.yaml`. The core
ingest service is tested with in-memory fakes — no live DB, no live Dynatrace (working agreement).

---

## STORY-020 — Named malformed-DQL-row error (1 pt, light pipeline: implementer + DoD gate)

Spec: Sprint 4 review follow-up. Replace the bare `KeyError` on a malformed DQL row with a named
`MalformedDqlRowError` (a `ValueError` subclass, matching `UnsupportedMonitorTypeError` /
`UnknownVendorOutcomeError`) that names the missing field. Files:
`backend/src/adapters/inbound/dynatrace/{dispatch.py,_assembly.py}`.

TDD steps:

- [x] 1. Failing test: a DQL row missing the dispatch key `synthetic_test.type` raises
        `MalformedDqlRowError` (naming the field) from `dispatch.normalize_row`, not `KeyError`.
        Implement. Commit.
- [x] 2. Failing test (parametrized): a row missing any of `timestamp`, `event.id`,
        `synthetic_test.id`, `synthetic_location.name` raises `MalformedDqlRowError` naming the field
        from `_assembly.assemble_observation`. Implement (define the error once, reuse it; keep
        `latency_ms`/`request.response_time_ms` OPTIONAL — absence is not an error). Commit.
        (Finished by orchestrator after the implementer subagent hit a session limit mid-step: it
        had committed step 1 + the shared MalformedDqlRowError/require_field in _assembly.py, and
        left a coherent uncommitted step-2 test missing only `import re`; orchestrator fixed the
        import and routed the 4 required fields in assemble_observation through require_field.)
- [ ] 3. **DoD gate** (all four exit 0): `pytest` (the 20 STORY-008 tests still pass unchanged +
        the new ones), `lint-imports`, `check_fk_direction.py`, `alembic upgrade head` (DB-gated).
        Forward blast radius: re-verify `dynatrace-adapter.md` (its code_refs include the package) —
        add a Fact about the named error + bump `verified_sha`. Record evidence. Commit.
