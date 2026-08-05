# Sprint 68 — Retrospective

**Run 2026-08-05, after the review (all four stories accepted, 10/10, both AC7 misses filed as
exceptions).** Branch `sprint-68`, 101 commits, `a270c29..e982927`.

Per **A15** the retro audits the rules already in force **before** proposing any new one, and its
default output is **zero amendments**. This retro proposes **two additions and one deletion**, and
recommends **keeping** three rules the six-sprint test flagged.

---

## 0. First, the number A15 exists to move

| Point | Governance bytes | |
| --- | --- | --- |
| A14/A15 landed (`2a7892b`) | 52,555 | the brake goes on |
| A15 baseline recorded (`2f31ec9`) | 54,722 | |
| Sprint 67 close (`a2acc09`) | 56,453 | A16 lands |
| **Sprint 68 close (HEAD)** | **56,453** | **unchanged** |

```
git diff --stat a270c29..HEAD -- .scrum/working-agreements.md .scrum/checklists/   # empty
```

**Sprint 68 added zero governance bytes** — the first sprint in this repo's record to add none.
That is not virtue; the sprint simply had no amendment land mid-flight. But it is the baseline this
retro must not casually spend, and it is why the two proposals below both name a **mechanical** rung
and why one of them is paid for by a deletion.

A16's own test ("governance must be SMALLER six sprints from now, AND at least one rule deleted on
its merits") comes due around sprint 72. Trajectory to date: **+3,898 bytes** since the brake went
on, and two deletions on their merits (D1, D2 at sprint 67). D3 below would make three.

---

## 1. Rule audit — has it fired in the last six sprints (63–68)?

Citation counts across `docs/scrum/sprints/*sprint-6[3-8]/` and the live board:

| Rule | Fired? | Evidence |
| --- | --- | --- |
| A1 / A3 (discrimination proof, sides must differ) | **yes, heavily** | 16 / 14 citations; every reality gate this sprint |
| A6 (`REQUIRE_DYNAMO`) | **yes** | 25 citations — the most-cited rule in the repo |
| A7 (gate is an exit code) | **yes** | 11; STORY-203's gate rebuilt around it |
| A15 (ratchet brake) | **yes** | 18; it is what shaped this document |
| A16 (citations lint) | **yes** | 11; landed sprint 67, cited through 68 |
| A4, A5, A9–A13 | yes | 4–9 each |
| A8 (spike reproduced vs timed) | yes, thinly | 3 |
| A14 (ladder exempt from freeze) | **yes** | 8; cited to justify both proposals below |
| Window Check (2026-07-29) | **yes** | 2 — and it is why this sprint's four session-limit deaths cost nothing |
| 2026-07-06 contention protocol | yes | 3 |
| 2026-07-15 `requires-env` gate warning | yes | 2 |
| 2026-07-15 external-delivery contract | yes (as a mode check) | every sprint since has been `in-process`; the rule is what makes that a *decision* |
| Boundary violations are build failures | **yes** | the sprint goal was built on it |
| 2026-07-13 genericity | **yes** | constrains both proposals below |
| **2026-07-14(b) clean-container gates** | **NO — 0 citations** | **→ D3, delete** |
| **2026-06-23 measure-before-optimizing-read-path** | **NO — 0 citations** | **→ keep, see §4** |
| **2026-01-01 effort cap (3× estimate)** | **NO — 0 citations** | **→ keep for now, see §4** |
| 2026-01-01 8-point split | no direct firing | refinement has produced no 8 since; keep (cheap, one line) |
| 2026-07-17 AWS credential freshness | no | 1 mention; no cloud sequence has run since sprint 51. Keep — it is dormant, not dead, and production is UNVERIFIED since 2026-07-29 |

---

## 2. What actually happened this sprint

**Delivery.** 10/10 points, four stories, four session-limit deaths, **zero lost work.** The TDD
commit-after-every-green-step cadence is the reason, and it is now the third sprint where that is
demonstrably true rather than asserted. Every resumption verified state (`git log`, tree) instead of
assuming it; one death left half-applied scraps and they were discarded per last-green-commit-is-truth.

**Review outcomes.** STORY-205 clean on both. STORY-204 **failed both** reviews and took three fix
rounds. STORY-203 spec FAIL on AC7 only, quality APPROVE with six minors. STORY-215 spec **PASS**
outright, quality FIX_REQUIRED with two MAJOR — **both inside the bullet written to document C3's
third failure.** That is the fifth consecutive sprint in which the independent quality pass caught
something the spec pass did not. The concurrent-and-separate reviewer design keeps paying.

**Where the sprint's effort actually went:**

| | Commits |
| --- | --- |
| `docs/scrum/wiki/` | **41** |
| `backend/src/` + `tools/` | 22 |
| `.scrum/` board | 22 |

