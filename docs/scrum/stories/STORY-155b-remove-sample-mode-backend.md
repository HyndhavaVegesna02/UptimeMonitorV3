---
id: STORY-155b
title: Remove sample_mode from the backend, and tombstone its article
type: chore
points: 5
status: ready
refined: 2026-08-15   # sprint-73 planning; split from STORY-155 (an 8) on measurement. PENDING PO lock.
sprint: null
---

## Depends on STORY-155a

**155a removes the consumer; this removes the producer.** Running them in the other order leaves the
SPA calling a 404. 155a must be `done` before this starts.

## Context

`sample_mode` is the on-demand outage simulator (STORY-048), **TEMPORARY by PO directive
2026-07-03**, superseded by the Grail demo engine. `CLAUDE.md` names STORY-155 as its removal.

### ⚠ "Inert" means the flag is off — NOT that the code is unwired

Measured at sprint-73 planning, and this is the one thing that makes this a 5 rather than a 3:
**`SampleModeIngest` is live in the pull loop.** `composition/run.py:101` wraps the real
`SignalIngestPort` in it on every build, and `composition/app.py:47` takes a `sample_mode_repo`
parameter. It is a **decorator over the ingest front door**, so removing it changes the wiring of
the live ingest path — behaviour-preserving only because the flag reads false. Treat it as surgery
on a live seam, not as deleting an unused module.

## The removal recipe exists — and it has drifted

`docs/scrum/wiki/sample-mode.md:226` holds a **complete mechanical deletion recipe** (STORY-048
AC7c). Follow it, but verify each line: at planning it named
`adapters/persistence/sample_mode_repository.py`, which **does not exist** — the file is
`dynamo_sample_mode_repository.py`. Its "all five files" claim for `api/v1/sample_mode/` is correct.

### A guard is already waiting for this story

`backend/tests/test_zr1_forbidden_list_completeness.py:35` and `:195-196` **already anticipate this
removal by name**, recording that deleting `sample_mode_repository.py` takes the correct count to
**8** and that AC1's set must move with it. Someone left this story a landing pad — the same
courtesy STORY-179 left STORY-173. Update it deliberately; do not let it go red and then "fix" it.

## Backend surface, measured at planning (27 files)

**Delete:** `composition/sample_mode.py` · `api/v1/sample_mode/` (5 files) ·
`core/ports/sample_mode_repository.py` · `adapters/persistence/dynamo_sample_mode_repository.py` ·
`tests/test_sample_mode_{repository_contract,endpoint,ingest,end_to_end}.py`

**Edit (seam removal — grep `STORY-048` for the marked lines):** `core/ports/__init__.py` ·
`api/dependencies.py` · `api/v1/__init__.py` · `composition/app.py` · `composition/run.py` ·
`tests/fakes.py` · `tests/test_dynamo_adapters.py` · `tests/test_run_live_loop.py` ·
`tests/test_zr1_forbidden_list_completeness.py` · `tests/demo_engine/test_scenario_coverage.py`

## Acceptance Criteria

- [ ] **AC1 (the live ingest path is provably unchanged)** — the pull loop ingests identically with
      `SampleModeIngest` removed. Prove it against behaviour, not by reading: a test over
      `build_live_loop`/`run_periodic` showing the same observations recorded before and after.
      **This is the AC that justifies the 5.** If it cannot be shown, split or block rather than
      shipping on the argument that the flag was false.
- [ ] **AC2 (no `sample_mode` remains in backend source or tests)** —
      `grep -ri "sample_mode" backend/` returns **zero** matches outside `__pycache__`.
      The `SampleModeRepository` port and its `__all__` entry are gone from `core/ports/__init__.py`.
- [ ] **AC3 (the ZR1 guard moves deliberately)** — `test_zr1_forbidden_list_completeness.py` is
      updated in the same commit as the deletion it accounts for, its count reaching the **8** that
      file already predicts. **Shown RED**: the guard must fail if the count is not updated, proving
      it was tracking the deletion rather than being edited to agree with it.
- [ ] **AC4 (the API surface loses the route cleanly)** — `GET`/`PUT /api/v1/sample-mode` no longer
      exists, the router registration is gone from `api/v1/__init__.py`, and **no other route
      changed**. A test asserts the remaining route table is otherwise identical.
- [ ] **AC5 (the DynamoDB `SAMPLE_MODE` row is addressed, not orphaned)** — the recipe
      (`sample-mode.md:311`) says the flag lives in the control table under the `SAMPLE_MODE`
      partition. Either delete it with a documented one-liner or record explicitly that a stale row
      in a dev table is harmless and why. **Do not leave it unmentioned.**
- [ ] **AC6 (the article is TOMBSTONED, not silently deleted)** — `docs/scrum/wiki/sample-mode.md`
      moves to `docs/scrum/wiki/archive/` as a `tier: reference` tombstone naming the sprint, this
      story, and **why the feature was removed** (superseded by the demo engine; PO directive
      2026-07-03) — the wiki protocol's rule that deletion adds knowledge. Its `code_refs` and Facts
      are dropped, since a `reference` article carries neither. **Every internal link to it is
      repointed or pruned**, verified by the link lint.
- [ ] **AC7 (nothing else claims sample_mode still exists)** — `CLAUDE.md`'s "Two things to know"
      caveat and any other live prose asserting the feature's existence are updated in the same
      commit. Historical records (story files, sprint history) are **left alone** — they describe
      the past correctly.
- [ ] **AC8 (gate, and the count is explained)** — the full 9-command gate exits 0 at the final
      HEAD. Four dedicated test files are deleted, so the backend count **will drop**: state the
      before/after and account for the delta exactly. An unexplained drop means something else went
      with them.

## Not in scope

Frontend removal (STORY-155a, which must land first). Repairing mojibake in other articles
(STORY-192 — though archiving this article removes ~110 of its 224 sequences, which should be
re-measured afterwards). Removing the demo engine or changing what replaced this feature.

## Open Questions

None.
