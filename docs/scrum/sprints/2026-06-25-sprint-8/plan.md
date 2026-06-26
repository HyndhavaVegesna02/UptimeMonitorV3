# Sprint 8 — Plan

**Goal:** Zone 4's pure-logic surface closes — anti-flap (stage 3) and the per-component skew flag,
both pure and injectable, no config-loading or proposal-persistence dependency.

**Branch:** `sprint-8` · **Start tag:** `sprint-8-start` · **Started:** 2026-06-25
**Capacity:** 6 (velocity last-3 mean) · **Committed:** 6 (STORY-028 = 3, STORY-026 = 3)

**Order:** STORY-028 first (anti-flap, critical path), then STORY-026 (skew, Tier-2).
**Model assignment (PO rule, mandatory):** implementer → Sonnet; reviewers → Opus.

Working agreements in force this sprint: empty-input behavior tested (sprint-6); range/threshold
math tests a NON-aligned boundary case (sprint-7); every wiki Fact's cited file must be in the
article's `code_refs` (sprint-7); implementer never writes `sprint-current.yaml`; parallel-shape
shares its assembly; scoped staging (never `git add -A`).

---

## STORY-028 — Core pipeline stage 3: anti-flap (3 pts, full pipeline)

Spec: dossier §10 (stage 3). PURE core in `core/services/pipeline.py` (or a sibling). Consumes
`Streak` (STORY-010: `{health: Health, length: int}`). Thresholds are INJECTED as a value object
(config loading deferred). Read `backend/src/core/services/pipeline.py` (collapse/streak/Streak
style) + `backend/src/core/domain/status.py` (`ComponentStatus`) FIRST.

`anti_flap(streak, thresholds) -> <outcome>` per §10:
- FAILING (`Health.DOWN`) streak: `length >= major` → `major_outage`; `>= partial` →
  `partial_outage`; `>= degraded` → `degraded`; a single failure (length 1, below `degraded`) →
  **internal warning** (a distinct outcome, NEVER a published `ComponentStatus`).
- sustained `Health.DEGRADED` streak → `degraded`.
- PASSING (`Health.UP`) streak `length >= recovery` → `operational`.
- below all thresholds → **nothing** (no proposed status).
Default thresholds (major=5, partial=3, degraded=2, recovery=2) live in the INJECTED value object,
not hard-coded. Model a clear result type distinguishing {proposed ComponentStatus} | {internal
warning} | {nothing}.

TDD steps (commit after every green step; stage only files you touched — never `git add -A`):
- [x] 1. Define the thresholds value object (frozen) + the anti-flap result/outcome type (frozen).
        Failing test → construct them. `pytest` + `lint-imports` green. Commit.
- [x] 2. Failing tests: a FAILING streak → `major_outage`/`partial_outage`/`degraded` by length vs
        the injected thresholds (test AT each threshold and JUST BELOW — sprint-7 boundary agreement).
        Implement the failing-branch lookup. Commit. (AC1, AC4)
- [x] 3. Failing test: a single failure (length 1) → internal warning (distinct, never a published
        status). Implement. Commit. (AC2)
- [x] 4. Failing tests: a sustained `degraded` streak → `degraded`; a passing streak `>= recovery` →
        `operational`; a streak below all thresholds → nothing. Implement. Commit. (AC2)
- [x] 5. Failing test: degenerate inputs — length 0, and (per the empty-input agreement) a streak
        with no actionable length — have defined behavior (nothing/no crash). Commit. (AC4)
- [x] 6. Self-review: pure (no vendor/HTTP/SQL); imports only `src.core.*`; thresholds injected, not
        read. Tidy residue. Commit.
- [x] 7. **DoD gate** (all four exit 0): `pytest`, `lint-imports`, `python scripts/check_fk_direction.py`,
        `alembic upgrade head` (DB-gated via `scripts/dev_db.py`; no migration — pure logic). Forward
        blast radius: update `core-pipeline-and-availability.md` (code_refs incl. `pipeline.py` — add an
        anti-flap Facts subsection + bump `verified_sha`; if you put anti-flap in a NEW file, ADD that
        file to the article's `code_refs` per the sprint-7 agreement). Record evidence in your FINAL
        MESSAGE. Commit.

**Reviews:** spec (Opus) vs AC1–AC4; then quality (Opus).

---

## STORY-026 — Per-component skew flag (3 pts, full pipeline)

Spec: dossier §11 (skew) + Tier-2 T2.7. PURE core in `core/services/` (e.g. `availability.py` or a
sibling). The peer set + watermarks + intervals are INJECTED (no topology load, no DB). Result is a
SEPARATE per-component skew type (names the lagging signals), NOT a field on `AvailabilityResult`.

`skew(feeders) -> SkewResult` where each feeder carries `signal_key`, watermark, `interval`: a
feeder is SKEWED when it lags the most-recent peer watermark by MORE than its own `interval`.

TDD steps:
- [x] 1. Define the input feeder shape + the `SkewResult` type (frozen; names lagging signals).
        Failing test → construct. Commit.
- [x] 2. Failing tests: a feeder lagging the peer-max by more than its interval is flagged; one
        within its interval is not; lagging by EXACTLY its interval is NOT skewed (sprint-7 boundary
        agreement — at vs just-over). Implement. Commit. (AC1, AC4)
- [x] 3. Failing test: skew is a SEPARATE result, can diverge from completeness (full completeness +
        a skewed feeder, and vice versa — exercise both). Implement/assert. Commit. (AC2)
- [x] 4. Failing test: degenerate inputs (empty peer set; single-signal component → no peers → no
        skew; a feeder with no watermark yet) — defined, no crash (empty-input agreement). Commit. (AC4)
- [x] 5. Self-review: pure (injected peers/watermarks/intervals; no DB/vendor/HTTP); imports only
        `src.core.*`. Commit.
- [x] 6. **DoD gate** (all four exit 0, as above; no migration). Forward blast radius: update
        `core-pipeline-and-availability.md` (add a skew Facts subsection; ensure the file holding
        `skew` is in that article's `code_refs` — sprint-7 agreement; bump `verified_sha`). Record
        evidence in your FINAL MESSAGE. Commit.

**Reviews:** spec (Opus) vs AC1–AC4; then quality (Opus). Both stories: in-memory fixtures only, no
live services; implementer never writes `sprint-current.yaml`.
