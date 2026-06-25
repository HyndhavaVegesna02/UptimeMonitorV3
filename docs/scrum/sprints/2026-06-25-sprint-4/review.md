# Sprint 4 — Review

**Goal:** Zone 3 ingest opens — the Dynatrace inbound adapter queries synthetic monitor
results via DQL and normalizes each location execution into a canonical `SignalObservation`,
vendor specifics fully contained so the core stays untouched.

**Branch:** `sprint-4` (commits `6cc0e9f..b46e6cb`) · **Committed:** 5 pts · **Done:** 5 pts
**Capacity:** 6 (velocity 8/6/6/6, last-3 mean). Deliberate single-story sprint.

---

## STORY-008 — Dynatrace adapter + DQL normalization (5 pts) — ✅ DONE

**Pipeline:** implementer (Sonnet) → spec review **PASS** (Opus) → quality review (Opus):
1 MAJOR → **fix loop 1** (fresh Sonnet agent) → re-review **APPROVE** (Opus) → DoD gate green.

What was built — a self-contained inbound adapter under
`backend/src/adapters/inbound/dynatrace/`:
- `query.py` — pure DQL builder (watermark − overlap window, dossier §8) + an injected
  `Executor` seam (no live Dynatrace, ever, in tests).
- `dispatch.py` — a `synthetic_test.type` → normalizer registry; unknown types raise
  `UnsupportedMonitorTypeError` (additive seam for future types).
- `http_normalizer.py` / `clickpath_normalizer.py` — per-type normalizers; clickpath
  collapses its multi-step journey to one monitor-level verdict, `steps` never modelled.
- `_assembly.py` — shared timestamp-parse + `SignalObservation`/`Provenance` construction
  (extracted in fix loop 1 to remove duplication).
- `health_mapping.py` — the only place vendor outcome words are read: success/failure/partial
  → up/down/degraded, total, raises on unknown.
- `adapter.fetch_observations(...)` — the pull-cycle entry point STORY-009 will call.
- 20 tests + 4 representative DQL fixtures under `backend/tests/fixtures/dynatrace/`.

### AC checklist (spec reviewer verified each MET against the diff)
- **AC1** — produces correct canonical `SignalObservation` per location execution, every §5
  field with expected values; one obs per location, no aggregation (asserted on the
  3-location fixture). ✅
- **AC2** — adapter entirely under `adapters/inbound/dynatrace/`; `lint-imports` green; vendor
  id only in `source.native_id`, never crosses into core. ✅
- **AC3** — separate per-type normalizers, type only as `native_kind`; clickpath multi-step
  collapses to one verdict, `not hasattr(obs,"steps")`. ✅
- **AC4** — all tests run off committed fixtures, zero live calls; health mapping explicit +
  unit-tested per outcome. ✅
- **AC5** — out-of-scope types (single-browser, NAM) raise rather than mis-normalize; asserted
  single-row and mixed-batch. ✅

### DoD evidence (re-run by the orchestrator at d9e5532; nothing changed since but doc commits)
| Command | Result | Exit |
|---|---|---|
| `pytest` | 109 passed | 0 |
| `lint-imports` | 3 kept, 0 broken | 0 |
| `python scripts/check_fk_direction.py` | 10 FKs checked, 0 violations | 0 |
| `alembic upgrade head` | no-op (no migration added) | 0 |

### Non-blocking minors recorded (candidate follow-ups, not bugs)
- Normalizers subscript required row fields directly → a malformed DQL row raises a bare
  `KeyError` rather than a named "malformed row" adapter error. (Fail-loud, not silent; deferred.)
- DQL `native_id` interpolation is unescaped (trusted vendor config; documented in-code). No
  action needed unless ids ever become untrusted.

### Demo
No live Dynatrace this sprint (by design — recorded fixtures). The adapter is exercised by its
20-test suite. To see it run:
`/.venv/Scripts/python.exe -m pytest backend/tests/test_dynatrace_adapter.py -q` → 20 passed.

---

## Blocked / carried
None. STORY-009 (pull loop, 5 pts) was **refined this session** (scheduler = asyncio) and is
`ready` in the backlog for Sprint 5 — it consumes `fetch_observations` from this adapter.

## Wiki
Compile pass done (blocks review, completed): no stale articles; new verified article
`docs/scrum/wiki/dynatrace-adapter.md` created; `architecture-boundary.md` re-stamped to
`b2ee794`. Internal links lint clean.

## PO verdict
- [ ] STORY-008 — **accept** (merge `sprint-4` to main) / **reject** (back to backlog with feedback)
