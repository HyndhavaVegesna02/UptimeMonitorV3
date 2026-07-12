# Spec Review Checklist — Uptime Monitor V3

> YourTeam v2, generated 2026-07-12 from `.scrum/working-agreements.md`. The agreements file
> remains authoritative until the PO approves `YOURTEAM_V2_MIGRATION_MAP.md`.

- [ ] **The test DRIVES the AC.** For every AC with a testable clause: the named test exercises the SCENARIO the AC names AND asserts the AC's OUTCOME. Read the test body and trace it to the AC's path — "an AC-named test exists and passes" is not verification (2026-06-29; the sprint-17 rigged test passed a name-matching review).
- [ ] **Run the trace tests.** Every MET verdict cites a test you actually ran, or concrete code evidence where no test applies.
- [ ] **Deletion check.** After the diff, every AC-named behavior still has a driving test; a net test deletion is justified in the implementer's report (genuine consolidation) or it is a finding (2026-06-29; sprint-21 deleted the `build_dql_query` tests to a green suite with zero coverage).
- [ ] **Live-path check.** An AC that cannot execute inside review is executed before sprint close OR carved out as an explicit tracked story — never deferred informally inside a "done" story (2026-06-29; sprint-21's deferred AC6 hid a live-path crash that cost all of sprint 22).
- [ ] **Plan-vs-AC conflicts are findings; the AC win.** Including AC that pre-declare wiki blast radius — the mechanical sweep is the sole decider (2026-07-03).
- [ ] **Scope additions flagged** (functionality no AC asked for) — the orchestrator decides; you only report.
- [ ] **PASS = every AC MET.** PARTIAL or NOT_MET on any AC is FAIL. There is no partial accept.
