# Sprint 71 — retro

**Default output is ZERO amendments (A15). This retro proposes ONE, at the SCRIPT rung, and it
removes a rule's side effect rather than adding a rule.**

## 1. Audit first: what the rules already in force did this sprint

| Rule | Fired? | Evidence |
| --- | --- | --- |
| **A9** (shown RED) | Yes, 6× | **And it was insufficient once, in a new way** — see §3. |
| **A12** (a guard's failure message is part of the guard) | Yes, 3× | Produced STORY-179's MAJOR 1 and both of STORY-213's MAJORs. The single most productive rule this sprint. |
| **A17** (reviewers race-immune by construction) | Yes, 3× of 4 | Three reviewers ran mutations in-process or in scratch clones. **The fourth breached it** — §3(a). |
| **A18** (wiki correction within the story) | Yes, 4× | Every story closed its own blast radius. Sweep CLEAN at every final commit. |
| **A19** (scratch work fatal-on-`cd`) | Yes, 5× | Landed last sprint. **Zero stray files in the repo root all sprint** — the incident it was written for did not recur. |
| **PROOF-LABEL rule** | Yes | Directly produced STORY-179's AC7 honest negative and STORY-213's 47-in-47. |
| **Plan verification** | Yes, decisively | Returned **RE-PLAN** against the orchestrator's own plan. |
| **STORY-219's citation ratchet** | Yes, 1× | Caught STORY-189's wiki note adding a bare-filename citation (188→189). |
| **`tools/evidence_check.py`** (sprint-70) | Yes, 1× | STORY-213 used `mutate` for its AC2 proof. The script rung being used in anger by a story that didn't build it. |
| **A15** (rules expire) | — | No rule cleared the six-sprint bar. **No deletions proposed.** |

**The rules are firing, and A12 is carrying more weight than anything else.**

## 2. The sprint's dominant finding — and why it gets no amendment

**Four of five stories produced a claim that read stronger than the observation behind it.**

- **STORY-222** — a tombstone's tier classification, with nine live-code citations still in it.
- **STORY-179** — a shown-RED that pinned a function the container port no longer came from.
- **STORY-213** — a mapping stated backwards, in a commit *titled* after correcting that mapping.
- **STORY-213 again** — a message branching on one field while printing the discriminating one
  directly above it.

This is the fifth consecutive sprint in this family. **Sprint 70 declined a prose amendment on the
grounds that `evidence_check.py` had landed the mechanism as code. That reasoning held up:** the
tool was used this sprint and worked. Every failure above was in **prose about a proof**, or in a
proof aimed at the wrong target — neither of which a mutation runner can catch.

**And the pipeline caught all four, unaided.** Two reviewers, independently, measuring rather than
reasoning. That is the system working as designed. A sixth prose restatement of "be careful with
proofs" is exactly the ratchet A15 exists to brake.

## 3. What went wrong that a rule does NOT cover

### (a) THE AMENDMENT — two agents reached for `git stash`, and the rules made them

**Occurrence 1 (STORY-222, implementer):** stashed the orchestrator's uncommitted
`.scrum/sprint-current.yaml` to obtain clean-tree gate evidence, restoring it after each run.

**Occurrence 2 (STORY-213, spec reviewer):** ran `git stash -u` then `git stash pop`; the tree was
clean so nothing was stashed, and the `pop` therefore hit a **pre-existing 2026-07-14 stash**,
leaving live merge-conflict markers in two `backend/src/` files.

Both disclosed. Neither caused lasting harm. **But this is not two lapses of judgement — it is one
mechanism squeezing two different agents into the same workaround.** Three rules interact:

1. `yt_gate.py` **refuses a dirty tree** (agreement 2026-06-29).
2. `.scrum/` is **orchestrator-owned**; subagents never write it.
3. The orchestrator edits `.scrum/sprint-current.yaml` **continuously**, including while agents run.

So an agent needing clean-tree gate evidence, on a tree the orchestrator has legitimately dirtied
with a file **no test reads**, has no sanctioned move. Telling it "don't stash" without removing the
squeeze just relocates the improvisation.

**A20 — the gate ignores orchestrator-owned paths when judging tree cleanliness.**

**Rung: SCRIPT** (`.claude/skills/yourteam/scripts/yt_gate.py`) — *not* a prohibition in an agent
definition, because the agents were not being careless; they were boxed in.

`tree_state()` excludes paths under `.scrum/` from the dirty check, reports them separately as an
informational line ("N orchestrator-owned path(s) modified, not gating"), and keeps refusing on any
other modified tracked file. `.scrum/` is read by no test and no gate command, so its state cannot
affect a gate result — which is exactly why excluding it is safe and why refusing on it was never
buying anything.

**Falsified by:** any future agent needing to modify, stash, or work around a tracked file to obtain
gate evidence.

*Why this rung:* the existing prohibitions are correct and stay. This removes the incentive to
violate them, which prose cannot do.

### (b) A shown-RED can pin the wrong thing — noted, not amended

STORY-179's AC1 test failed genuinely against old code and passed against new. It still left the
headline behaviour unpinned, because the mutation it was written against was not **the defect the
story exists to prevent**. The reviewer chose a different mutation — revert `start_container` — and
the suite stayed green.

**No amendment.** The quality reviewer found it unaided, by asking what the test actually
constrains; that is the reviewer definition working. Recording it because the *shape* is new —
previous occurrences in this family were proofs that were weak, not proofs aimed at the wrong
target — and because a future retro may want the second data point.

### (c) The orchestrator wrote three story files in filing shape and put them in a sprint

Plan verification returned **RE-PLAN** on this. STORY-179/173/192 were `points: null`,
`status: draft`, twelve open refinement questions between them, and I committed them as 9 of 11
points. Definition of Ready exists to prevent exactly that.

**No amendment: the mechanism caught it before lock, which is what it is for.** Recorded because the
failure was mine and the board should say so — the same disposition as sprint 70's AC7 miss.

## 4. Estimates

All five landed at their estimate. Four needed fix rounds, but every one was triggered by a defect
**found**, which is the process working rather than an estimate miss. Two estimates moved *during*
planning on measurement (STORY-173 2→3 on blast radius, STORY-222 2→3 on missing surfaces) and both
held. **No re-pricing proposed.**

## 5. Wiki

**13 map-tier articles, 4 reference** — the map tier **shrank by one** (STORY-222's tombstone
conversion), the first decrease since tiers were introduced. **Stale articles 3 → 2.**

Sweep, facts, links, integrity CLEAN at every story's final commit. **The citation advisory held
flat at 146 across 51 commits**, and the ratchet caught the single attempt to add to it.

**Owed:** two articles remain `status: stale` — `core-pipeline-and-availability.md` and
`frontend-zone.md`. Third sprint carrying them. STORY-223 must decide whether it rehabilitates them
or excludes stale articles from the enforcing lint; that decision separates a ~3 from a ~8.
