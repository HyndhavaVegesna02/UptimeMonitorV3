---
id: STORY-080
title: dev_db test harness — kill the standing full-gate false-red (free ports + unique names + contention hardening across the test_dev_db_* family)
type: defect
---

## Context
Filed from sprint 44 (STORY-079's gate self-run, 2026-07-12), per the 2026-07-06 agreement that
a contention-capable gate is never left standing. ESCALATED to top priority at the sprint-46 retro
(2026-07-15): the dev-db harness tests false-red'd BOTH sprint-46 full-gate runs — `test_dev_db_cli.py`
at 8153b53 and `test_dev_db_fixture.py` at 6c4a257 — each forcing a contention-proof cycle. It is now a
**standing full-gate false-red** that taxes every sprint's close.

Two distinct-but-related failure mechanisms across the `test_dev_db_*` family, both rooted in the
self-container-spawning harness tests contending for host resources under full-suite Docker load:

1. **Fixed-port / fixed-name collision (the originally-filed defect).**
   `backend/tests/test_dev_db_cli.py` hardcodes host port `55433` (`_TEST_PORT`, line 34; also a literal
   `docker -p 55433:5432` at line 116) and a fixed container name `uptime_pg_pytest_cli_test`
   (`_TEST_CONTAINER`, line 33). Any externally running container on that port/name (e.g. a second
   reviewer/demo DB, or the gate's own dev-DB) false-reds them. `scripts/dev_db.py` already exposes the
   remedy: a `--port` flag (default `HOST_PORT`) and `_free_tcp_port()` / `unique_container_name()`
   helpers — the tests simply don't use them.

2. **Connection-disconnect under Docker resource contention (`test_dev_db_fixture.py`).**
   Under full-suite load alongside the gate's own DB container, the fixture-spawned Postgres intermittently
   drops connections ("server closed the connection unexpectedly"), a DIFFERENT member failing each run.
   pytest here already runs SERIALLY (no xdist, no addopts) — this is resource contention, not a
   parallelism bug, so serialization knobs are a no-op. The durable remedy is readiness/robustness
   hardening (retry-until-ready, connection-establishment retry on the freshly-started container) so a
   momentarily-overloaded-but-healthy container is not read as a failure.

Both are PROVEN contention per the 2026-07-06 protocol: empty product diff since each sprint cut, and
each file passes in single-file isolation (cli 2/2 ~15s; fixture 6/6 ~9s) with adequate resources.

## Description
Make the whole `test_dev_db_*` family gate-robust so no member false-reds the canonical `pytest` gate
under concurrent-container / full-suite load — WITHOUT skipping, xfailing, or removing any test (the
teardown-on-failure contract in `test_dev_db_fixture.py` and the idempotent-against-leftover contract in
`test_dev_db_cli.py` must keep asserting exactly what they assert today). Two prongs:

1. **Collision-proofing:** replace the hardcoded `55433` and fixed container name in
   `test_dev_db_cli.py` with a free scratch port + unique container name chosen at test time, reusing the
   existing `scripts/dev_db.py` helpers (or an env override). The idempotent-against-leftover test keeps
   proving its contract on its own uniquely-named container.
2. **Contention-hardening:** make the container-readiness / connection-establishment path in the shared
   harness (`scripts/dev_db.py` startup wait and/or the `test_dev_db_fixture.py` container spawn) resilient
   to transient "server closed the connection" under load — retry-until-ready with a bounded budget
   (honoring the existing `DEV_DB_READY_TIMEOUT_SECONDS`), so a healthy-but-busy container is not misread
   as a hard failure.

## Acceptance Criteria
- [ ] AC1 (no fixed port/name): the dev_db CLI tests no longer bind a fixed host port or container name —
      a container already bound to `55433` (or holding the old fixed name) does not affect them; a
      regression test/pattern proves it (e.g. an unrelated container pre-bound to the old port).
- [ ] AC2 (CLI gate-robust): canonical `pytest` is green with an unrelated Postgres container running on
      `55433` — the previously-colliding CLI tests pass, not skip.
- [ ] AC3 (fixture contention-hardening): the container-readiness / connection path retries transient
      disconnects until ready within a bounded budget; a simulated transient "connection closed" during
      readiness is recovered rather than surfaced as a test failure (unit-level test of the retry logic,
      Docker probed via the injected/monkeypatched style already used in `test_dev_db_cli.py` /
      `scripts/dynamo_local.py`).
- [ ] AC4 (contracts preserved): no `test_dev_db_*` test is skipped, xfailed, or deleted; the
      teardown-on-failure contract (`test_dev_db_fixture.py`, proven by a `.throw()` test) and the
      idempotent-against-leftover contract (`test_dev_db_cli.py`) still assert exactly what they do today.
- [ ] AC5 (gate + boundaries): six backend gates green; import-linter contracts pass; wiki blast radius
      resolved (sweep decides — `dev-setup-and-dod.md` / `migrations-and-db.md` are candidates).

## Open Questions
<!-- none -->

## History
- 2026-07-12: filed from sprint-44 STORY-079 gate contention (proof recorded in the story report).
- 2026-07-15: ESCALATED at sprint-46 retro to top priority — standing full-gate false-red across the
  whole `test_dev_db_*` family (CLI at 8153b53, fixture at 6c4a257).
- 2026-07-15: RE-REFINED at sprint-47 planning. PO widened scope from the CLI-only port fix to the whole
  `test_dev_db_*` contention family (collision-proofing + readiness/connection contention-hardening),
  estimated 5 points. Status: ready.
