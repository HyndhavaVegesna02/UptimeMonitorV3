# Sprint 73 — Retro

**13/13 points, 3/3 accepted. Highest delivery in this project's history** (prior best 11, prior
sprint 8). Gate 9/9 at `b55cc74`. 63 commits. Zero blocked stories.

**Proposed amendments: ZERO.** A15's default, and this sprint genuinely earns it — every incident
below was *caught by a mechanism that already exists*, which is the outcome the rules were built for.

---

## A15 §1 — the audit of rules in force, performed BEFORE proposing anything

Sprint 72 owed a **checklist walk-through** that was not done (only A6–A20 were audited). Discharged
here.

### The agreements

| Rule | Fired this sprint? | Verdict |
| --- | --- | --- |
| **A6** — a green pytest may not hide a skipped floor | **Yes, 5×** — every gate run recorded `0 skipped` explicitly | Keep |
| **A7** — a reality gate is an exit code, not a paragraph | **Yes, 3×** — all three reality gates were executed commands with output, not prose | Keep |
| **A8** — a spike separates REPRODUCED from TIMED | No spikes this sprint | Keep (dormant, not expired — 3 sprints) |
| **A14** — the ladder is exempt from the tooling freeze | Not invoked | Keep |
| **A15** — rules expire; audit before adding | **Firing now** | Keep |
| **A16** — the Facts lint may not report CLEAN about unchecked text | **Yes** — the `status: stale` demotion is exactly this: quarantine rather than a false CLEAN | Keep |
| **A17** — reviewers are race-immune by construction | **Yes, 3×** — three concurrent spec+quality pairs, zero interference; `node_modules` survived all three at 216 | Keep |
| **A18** — forward wiki blast radius, re-verified in-story | **Yes, heavily** — it is the rule that priced STORY-155b at 7 instead of 5, and 14 articles were touched under it | Keep — highest-value rule in force |
| **A21** — the Window Check is a hook | **Yes** — and see below | Keep |

**No rule is a deletion candidate.** The oldest (A6) fired five times this sprint. A8 has been
dormant three sprints — short of A15's six-sprint threshold, and it costs one table row.

### The checklists (the half sprint 72 owed)

Walked `implementer`, `spec-review`, `quality-review`, `plan-verification`. Every item fired at
least once this sprint except the external-delivery clauses in `plan-verification` (this was an
`in-process` sprint, so they are correctly inert, not stale). The taxonomy items in
`quality-review` earned their place three times over — see below. **No checklist item proposed for
deletion.**

---

## What actually happened, and why none of it needs a new rule

### 1. An implementer died mid-story and it cost one verification, not one story

STORY-147's first implementer hit the session limit having made 14 commits, with one uncommitted
edit in flight. Recovery cost: reading a diff and verifying one claim. **The commit-after-every-
green-step cadence is what made that true**, and it is already an implementer-definition rule.

Its dying words reported a real finding — an abbreviated citation path — which I verified against
the repo convention before preserving rather than taking on trust. **The right instinct was already
mechanised; nothing to add.**

### 2. The parity guard's first real catch was the ORCHESTRATOR

I marked STORY-147 `done` on the board and left `backlog.yaml` at `ready`. STORY-155a's gate run
went red on it. The implementer **refused to touch `.scrum/` and reported it instead** — the exact
behaviour whose absence broke STORY-224's AC1 last sprint.

This is the most encouraging event of the sprint: a guard that landed at the *script* rung caught
drift in the one participant no prose rule can discipline, and the ownership boundary held under
pressure. **Adding a rule here would be adding prose to something already working in code.**

### 3. Every story needed exactly one fix round, each for a MAJOR the author missed

- **147**: a staleness guard carrying a stale number *and* a false "cannot go stale" proof-label
- **155a**: dead CSS the removal itself created, one rule of which the author's own list omitted
- **155b**: a ticked AC checkbox with no deliverable, plus a stale claim in the doc `CLAUDE.md`
  names as authority — whose sibling that same story had fixed

Three stories, three MAJORs, **zero found by the implementer's own self-report**. Concurrent
spec+quality is not ceremony; it is the thing catching these. Already the rule for 3+ point stories.

### 4. AC1's cheap fake was named in advance and refused

STORY-155b's AC1 told the implementer exactly how to fake it. It didn't. Quality then
**reconstructed the deleted module from the pre-removal commit** and confirmed the captured literal
field-for-field; spec independently mutated the health mapping and watched it red.

That is a story file doing the work a rule cannot: naming the specific lie available in *this*
story. **The lesson is about story-writing, and it is already how these stories are written.**

### 5. Two of my own commands were wrong in the same way

- `grep -E "^OK|FAILED"` used as a gate: `grep` exits **0 when it finds** the pattern, so matching
  `FAILED` *satisfied* the `&&` chain and let a commit through on a red self-test.
- Earlier in the sprint, reading `$?` after a pipe captured the wrong process.

Same root cause: **treating a command's output as its exit status.** Tempting to legislate — and I
am not proposing it, because the ladder has no rung for "the orchestrator wrote a sloppy shell
one-liner" short of prose, and A15 §3 is explicit that adding prose to fix a prose-adherence failure
is the anti-pattern. It goes in the record so a second occurrence is a data point, not a surprise.
**Recorded, unlegislated.** *(Same disposition as sprint 72's `node_modules` incident, which did NOT
recur this sprint across three concurrent review windows.)*

### 6. The pause was the sprint's most important decision

At 82% — still inside "dispatch freely" — I stopped rather than start a 7-point story. The
alternative was a guaranteed mid-story death and a half-removed feature, which is exactly what the
sprint's own goal forbids. **A21's hook made the number visible; the atomicity rule on the board
made the consequence explicit.** Both mechanisms existed. They worked.

### 7. Estimation was right where it has been wrong before

STORY-155b was re-priced 5 → 7 at pre-lock verification *because* A18's wiki cost was being applied
to the small story and withheld from the big one. It landed at 7 with 29 commits and nine articles.
**The re-pricing was correct**, and the discipline that produced it — applying the same rule to
both stories — is the thing to keep.

---

## Carried forward

1. **A15's checklist walk-through: DISCHARGED** (owed from sprint 72).
2. **Two orchestrator shell errors, unlegislated.** A third is a pattern.
3. **`node_modules` survived three concurrent review windows** — sprint 72's incident did not
   recur, so it stays a single incident and no `.bin/vitest` preflight is proposed.
4. **I told the PO "11 carried minors" at review; the true count was 14** (5+3+6). Corrected before
   filing, so the filing scope was right — but the review document was wrong when the PO read it.
   Arithmetic in a summary is a claim like any other.

## Amendments proposed to the PO

**None.**

Every incident this sprint was caught by an existing mechanism, and the two that were not
(my shell errors) have no rung available above prose. A15 §3: *a repeat incident under an existing
rule means that rule isn't being read* — but there was no repeat under an existing rule this sprint.
The ratchet stays where it is.
