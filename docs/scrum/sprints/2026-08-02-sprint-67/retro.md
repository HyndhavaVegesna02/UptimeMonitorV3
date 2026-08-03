# Sprint 67 — Retro

**Accepted:** 11/11 points, all four stories, PO-accepted 2026-08-03. Velocity recorded.
**Run under A15**, which makes the default output **zero amendments** and requires auditing the
rules already in force *before* looking for new ones.

## Part 1 — The audit (A15 §1), done first

**Governance size, measured with A15's own command:**

| | 3-file governance sum |
| --- | --- |
| `2f31ec9` (A15 landing, 2026-08-01) | **54,722 bytes** |
| `HEAD` (`9426c94`) | **54,722 bytes** |

`git diff 405ab09..HEAD -- .scrum/working-agreements.md .scrum/checklists/` is **empty**. Sprint 67
did not add a single governance byte.

That is the first sprint in this project's recorded history where governance did not grow. It is
also not yet evidence that A15 works — a flat sprint is the *minimum* A15 asks for. Its actual test
is at the sixth sprint from its landing, and it demands governance be **smaller**, with at least one
rule deleted on its merits. This retro proposes the first two such deletions.

### What fired this sprint

Named because A15 asks the question, and because a rule that fires is a rule worth its bytes.

| Rule | Fired how |
| --- | --- |
| **A1-refinement** (worktree proofs must prove which code ran) | **Three times.** Both quality reviewers printed `__file__` to confirm provenance before reporting a mutation; I did the same on MUT-6. The rule that was "not taken at the script rung because tooling was frozen" is now the most-exercised rule in the file. |
| **A6** (`REQUIRE_DYNAMO` makes the fixture fail, not skip) | Every gate run. **0 skipped** on all four — load-bearing for STORY-199, whose tests cannot exist against the fakes. |
| **A4** (computational deliverable pinned by mutation) | STORY-199 AC6, STORY-200 AC7. |
| **A3** (two sides must differ) | STORY-202 AC4's pre-fix DISAGREE / post-fix AGREE. |
| **A14** (ladder exempt from the mid-sprint freeze) | STORY-210 landed policy-block detection at the **script** rung mid-sprint, citing A14 explicitly. Without it that lesson would have been prose again. |
| **A15** | This document. |
| **2026-07-13 project-generic** | STORY-210 AC6; quality review filed a minor for `STORY-210`/`AC5` jargon in a shipped docstring. |
| **Window Check** | The prior session parked at 82% with a committed handoff — see the honest caveat below. |
| **One-session lock** | Park and clean resume across a session limit. |

### Proposed for DELETION — two rules that are dead, not merely quiet

**D1 — "Defer auth cleanly" (2026-06-23), the CORS clause.** It reads: *"From the deployment story
onward, CORS is restricted to the Vercel origin (+ localhost for dev)."*

Verified at HEAD: `grep -rn "CORSMiddleware\|allow_origins" backend/src/` returns **nothing**. There
is no CORS middleware, and CLAUDE.md states plainly that none is needed — dev goes through the Vite
proxy, production is same-origin behind CloudFront. **Vercel was superseded** (`docs/project-history.md`).

This is a binding agreement that instructs a future story to do something factually wrong. It is the
same failure class as every blocking finding this sprint, sitting in the rules file itself. The
"auth's absence never blocks a story" half is still live and should be **kept**; only the CORS
sentence is dead.

**D2 — "Expedite STORY-080" (2026-07-15).** It elevated STORY-080 to top backlog priority and said
*"Until it lands, the existing 2026-07-06 contention false-red protocol governs."* **STORY-080 is
`done` — accepted at sprint 47.** The amendment is fully spent: its subject shipped, and the
`test_dev_db_*` family, `alembic`, and `DATABASE_URL` it names belong to the retired Postgres layer.
The 2026-07-06 protocol it points to stands on its own and is unaffected.

### Not fired in six sprints — reported, deletion NOT recommended

A15 says to propose these. I am reporting them and recommending **keep**, with reasons, because the
rule's purpose is to stop the ratchet, not to strip safety valves:

- **Effort cap** (3× estimate → auto-Blocked) and **the 8-point split rule.** Zero blocked stories in
  sprints 62–67, so neither has fired. Both are cheap, structural, and their value is precisely that
  they have not been needed. Deleting a circuit breaker because it never tripped inverts the point.
- **A8** (spike: reproduced vs. timed) — no spike since sprint 64. Dormant, not dead.
- **A5** (review debt on the board) — did not fire this sprint because there was no review debt.
- **2026-07-17 AWS credential freshness** — no live-cloud sequence since sprint 51.

PO may overrule any of these; I would not.

## Part 2 — What actually happened, and what it means

### The sprint's one real finding

> **Eleven blocking review findings across four stories. Ten were prose. The code was sound every
> time.**

Every story passed spec review and failed quality review — four for four, and the fourth consecutive
sprint the independent pass caught something real. But the *shape* has changed. These were not code
defects and not documentation drift. They were documents that **actively misinformed**, written by
the same commit that made them false:

