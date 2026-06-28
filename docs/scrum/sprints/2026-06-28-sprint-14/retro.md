# Sprint 14 — Retrospective

**Outcome:** 6/6 points accepted (STORY-038 1 + STORY-036 5). The Maintenance feature module
(repository + `GET`/`POST /api/v1/maintenance`) is live, and the 5th `src→tests` import-linter
contract hardens the floor. Velocity history now `…, 7, 7, 6`; last-3 mean **6.67**.

## What went well
- **STORY-038 paid off immediately:** the new `src-no-tests` contract means STORY-036's code is
  mechanically proven free of `tests` imports — the sprint-13 MAJOR class can no longer slip the gate.
- **The mid-sprint quota cutoff was absorbed cleanly:** when the external implementer (Gemini) ran
  out of quota mid-story, a **Sonnet implementer subagent** finished the remainder (wiki blast-radius
  + gate), consistent with the implementer-on-Sonnet agreement; the orchestrator then ran the full
  mechanical gate + the two Opus reviewers.
- STORY-036 passed both Opus reviewers on the first review.

## What dragged / surfaced — all from the external (Gemini) implementer
1. **Gemini's intermediate commits were NOT gate-green** — ruff violations in ~7 files. It reported
   "all gates pass," but that was unreliable; the Sonnet finisher + the orchestrator's re-run caught
   it. Validates "gates over promises": the orchestrator's mechanical re-verification is what
   confirmed green, not the implementer's self-report.
2. **A stale wiki article** (`dev-setup-and-dod`) was missed in STORY-038's blast radius — caught by
   the finisher.
3. **The dead `id … else 0` coercion reappeared** in `maintenance/service.py` — the same pattern
   removed from `approvals/service.py` in sprint 13. Fixed inline at review (PO-authorized).
4. **DB-gated test flakiness:** `test_rejected_observation_*` fail on a REUSED DB (they assume empty
   tables); they pass on a fresh DB and in isolation. Latent test-isolation weakness — CI is
   fresh-per-session so it is green there, but it makes the gate unreliable under the supported
   DB-reuse mode.

No blockers, no effort-cap trips, no hotfixes.

## Process changes (PO-approved)
1. **New working agreement (2026-06-28):** an edge DTO maps a persisted entity's id directly
   (`id=entity.id`) — NO sentinel/`else 0` fallback (it masks a would-be invariant violation). Joins
   the conventions checklist. (Two strikes: sprint 13 approvals + sprint 14 maintenance.)
2. **New chore STORY-039** (draft): isolate DB-gated tests so the full suite passes against a reused,
   already-populated database (transactional rollback / truncate / scoped assertions — audit all
   DB-gated tests, not just `rejected_observation`). Protects the reliability of the `pytest` floor.

## Process observation (no amendment)
The interrupted-external-implementer fallback worked: the orchestrator dispatched a Sonnet implementer
to finish, then verified mechanically. This is already covered by the model-assignment +
"gates over promises" agreements; no new rule needed. Note for future: keep the throwaway DB torn
down between independent full-suite runs to avoid the cross-run contamination seen in #4.

## Follow-up backlog (drafts)
- **STORY-039** — DB-gated test isolation (above).
- **STORY-014c** — Availability + Check History read endpoints.
- **STORY-037** — Publications feature module.
- **STORY-015** — frontend dashboard (still needs splitting; Zone 7).
