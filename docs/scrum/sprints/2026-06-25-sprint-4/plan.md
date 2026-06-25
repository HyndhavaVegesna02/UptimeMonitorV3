# Sprint 4 — Plan

**Goal:** Zone 3 ingest opens — the Dynatrace inbound adapter queries synthetic monitor
results via DQL and normalizes each location execution into a canonical
`SignalObservation`, vendor specifics fully contained so the core stays untouched.

**Branch:** `sprint-4` · **Start tag:** `sprint-4-start` · **Started:** 2026-06-25
**Capacity:** 6 (velocity 8/6/6/6, last-3 mean) · **Committed:** 5 (STORY-008 only)

**Why a single-story sprint:** STORY-008 is the dependency root of Zone 3 and its highest-risk
unknown (vendor DQL parsing + per-type normalizers). It is sequenced first and alone within
capacity; STORY-009 (pull loop, asyncio) is `ready` for Sprint 5.

**Model assignment (PO rule, mandatory):** implementer → Sonnet; both reviewers → Opus.

---

## STORY-008 — Dynatrace adapter + DQL normalization (5 pts, full pipeline)

Spec: dossier §5 (canonical signal + normalization) · §6 (ports) · §7 (mapping) · §8 (ingest).
Scope: **HTTP + browser clickpath** only (single-browser + NAM out of scope, kept additive).
All new code under `backend/src/adapters/inbound/dynatrace/`; fixtures under
`backend/tests/fixtures/dynatrace/`. The adapter is dumb + lossless — **one observation per
location execution, no aggregation** (collapse is a core step, §10).

Canonical target shape (`backend/src/core/domain/signal.py`): `SignalObservation` =
`signal_key, observed_at` (tz-aware UTC — naive/non-UTC is rejected by the domain validator),
`health` (up/down/degraded), `source_event_id`, `source = Provenance{system, native_id,
native_kind}`, `location`, optional `latency_ms`, optional `raw_ref`. Vendor ids live ONLY in
`source`.

TDD steps (commit after every green step; stage only the files you touched — never `git add -A`):

- [x] 1. Create package skeleton `adapters/inbound/dynatrace/__init__.py` + an empty test
        module. Run `pytest` + `lint-imports` to confirm the new package keeps both green. Commit.
- [x] 2. Author recorded DQL response fixtures (one HTTP, one browser-clickpath; each with
        multiple locations, and the clickpath multi-step) under `backend/tests/fixtures/dynatrace/`,
        from the documented DQL row shape (§8). Commit.
- [x] 3. Failing test: HTTP normalizer maps one location-execution row → correct
        `SignalObservation` (every §5 field; `observed_at` tz-aware UTC; `native_kind="http"`).
        See it fail. Commit test.
- [x] 4. Implement the HTTP normalizer minimally; see step-3 test pass. Commit.
- [x] 5. Failing test: HTTP health mapping success/failure/partial → `up`/`down`/`degraded`,
        derived only from canonical-meaningful fields. Implement; pass. Commit.
- [x] 6. Failing test: clickpath normalizer — a multi-step execution collapses to ONE
        monitor-level `health` verdict, `native_kind="clickpath"`, one observation per location,
        step detail not modelled (raw payload referenced via `raw_ref`). Implement; pass. Commit.
- [x] 7. Failing test: the adapter dispatches a mixed DQL response by monitor type → a flat list
        of canonical observations, one per location execution, no aggregation across locations.
        Implement the dispatch + adapter entry point (e.g. `fetch_observations(signal_key, since)`).
        Pass. Commit.
- [x] 8. Failing test: an out-of-scope monitor type (single-browser / NAM) is surfaced as
        unsupported (raised or recorded) rather than silently mis-normalized — proving future
        normalizers are purely additive. Implement the guard; pass. Commit.
- [x] 9. Failing test: the DQL query builder produces a query scoped to a signal + a
        "newer than watermark, with overlap window" range (assert on the built query
        structure/string). The live executor is a thin injected seam (mocked in tests — no live
        Dynatrace). Implement the builder + seam. Pass. Commit.
- [x] 10. **DoD gate** (all four, exit 0): `pytest`, `lint-imports` (core untouched + no
        adapter→adapter import), `python scripts/check_fk_direction.py`, `alembic upgrade head`
        (DB-gated — obtain a migrated throwaway Postgres via `scripts/dev_db.py up`, per the
        working agreement; tear down with `down`). Forward blast radius: re-verify
        `canonical-types-and-ports.md` + `architecture-boundary.md` (their `code_refs` overlap the
        diff) — update or bump `verified_sha`. CLAUDE.md: update only if a command/stack/topology
        changed (the adapter adds none expected). Record evidence in `sprint-current.yaml`. Commit.

**Reviews (after step 10):** spec reviewer (Opus) against the PO-approved AC1–AC5 verbatim;
then code-quality reviewer (Opus). No live Dynatrace in any test (working agreement: pure core,
mockable edges — recorded fixtures only).
