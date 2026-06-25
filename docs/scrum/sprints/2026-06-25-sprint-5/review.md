# Sprint 5 — Review

**Goal:** Zone 3 ingest closes — the core ingest service + an asyncio pull loop pull from the
Dynatrace adapter, validate-then-quarantine, dedupe on `source_event_id`, and advance the
per-signal watermark over accepted observations only, committing before advancing so a crash
mid-loop loses nothing.

**Branch:** `sprint-5` (commits `2229ed9..84aa1fb`) · **Committed:** 6 pts · **Done:** 6 pts
**Capacity:** ~6 (velocity 8/6/6/6/5, last-3 mean).

---

## STORY-009 — Pull loop + watermarks + validation gate (5 pts) — ✅ DONE

**Pipeline:** implementer (Sonnet) → spec review **PASS** (Opus) → quality review **APPROVE**
(Opus) → DoD gate green. **No fix loop.**

Built:
- `core/services/ingest_service.py` — `IngestService` (the concrete `SignalIngestPort`), owning
  the dossier §8 ordering: validate→quarantine → dedupe+persist → advance watermark
  (accepted-only, after persist). Pure core; imports only `src.core.*`.
- `core/ports/rejected_observation_repository.py` — new `RejectedObservationRepository` port (the
  6th port; first quarantine sink).
- `adapters/persistence/rejected_observation_repository.py` — `PostgresRejectedObservationRepository`
  (3rd repo adapter; writes the no-FK `rejected_observations` table).
- `composition/pull_loop.py` — `run_cycle` + `run_periodic`: a plain asyncio loop, no new
  dependency, no domain logic — wires `watermark.get → fetch_observations → ingest_observations`.

### AC checklist (spec reviewer verified each MET against the diff)
- **AC1** — future-timestamp obs quarantined to `rejected_observations` (reason+payload), excluded
  from persist, rest of batch proceeds; validate-before-dedupe. Live-DB row test included. ✅
- **AC2** — watermark advances over accepted-only; explicit year-2099 test; no advance when all
  rejected. ✅
- **AC3** — `IngestResult.accepted` = `save_new` return (true newly-inserted), duplicate is a no-op. ✅
- **AC4** — `save_new` failure leaves the watermark un-advanced (commit-before-advance); idempotent
  replay loses nothing / double-counts nothing. ✅
- **AC5** — plain asyncio, no new dependency (`pyproject.toml` unchanged), loop holds no domain
  logic, core tested with in-memory fakes; `lint-imports` green. ✅

### Non-blocking minors recorded (quality review)
- Single-signal-batch assumption (`signal_key = valid[0].signal_key`) — documented, matches
  `fetch_observations` (1 signal/cycle); latent only if a future multi-signal batch arrives.
- `stop_event` checked twice in `run_periodic` (intentional; a comment would help).
- New persistence adapter mirrors the existing repos acceptably (no extractable shared assembly).

---

## STORY-020 — Named malformed-DQL-row error (1 pt) — ✅ DONE

**Pipeline:** light (implementer + DoD gate; no reviewers at 1 pt).

A missing required DQL field (`timestamp`, `event.id`, `synthetic_test.id`, `synthetic_test.type`,
`synthetic_location.name`) now raises a named `MalformedDqlRowError` via a shared `require_field`
helper, instead of a bare `KeyError`. `request.response_time_ms` stays optional. 5 new tests
(4 parametrized missing-field + 1 optional-latency).

**Process note:** the implementer subagent hit a session limit after committing step 1 (and the
shared error/helper). The orchestrator finished the trivial remainder per the verify-the-tree
working agreement — preserved the coherent uncommitted step-2 test (fixing only a missing
`import re`) and routed `assemble_observation`'s four required fields through `require_field`.

---

## DoD evidence (orchestrator re-ran the full gate at each story's done)
| Command | STORY-009 (5a62ba6) | STORY-020 (4afb5a2) |
|---|---|---|
| `pytest` | 127 passed | 133 passed |
| `lint-imports` | 3 kept, 0 broken | 3 kept, 0 broken |
| `check_fk_direction.py` | 10 FKs, 0 violations | 10 FKs, 0 violations |
| `alembic upgrade head` | no-op (no migration) | no-op (no migration) |

## Demo
- Ingest service + loop: `pytest backend/tests/test_ingest_service.py backend/tests/test_pull_loop.py`.
- Malformed-row error: `pytest backend/tests/test_dynatrace_adapter.py` (26 passed).
- No live Dynatrace / DB in core tests (working agreement); the rejected-obs adapter + FK/migration
  gates run against a throwaway Postgres via `scripts/dev_db.py`.

## Wiki
Compile pass done (blocks review): `architecture-boundary.md` rehabilitated from stale (core/services
now populated; full layering chain exercised) and re-verified; new article
`ingest-service-and-pull-loop.md` (the §8 ordering + asyncio loop); `canonical-types-and-ports.md`
+ `persistence-adapters.md` updated by the implementer (new port + adapter); `dynatrace-adapter.md`
gained the `MalformedDqlRowError` Fact. Links lint clean; no stale articles remain.

## Carried into Sprint 6
- STORY-021 (reject `native_id` in the DQL builder, 1 pt) — `ready`.
- Zone 4 (STORY-010 four-stage core pipeline, STORY-011 availability) — `draft`.

## PO verdict
- [ ] STORY-009 — accept / reject
- [ ] STORY-020 — accept / reject
