# Sprint 21 — Review

**Story:** STORY-016b — Live Dynatrace reconciliation, verified internally. **5 pts. Accepted.**
**Branch:** `sprint-21`. **Final SHA:** `213034b` (code) + `442b97d` (wiki).

## What shipped
The Dynatrace ingest path now matches the PO's REAL Grail tenant (proven by a live probe), and the live
loop runs Dynatrace-only for internal verification (Statuspage deliberately out of scope):
- **Query** targets `dt.synthetic.events`, filters `dt.synthetic.monitor.id` (the placeholder
  `dt.synthetic.executions` / `synthetic_test.id` were invalid).
- **Executor** handles the ASYNC Grail API: `execute` → 202 + `requestToken` → poll `query:poll` until
  `SUCCEEDED`, with a real poll budget (60 × 1.0s); FAILED/CANCELLED/exhaustion → `GrailQueryError`.
- **Normalizer** maps the real fields: 9-digit **nanosecond** timestamps (truncated to µs so
  `fromisoformat` accepts them), `dt.synthetic.monitor.id`→native_id, `result.statistics.duration`
  ns→`latency_ms` ms, `dt.entity.synthetic_location`→location; dispatch on `event.type`.
- **Health** via `map_synthetic_status` — `HEALTHY`/`0`→UP, **fail-loud** on anything else (the real
  failure code is captured in the AC6 live run, never guessed).
- **Driver** is Dynatrace-only when Statuspage is absent (`LoggingPublisher` no-op); the full
  `BestEffort(Recording(Statuspage))` chain returns automatically once Statuspage is configured.

## DoD gate (orchestrator-run, clean committed tree `213034b`)
All six exit 0: **pytest 416 passed** (full suite minus the 2 `dev_db` container-harness meta-test
files) + those 8 meta-tests pass clean in a churn-free env = **all green**. The 3 transient failures
during gate runs were the orchestrator's own repeated `dev_db` container churn (Docker readiness
timeouts), not the code — confirmed by a clean re-run. lint-imports 5/0 · fk 11/0 · alembic up-to-date
(no migration) · ruff clean.

## Review — one fix loop
Both Opus reviewers flagged the same blocking pair; structural agreements (real-object composition
tests, genuinely-driven async poll, correct ns-parse, named errors) all held:

1. **AC4 (both reviewers) — invented failure mappings.** `map_synthetic_status` guessed `code 1→DOWN`,
   `2→DEGRADED` + message strings, against the plan's explicit, twice-stated "do not invent; fail-loud
   until observed live." This would mask the real failure code the AC6 live run exists to capture, and
   was untested. **Fixed:** stripped to `HEALTHY/0→UP` + `UnknownVendorStatusError`.
2. **AC1 (spec) — query tests deleted, not updated.** The `build_dql_query` unit tests were removed with
   no replacement, so nothing drove the new data object / filter field / injection guard / tz-rejection.
   **Fixed:** restored 4 tests against the real schema.

A consequence surfaced during the fix: two `pull_loop` failure tests had relied on the (now-removed)
invented mapping to turn `code "1"/"ERROR"` rows into DOWN. **Fixed:** those tests now mock the
vendor-mapping edge (production stays fail-loud). Non-blocking minors folded in: `parse_ns_timestamp`
edge tests, stale docstrings, `LoggingPublisher` import hoist, and a real poll budget (~3s → 60s) for
the live run.

## AC outcome
AC1 (query) — MET (after fix) · AC2 (async executor) — MET · AC3 (real-field normalizer) — MET ·
AC4 (fail-loud health) — MET (after fix) · AC5 (Dynatrace-only driver) — MET · **AC6 (live internal
verification) — pending the manual PO run.**

## Wiki blast radius
Compile pass `442b97d`: 4 articles updated (`dynatrace-adapter` a major rewrite to the real schema;
`ingest-service-and-pull-loop`, `statuspage-publish`, `migrations-and-db` for the publisher selection +
optional Statuspage). Sweep: **0 stale / 0 missing refs / 0 bad links** across 11.

## Verdict
**STORY-016b accepted — 5/5.** The ingest path is now built to the real tenant and fails loud where it
doesn't yet know the truth. The remaining step is the live internal verification (AC6): run the loop
against the real monitor, force a failure, read the real DOWN code, and commit it.
