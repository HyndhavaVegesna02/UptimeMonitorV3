# Spec Review Checklist — Uptime Monitor V3

> YourTeam v2. Migration map PO-approved 2026-07-12 — this checklist is the BINDING home for
> these items; dates cite the original motivating agreement (full text in git history).

- [ ] **The test DRIVES the AC.** For every AC with a testable clause: the named test exercises the SCENARIO the AC names AND asserts the AC's OUTCOME. Read the test body and trace it to the AC's path — "an AC-named test exists and passes" is not verification (2026-06-29; the sprint-17 rigged test passed a name-matching review).
- [ ] **Run the trace tests.** Every MET verdict cites a test you actually ran, or concrete code evidence where no test applies.
- [ ] **For any test that IS the story's primary evidence, ask "could this test fail?" before awarding MET.** Two checks, both cheap: (a) does every fixture the test constructs actually reach the code under test — a fake that is built, never wired up, then asserted on is asserting on a value the test itself supplied; (b) mentally (or actually) mutate the guarded behaviour to something plainly wrong and decide whether this test goes red. If you cannot say yes, the verdict is NOT_MET, not MET-with-a-note. (2026-07-30, sprint-65 retro amendment A9 — two defective tests shipped in one sprint and both survived the orchestrator's own review: one built a `watermark_repo` it never wired up and asserted it was still `None`; the other asserted `len(x) > 0` and `isinstance(rows, list)` on a function already annotated `-> list[dict]`, and only fell when the code was mutated to emit the exact regression it was supposed to guard.)
- [ ] **Deletion check.** After the diff, every AC-named behavior still has a driving test; a net test deletion is justified in the implementer's report (genuine consolidation) or it is a finding (2026-06-29; sprint-21 deleted the `build_dql_query` tests to a green suite with zero coverage).
- [ ] **Live-path check.** An AC that cannot execute inside review is executed before sprint close OR carved out as an explicit tracked story — never deferred informally inside a "done" story (2026-06-29; sprint-21's deferred AC6 hid a live-path crash that cost all of sprint 22).
- [ ] **Plan-vs-AC conflicts are findings; the AC win.** Including AC that pre-declare wiki blast radius — the mechanical sweep is the sole decider (2026-07-03).
- [ ] **Scope additions flagged** (functionality no AC asked for) — the orchestrator decides; you only report.
- [ ] **Failure-path AC clauses need failure-path tests.** For any AC clause naming a
      failure / negative / cleanup behavior — "teardown stays leak-free", "rejects X",
      "does not write", "raises on missing", "never fails on Y" — the driving test must
      exercise that FAILURE/negative path, not just the happy path. A happy-path-only test
      for a negative clause is a finding (FAIL), even if it passes (2026-07-15; sprint-48
      STORY-091 AC2 "teardown stays leak-free" — the leak lived on the blocker-start-fails
      branch, the delivered test only ran the happy path, quality review approved it, spec
      review caught it by reproducing the failure path).
- [ ] **Deletion-reason trace.** When the story's diff DELETES code (files/functions removed),
      confirm the deletion reason is recorded in the story-file History — the DoD standing rule
      requires it, and nothing mechanical checks it, so trace it explicitly. A code deletion with
      no recorded reason is a finding (2026-07-16; sprint-49 STORY-087 deleted the entire Postgres
      stack — nine adapters, the Alembic tree, dev_db/check_fk_direction — with no reasons recorded
      in the story until the review tail; the deletion itself was correct, the provenance was
      missing, which is how future sprints re-make removed mistakes).
- [ ] **PASS = every AC MET.** PARTIAL or NOT_MET on any AC is FAIL. There is no partial accept.
