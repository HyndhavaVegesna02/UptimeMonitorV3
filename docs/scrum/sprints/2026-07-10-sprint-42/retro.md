# Sprint 42 Retro — API-restructure "now" phase

- **Date:** 2026-07-10
- **Committed / accepted:** 7 / 7 pts. Three stories, no blocks, no hotfixes, no scope changes.

## What went well
- **The proposal-as-contract worked.** Stories cited an in-repo, adversarially-verified design doc (§6.2/§6.3 verbatim), so the contract TOML and target layout were unambiguous — the external agent reproduced them exactly. Pre-verifying the two contracts green *before* filing the story (STORY-074) removed all risk from Phase 1.
- **The two-Opus review caught a real regression the gates could not.** All six gates were green on the external agent's STORY-075, yet spec + quality review independently flagged the `ValueError → 422` catch-all (masking 500s) and the fake "registry." A green gate is not a correct design — the review layer earned its cost.
- **The fix stayed out of core.** Investigation during the fix loop found the clean fix was entirely in the api zone (hoist `SyntacticValidationError` + a syntactic UTC check), *better* than the pre-approved option that would have touched `core/domain` — because pydantic re-wraps validator exceptions, a domain-exception approach would not have propagated as itself. Verifying the mechanism before implementing avoided a wrong, core-touching fix.
- **Crash recovery held.** The fix-loop agent died on a session limit but had committed every step first (commit-after-green cadence); the orchestrator verified the clean tree and ran the gates the agent never reached, per the 2026-06-25 agreement — zero lost work.

## What was bumpy
- **STORY-073's flaky Docker-lifecycle gate struck twice this sprint** (canonical `pytest` false-red on `test_dev_db_cli.py`/`test_dev_db_fixture.py` under container contention). Handled per the 2026-07-06 agreement (proof + valid-signal + isolation), but it cost two extra verification runs. STORY-073 remains open and is now a recurring tax on every backend sprint's DoD gate.
- **The `next_story_id` counter was stale** (said 73 while STORY-073 already existed) — a bump was missed at STORY-073's filing in sprint 41. Fixed at this sprint's refinement.

## Amendments proposed
1. **Prioritize STORY-073 (flaky Docker-lifecycle gate) into the next sprint.** It has now degraded the DoD gate signal in sprints 41 and 42; the mechanical floor is meant to be trustworthy, and a gate that needs a manual contention-proof every run erodes that. (Motivated by: STORY-073 false-reds recurring across two consecutive backend sprints.) — *PO decision pending at next planning.*

## Working-agreement changes
None strictly required this sprint. The existing agreements (proposal-as-contract self-containment, model tiering, external-implementation exception, crash recovery, contention-proof) all applied cleanly. The 2026-07-10 external-implementation exception was a one-sprint measure and lapses now — the 2026-07-02 in-process implementer rule resumes for sprint 43 unless the PO renews it.

## Carry-forward
- STORY-077 (this sprint's 2 MINORs) filed → backlog.
- The `core/queries/` CQRS-lite move remains the recorded, trigger-gated future phase (proposal §8) — not yet triggered.