**Wiki churn was 41% of the sprint** — in a sprint whose defining defect was wiki/catalogue drift.
The sprint-45 token audit measured the same shape (10 of 33) and it has grown. This is context for
proposal A18, not a separate finding: the catalogue is where this project spends its commits, and
it is the one artifact with no content-level mechanical check.

**Estimates.** All four delivered at estimate. But rounds do not track points: the **2-point**
STORY-204 consumed four rounds and the 3-point STORY-205 consumed one. Points measured the change
correctly and measured the *risk* not at all.

---

## 3. The two proposals

### A17 — the reviewers must be race-immune by construction, and the existing rule must stop being bypassable via Bash

**Rung: AGENT DEFINITION (both reviewers). Not a new rule — a tightening of one that already exists
and was violated.**

**What happened (RC-1).** The two reviews run concurrently by design. On STORY-205 the quality
reviewer mutated tracked source to probe a guard (`_COMPONENT_SK_PREFIX = "COMPONENTX#"`); the spec
reviewer opened its session, found the file dirty, judged it outside its diff, and ran
`git checkout --` on it — restoring the mutation out from under a live run. It then reported the
stray mutation, which is the only reason anyone noticed.

**Why this is a §2 case, not a §3 case.** A15 §2: *an addition must show no existing rule covered
the incident.* One did. `yt-quality-reviewer.md:12` already says **"You never modify files"**, and
the agent carries no Write or Edit tool. It modified files anyway — **through Bash**, which the same
line grants for "git inspection and running tests." The prohibition was not unwritten; it was
unenforceable at the only rung that could enforce it. So the correct response is to **make the
existing line concrete**, never to add a second line saying it harder.

**The change:**

- `yt-quality-reviewer.md` — replace the bare "You never modify files" with the same rule stated
  where it leaks: *Bash may not write to the working tree — no redirection into tracked files, no
  `sed -i`, no `git checkout/stash/apply/restore`, no `patch`. To probe a mutation, copy the file
  into a scratch directory outside the repo, or monkeypatch in-process.*
- `yt-spec-reviewer.md` — *never clean the tree. A dirty file outside your diff is reported, not
  restored; a concurrent reviewer may be mid-probe.*

Both techniques are **already proven in this sprint**: the spec reviewer used a scratch copy for
STORY-205's AC4 and an in-process monkeypatch for AC2, unprompted, and reproduced both claims. And
the RC-1 mitigation applied by hand from STORY-204 onward — briefs forbidding tracked-file mutation
— held across four stories while **the constrained reviewers still produced the sharpest findings of
the sprint.** The evidence that this costs nothing is already in.

**Do NOT serialise the reviews.** Their concurrency and independence is the point.

**Net bytes:** roughly zero — it rewrites two existing lines. Loaded per dispatch, so it must stay
short; both replacements are one sentence.

### A18 — constraint C3 gets a mechanism, and the honest half of one is better than a sixth restatement

**Rung: SCRIPT (`yt_wiki.py --range`), plus STORY-219 for the half it cannot reach.**

**What happened (RC-2).** C3 — *the catalogue moves in the same commit as the code it describes* —
**failed five times in one sprint.** It was in the sprint constraints, in `plan.md`, on the board,
and stated prominently in every implementer brief, including an explicit "STORY-204 missed this and
the miss is permanent; do not repeat it" written into STORY-203's. It was missed anyway, and two of
the five are now permanent AC failures the PO has accepted as filed exceptions.

Under A15 §2 and the skill's ratchet brake, **a rule that existed and went unfollowed must be
relocated, never restated.** Writing C3 in a sixth place is the one response the process forbids.

**What a mechanism can and cannot reach — stated before proposing, not after:**

| # | Occurrence | Per-commit sweep | Citation resolution |
| --- | --- | --- | --- |
| i | STORY-204: prose landed two commits after its code | **catches** | catches |
| ii | STORY-203: same | **catches** | catches |
| iii | STORY-215 `7fb87fe`: `verified_sha` bumped over a Fact never re-read | misses | catches |
| iv | STORY-203 `1d43b1b`: stamp over Facts displaced by its own import line | misses | catches |
| v | citation into a file absent from the article's `code_refs`, plus a source docstring | misses **structurally** | catches |

(iii) and (iv) are the same class: **a `verified_sha` bump is a claim about what an agent re-read,
and no git arithmetic can audit a claim.** (v) is worse — `scripts/seed_topology.py` is not in
`config-layer.md`'s `code_refs`, so no staleness check can ever flag that article however wrong the
citation becomes, and the second site is a **source-code docstring** no wiki tooling covers at all.

**The proposal, in two parts:**

