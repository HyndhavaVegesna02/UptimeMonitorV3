# Sprint 6 — Plan

**Goal:** Zone 4 opens — the first two pure pipeline stages (collapse + streak) land as
provider-blind core logic, and the three carried 1-pt chores clear the small debt.

**Branch:** `sprint-6` · **Start tag:** `sprint-6-start` · **Started:** 2026-06-25
**Capacity:** ~6 (velocity 8/6/6/6/5/6, last-3 mean) · **Committed:** 6
(STORY-010 = 3, STORY-021/022/023 = 1 each)

**Order:** STORY-010 first (high-risk new Zone 4 work), then 021, 022, 023.
**Model assignment (PO rule, mandatory):** implementer → Sonnet; reviewers → Opus.

---

## STORY-010 — Core pipeline stages 1–2: collapse + streak (3 pts, full pipeline)

Spec: dossier §10 (stages 1–2 only). Split from the original 4-stage story (which was an 8);
stages 3–4 (anti-flap + decide) are STORY-024. PURE core in `core/services/` — no vendor / HTTP
/ SQL imports. Maintenance status is an INJECTED input (a predicate/flag), never a table query,
so the stages stay pure and fake-testable.

Canonical types: observations are `core/domain/signal.SignalObservation` (`health` ∈ up/down/
degraded). A new `Verdict` domain type (signal_key, cycle instant, `health`, maintenance marker)
lives in `core/domain/`. Read `backend/src/core/domain/signal.py` + the existing `core/services/
ingest_service.py` to match style (frozen Pydantic, docstrings citing dossier, injected deps).

TDD steps (commit after every green step; stage only files you touched — never `git add -A`):

- [x] 1. Add the `Verdict` domain type in `core/domain/` (frozen Pydantic v2) + export from
        `core/domain/__init__.py`. Failing test: construct a `Verdict`. `pytest` + `lint-imports`
        green. Commit. (513b2a9)
- [x] 2. Failing test: `collapse` maps a cycle's per-location observations → one `up` verdict when
        ALL are `up`. Implement minimal `collapse` in a new `core/services/pipeline.py`. Pass. Commit.
        (137977e)
- [x] 3. Failing tests: `collapse` → `down` when ALL `down`; → `degraded` for any mix / any non-up
        (down or degraded) alongside others (dossier §10). Implement. Commit. (fa80b63)
- [x] 4. Failing test: a cycle flagged under maintenance (injected predicate) is EXCLUDED from the
        verdict and short-circuits the pipeline (yields a maintenance marker, not up/down). Implement
        the maintenance check at collapse. Commit. (AC2) (2c22901)
- [x] 5. Failing test: `streak` counts consecutive same-health verdicts reading BACKWARD over a
        sequence; a health change terminates the count. Implement `streak`. Pass. Commit. (AC3)
        (5b444b3)
- [x] 6. Failing test: `streak` skips/excludes maintenance verdicts (counts over non-maintenance
        only, per §10). Implement. Commit. (AC2/AC3) (28f6f04)
- [x] 7. Self-review: the module is pure (no vendor/HTTP/SQL imports); `core/services` imports only
        `core`; tidy TDD residue. Commit. (12febf1)
- [x] 8. **DoD gate** (all four exit 0): `pytest`, `lint-imports` (core-independence +
        core-internal-layering stay green), `python scripts/check_fk_direction.py`,
        `alembic upgrade head` (DB-gated via `scripts/dev_db.py`). Forward blast radius: update
        `canonical-types-and-ports.md` (code_refs incl. `core/domain/` — you ADD the `Verdict` type →
        update its Facts + bump `verified_sha`). CLAUDE.md: only if a command/stack changed (none).
        Record evidence in your FINAL MESSAGE (orchestrator writes the board). Commit. (a513b11)

**Reviews (after step 8):** spec reviewer (Opus) against AC1–AC4 verbatim; then code-quality
reviewer (Opus). Working agreements: parallel-shape work shares its assembly; implementer never
writes `sprint-current.yaml`; tests use in-memory canonical fixtures (no live services).

---

## STORY-021 — Reject native_id in the DQL query builder (1 pt, light: implementer + DoD)

Spec: Sprint 4 review follow-up. In `backend/src/adapters/inbound/dynatrace/query.py`,
`build_dql_query` interpolates `native_id` unescaped (documented as trusted). REJECT (not escape):
validate `native_id` and raise a clear named error on a query-breaking char (e.g. `"`).

- [x] 1. Failing test: `build_dql_query(native_id='a"b', ...)` raises a clear named error; a
        well-formed `native_id` builds the same query as today (no regression). Implement the guard
        (a named `ValueError` subclass in the dynatrace package). Commit.
- [x] 2. DoD gate (all four exit 0). Forward blast radius: re-verify `dynatrace-adapter.md`
        (note the native_id guard) + bump `verified_sha`. Record evidence. Commit.

---

## STORY-022 — Fail loud on a mixed-signal batch (1 pt, light: implementer + DoD)

Spec: Sprint 5 review follow-up. In `backend/src/core/services/ingest_service.py`,
`ingest_observations` assumes one signal per batch (`signal_key = valid[0].signal_key`). Guard the
WHOLE batch UP FRONT (PO-approved): raise a named error (e.g. `MixedSignalBatchError`, in core)
if the batch spans >1 distinct `signal_key`, before any validation/persist/watermark work.

- [ ] 1. Failing test: a batch spanning >1 `signal_key` raises `MixedSignalBatchError` naming the
        keys, before any repo call; a single-signal batch behaves as today; an empty batch is still a
        clean no-op; existing STORY-009 ingest tests pass unchanged. Implement the up-front guard.
        Commit.
- [ ] 2. DoD gate (all four exit 0). Forward blast radius: re-verify `ingest-service-and-pull-loop.md`
        (the single-signal-batch assumption is now ENFORCED, not just documented) + bump `verified_sha`.
        Record evidence. Commit.

---

## STORY-023 — Clarify the double stop_event check (1 pt, light: implementer + DoD)

Spec: Sprint 5 review follow-up. Comment-ONLY. In `backend/src/composition/pull_loop.py:93`, add
a brief inline comment explaining why the post-cycle `stop_event.is_set()` check exists (skip the
final `sleep` on a mid-cycle stop). No behaviour change.

- [x] 1. Add the clarifying comment. Run `pytest` (existing pull-loop tests pass unchanged) +
        `lint-imports`. Commit. (9e5b329 — done directly by orchestrator: comment-only, no testable
        behaviour change; existing pull-loop tests are the regression guard.)
- [x] 2. DoD gate (all four exit 0): pytest 162, lint-imports 3 kept, FK 10/0, alembic no-op
        (consolidated DB gate at the final tree). `ingest-service-and-pull-loop.md` re-verified
        (comment-only, no Fact change) + verified_sha bumped to 9e5b329.
