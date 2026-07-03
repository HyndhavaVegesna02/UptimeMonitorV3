# Sprint 31 — Review

**Sprint goal:** an on-demand outage simulator (STORY-048) — DB-persisted sample-mode flag
(default OFF), API toggle, live loop records incoming observations as DOWN while ON;
**TEMPORARY feature by PO directive, removability designed in (AC7).**

**Committed:** STORY-048 (5 pts). **Delivered for verdict:** STORY-048 — Done (gate + both
reviewers green, first pass, zero fix loops). Story commits `e7ff8b9..61d786a` on `sprint-31`
(6 commits; T1–T5 by the implementer, the T6 wiki tail recovered + committed by the
orchestrator after a watchdog stall — see Process notes).

---

## STORY-048 — Sample switch backend (5 pts, TEMPORARY)

### What was built

1. **Flag storage (T1, `e7ff8b9`)** — migration `09e9aa2cee32`: dedicated single-row
   `sample_mode` table (`CHECK (id)` pins it to one row; no FK; reversible; droppable).
   `SampleModeRepository` port (`is_enabled` → `False` when never set — the default-OFF lives
   in the port, not a seed; `set_enabled` idempotent upsert) + Postgres adapter + fake, proven
   by ONE parity contract body against both.
2. **API toggle (T2, `d51b5a2`)** — five-file `api/v1/sample_mode/`: `GET /api/v1/sample-mode`
   → `{enabled}`, `PUT /api/v1/sample-mode` `{"enabled": true|false}` → applies + echoes;
   invalid body → 422; wired through `create_app`/`app.state`/DI symmetric with peers.
3. **The override (T3, `565d209`)** — `composition/sample_mode.py::SampleModeIngest`, a
   decorator over the ingest port: reads the flag once per call; OFF → the delegate receives
   the IDENTICAL batch objects; ON → each observation `model_copy`'d to `health=DOWN` +
   `raw_ref="sample-mode:forced-down"` with every other field unchanged (dedup/watermarks
   unaffected). Core domain + services byte-identical.
4. **The seam (T4, `fbf286b`)** — ONE marked line in `run.py::build_live_loop` wraps the real
   `IngestService`. Two-cycle test proves a flip takes effect the NEXT cycle, no restart (AC4).
5. **End-to-end proof (T5, `0ea652e`)** — through the REAL `IngestService`: ON → persisted rows
   are DOWN + marked; OFF → persisted rows are the same instances the vendor sent.
6. **Wiki + REMOVAL inventory (T6, `61d786a`)** — new `docs/scrum/wiki/sample-mode.md` with the
   complete mechanical deletion recipe (files to delete, seam lines to revert — all grep-able
   via `STORY-048` — the DROP migration, and `raw_ref LIKE 'sample-mode%'` data cleanup);
   7 blast-radius articles updated.

### AC evidence (spec reviewer: PASS, AC1–AC7 ALL MET — it RAN all 46 story tests)

| AC | Verdict | Evidence (reviewer-run) |
|----|---------|--------------------------|
| AC1 persisted flag, parity, default OFF | MET | Parity contract 4/4 incl. DB-gated Postgres half (executed, not skipped); never-set → False; cross-instance persistence via `make_repo` factory. |
| AC2 five-file API, 422, DB round-trip | MET | `test_sample_mode_endpoint.py` 8/8 incl. shape test + DB-gated round-trip through a real Postgres-backed `create_app`. |
| AC3 ON→DOWN via loop, OFF unchanged, core pure | MET | e2e through the REAL IngestService both states; decorator unit tests 9/9; lint-imports confirms core purity. |
| AC4 per-cycle flip, no restart | MET | Three-cycle OFF→ON→OFF test; assembly test proves the same ingest_port threads into every loop. |
| AC5 simulated ≠ genuine DOWN | MET | Genuine DOWN has `raw_ref=None`; simulated carries the sentinel — asserted on rows persisted by the real chain. |
| AC6 six gates + blast radius | MET | Orchestrator gate below; sweep 13/13 CURRENT (reviewer independently re-ran it). |
| AC7 removability | MET | (a) seam comments grep-verified on all 8 existing-file edits, NO other production file changed, `core/domain`/`core/services` byte-identical; (b) OFF-path asserts object IDENTITY; `test_pull_loop.py` + `test_ingest_service.py` UNMODIFIED and green (7+12 passed); only the assembly-shape test updated (sanctioned); (c) REMOVAL inventory complete and accurate against the diff. |

