# Spec Review Checklist — <PROJECT>

> YourTeam v2 template (yourteam_version: 2.0.0).

- [ ] **The test DRIVES the AC.** For every AC with a testable clause: the named test exercises the SCENARIO the AC names AND asserts the AC's OUTCOME. Read the test body and trace it to the AC's path — "an AC-named test exists and passes" is not verification (a rigged test once passed a name-matching review).
- [ ] **Run the trace tests.** Every MET verdict cites a test you actually ran, or concrete code evidence where no test applies.
- [ ] **Deletion check.** After the diff, every AC-named behavior still has a driving test; a net test deletion is justified in the implementer's report or it is a finding.
- [ ] **Live-path check.** An AC that cannot execute inside review is executed before sprint close OR carved out as an explicit tracked story — never deferred informally (a deferred live AC once hid a crash that cost an entire sprint).
- [ ] **Plan-vs-AC conflicts are findings; the AC win.** AC never pre-declare wiki blast radius — the mechanical sweep decides.
- [ ] **Scope additions flagged**; the orchestrator decides.
- [ ] **PASS = every AC MET.** No partial accept.

## Project additions (this project)

<!-- Seeded empty at inception; grows via retro routing. -->
