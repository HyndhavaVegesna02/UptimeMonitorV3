# Sprint 70 — retro

**Default output is ZERO amendments (A15). This retro proposes ONE, and proposes it at the agent-definition rung, not prose.**

## 1. Audit first: what the rules already in force did this sprint

A15 requires auditing what exists before adding to it. Every amendment in force was exercised this
sprint, and several were exercised *hard*:

| Rule | Fired? | Evidence |
| --- | --- | --- |
| **A9** (shown RED) | Yes, 5× | And it was *insufficient* three times — see §2. That is the finding, not a failure of A9. |
| **A17** (reviewers race-immune by construction) | Yes, 3× | All three quality reviewers ran mutations **in-process** via pytest plugins, modifying no repo file. The construction held without anyone policing it. |
| **A18** (wiki correction within the story) | Yes, 4× | Every story that shifted a cited line closed its own blast radius. Sweep CLEAN at every story's last commit. |
| **PROOF-LABEL rule** (sprint-69) | Yes, 3× | Directly produced the STORY-220 branch-collision finding and the STORY-219 docstring finding. |
| **Reviewer-definition limits not liftable by a brief** (sprint-69) | Yes, 1× | The STORY-212 spec reviewer refused to delete junk files it had itself created, and reported them instead. Exactly the intended behaviour. |
| **A15** (rules expire) | — | No rule cleared the six-sprint bar for deletion that was not already adjudicated in the sprint-68/69 retros. **No deletions proposed.** |

**Nothing here needs restating.** The rules are being read and they are firing.

## 2. The sprint's dominant finding — and why it needs NO amendment

**Every one of the five stories produced a proof that read stronger than it was.**

- **STORY-217** — the retired token grep returned 12, 13, and 19 for the same command on the same
  day. Six of the 19 were `__pycache__`. Neither agent was wrong; the *method* was.
- **STORY-220** — two shown-RED mutations, presented as two proofs, both fired the same assertion
  branch. The other branch had never fired.
- **STORY-218** — AC5's mutation went red for a reason unrelated to what it claimed (eager default-arg
  evaluation), and nothing pinned the story's own central invariant.
- **STORY-219** — the docstring stating the enforced scope carried a number the story's own edits had
  invalidated, and counted the passing subset while describing the checked set.
- **STORY-212** — the evidence checker itself reported `OK: mutation turned RED` on a run where **zero
  tests executed**.

Five occurrences, one shape: **a claim in prose outruns the observation behind it.**

**And the correct response is to propose nothing**, because the mechanism landed this sprint as code.
`tools/evidence_check.py` now mechanises the three non-bespoke checks, and the quality checklist now
says *"a pasted tail is the implementer's evidence, not yours."* Writing a sixth prose amendment
saying "be careful with proofs" is precisely the ratchet A15 exists to brake — and the six-amendment
family that stated this idea is why the brake was installed.

**The one thing worth noticing:** STORY-212's own CRITICAL is the argument for its existence. The tool
that catches false proofs shipped with a false proof inside it, and it took a reviewer *running the
tool* rather than reading it to find that. That belongs in the narrative, not in a new rule.

## 3. What went wrong that a rule does NOT cover

**(a) A silent `cd` failure wrote into the live repo.** The STORY-212 spec reviewer built a throwaway
git repo under the scratchpad; an early `cd` failed, and because `cd` failure does not abort a bash
script, the following lines executed against `C:\Hyn\uptime_monitor_v3` instead, leaving `target.py`
and `noop.patch` in the repo root. The reviewer could not clean up (its constraints forbid tree
modification) and disclosed instead, which is the right behaviour and the only reason it was visible.

This is not a judgment failure and no existing rule addresses it. **This is the one amendment
proposed — at the AGENT DEFINITION rung, not prose.**

**(b) The orchestrator's own check was the weaker one.** I reviewed AC7's checklist diff, confirmed
every mechanic was preserved, and passed it. The quality reviewer found that *independence itself* was
the casualty. No amendment: the reviewer caught it, which is the pipeline working. Recorded because
the failure was mine and the board should say so.

**(c) A commit was not green on the full suite.** STORY-219's `db76941` — a new literal in `tools/`
tripped the ZR-3 guard; the implementer had run only the targeted file, caught it on the full run,
and fixed it in the very next commit. **No amendment proposed:** the implementer disclosed it, the
final HEAD is green, and the next brief already carried "run the FULL suite before each commit" —
which STORY-212's implementer then did. The lesson propagated without a rule.

## 4. Proposed amendment — ONE, at the agent-definition rung

**A19 — scratch work is fatal-on-`cd`, and never defaults to the live tree.**

**Rung: AGENT DEFINITION** (`.claude/agents/yt-spec-reviewer.md`, `yt-quality-reviewer.md`,
`yt-implementer.md`) — *not* a checklist item and not a working agreement, because the agents are
where scratch repos get built and a brief must not be able to soften it.

Two clauses, both mechanical:
1. Any `cd` into a scratch directory is written `cd X || exit 1`. A silent `cd` failure redirects
   every following line at the repo root.
2. A tool whose `--repo-root`-style argument defaults to the working tree is given an explicit
   scratch path in scratch work. Never rely on the default.

**Falsified by:** any future stray file appearing in the repo root from agent scratch work.

*Why this rung:* the existing reviewer definitions already carry "never modify the working tree", and
this incident modified it *without* violating that rule — the write went through a shell redirect, not
a git command. The gap is in the same file, so the fix belongs in the same file.

## 5. Wiki

**14 map-tier articles, 3 reference — the map tier did NOT grow.** New knowledge routed to tests and
checklists instead: three new guard test modules and two checklist edits. That is routing row 1 doing
its job, and it is the first sprint since the tiers were introduced where the count held flat.

Sweep, facts, links, integrity: CLEAN at final HEAD.

**Owed:** three articles remain `status: stale` and unswept — `core-pipeline-and-availability.md`,
`deployment-and-infra.md`, `frontend-zone.md`. They were deliberately demoted at sprint-69 close
(`3303c6c`) as honestly unverified rather than left claiming currency. Rehabilitating them means
re-verifying every Fact and is filed for sprint-71, not quietly carried a third sprint.

## 6. Estimates

All five stories landed at their estimate. STORY-212 needed a fix round that its 3 points did not
account for — but the fix round was triggered by a defect *found*, which is the process working, not
an estimate miss. No re-pricing proposed.
