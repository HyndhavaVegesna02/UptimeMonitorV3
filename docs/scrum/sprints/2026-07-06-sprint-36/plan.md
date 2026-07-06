# Sprint 36 — plan (locked 2026-07-06)

**Goal:** Production-hardening: the live loop survives transient vendor/network errors
(STORY-050), the documented `.env`-based startup actually works (STORY-043), and the
accumulated quality minors are cleared (STORY-047).

**Committed:** 050 (3) + 043 (2) + 047 (1) = 6, a deliberate one-point over-commit at
explicit PO direction; 047 is last and drops first.
**Order:** 050 → 043 → 047 — 050 and 043 both touch `composition/run.py`, so strictly
sequential dispatches.
**Parked sprint:** sprint 35 (deployment) is paused on its unmerged branch; see
`sprint-current.yaml`'s PARKED SPRINT NOTE for the resume recipe. Sprint 36 must not
touch STORY-017's files beyond the unavoidable shared ones (pyproject.toml, CLAUDE.md —
conflicts get resolved at 35's rebase).

---

## STORY-050 — live-loop transient-error resilience (defect, 3 pts, full pipeline)

Story: `docs/scrum/stories/STORY-050-live-loop-transient-error-resilience.md` (refined —
AC1–AC3 binding; AC3 = LOG-ONLY per PO decision; publish-path out of scope).

Design pins:
- The catch lives in `composition/pull_loop.py::run_periodic` around the `run_cycle` call
  — composition zone, no core change, no new domain type. Catch `Exception` (not
  BaseException — KeyboardInterrupt/SystemExit/asyncio.CancelledError must still
  propagate; note `CancelledError` is BaseException in 3.13, so a bare `except Exception`
  already lets it through — pin with a test that cancellation still stops the loop).
- Log shape: `logger.exception` (full traceback) with signal_key and the consecutive
  count for THAT signal (per-loop counter — each `run_periodic` instance owns one signal).
- Success path resets the counter; `on_cycle` hook behavior unchanged on success; a
  failed cycle does NOT invoke `on_cycle` (no result to hand it) — pin this in a test.
- `stop_event` semantics unchanged (the post-cycle stop check still runs after a FAILED
  cycle too — a stop requested during a failing cycle must not wait another interval).

### Tasks (TDD, commit per green step)
- [x] 1. Failing test: fake executor raises `GrailQueryError` once then succeeds —
      `run_periodic` (with a 2-cycle stop) completes both cycles; second cycle's ingest
      ran; ERROR logged with signal_key (caplog).
- [x] 2. Minimal catch in `run_periodic` + green.
- [x] 3. Consecutive-counter tests: N failures log increasing counts; success resets
      (fail, fail, succeed, fail → counts 1,2,reset,1); loop never exits (drive ≥3
      consecutive failures, assert still scheduling).
- [x] 4. Guard tests: cancellation still cancels; stop_event honored after a failed
      cycle; startup fail-fast pinned (missing secrets raises BEFORE any loop —
      existing `load_live_secrets` behavior, one test).
- [x] 5. Docstring updates (module + `run_periodic`) citing dossier §8 + STORY-050.
- [x] 6. Six-gate DoD (isolated pytest DB) + mechanical wiki sweep (expect
      `ingest-service-and-pull-loop.md` at minimum), article-by-article commits.

## STORY-043 — `.env` never loaded (defect, 2 pts, gate-only)

Story: `docs/scrum/stories/STORY-043-live-loop-dotenv-not-loaded.md` (AC1–AC5 binding).
Pinned at planning: `python-dotenv` is a RUNTIME dependency (imported by entrypoints —
same D1 reasoning as sprint-35's uvicorn move). Loading happens at the two process
entrypoints ONLY (`run.py::main` start + `asgi.py` module init), never inside
`load_settings`/`load_live_secrets` (AC4); `load_dotenv()` default semantics — existing
env vars WIN (AC3) — with a test proving an exported var is not overridden by `.env`.
AC5 fixes BOTH docs: CLAUDE.md's two claims AND the `dev-setup-and-dod.md` wiki Fact
(verified_sha bumped) — this is that story's OWN wiki blast radius, not the sweep's.

### Tasks
- [x] 1. Failing test: temp `.env` + scrubbed env → entrypoint loader resolves secrets;
      exported-var precedence test.
- [x] 2. `python-dotenv` to runtime deps; entrypoint `load_dotenv(...)` calls; green.
- [x] 3. AC5 doc fixes (CLAUDE.md same commit) + wiki `dev-setup-and-dod.md` update.
- [x] 4. Six-gate DoD + sweep (pyproject.toml will re-flag the shared articles).

## STORY-047 — quality-review minors (chore, 1 pt, gate-only, DROPPABLE)

Story: `docs/scrum/stories/STORY-047-publisher-wiring-minors.md` — the enumerated
STORY-045 publisher-wiring + STORY-044 availability-DTO minors, verbatim from the story
file. No design decisions; mechanical. Six-gate DoD + sweep.

### Tasks
- [ ] 1. Apply the story-file minors (one commit per coherent fix).
- [ ] 2. Six-gate DoD + sweep.

### Conventions checklist (standing)
(a) doc comments citing the dossier §/story; (b) empty-input/boundary tests where
applicable; (c) scoped staging; (d) match existing patterns; (e) tests drive the named
scenario (caplog assertions check the MESSAGE CONTENT, not just "something logged");
(f) contract changes rewrite covering tests; (g) no `.env`/secret values anywhere.
