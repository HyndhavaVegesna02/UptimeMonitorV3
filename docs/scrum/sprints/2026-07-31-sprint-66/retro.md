# Sprint 66 — Retro

**Date:** 2026-07-31 · PO accepted the sprint ("i accept"), velocity **11/11**.
Amendments **A11** and **A12** landed at their rungs under the PO's standing autonomy directive.

Process, not product. The product verdict is in `review.md`.

## Velocity

| Sprint | 62 | 63 | 64 | 65 | 66 |
| --- | --- | --- | --- | --- | --- |
| Accepted | 9 | 7 | 8 | 13 | **11** |

11 was inside the stated ~9–11 baseline, and **it still needed four fix rounds — one per story.**
Sprint 65 ran 13 and needed three. So the fix-round cost is not driven by sprint size; it is driven
by story *kind*. An audit sprint's deliverable is prose and judgement, and prose fails review in ways
code does not: a wrong line number, an overstated verdict, a count that no longer reproduces. None of
those has a compiler.

## The finding that dominates everything else

**The audit's value came overwhelmingly from adversarially reviewing the audit, not from the audit.**

- **STORY-195** first reported zero violations across 58 files with 57 `CLEAN` verdicts. Its quality
  reviewer independently re-read ~46 of those same files and found **three MAJORs inside files
  already verdicted `CLEAN`** — including a live production defect that does not raise
  (`is_under_maintenance` silently disabling maintenance suppression past a 1 MB page).
- **STORY-196** applied that lesson, annotated every file read-vs-grep, and **passed spec review on
  the first pass** — and its quality reviewer still found four MAJORs, including
  `composition/seed_dynamo.py` being an adapter in composition's clothing.
- **STORY-197** had no reviewer at all until the PO asked for one. That pass then found a guard that
  gave *actively harmful advice* (below).

Both reviewers found real defects in **every** story this sprint, including several I had personally
accepted. That is the third sprint running. **The two-reviewer ceremony is not overhead; on this
evidence it is where most of the defect-finding actually happens.** Any future proposal to trim it to
save budget should be refused on the strength of this record.

The corollary is uncomfortable and worth stating plainly: an audit that is not itself audited is
close to worthless. A single pass produces a confident document, and a confident document about
"zero violations" is indistinguishable from a thorough one until someone re-reads the same files.

## What cost the most, in order

### 1. A guard that was green, met its AC, and gave dangerous advice

ZR-7's guard decided "this method paginates" by finding the string `LastEvaluatedKey` anywhere in the
method. On a hit, its stale-exemption test emitted *"now loops on LastEvaluatedKey; remove this
exemption, the fix has landed"*.

The reviewer added a realistic warn-on-truncation stopgap — `if response.get("LastEvaluatedKey"):
logger.warning(...)`, still reading one page — and the guard instructed the removal of the exemption
covering **the live production defect**. Follow the instruction and the guard goes green forever
while the defect is unguarded.

Nothing in the existing ladder catches this. The tests were green. The AC were met. The RED proofs
were real. The danger lived entirely in the **wording of a failure message** and in the gap between a
proxy and the property it stands for. That is what A12 closes.

### 2. Orchestrator self-review, three times

The implementer for STORY-197 was stopped mid-story and could not be resumed, so I completed AC4–AC7
and then accepted my own work. Reviewers subsequently caught:

- my recovery commit for STORY-195 shipping unfilled `[[…PLACEHOLDER]]` tokens under headings that
  claimed "real output" (I had grepped the rescued work for `TBD` and missed them);
- `CLAUDE.md` still instructing the blocked `pytest`/`cfn-lint` shims after I changed the DoD —
  violating the exact AC4 discipline that story enforces;
- my "8 citation-sweep failures" count being stale at 11.

Not one was caught by me. **The lesson is not "be more careful" — it is that the orchestrator writing
story content is a structural hazard**, because the same person then decides whether it passes. When
an implementer dies mid-story, finishing it myself is sometimes the only option; the mitigation is
that such a story must get a reviewer pass, not that I should try harder.

### 3. A count that went stale inside its own explanation

I recorded "8 failures, all false" — correct when written. The paragraph explaining those failures
then quoted three of them by bare filename, which the sweep's own regex matched as three *new*
citations. The true figure was 11.

This is a small error with a general shape: **a measurement quoted in prose that the same prose then
invalidates.** It survived my review, the article's own limitation section, and a commit message. The
spec reviewer caught it by re-running the command — which is exactly the C2 rule the sprint had been
enforcing on everyone else. A12b makes it explicit.