Scope additions: **none**.

### Quality review (Opus): APPROVE — 0 Critical, 0 Major

Verified: decorator reads the flag exactly once per call, propagates repo failures, and the
frozen-model `model_copy` is safe (the only validator is on the untouched `observed_at`);
single-row CHECK migration correct + reversible; upsert SQL correct; the fake's optional
shared-store design judged HONEST parity (mirrors two adapters sharing one engine); assembly
test builds real objects and patches only `run_periodic`; REMOVAL inventory spot-checked
entry-by-entry; no debug scraps anywhere.

**Minors (non-blocking, recorded):**
1. Wiki `verified_sha` pinned at `0ea652e` (last code commit) rather than the wiki commit
   itself — functionally correct (the wiki commit is .md-only; sweep reports all CURRENT).
2. `FakeSampleModeRepository` uses bare `dict` type hints where peer fakes parametrize.

### DoD gate (orchestrator-run, committed HEAD `61d786a`, clean tree, single non-concurrent DB run)

| # | Command | Result |
|---|---------|--------|
| 1 | `pytest` | **498 passed** in 174.64s (+23 over sprint-30's 475) |
| 2 | `lint-imports` | 5 contracts kept, 0 broken |
| 3 | `check_fk_direction.py` | 11 FKs, 0 violations |
| 4 | `alembic upgrade head` | exit 0 (`09e9aa2cee32` applied) |
| 5 | `ruff check .` | All checks passed |
| 6 | `ruff format --check .` | 181 files already formatted |

### Wiki compile pass

Mechanical sweep: **13/13 articles CURRENT, 0 broken links** (run twice: orchestrator + spec
reviewer). New: `sample-mode.md` (Facts + the REMOVAL inventory — the PO's deletion recipe).
Updated: `api-five-file-convention`, `architecture-boundary`, `canonical-types-and-ports`
("eleventh port, deliberately not counted among the ten stable ones"), `config-layer`,
`dev-setup-and-dod`, `ingest-service-and-pull-loop`, `statuspage-publish`.

### Demo steps (local — the feature's reason to exist)

```bash
.venv/Scripts/python.exe scripts/dev_db.py up            # throwaway DB
# export the printed URLs; start uvicorn (:8000) + the live loop (source .env first)
curl http://localhost:8000/api/v1/sample-mode
#   -> {"enabled": false}                                # default OFF
curl -X PUT http://localhost:8000/api/v1/sample-mode -H "Content-Type: application/json" -d '{"enabled": true}'
#   -> {"enabled": true}                                 # next loop cycle records DOWNs
# ... after enough DOWN cycles trip the streak/anti-flap thresholds:
curl http://localhost:8000/api/v1/approvals              # -> a REAL degradation proposal
# approve it via the Dashboard/POST /decisions -> publications row + components.status change
curl -X PUT http://localhost:8000/api/v1/sample-mode -d '{"enabled": false}'
#   -> recovery cycles begin; the auto-publish recovery branch fires
# simulated rows remain identifiable: SELECT ... WHERE raw_ref LIKE 'sample-mode%'
```

### Process notes (retro input)

- **Second consecutive implementer stall at the 600s watchdog, same shape as sprint 29:**
  T1–T5 committed clean, stall during the T6 wiki pass, coherent uncommitted tail recovered by
  the orchestrator. The commit-after-green cadence again absorbed it with zero work lost — but
  twice-in-a-row is a pattern now, not an incident.
- **Both first-dispatch Opus reviewers were killed mid-run by a session limit** (no verdicts);
  fresh re-dispatches per the 2026-06-25 fresh-agent rule both passed. No fix loop either way.
- Zero blocking review findings — third consecutive zero-fix-loop sprint.

## Verdict (PO, 2026-07-03)

- STORY-048: **ACCEPT** — merged to main (5/5 points). Of the two cosmetic minors, the
  actionable one (fake's bare `dict` hints) folded into STORY-047 (item 5 / AC5, estimate
  stays 1); the verified_sha-pin note needs no chore (sweep-clean; pins refresh on next touch).
  STORY-049 (the Dashboard toggle) is now unblocked.
