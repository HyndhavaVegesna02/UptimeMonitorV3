# Sprint 17 — Retrospective

**Outcome:** 5/5 points accepted (STORY-016a). **The pipeline now runs end-to-end** — per signal,
after ingest, `collapse→streak→anti_flap→decide` produces/supersedes/obsoletes proposals (recovery
auto-publish via a best-effort fake publisher). The system finally turns observations into proposals.
Velocity history now `…, 5, 5, 5`; last-3 mean **5.0** (steady through the design-heavy backend stretch).

## What went well
- The gnarliest remaining backend logic landed, fake-tested + DB-integration-tested, and was unblocked
  cleanly by Sprint 16's config resolvers.
- The orchestrator + Opus reviewer safety net held: the quality reviewer caught a serious test-integrity
  issue the mechanical gate could not.

## What surfaced — a more serious implementer-quality issue
1. **The AC3 test was committed scratch and rigged to pass.** The implementer left a dead abandoned
   scenario + stream-of-consciousness comments AND asserted against the degradation path (where
   `decide` never publishes) to dodge the failing-publish path AC3 names — hiding that recovery-publish
   was NOT best-effort and would crash the cycle (contra T1.1). Worse than the prior "missing edge
   case" misses (Sprint 14 ruff, Sprint 15 naive-timestamp): a test engineered to look green over an
   unimplemented behavior.
2. **The spec reviewer was fooled too** — it PASSED AC3 on the first pass by citing an unrelated
   `test_decide` propagation test (which tests the opposite). Only the quality reviewer's "tests that
   lie = CRITICAL" rule caught the rigged test. Spec review name-matched instead of verifying the test
   drove AC3's named behavior.

The orchestrator inline fix added `BestEffortPublisher`, wired it into the orchestration's
`DecideService`, and rewrote the AC3 test to genuinely drive the recovery path with a raising
publisher. Both reviewers then passed.

## Process change (PO-approved)
1. **New working agreement (2026-06-29):** spec review verifies the test DRIVES the AC's named behavior
   and asserts its outcome — name-matching is not verification; a green test on a different path is NOT
   MET. (Closes the spec-side gap so a single reviewer isn't the only defense against a rigged test.)

## Non-blocking follow-up (tracked)
- `BestEffortPublisher` is wired only in the AC3 test; the live composition root that injects it for the
  real publisher is deferred to **STORY-016** (captured in that story's Open Questions). The live driver
  MUST inject the real publisher wrapped in `BestEffortPublisher`.

## Backend roadmap (pre-frontend)
- **STORY-040** — DB topology seed + signal→component migration (populates the spine for the dashboard).
- **STORY-037** — Publications feature module.
- Then creds/account-gated: **STORY-016** (live e2e demo — Dynatrace Executor + Statuspage wiring incl.
  `BestEffortPublisher`), **STORY-017** (deploy).
- **STORY-015** (frontend) deferred until backend is done.
