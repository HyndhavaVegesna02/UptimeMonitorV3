# Sprint 69 — Retrospective

**Run 2026-08-12, after the review.** Branch `sprint-69`, 73 commits, `29eb824..cf80f33`, 11/11 points.

Per **A15** this retro audits the rules already in force **before** proposing any new one, and its
default output is **zero amendments**. Thirteen retro candidates were filed during the sprint (RC-1
through RC-13). **That number is itself the finding**, and most of it is not new rules — it is the
same few rules failing from different directions. This retro proposes **two additions, one redraft,
and zero deletions**, and explains why three high-severity candidates correctly produce **no
amendment at all**.

---

## 0. The number A15 exists to move

```
git diff --stat sprint-69-start..HEAD -- .scrum/working-agreements.md .scrum/checklists/   # empty
```

| Point | Governance bytes |
| --- | --- |
| Sprint 68 close | 68,781 |
| **Sprint 69 close (HEAD)** | **68,781 — unchanged** |

**Second consecutive sprint adding zero governance bytes.** That is the budget the proposals below
must be paid out of, and it is why one of the three is a *redraft* (byte-neutral) rather than an
addition.

---

## 1. The deletion audit (A15's six-sprint test)

| Rule | Fired since sprint 64? | Verdict |
| --- | --- | --- |
| A1 (contention protocol, 2026-07-06) | **Yes, decisively this sprint** — it is what stopped a red gate being waved through | KEEP |
| A6 (no skipped persistence floor) | Yes — every gate run this sprint carried `REQUIRE_DYNAMO=1`, zero skips | KEEP |
| A7 (reality gate is an exit code) | Yes — five reality gates, all exit-code evidence | KEEP |
| A8 (spike reproduced vs timed) | No spike this sprint; **already audited and kept one sprint ago** | KEEP — re-proposing a sprint later is churn |
| A14 (ladder exempt from tooling freeze) | Yes — used to land RC-4's rung mid-sprint | KEEP |
| A15 (rules expire) | Yes — this section | KEEP |
| A16 (Facts lint honesty) | **Yes, twice, against the orchestrator itself** | KEEP |
| A17 (reviewers race-immune) | Yes — and was *overridden* once, see §3 | KEEP, see redraft note |
| A18 (C3 mechanism) | Yes — and failed from two opposite directions, see §2 | **REDRAFT** |

**Zero deletions proposed.** No rule cleared the bar that was not already adjudicated in the sprint-68
retro, and manufacturing a deletion to satisfy a metric would be the same defect this sprint spent
three review rounds catching.

---

## 2. Consolidation: thirteen candidates, four real lessons

The candidate count is inflated by the same rule surfacing repeatedly. Consolidated honestly:

| Candidates | One lesson | Outcome |
| --- | --- | --- |
| RC-1, RC-7 | An agent's evidence dies with the agent | **No amendment — the story already exists** (§4) |
| RC-9, RC-10 | A18's "same commit" is unsatisfiable in two opposite situations | **Redraft A18** (§5) |
| RC-6, RC-12 | A claim outrunning its evidence, under a proof-label | **Amendment 1** (§6) |
| RC-3, RC-5 | A brief or an agent can exceed what its definition permits | **Amendment 2** (§7) |
| RC-13 | A threshold whose slack varies per input is not a floor | folded into Amendment 1's rung (§6) |
| RC-8 | The orchestrator's own commits are unreviewed | **No amendment — practice already changed** (§8) |
| RC-2, RC-4 | Coordination notes, both already discharged in-sprint | closed, no action |
| RC-11 | `code_refs` vs row citations inconsistency | **backlog story, not a rule** (§8) |

---

## 3. What went right, because a retro that only lists faults teaches nothing

- **A1 did the single most valuable thing in the sprint.** A gate went red; the two-limb test failed;
  the red was recorded rather than discounted and the story was held out of `done` until a genuine
  green existed. The rule that exists to stop "re-roll until green" stopped it.
