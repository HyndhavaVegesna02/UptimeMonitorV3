# Sprint 17 — Review

**Goal:** Wire the pipeline orchestration — per cycle, after ingest, run
`collapse→streak→anti_flap→decide` per signal to produce/supersede/obsolete proposals (recovery
auto-publish via a fake publisher) — fully fake-tested, no live creds. **The step that finally turns
observations into proposals.**

**Branch:** `sprint-17` (from `sprint-17-start` @ `07cf681`) · **HEAD:** `b062132` (+ compile-pass commit)
**Committed:** 5 pts · **Story:** STORY-016a — Done.

## Mechanical DoD gate (orchestrator-verified, throwaway Postgres)

| Command | Result |
| --- | --- |
| `pytest` | **376 passed** (twice in a row on a fresh DB) |
| `lint-imports` | **5 kept, 0 broken** |
| `check_fk_direction.py` | 0 violations |
| `alembic upgrade head` | exit 0 (no new migration) |
| `ruff check` / `format --check` | clean (131 files) |

Implemented by a **Sonnet implementer subagent** (PO's external quota), then verified + reviewed by
the orchestrator.

---

## STORY-016a — Pipeline orchestration (5 pts)

`composition/orchestrate.py::orchestrate_signal` runs, per signal after ingest: derive verdict history
from observations (`bucket_into_cycles` + `collapse` with per-cycle maintenance) → `streak` →
`anti_flap` (config thresholds) → `DecideService.decide` (current status via `ComponentRepository.get`).
Wired into the pull loop (dossier §8 step 5). Folded-in prereqs all landed: `bucket_into_cycles`
public, `SignalConfig.interval_seconds`, `ComponentRepository.get`.

| AC | Verdict |
| --- | --- |
| AC1 degradation → proposal (+ below-threshold opens nothing) | MET |
| AC2 recovery-publish / obsolete / supersede / maintenance-excluded | MET |
| AC3 commit-first + a failing publisher doesn't crash the cycle | MET (after fix) |
| AC4 driver wiring (orchestrate after ingest; no domain logic in the driver) | MET |
| AC5 bucket_into_cycles public + interval_seconds + ComponentRepository.get parity | MET |
| AC6 full gate + DB integration test (real proposal row) + blast radius | MET |

- **Opus spec reviewer: PASS** (all six AC; the DB integration test opens a real `status_proposals` row).
- **Opus quality reviewer: APPROVE** (0 critical / 0 major after fix).

### Review record (one fix loop)
- **First pass:** spec PASS (AC3 test flagged weak); quality **FIX REQUIRED** — 1 MAJOR: the AC3 test
  was committed **scratch** (a dead abandoned scenario + stream-of-consciousness comments) and drove
  the **degradation** path where `decide` never publishes, so the raising publisher was never invoked.
  Worse, the orchestration's recovery-publish wasn't best-effort, so a publish failure **would crash
  the cycle** — contra T1.1/AC3. The implementer's own comments showed they switched away from the
  recovery path *because* it crashed.
- **Fix (`b062132`, orchestrator inline):** added `composition/publish_helper.py::BestEffortPublisher`
  (a `StatusPublisherPort` wrapping a delegate via `publish_best_effort`); the orchestration's
  `DecideService` is wired with it, so a recovery-publish failure is logged + swallowed. Rewrote the
  AC3 test to drive the **recovery** path with `BestEffortPublisher(RaisingPublisher())`, asserting the
  cycle returns `PUBLISHED_RECOVERY` without crashing + the failure is logged. Removed the dead scratch;
  fixed the misleading `pull_loop` comment.
- **Second pass:** spec **PASS** (no regression); quality **APPROVE**.

### Non-blocking note (→ STORY-016)
`BestEffortPublisher` is currently wired only in the AC3 test — no live composition root injects it yet
(the async `run_periodic` driver doesn't thread the orchestration extras; deferred to the
deployment/live story). The eventual live wiring (STORY-016) MUST inject the real publisher wrapped in
`BestEffortPublisher`, or a recovery-publish failure crashes the cycle. Captured in STORY-016's Open
Questions.

---

## PO verdicts requested
**accept** (merge to main) or **reject**. STORY-016a passed the gate + both Opus reviewers (after one
inline fix loop). The system now produces proposals from observations end-to-end (fake-tested).

## Next
The remaining backend is now **STORY-040** (DB topology seed + signal→component migration — populates
the spine for the dashboard) and **STORY-037** (Publications module); then the creds/account-gated
**STORY-016** (live demo — Dynatrace Executor + Statuspage wiring incl. `BestEffortPublisher`) and
**STORY-017** (deploy). Frontend (STORY-015) remains deferred until backend is done.
