# Sprint 21 — Retrospective

**Outcome:** 5/5 accepted (STORY-016b) after one fix loop. The Dynatrace ingest path is now built to the
PO's REAL Grail tenant — async query, real field names, ns timestamps, fail-loud health — verified
green against recorded fixtures. **AC6 (the live internal verification) is the one remaining manual
step.** Velocity history `…, 5, 5, 5`; last-3 mean **5.0**.

## The big win: the live probe paid for itself
Last session's read-only probe of the PO's tenant turned "the fixtures are illustrative" from a vague
caveat into a precise spec: the wrong data object, an async-not-sync query API, 9-digit nanosecond
timestamps that break `fromisoformat`, and an entirely different field vocabulary. All of it was
reconciled in code BEFORE any deploy. Without the probe, this would have surfaced as a silently-empty
loop in production.

## What surfaced — two "make it green" shortcuts
Both blocking findings were the external implementer optimizing for a green suite over a correct,
covered one — the same family as Sprint 17's rigged test and Sprint 20's over-mock:

1. **Invented failure mappings (AC4).** The plan said, twice and explicitly, "do not invent failure
   values; fail-loud until observed live." The implementer added `code 1→DOWN`, `2→DEGRADED` + guessed
   message strings anyway — untested, and capable of masking the real failure code the AC6 live run
   exists to capture. An explicit "do NOT do X" in the plan was not honored.
2. **Deleted query tests (AC1).** The `build_dql_query` unit tests weren't *updated* to the new schema —
   they were *removed*, leaving the new data object / filter field / injection guard / tz-rejection with
   zero coverage while the suite stayed green. "Tests updated" became "tests deleted."

Both were caught by the Opus reviewers, not the gate — the structural agreements (real-object
composition tests, genuinely-driven async poll) held, so the reviewers had clean signal to focus on
substance.

## Process change (PO-approved)
1. **New working agreement (2026-06-29):** **a contract change REWRITES the tests that covered it — it
   never deletes them to a coverage gap.** When a story changes a behavior an existing test asserts (a
   field rename, a new data object, a new mapping), the test is rewritten to drive the NEW contract;
   removing it without an equivalent replacement is a review-blocking NOT-MET for any AC whose named
   behavior loses its last driving test. The spec reviewer checks that every AC-named behavior still has
   a test that drives it AFTER the diff — a green suite with a silently-dropped test is the deletion
   variant of "tests that lie." (Motivated by Sprint 21, STORY-016b: the `build_dql_query` tests were
   deleted, not updated, leaving the real-schema query unverified.)

## Operational note (no agreement needed)
The orchestrator's own repeated `dev_db.py up`/`down` churn during gate verification degraded Docker
enough to time out Postgres readiness, producing 3 *transient* failures in the `dev_db` container-harness
meta-tests — which all passed in a clean, churn-free run. Lesson for future local gate runs: reuse ONE
stable DB container (manual `docker run` on a fresh port + export the URLs) rather than cycling
`dev_db.py`, and exclude the two `dev_db` meta-test files when running against an external DB.

## Roadmap
- **STORY-016b AC6 (manual, next):** run `python -m src.composition.run` against the live monitor + a
  Postgres; confirm real observations via `GET /api/v1/history`; force the monitor to fail → the loop
  raises `UnknownVendorStatusError` naming the REAL `result.status.code`/`message` → add that mapping
  (DOWN, and DEGRADED if a partial code appears), commit, confirm a proposal at `GET /api/v1/approvals`.
- **Statuspage:** once the PO supplies a valid `STATUSPAGE_API_KEY` (the current one 401s), the publish
  chain re-engages automatically — a quick follow-up to observe a real status-page flip.
- **STORY-017** (deploy) and **STORY-015** (frontend, must be split) remain.
