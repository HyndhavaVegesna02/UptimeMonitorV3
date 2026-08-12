# Quality Review Checklist — Uptime Monitor V3

> YourTeam v2. Migration map PO-approved 2026-07-12 — this checklist is the BINDING home for
> these items; dates cite the original motivating agreement (full text in git history).
>
> **Amendments are audited for expiry at every retro** (2026-08-01 agreement). Motivating
> incidents live in the originating sprint's `retro.md` — this file carries the CHECK.

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
- [ ] If the story touches a wiki article's `code_refs`, run
      `python .claude/skills/yourteam/scripts/yt_wiki.py c3 --range <story-range>` and read the
      notes: a commit that changed a file an article CITES without touching the article left the
      catalogue false for that window. Notes, not verdicts — it cannot tell a completing commit
      from a TDD step, so judge each. (A18, sprint-68 retro: C3 failed 5x in one sprint as prose.)
- [ ] Error paths: everything that can realistically fail has a handled, tested failure path.
- [ ] YAGNI applies to your own suggestions — no abstractions for hypothetical futures; do not demand restructuring beyond the story's footprint.

- [ ] Any hardcoded external-service identifier in the diff (cloud managed-policy IDs,
      prefix-list IDs, ARNs, account/region-specific values, vendor entity IDs) carries
      live-derivation evidence — the CLI/API command and output that produced it — never
      accepted from memory or generation. Plausible-looking is not verified. (2026-07-17;
      sprint-50 STORY-089 — the CloudFront `CachePolicyId` labeled "CachingOptimized" was a
      fabricated ID that survived cfn-lint AND a quality APPROVE, and 404'd only at live
      stack create.)

## Evidence discipline — audit the artifact, not its output

- [ ] **Every evidence artifact in the diff must have been demonstrated FAILING.** The
      implementer-side rule is one item in `implementer.md`; this is the independent check that it
      actually happened. Verify each of the five mechanics that applies:
      - **Exit path, not printed values.** An artifact that computes the right numbers, PRINTS
        them, asserts nothing and exits 0 regardless is a REPORT, not a gate — and a reviewer
        reading correct numbers out of stdout cannot tell the difference. Require: explicit verdict,
        non-zero exit on failure, and recorded evidence it was fed deliberately bad input and failed.
        A polling step that times out must FAIL, not continue with a flag set.
      - **Reject any two-sided proof whose sides came back IDENTICAL.** That is inverted evidence,
        not weak evidence: the result is indistinguishable from "the thing under test does not
        matter", so the proof argues against a correct fix. Check the MECHANISM (import provenance,
        attribute names, fixture skips), not just the numbers.
      - **Mutate a computational deliverable yourself — do not infer pinning from reading.** A
        green, fully AC-traced suite can leave its story's central arithmetic unpinned. Hardcode or
        perturb the computation, run the story's tests, report which went RED. Zero RED is a
        finding, and it outranks anything found by reading. Restore and confirm the tree is clean.
      - **Import provenance where that is the mechanism:** confirm the proof actually called
        `tools/import_provenance.py::assert_import_root` per side (STORY-187) rather than asserting
        divergence without checking which tree ran. For every other mechanism the helper does not
        apply — read the test body and confirm the sides could actually have diverged.
      - **State set up through the production interface**, never a parallel hand-rolled one; a
        precondition that writes and re-reads its own wrong key passes vacuously.
      (Collapsed 2026-08-01 from A3, A4 and A7 — the reviewer-side halves of the six-amendment
      family described in `implementer.md`. Incidents in the sprint-63 and sprint-64 `retro.md`.
      This is exactly how STORY-176's critical was found, and nothing else in the pipeline would
      have found it.)

- [ ] **Recorded numbers and command output must be CURRENT, not merely real.** Re-run every
      command the story records and compare against the pasted output. A stale record — true when
      captured, false at the final commit — is the most common defect class in this repo's recent
      history, and it reads as verified evidence, which is what makes it dangerous. This includes
      counts the story's OWN edits invalidated: if a story edits the thing it measured, including
      its own report, the count must have been re-derived after that edit.
      (Merged 2026-08-01 from A12b and A13, which were two statements of one rule. Sprint-66's
      STORY-197 recorded "8 citation-sweep failures" — correct when written; the very paragraph
      explaining them quoted three by bare filename, which the sweep's regex then matched as three
      NEW citations. The true figure was 11.)

- [ ] **A guard's FAILURE MESSAGE is part of the guard, and it must not instruct an action its own
      check cannot justify.** Where the check is a PROXY for the real property, the message must say
      so and tell the reader to verify, never assert the conclusion outright. Read every message the
      guard can emit and ask: if someone does exactly what this says, without thinking, is the
      result correct? (2026-07-31, A12 — STORY-197's ZR-7 guard decided "this method paginates" by
      finding the STRING `LastEvaluatedKey` anywhere in it, and on a hit emitted "now loops on
      LastEvaluatedKey; remove this exemption, the fix has landed". A reviewer added a realistic
      warn-on-truncation stopgap that still read ONE page: the guard then instructed removal of the
      exemption covering a LIVE PRODUCTION DEFECT. Tests green, AC met, guard actively dangerous.)

- [ ] **A claim carrying a PROOF-LABEL must name its falsifier.** Where any artifact you are
      reviewing says "proven", "verified", "verified by mutation", "shown RED", "confirmed",
      "decisive", or "evidence read at re-verification", it must state — in one clause — the single
      observation that would falsify it. If no such observation can be named, the LABEL is wrong and
      the claim must be downgraded to what was actually measured. This applies to wiki Facts, board
      records, commit messages and diagnoses, not only to code. (2026-08-12, sprint-69 retro, RC-6 +
      RC-12. FOUR instances in one sprint across THREE authors, two of them the orchestrator's:
      QM-2's copied from-sha; QM-4's frontmatter mismatch; ZR-1's residue sentence, written wrong
      TWICE under a "verified by mutation" stamp; and a Docker diagnosis called "DECISIVE" that
      self-healed an hour later. Every one shares a shape — a chain of TRUE observations, a
      conclusion one step beyond them, and a label that stops the next reader checking. The reality
      gate forces this for GUARDS, because a mutation makes the claim executable; nothing forces it
      for diagnoses, status claims or Facts. RC-6 is the same defect from the other side: a spec
      re-review passed a FALSE residue as "consistent, no contradiction found" the same hour a
      quality reviewer falsified it by mutation. CONSISTENCY IS NOT TRUTH.)

- [ ] **A threshold assertion whose SLACK VARIES PER INPUT is not a floor for the inputs with
      slack.** When a guard compares two counts derived from the same record (references vs markers,
      rows vs expected ids, hits vs sites), a record with a surplus in one count MASKS a loss in the
      other — and the guard stays green while its coverage silently shrinks. Ask which input has the
      most slack and mutate THAT one. (2026-08-12, sprint-69 retro, RC-13 — tests-that-lie taxonomy.
      STORY-216 produced this defect TWICE at different scopes: a GLOBAL floor let any single row
      drop to zero coverage while green; the replacement PER-ROW floor was then absorbed on ZR-8,
      the one multi-reference cell, at 40% of the guard's coverage. The second evasion was verbatim
      the shape the guard's OWN test pinned — it fired on a single-reference row and was absorbed on
      the multi-reference one. A reviewer caught it both times.)