- a guard's docstring declaring five defects live, twenty lines above the exemption block correctly
  cut to one;
- a `status: verified` wiki Fact stating a hot-path cost **backwards**;
- six citations copied from the AC text that explicitly said to re-derive them;
- a docstring asserting a Postgres CHECK constraint retired at STORY-087, in the one place where it
  would justify deleting the guard that replaced it;
- and a rule catalogue marking a row **`ENFORCED-BY`** a guard that **does not exist** — proven by
  reverting the entire fix and watching the suite stay at 696 passed.

### Why I am not writing an amendment about it

A15 §2 is explicit: if a rule existed and was not followed, the answer is to shorten or relocate it —
never to add a second one saying the same thing more emphatically.

A rule already covered the worst instance. `zone-rules.md`'s own table defines `ENFORCED-BY` as
requiring a guard **"shown RED — never merely 'is green'"**, twelve lines above the row that violated
it. ZR-3 and ZR-7 record their red demonstrations. ZR-6's row recorded none, **and none was
possible.** The definition was right there and went unread.

An amendment saying "re-read the prose you wrote" would be the weakest rung in the ladder, aimed at a
failure that has now recurred under a rule that already existed. That is exactly the six-amendment
pattern A15 was written to stop.

### The one amendment I do propose

**A16 — the Facts lint must not silently skip a citation it cannot resolve. (Rung: SCRIPT.)**

This sprint found **two independent ways** a false claim passed `facts: CLEAN`, and they are
different mechanisms, which is what makes this a defect in the floor rather than a lapse:

1. **Bare `:NNN` citations have no filename to anchor on** (STORY-202) — five wrong line numbers
   sailed through, pointing at `],`, `stdout=out_fh,`, a docstring and a comment, inside a freshly
   stamped `verified` article.
2. **Abbreviated paths are dropped without a word** (STORY-200) — `yt_wiki.py:213` skips any citation
   that does not resolve from the repo root, so a Fact about `core/services/approval.py` passed while
   that file was absent from the article's `code_refs`. Future edits would never have flagged it
   stale.

The fix is small, generic, and lands in a mechanism that already exists (A14 applies): **`yt_wiki`
reports a citation it could not resolve, instead of skipping it** — as an advisory `citations` line
alongside the existing `refs` notes, promotable to blocking later. It does not need to judge whether
a claim is true; it only needs to stop reporting CLEAN about text it never checked.

Evidence it is not a one-off: `canonical-types-and-ports.md:99` carries the same abbreviated form,
predating this sprint. It is a habit.

### Two things filed as stories rather than amendments

Per A14's scope guard — where the mechanical rung is substantial new code, it is a story:

- **STORY-216** — mechanise the `ENFORCED-BY` claim in `zone-rules.md`: a test asserting every row
  claiming enforcement names a guard that exists and has a recorded red demonstration. This is the
  MAJOR-1 lesson at the rung that can actually hold it.
- **STORY-213/214/215** — filed during the sprint, evidence attached (see `review.md`).

## Part 3 — Process observations, no amendment attached

**The Window Check has a gap it cannot close, and it should be stated rather than patched.** It
reads the window at agent *boundaries*, which is correct and worked — the prior session parked at 82%
with a committed handoff. But STORY-202's implementer still died **mid-agent**, because a limit
arriving inside a long run is invisible to a boundary check by construction. The recovery was clean:
four commits survived, coherent uncommitted prose was preserved, and the story finished. **No
amendment proposed** — the rule already documents this caveat, and the recovery path worked exactly
as designed. Recorded so nobody later mistakes the gap for a rule failure.

**Refusing an unearned verification stamp turned out to be the highest-leverage action of the
sprint.** When the interrupted implementer's wiki prose contained a false claim and asserted an AC6
check that had never run, leaving both articles **stale** — readable, quarantined, barred from any
brief — cost nothing and preserved the work. The protocol's third state did its job. No rule change;
this is the protocol working.

**Disclosure worked better than enforcement, twice.** STORY-200's implementer volunteered that it had
restated a reviewer's mutation number without re-measuring — which is the only reason I re-derived
MUT-6 myself before it became a Fact in a verified article. STORY-199's implementer disclosed a
concurrent-gate overlap nobody would have detected. Both disclosures were unprompted. Whatever is
producing that behaviour is worth not disturbing.

## Summary for the PO

| | |
| --- | --- |
| **Deletions proposed** | **2** — D1 (the dead CORS/Vercel clause), D2 (spent STORY-080 expedite) |
| **Amendments proposed** | **1** — A16, at the **script** rung |
| **Stories filed instead of amendments** | 1 new (STORY-216) + 3 during the sprint |
| **Governance delta this sprint** | **0 bytes** |

If D1, D2 and A16 are approved, this is the first retro in the record to **delete rules on their
merits** and to land its only addition at a mechanical rung — which is the behaviour A15 was written
to produce.
