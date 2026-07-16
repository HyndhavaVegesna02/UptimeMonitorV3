# Quality Review Checklist — Uptime Monitor V3

> YourTeam v2. Migration map PO-approved 2026-07-12 — this checklist is the BINDING home for
> these items; dates cite the original motivating agreement (full text in git history).

## Tests-that-lie taxonomy — every member is CRITICAL

Read test BODIES, not names. Six incidents, one family — each escape wore a new disguise:

1. **Rigged path** — the test drives a different path than the behavior it names, dodging the failing one (sprint 17).
2. **Over-mock** — patching the `__init__`/internals of the thing under assembly; asserting only call counts; a wrong constructor kwarg passes silently (sprint 20: all six gates green, app crashed on startup).
3. **Deleted coverage** — a contract change removed the covering test instead of rewriting it (sprint 21).
4. **Invented fixtures** — fixture scale/shape not derived from a real sample; tests validate the shared wrong assumption (sprint 32: percent vs fraction survived 146 green tests and two reviewers).
5. **Dirty-tree green** — the result reproduces only with uncommitted changes; committed HEAD would fail (sprint 19).
6. **Asserting nothing** — vacuous/disabled assertions, testing the mock instead of behavior.

When you suspect over-mocking: construct the real object / hit the real entrypoint and compare.

## Severity

- **CRITICAL (blocks):** bugs, race conditions, broken error paths; security (injection, secrets in code, unsafe input handling); any taxonomy member above; module-scope side effects that can crash import/collection (sprint-43 M1); debugging leftovers, commented-out code, dead code.
- **MAJOR (blocks):** violations of working agreements or `.scrum/checklists/implementer.md`; duplication of logic that exists elsewhere (check — don't assume); inconsistency with established codebase patterns; missing error handling on realistically failing paths; stale prose/doc references to files the diff moved or deleted (sprint-43 M2).
- **MINOR (never blocks):** naming, readability, micro-structure.

## Standing checks

- [ ] Spot-check the implementer checklist items applicable to this diff (validators on new frozen types, empty-input + non-aligned boundary tests, fake/adapter parity, five-file shape test, tz-aware validation, docstrings).
- [ ] Duplication scan against the existing codebase for any new helper/assembly logic.
- [ ] Error paths: everything that can realistically fail has a handled, tested failure path.
- [ ] YAGNI applies to your own suggestions — no abstractions for hypothetical futures; do not demand restructuring beyond the story's footprint.

- [ ] Any hardcoded external-service identifier in the diff (cloud managed-policy IDs,
      prefix-list IDs, ARNs, account/region-specific values, vendor entity IDs) carries
      live-derivation evidence � the CLI/API command and output that produced it � never
      accepted from memory or generation. Plausible-looking is not verified. (2026-07-17;
      sprint-50 STORY-089 � the CloudFront `CachePolicyId` labeled "CachingOptimized" was a
      fabricated ID that survived cfn-lint AND a quality APPROVE, and 404'd only at live
      stack create; the sibling OriginRequestPolicyId was a real ID whose comment named a
      different policy.)