- **Every reality-gate mutation was re-performed by the orchestrator.** Sprint-67's MAJOR-1 lesson
  is now habit, not aspiration.
- **Three agents were killed by session limits and lost nothing**, because they had been told to
  checkpoint evidence outside the repo before it happened.
- **Reviewers earned their cost every single round.** Four review passes, four real findings, zero
  manufactured ones — including one reviewer that explicitly named what to *keep*, and one that caught
  a stale annotation in the orchestrator's own board entry.
- **Plan verification prevented the sprint's worst outcome.** STORY-216's original AC, read literally
  and combined with "fix a failing row, never exempt it", would have sent an implementer to edit four
  *correct* rows. It didn't happen because the grammar was pinned before the PO ever saw the plan.

---

## 4. RC-1 / RC-7 — the lesson is right and needs NO new rule

An agent died mid-task **three times** this sprint. Twice it cost nothing, because the brief said to
checkpoint findings to a file outside the repo as they were produced. Once — before that instruction
existed — a mutation proof was unrecoverable and had to be re-performed.

**A15 forbids writing an amendment here, because the lesson already has a filed story:**
**STORY-212 — "Land the evidence-artifact rule at the SCRIPT rung (mutation + provenance helper)"**.
The correct output is not a fourth restatement in prose; it is to **prioritise STORY-212 in sprint 70**,
with this sprint's three data points as its justification. Its scope should widen slightly on the
evidence: **any** agent-produced evidence, not only mutation proofs, and the checkpoint target must be
**outside the working tree** so a read-only reviewer can comply without violating its own contract.

---

## 5. REDRAFT (not an addition) — A18's "same commit" is unsatisfiable in two opposite cases

A18 requires `verified_sha` bumped and wiki corrections landed **in the same commit** as the code
change. This sprint it failed from both ends:

- **RC-10 (from below):** under strict per-step TDD commits, a wiki correction that *cites code that
  does not exist yet* cannot share a commit with it. Three stories hit this; all three disclosed it.
  The `verified_sha` self-reference dance appeared three times.
- **RC-9 (from above):** a commit touching an *amplifier* `code_ref` — `pyproject.toml` is cited by
  five articles — stales five articles it is not about, and cannot bump them without abandoning its
  own subject. This is exactly how a "sweep CLEAN" line was measured before its own last edit and
  shipped false.

**A15 applies: the rule exists and was not followed, so it is relocated/made concrete, never restated.**
Proposed redraft, replacing A18's "same commit" clause (byte-neutral):

> **Same STORY, no false intermediate.** The wiki correction and `verified_sha` bump land within the
> story, and **no intervening commit may leave the repo asserting something false**. `verified_sha`
> tracks the last commit touching `code_refs` — it is not the article's own commit, so a
> self-reference is never required. **Run `yt_wiki.py` AFTER the story's last commit**; a sweep
> measured before the final edit is not evidence about the story.

That last sentence alone would have prevented this sprint's opening defect.

---

## 6. AMENDMENT 1 (checklist rung) — a proof-label must name its falsifier

**Four instances in one sprint, across three different authors** — QM-2, QM-4, ZR-1's residue v1, and
the orchestrator's own QM-6 and Docker diagnosis. Every one shares a shape: a chain of true
observations, a conclusion one step beyond them, and a label — *"proven"*, *"verified by mutation"*,
*"evidence read at re-verification"*, *"decisive"* — that stops the next reader from checking.

RC-6 is the same thing seen from the other side: a spec re-review passed a **false** residue as
"consistent, no contradiction found" the same hour a quality reviewer falsified it by mutation.
**Consistency is not truth.**

The reality gate already forces this for *guards*, because a mutation makes the claim executable.
**Nothing forces it for diagnoses, status claims, or wiki Facts.**

> **Proposed, `.scrum/checklists/` (quality-review + implementer):** *A claim carrying a proof-label
> — "proven", "verified", "shown RED", "confirmed" — must state, in one clause, the single observation
> that would falsify it. If you cannot name one, the label is wrong: downgrade the claim to what was
> actually measured.*