1. **Land now, at the retro** (the 2026-01-01 freeze permits tooling change *at planning or retro*;
   A14 permits it regardless): a `yt_wiki.py --range <base>..<head>` mode. For each commit in the
   range, if the commit touches any file in an article's `code_refs`, that same commit must touch
   that article. Pure git arithmetic over `git show --name-only` — no checkout, no new dependency,
   fully project-generic (it reads only `code_refs`, which is the skill's own schema). **It would
   have gone RED on both AC failures at the offending commit.** Then wire it as a reviewer-run
   command so it cannot be skipped by attention.
2. **STORY-219 carries the rest** — wiring `tools/citation_sweep.py`, the only thing that catches
   all five. PO-prioritized into sprint 69 refinement.

**Stated honestly so nobody reads part 1 as the fix: it catches 2 of 5.** It is proposed anyway
because those 2 are exactly the class that cost this sprint two AC failures, and because RC-2's own
warning applies — *do not let "the full mechanism is a story" become the reason to take prose again.*
That exact move is how this repo grew a six-amendment family (A1–A9) all stating one idea.

**A note on `tools/citation_sweep.py` that changes STORY-219's shape.** Its regex already requires a
line number (`` `path:line` ``), so STORY-219's option (3) — "enforce only line-numbered citations"
— **is already the tool's behaviour** and buys nothing. Its 126 findings are line-numbered
citations, and the large false-positive class is a **filename with a line number but no directory**
(`decide.py:44`), which fails `resolve_path` outright. Resolving those by unique-basename search is
the cheap win, and it is what refinement should size. Recorded here so refinement does not
re-derive it.

**Net bytes:** the working-agreements entry must be SHORT — the enforcement is in the script and
this file is read at every standup. A16's precedent.

---

## 4. Rules the six-sprint test flagged — three verdicts, one deletion

### D3 — DELETE the 2026-07-14 "clean-container gates" clause (b)

> *(b) Clean-container gates: before any full gate run, stop idle dev-DB containers so only the
> gate's own DB is running … STORY-080 is the durable fix and is PO-prioritized for next refinement
> … (Rung: prose until STORY-080 lands the test-rung fix.)*

**Fully spent, on the same evidence that retired D2 one sprint ago:**

- **Its stated expiry condition has been met.** STORY-080 was accepted at **sprint 47**
  ("Standing gate false-red resolved"). The clause says it is prose *until* that lands. It landed.
- **Its subject is retired.** "dev-DB containers" means the Postgres layer. `backend/tests/` no
  longer contains a `test_dev_db_*` file; it contains `test_no_postgres_guard.py`. D2 removed the
  sibling "Expedite STORY-080" amendment at the sprint-67 retro on exactly this reasoning.
- **Zero citations across sprints 63–68.**
- **Nothing is lost.** The general case — *a gate red caused by resource contention is an invalid
  signal, prove it, re-run isolated* — is the **2026-07-06 contention protocol**, which HAS fired
  (3 citations) and is untouched by this deletion.

Clauses (a), (c) and (d) of the same 2026-07-14 amendment all still fire and stay: `--only` scoped
gates appear in 9 sprint documents, evidence hygiene ran at this sprint's close, and (d) is landed
script/agent behaviour.

### KEEP — 2026-06-23 "measure before optimizing the read path" (0 citations)

Flagged by A15's six-sprint test; **recommend keeping, and the reason is a finding about A15
itself.** D1 was deleted for being factually *wrong* at HEAD; D2 for being *spent*. This rule is
neither. It is a **preventive prohibition** — no caching story may be created until a measurement
story proves a real read problem — and derive-on-read is still the live architecture. It has not
fired because nobody proposed caching, which is the rule working, not the rule dying.

**A15's test cannot distinguish a dormant preventive rule from a dead one.** That is a real limit,
recorded here rather than patched with another rule; STORY-212 (A15's mechanical rung) should size
it. One line, read once per session — the cheapest rung there is.

### KEEP FOR NOW — the 2026-01-01 effort cap (0 citations), with its trigger flagged

*A story exceeding 3× its estimate in attempts is auto-Blocked.* It did not fire on the 2-point
STORY-204's **four rounds** — because "3× its estimate in attempts" has **no unit**: points are not
attempts, and nothing defines what one attempt is. A rule that cannot be evaluated cannot fire, so
its zero count is not evidence about its value.

No amendment proposed — per A15 §2 the answer to an unfollowed rule is to fix the existing one, and
this retro is already spending its budget on A17 and A18. **Flagged as the leading candidate for the
sprint-69 or -70 retro:** either give it a countable trigger (fix rounds per story, which the board
already records) or delete it.

---

## 5. Carried, not proposed

- **Sprint 68's own orchestrator error is recorded, not ruled on.** A fix-round brief asserted a
  CRLF trigger that does not exist; the implementer wrote it into a `verified`-stamped wiki Fact in
  good faith and the quality reviewer disproved it end-to-end. Corrected in the wiki *and* on the
  board. No rule is proposed: A18's mechanism does not reach a false claim in a brief, and no rule
  can. The record is the response.
- **RC-2's count was wrong twice** (3 → 4 → 5), corrected each time by someone other than the
  orchestrator. The corrections were appended rather than rewritten, because the sequence is the
  evidence.
- **STORY-217, STORY-218, STORY-219** — filed from review findings, all `draft`, refined at sprint-69
  planning.

---

## 6. PO decisions requested

1. **A17** — tighten both reviewer agent definitions so tree-mutation is impossible by construction
   rather than by scheduling. *(Rung: agent definition. ~0 net bytes.)*
2. **A18** — land `yt_wiki.py --range` now; STORY-219 carries the rest. *(Rung: script. Short prose
   record only.)*
3. **D3** — delete the 2026-07-14 clean-container clause (b). *(Third rule deleted on its merits.)*

Approving all three lands two mechanisms and removes one piece of prose, for roughly zero net
governance growth.

---

## 7. LANDED — PO approved all three, 2026-08-05

### A17 — landed at the agent-definition rung

`yt-quality-reviewer.md` and `yt-spec-reviewer.md`, mirrored into
`.claude/skills/yourteam/templates/agents/` (parity verified; `yt_selftest.py` 43/43 OK). Both
markers bumped to `yourteam_version: 2.2.1`. Kept project-generic per the 2026-07-13 rule.

### A18 — landed as `yt_wiki.py c3 --range BASE..HEAD`

**Discrimination proof (A1/A3 — both sides recorded, and they differ):**

| Side | Range | Result | Exit |
| --- | --- | --- | --- |
| STORY-204's offending commit | `d38334b~1..d38334b` | **4 findings, `zone-rules.md` named** | **1** |
| STORY-203's offending commit | `e9cb8c8~1..e9cb8c8` | **1 finding, `zone-rules.md` named** | **1** |
| the catalogue commit that fixed 204 | `22895b0~1..22895b0` | CLEAN | 0 |
| a commit moving code AND article together | `f643081~1..f643081` | CLEAN | 0 |
| bad range | `nosuchref..HEAD` | setup error on stderr | **4** |

It goes RED on both commits that produced a real AC failure and names `zone-rules.md` — the article
C3 was about — on both. The negative side is not "green because nothing ran": three ranges that
genuinely satisfy C3 come back clean, including one where code and article moved together.

**A defect this check had, found by testing its own error path.** A bad range first reported as an
advisory *note* and exited **0** — a check that could not run, reading as a check that found
nothing. That is the exact A7 failure mode this repo has already paid for. Setup failures now return
exit **4** and never a finding. Worth recording because it was caught by testing the failure path
rather than the happy one, which is what A7 asks for and what would otherwise have shipped.

**Two bugs fixed on the way, both pre-existing:**

- `git()` decoded subprocess output with the **platform locale codec** (cp1252 on Windows), which
  raises on any non-ASCII byte and leaves `stdout` as `None`. Harmless while git output was only
  ASCII paths; fatal the moment a check reads a blob. Now pinned to UTF-8 with `errors="replace"`.
- The module docstring said "three mechanical checks" while listing six.

**Honest measurement, which is why it ships ADVISORY and not blocking.** The filters — only
MODIFIED files (a newly added file cannot falsify prose written about it), and only files an
article both lists in `code_refs` *and* cites by name in its Facts — cut the noise but did not
remove it: **45 notes across sprint 68's 101 commits, 11 of them on STORY-205, a story no reviewer
faulted.** The cause is structural: mid-story green steps do not falsify a "this violation is live"
claim; only the **completing** commit does, and arithmetic cannot see which commit that is. Wired
into `.scrum/checklists/quality-review.md` as a per-story command whose output is **notes to judge,
not verdicts.** The "completing commit" question goes to STORY-219's refinement.

### D3 — landed

Clause (b) removed; the deletion recorded in the prune record with its three grounds. Clauses (a),
(c), (d) untouched.

### Correction to §6's closing claim

I wrote that approving all three would cost "roughly zero net governance growth." **That was wrong,
and the measured number is +2,528 bytes**, even after A17/A18 were cut back to pointers:

| File | Start | HEAD | |
| --- | --- | --- | --- |
| `working-agreements.md` | 38,990 | 41,067 | +2,077 — read **once per session** |
| `checklists/quality-review.md` | 7,574 | 8,025 | +451 — read **per dispatch** |
| `checklists/implementer.md` | 9,889 | 9,889 | unchanged |

D3 removed a clause but the prune record that documents it costs more than the clause did — which
is A15's own thesis restated: **this file cannot delete without writing.** No further trimming was
done, because what remains is the evidence A15 requires. The number is reported rather than
explained away; the sixth-sprint test in A16 is the one that settles whether the brake works.
