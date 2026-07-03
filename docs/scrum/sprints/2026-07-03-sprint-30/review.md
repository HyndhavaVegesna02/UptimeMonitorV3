# Sprint 30 — Review

**Sprint goal:** expose the topology + component-grain availability the frontend is blind to
(STORY-044) — component→signals enumeration, rollup-plus-children availability, authoritative
server-side per-signal intervals (kills audit H2's 60-vs-120 completeness mis-compute). Unblocks
STORY-015d and STORY-015e.

**Committed:** STORY-044 (5 pts). **Delivered for verdict:** STORY-044 — Done (gate + both
reviewers green, first pass). Story commits `d8231c4..d1ca619` on `sprint-30`
(5 commits, ~2 190 insertions / 35 files).

---

## STORY-044 — Availability & topology API (5 pts)

### What was built

1. **Schema + seed (T1, `d8231c4`)** — Alembic revision `5ed254a8daab` adds
   `signals.interval_seconds` (nullable Integer, no FK — spine boundary untouched; reversible,
   verified both directions). `composition/seed.py` now persists each signal's configured
   interval on every boot upsert — the DB read model finally carries the cadence the config
   has declared since STORY-016a.
2. **Core port + adapter (T2, `746cf77`)** — new frozen domain type `core/domain/topology.py::Signal`
   (`interval_seconds > 0` when set, enforced by validator) + `SignalNotFoundError` /
   `SignalIntervalUnconfiguredError`; new `SignalRepository` port (`list_signals` ordered,
   `get → None` on unknown — parity with `ComponentRepository.get`);
   `PostgresSignalRepository` + `FakeSignalRepository` proven by ONE shared contract-test body
   (Postgres half DB-gated, genuinely executed).
3. **Topology enumeration (T3, `f39a408`, AC1)** — new five-file `api/v1/topology/` module:
   `GET /api/v1/topology` returns every component with nested signals
   (`signal_key`, `name`, `interval_seconds`, `component_id`), sourced from the seeded DB —
   never from config files at request time. Empty topology → `200 []`.
4. **Component-rollup availability (T4, `280c1e3`, AC2)** —
   `GET /api/v1/availability/component/{component_id}`: per-signal `AvailabilityResult`
   children (each computed with ITS OWN configured interval) + the `rollup_group` MIN/SUM
   rollup in one payload. Unknown component → 404; naive datetime → 422; unconfigured
   interval → 409; no-data / zero-signal → nulls, never a 500.
5. **Real default interval (T5, `280c1e3`, AC3)** — `GET /availability` without
   `interval_seconds` now uses the signal's seeded interval; the 60s stopgap default and the
   false "STORY-040 will supply" comment are gone. Explicit caller interval still wins
   (back-compat); unknown signal on the default path → honest 404.
6. **Wiki blast radius (T6, `d1ca619`, AC4)** — 5 articles updated + 2 re-verified, all at
   `verified_sha 280c1e3`; `core-pipeline-and-availability` + `frontend-zone` untouched as the
   AC predicted.

### AC evidence (spec reviewer: PASS, all MET — it RAN the cited tests)

| AC | Verdict | Evidence |
|----|---------|----------|
| AC1 enumeration, seeded source, DB-gated test | MET | `test_topology_endpoint.py` (6) incl. `test_topology_db_gated_sourced_from_seeded_topology` — real Postgres via `migrated_db`, seeds via `seed_topology`, asserts `interval_seconds` comes back from the DB. Ran; passed, did not skip. |
| AC2 rollup + children, per-child intervals, 422/404/nulls | MET | `test_component_availability_multi_signal_rollup_min_and_sum`: sig_a interval 60 → 1.0, sig_b interval 120 → 0.5; rollup avail = MIN = 0.5, counts SUM (6 total / 5 passing); + naive→422, unknown→404, no-data→nulls, zero-signal→`signals: []`, non-aligned window. All ran green. |
| AC3 default = configured interval; explicit wins | MET | H2 regression test: 120s signal, 4 obs / 480s window → completeness 1.0 (not the halved 0.5 the old 60s default produced); explicit `interval_seconds=60` still overrides. Stopgap text verified gone. |
| AC4 shape test, six gates, blast radius | MET | `test_topology_module_five_file_shape` passed; six gates green (below); sweep 12/12 CURRENT. |

**Spec finding (non-blocking, wording):** AC4's parenthetical listed `api-five-file-convention`
among "untouched" articles, but AC1's new five-file module makes updating that article MANDATORY
under the mechanical-sweep agreement. The implementer resolved it the only correct way (updated
it). **Scope addition flagged:** the 409 unconfigured-interval path — no AC names it, but it is
plan-pinned (D2/D4/D5) edge behavior for the nullable column, tested on both endpoints. Keep.

### Quality review (Opus): APPROVE — 0 Critical, 0 Major

Verified: core `availability.py` byte-identical (rollup consumed as-is); migration matches D1
exactly; parity contract genuinely two-impl; per-child intervals real (not one shared interval);
`create_app` injection symmetric with peers; pyproject change only adds `topology` to the
api-feature-independence contract; wiki symbol citations spot-checked accurate.

**Minors (non-blocking, recorded):**
1. `availability/service.py::get_component_availability` spells out all nine `AvailabilityDTO`
   fields inline per child instead of reusing `_to_dto` — field-list duplication that would
   drift if the DTO gains a field.
2. `children_signals` iterated twice (null-interval guard, then compute) — intentional
   fail-fast; noted only.

### DoD gate (orchestrator-run, committed HEAD `d1ca619`, clean tree, single non-concurrent DB run)

| # | Command | Result |
|---|---------|--------|
| 1 | `pytest` | **475 passed** in 91.59s (+31 over sprint-29's 444) |
| 2 | `lint-imports` | 5 contracts kept, 0 broken |
| 3 | `check_fk_direction.py` | 11 FKs, 0 violations |
| 4 | `alembic upgrade head` | exit 0 (`5ed254a8daab`; reversibility verified) |
| 5 | `ruff check .` | All checks passed |
| 6 | `ruff format --check .` | 168 files already formatted |

(Gates 3–4 re-ran sequentially after the first invocation missed the env-var export — an
orchestrator shell slip, never concurrent, code never at fault.)

### Wiki compile pass

Mechanical sweep: **12/12 articles CURRENT, 0 broken links.** Updated this sprint:
`api-five-file-convention`, `canonical-types-and-ports`, `persistence-adapters`,
`migrations-and-db`, `architecture-boundary` (+ `config-layer`, `dev-setup-and-dod`
re-verified). Candidate future cleanup (implementer-flagged): `composition/seed.py` is in no
article's `code_refs` — a pre-existing coverage gap, not this story's obligation.

### Demo steps (local)

```bash
.venv/Scripts/python.exe scripts/dev_db.py up          # throwaway DB, migrated
# export the two printed URLs, then:
.venv/Scripts/python.exe -m uvicorn src.composition.asgi:app --port 8000
# boot seed populates topology from config/apps/httpcheck.yaml (interval_seconds now persisted)
curl http://localhost:8000/api/v1/topology
#   -> [{"id":"http-check","name":"HTTP Check","signals":[{"signal_key":"http-check",
#       "name":"HTTP Check","interval_seconds":120,"component_id":"http-check"}]}]
curl "http://localhost:8000/api/v1/availability/component/http-check"
#   -> {"component_id":"http-check","rollup":{...},"signals":[{"signal_key":"http-check",...}]}
curl "http://localhost:8000/api/v1/availability?signal_key=http-check"
#   -> completeness computed at the REAL 120s interval (was silently halved before)
```

### Process notes (retro input)

- Implementer deviation: T4+T5 landed in one commit (shared `AvailabilityService` plumbing);
  both were still test-first, justification reported proactively. No harm; worth a retro look
  at whether the plan should have merged them into one task up front.
- Clean single pass: no stall, no fix loop, zero blocking review findings — second consecutive
  zero-fix-loop sprint.

## Verdict (PO, 2026-07-03)

- STORY-044: **ACCEPT** — merged to main (5/5 points). The two quality minors folded into the
  existing STORY-047 chore (retitled: quality-review minors, STORY-045 + STORY-044), items 3–4 /
  AC4; estimate stays 1.