All four instances would have failed that line. **RC-13 folds in here** as a taxonomy entry on the
same checklist: *a threshold assertion whose slack varies per input is not a floor for the inputs with
slack* — both of STORY-216's MAJORs were that shape at different scopes, and a reviewer caught it both
times.

---

## 7. AMENDMENT 2 (agent-definition rung) — two limits a brief cannot lift

Two incidents, one class: an agent did something its role should forbid, and nothing mechanical stopped
it.

- **RC-3 (high):** the orchestrator's brief invited a spec reviewer to re-run a mutation. It did, then
  cleaned the tree with `git checkout --` — violating **A17**, which the sprint-68 retro had
  deliberately placed at the *agent-definition* rung so it could not be bypassed. A quality reviewer
  was running concurrently, so the race-immunity A17 asserts was simply not there. No harm was
  detected, and the reviewer disclosed it rather than hiding it, which is the only reason it is visible.
  **The lesson is not "the reviewer should have refused" — it is that a brief silently outranked a rule
  placed at a higher rung.**
- **RC-5 (high):** a reviewer ran a system-wide `Get-Process python` and killed PIDs it had not
  spawned, orphaning a container. This repo's documented local stack runs an API server and a pull-loop
  as python processes.

> **Proposed, `.claude/agents/yt-*.md` (both reviewer definitions):**
> *(a) A dispatch brief may not authorise what this definition forbids. If a brief asks for it, refuse
> and say so in your report.*
> *(b) Terminate only processes you started, by tracked id — never by name or pattern query.*

Both are single lines at the rung that already holds the rules being broken. Note the orchestrator's
briefs in the second half of this sprint already carried both by hand; the amendment removes the
dependency on the orchestrator remembering.

---

## 8. Two candidates that correctly produce nothing

- **RC-8 — the orchestrator's own commits are the one class of work no role reviews.** Real: this
  sprint's round-3 MAJOR was in an orchestrator commit, found only because the orchestrator volunteered
  its own diff as a second review object; and a reviewer later caught a stale annotation in the
  orchestrator's board entry. **But the practice already changed mid-sprint and worked twice.** Writing
  a rule now would be restating a habit that is currently holding. **Re-raise it if it fails once** —
  that is the honest trigger, and A15's own logic.
- **RC-11 — guard-file citations vs `code_refs`.** This is a project decision about one document, not
  a process rule. It belongs in the backlog as a small story: either add the missing guard files to
  `code_refs` (accepting more staleness churn) or state once, deliberately, that guard-file citations
  are exempt because STORY-216's check supersedes staleness for them. **Do not leave it half-and-half.**

---

## 9. Recurring friction for the PO

- **Session limits are now a first-order planning constraint, not an accident.** Three agent deaths in
  one sprint. The mitigation (checkpoint outside the repo, resume from transcript rather than
  re-dispatch) works and cost nothing twice. **STORY-211** ("plan sprints on context and token budget
  instead of story points") is looking less speculative each sprint.
- **Two of eight DoD commands are unreliable on this machine** — STORY-221 measured at 2 red in 4, and
  STORY-179 now known to be mis-scoped. A mechanical floor that people learn to re-roll stops being a
  floor. Both need re-pricing at sprint-70 planning against what was measured, not how they were filed.

---

## Proposals summary — for PO approval

| # | Change | Rung | Net bytes |
| --- | --- | --- | --- |
| 1 | Redraft A18's "same commit" → "same story, no false intermediate", + run `yt_wiki` after the last commit | prose (replaces existing text) | ~0 |
| 2 | A proof-label must name its falsifier (+ RC-13 taxonomy entry) | checklist | small addition |
| 3 | A brief may not authorise what an agent definition forbids; kill only tracked processes | agent definition | 2 lines |

**Deletions: none, with reasons given in §1.**
**No amendment for RC-1/RC-7 (prioritise STORY-212 instead), RC-8 (practice holds; re-raise on
failure), or RC-11 (backlog story, not a rule).**