### 4. The environment regressed mid-sprint, and the process handled it correctly

`pytest` and `cfn-lint` were blocked by Device Guard between 11:16 and 16:33 UTC, taking the gate RED
with no code change. The 2026-07-06 "prove it's environmental" agreement did its job: I proved it
(module-form pass, untouched `infra/`, reproduced twice, timestamps), filed `STORY-210`, and **left
STORY-197 Blocked rather than marking it Done over a red gate**. The PO then approved the invocation
change, mirroring the 2026-07-12 `lint-imports` precedent.

Recorded as a success, not a cost — but note the near-miss: it would have been easy, and wrong, to
call it "obviously environmental" and wave it through. Both gate records are kept in `dod_evidence`
so the regression stays visible in history.

## Amendments (landed 2026-07-31)

### A11 — backlog and story files must not drift apart · rung: **SCRIPT**

Landed as `.claude/skills/yourteam/scripts/tests/test_backlog_story_parity.py`, inside `yt_selftest`.

- a `file:` pointing at a path that does not exist → **hard failure** (planning follows the pointer
  and loses the story's detail);
- a story file with no backlog entry → **hard failure** (the backlog is what planning reads, so an
  orphan is invisible to it);
- `file: null` → **advisory note with a count**, never a failure, because a fresh draft legitimately
  has no file yet.

**Shown RED in both directions** before being trusted, then reverted.

*Why a script and not a checklist:* this is pure state parity between two files — exactly what a
machine should check. The motivating incident is that this sprint filed thirteen stories, four got
files, and **nine existed only as backlog entries** with their detail spread across two reports and a
YAML comment block. Nobody noticed until the PO went looking and could not find them. The advisory
immediately surfaced something bigger: **30 not-done entries repo-wide have no story file**, a
pre-existing accumulation none of us had counted.

### A12 — a guard's failure message is part of the guard · rung: **CHECKLIST**

Landed in `.scrum/checklists/quality-review.md` and `.scrum/checklists/spec-review.md`.

- **A12:** a guard's failure message must not instruct an action its own check cannot justify. Where
  the check is a proxy, the message must say so and tell the reader to verify. Read every message the
  guard can emit and ask: *if someone does exactly what this says, without thinking, is the result
  correct?*
- **A12b:** a recorded count must be re-derived after the last edit to the text that produces it.

*Why a checklist and not a script:* no tool can tell whether a message's advice is sound — that needs
someone who knows what the check is a proxy *for*. Both defects took minutes to see once the question
was asked, and neither was visible from a green test run.

## Deliberately NOT amended

- **The two-reviewer ceremony.** Working exactly as intended; the evidence says strengthen, not trim.
- **The exemption-list pattern for guards.** Both reviewers examined it and agreed the call was right:
  a zero-tolerance guard would have turned the gate RED and blocked every future story until the fix
  stories land, which C4 forbids. The per-entry fix-story citation is the anti-suppression device, and
  line-shift behaviour was measured as loud, not silent.
- **`(file, line)` exemption keys.** The quality reviewer proposed `(file, qualname)` as strictly
  better — it would end the routine false-RED on any edit above a pinned line. Real improvement, but
  it changes guard semantics and belongs in its own story with its own RED proof, not in a retro.
  Recorded here so it is not lost.
- **Sprint sizing.** 11 was inside the baseline and still needed four fix rounds. Size was not the
  variable; story kind was. No sizing rule would have helped.

## Carried into sprint-67 planning

1. **`STORY-210` first — it blocks the DoD gate itself.** The invocation change is in, but the Device
   Guard policy is the real problem and it *widened during this sprint*. If it keeps widening, the
   next casualties are `ruff.exe` or the npm toolchain, and the module-form workaround only stretches
   so far. Worth raising with whoever administers the policy.
2. **Thirteen stories filed this sprint, 24 points** — 198–205 (findings), 206–209 (deferred guards),
   210. All are drafts; every one needs refinement and a citation re-check before it can enter a
   sprint, because this sprint repeatedly found drifted line numbers.
3. **`STORY-199` is the highest-value fix**: a live production defect that silently disables
   maintenance suppression. **`STORY-202`** is next on risk (the seven env-var names, `CONFIG_DIR`
   most severe — it *is* the publish guard).
4. **30 backlog entries repo-wide have no story file** (A11's advisory). Not urgent, but it is a
   standing pool of detail that only exists in YAML comments.
5. The four deferred guards (206–209) are clean-tree rules, so each needs a **mutation** proof rather
   than a live violation — cheaper to land alongside its own story than in a batch.
