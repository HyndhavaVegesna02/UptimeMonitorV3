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
      live-derivation evidence — the CLI/API command and output that produced it — never
      accepted from memory or generation. Plausible-looking is not verified. (2026-07-17;
      sprint-50 STORY-089 — the CloudFront `CachePolicyId` labeled "CachingOptimized" was a
      fabricated ID that survived cfn-lint AND a quality APPROVE, and 404'd only at live
      stack create; the sibling OriginRequestPolicyId was a real ID whose comment named a
      different policy.)

- [ ] **For a computational deliverable, MUTATE it -- do not infer pinning from reading.** A green,
      fully AC-traced suite can leave its story's central arithmetic unpinned. Hardcode or perturb
      the computation, run the story's tests, and report which went RED; zero RED is a finding, and
      it outranks anything found by reading. Restore and confirm the tree is clean. (2026-07-30,
      sprint-63 retro amendment A4 -- this is exactly how STORY-176's critical was found, and
      nothing else in the pipeline would have found it.)

- [ ] **Reject any two-sided proof whose sides came back IDENTICAL.** When a discrimination proof
      reports the same outcome on both sides, that is inverted evidence, not weak evidence -- the
      failure is indistinguishable from "the thing under test does not matter", so the proof argues
      against a correct fix. Check the mechanism (import provenance, attribute names, fixture
      skips), not just the numbers.

- [ ] **A reality-gate / discrimination artifact must be able to FAIL. Check its exit path, not its
      output.** An artifact that computes the right values and PRINTS them, while asserting nothing
      and exiting 0 regardless, is a REPORT, not a gate -- and a reviewer reading correct numbers out
      of its stdout cannot tell the difference. Confirm: an explicit verdict, a non-zero exit on
      failure, and evidence that it was fed deliberately bad input and failed. (2026-07-30, sprint-64
      retro amendment A7 -- STORY-182's positive-side harness asserted only AC1, printed AC3/AC4/AC5,
      and exited 0 unconditionally; a polling timeout set a flag and CONTINUED. The values happened to
      be correct, so it was reported as PASS. Its two sibling gates in the same story got this right
      (`sys.exit(0 if main() else 1)`), which is what made the inconsistency reviewable at all. The
      fix was closed by feeding all four new assertions bad evidence and confirming 13/13 raise --
      that is the expected practice, not an extra.) When the mechanism IS import provenance, confirm the proof
      actually called `tools/import_provenance.py::assert_import_root` (STORY-187) per side rather
      than asserting divergence without checking which tree ran; for every other mechanism (attribute
      names, fixture skips, etc.) the helper does not apply -- read the test body and confirm the
      sides could actually have diverged. (2026-07-30, sprint-63 retro amendment A3 -- three
      occurrences in one sprint, each via a DIFFERENT mechanism.)

- [ ] **A guard's FAILURE MESSAGE is part of the guard, and it must not instruct an action its own
      check cannot justify.** Where the check is a PROXY for the real property, the message must say
      so and tell the reader to verify, never assert the conclusion outright. Read every message the
      guard can emit and ask: if someone does exactly what this says, without thinking, is the
      result correct? (2026-07-31, sprint-66 retro amendment A12 -- STORY-197's ZR-7 guard decided
      "this method paginates" by finding the STRING `LastEvaluatedKey` anywhere in it, and on a hit
      emitted "now loops on LastEvaluatedKey; remove this exemption, the fix has landed". A reviewer
      added a realistic warn-on-truncation stopgap that still read ONE page: the guard then
      instructed the removal of the exemption covering a LIVE PRODUCTION DEFECT. Following that
      advice would have left the defect permanently unguarded. The tests were green, the AC were
      met, and the guard was actively dangerous -- the defect existed only in the message's wording
      and in the gap between the proxy and the property.)

- [ ] **A recorded COUNT must be re-derived after the last edit to the text that produces it.** A
      number measured mid-story and then quoted in prose goes stale silently, because nothing
      recomputes it and the reviewer's instinct is to trust a specific figure. If the story edits
      the thing being counted -- including its own report -- re-run the count and paste the fresh
      output. (2026-07-31, sprint-66 retro amendment A12b -- STORY-197 recorded "8 citation-sweep
      failures, all false" and the number was correct WHEN WRITTEN; the very paragraph explaining
      those failures quoted three of them by bare filename, which the sweep's own regex then matched
      as three NEW citations. The true figure was 11. Caught at spec review, under exactly the
      re-derivability rule the same sprint had been enforcing on everyone else.)


- [ ] **Recorded command output must be CURRENT, not merely real.** For every command the story
      records, re-run it and compare against the pasted output. A stale record -- true when captured,
      false at the final commit -- is the single most common defect class in this repo's recent
      history, and it reads as verified evidence, which is what makes it dangerous. Where a story's
      own edits changed the thing it measured, the count must have been re-derived AFTER that edit.
      (2026-07-31, sprint-66 retro amendment A13, PO-directed -- the author-side rule is in
      `implementer.md`; this is the check that it happened.)
