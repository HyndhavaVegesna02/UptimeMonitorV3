# Quality Review Checklist — <PROJECT>

> YourTeam v2 template (yourteam_version: 2.0.0).

## Tests-that-lie taxonomy — every member is CRITICAL

Read test BODIES, not names:

1. **Rigged path** — the test drives a different path than the behavior it names, dodging the failing one.
2. **Over-mock** — patching the `__init__`/internals of the thing under assembly; asserting only call counts (a wrong constructor kwarg once passed every gate while the app crashed on startup).
3. **Deleted coverage** — a contract change removed the covering test instead of rewriting it.
4. **Invented fixtures** — fixture scale/shape not derived from a real sample; tests then validate a shared wrong assumption.
5. **Dirty-tree green** — the result reproduces only with uncommitted changes.
6. **Asserting nothing** — vacuous/disabled assertions, testing the mock instead of behavior.

When you suspect over-mocking: construct the real object / hit the real entrypoint and compare.

## Severity

- **CRITICAL (blocks):** bugs, race conditions, broken error paths; security (injection, secrets in code, unsafe input handling); any taxonomy member above; module-scope side effects that can crash import/collection; debugging leftovers, commented-out code, dead code.
- **MAJOR (blocks):** violations of working agreements or the implementer checklist; duplication of existing logic (check — don't assume); inconsistency with established patterns; missing error handling on realistically failing paths; stale prose/doc references to files the diff moved or deleted.
- **MINOR (never blocks):** naming, readability, micro-structure.

## Standing checks

- [ ] Spot-check the implementer checklist items applicable to this diff.
- [ ] Duplication scan for any new helper/assembly logic.
- [ ] Error paths: everything that can realistically fail has a handled, tested failure path.
- [ ] YAGNI applies to your own suggestions — no abstractions for hypothetical futures.

## Project additions (this project)

<!-- Seeded empty at inception; grows via retro routing. -->
