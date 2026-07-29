# Sprint 63 retro — three false-passing proofs in one sprint, all caught, none by the same mechanism

**Process, not product.** 7 points committed, 7 delivered, 3/3 Done, no story blocked, no hotfix, no
scope change, no PO interrupt. The full 8-command gate was green on the final HEAD. So the interesting
material is not delivery — it is that **this sprint's verification machinery tried to lie three
separate times**, and the mechanisms were all different.

## What went well

- **Sizing held.** 7 points at the low edge of the ~9–11 baseline, per the standing pacing directive.
  The 3-pointer needed a full fix round plus three orchestrator-run proofs and still closed — at 10+
  points it would not have.
- **Splitting STORY-176 was right.** The verifier's 6-point re-estimate drove the split into part 2a
  (this sprint) and STORY-182 (the run). The guard shipped a sprint *ahead* of the run, which makes
  the ordering impossible to reshuffle.
- **Ordering the 2-pointer first paid off.** STORY-180 opened `tools/demo_engine/` so STORY-176
  inherited a bounded cache and a window that cannot diverge silently, instead of working around them.
- **The pre-lock verifier pass earned its cost again.** Six blocking findings, all folded in before
  the PO saw the plan — including the publish-guard **bypass** (component-id collision) that became
  AC3(c) and was demonstrably caught by the reality gate.

## The three false-passing proofs

| # | Proof | How it lied | Caught by |
|---|---|---|---|
| 1 | STORY-180's discrimination proof | Green on **both** sides — editable install resolved `src.*` to the main tree from inside the worktree, so the patched file never ran | Printing the imported module's `__file__` |
| 2 | STORY-176's own test suite | A mutant ignoring `interval_seconds` passed **all 30** new tests; the staggered test compared bucket sets built from arguments the test itself supplied | The quality reviewer running an actual mutation |
| 3 | My own reality-gate harness | Walked a `delegate` attribute (the layers store `_delegate`), so it reported a one-element chain on **both** sides — safe side green for the wrong reason, unsafe side falsely looking safe | Noticing the unsafe side *should* have differed |

**The pattern, and why it matters more than any single instance:** in #1 and #3 the failure was *both
sides agreeing*. A two-sided proof is supposed to derive its authority from the sides **differing**;
when both come back the same, that is not weak evidence, it is **inverted** evidence — #1 would have
been read as "this constant doesn't matter", i.e. it would have argued against a correct fix. The A1
refinement I landed mid-sprint covers import provenance only, so it would **not** have caught #3.

## Proposed amendments (enforcement-ladder routed)

**A3 — a two-sided proof must assert that the two sides DIFFER.** Not merely that each side matches
expectation. Proposed rung: **checklist** (`.scrum/checklists/implementer.md` + the reviewer
checklists), one line — *"a two-sided/discrimination proof records both outcomes AND asserts they
differ; identical outcomes on both sides is a FAILED proof, never a passed one, regardless of which
value appeared."* Prose can't be mechanized here because the harness is written fresh each time —
but the assertion itself can be, which is the point.

**A4 — the mutation test is the only proof that a test pins behaviour.** STORY-176's suite was green,
reviewed, and traced AC-to-test — and still didn't pin its headline behaviour. What found it was
running a mutant. Proposed rung: **checklist**, scoped narrowly to avoid becoming a tax — *"a story
whose headline deliverable is computational (arithmetic, spacing, ordering, thresholds) mutates the
computation once and records which tests go RED. Zero tests RED means the behaviour is unpinned,
even if coverage is complete."*

**A5 (smaller) — record what a reviewer did NOT see.** Three 529s killed the fix-round re-reviewer;
I substituted mechanical verification and recorded the gap, but nothing in the process *required* me
to. Proposed rung: **board schema** — a `review_debt` field on a story gate, so an unreviewed diff
cannot pass silently into review.

## Friction to raise, not amend

- **Upstream instability cost real time.** Two agents died on 529s (a fix implementer mid-run, the
  re-reviewer three times), and the **shell safety classifier went unavailable for a stretch** —
  only previously-approved commands would run, so both gates were unrunnable while the story sat
  verified-but-not-Done. Worth noting: an outage that permits *cached* commands is indistinguishable
  from a working shell until a command is refused. Mitigation that worked: write the harness while
  blocked, run it in one shot on recovery.
- **STORY-179** (`dynamo_local` ephemeral port not routable on Windows) — worked around with a
  fixed-port container for the third sprint running. It is now a standing tax on every gate.
- **STORY-178** (ANSI in the gate fragment) — **did not reproduce** this sprint even with
  `npm run build` in the full gate. Do not close it on one clean run; do record it.
- **A grep is a check, not a scope definition** — three independent demonstrations inside one story
  (STORY-181's AC6). Already reflected in the story's own History; no new rung needed, but it is the
  clearest example yet of an AC whose *mechanical* check was unachievable as written.

## Amendments from earlier sprints, checked

- **A1** (every reality gate needs a discrimination proof or two-sided note) — honoured by all three
  gates. Its mid-sprint refinement (a worktree proof must prove *which* code it ran) came out of
  failure #1 above.
- **A2** (behavioural wiki Facts cite their pinning test) — honoured, and it caught a real defect:
  STORY-176's wiki Fact claimed two monitors "share no cycle boundary", which was **false** (they
  share `end_time`) and cited a test that only asserted set inequality. Corrected with a labelled
  correction rather than a silent edit.
