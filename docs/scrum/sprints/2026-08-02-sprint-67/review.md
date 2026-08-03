# Sprint 67 — Review

**Date:** 2026-08-03 · **Branch:** `sprint-67` (off `sprint-66`, which stays unmerged)
**Committed:** 11 points / 4 stories · **Delivered: 11 points / 4 stories, all Done**
**Final HEAD:** `9bccac8` · **Sprint-close gate: 8/8 GREEN, exit 0**

## The goal, and whether it was met

> Turn sprint 66's audit report into landed fixes. A report is a document; a document does not fix a
> production defect.

**Met.** The live production defect is fixed, both standing guards' exemption lists shrank to their
stated targets, and the DoD gate is hardened against the policy that took it red mid-sprint.

| Measure | Committed | Delivered |
| --- | --- | --- |
| ZR-7 `_EXEMPTIONS` | six → one | **six → one** (the `PERMANENT` `list_recent` entry survives, correctly) |
| ZR-3 collisions | lose STORY-202's two | **15 → 13**, re-derived by the orchestrator, not carried forward |
| DoD gate | hardened | `ruff` on module form; policy-block classification that labels without ever excusing |

## What each story delivered

| Story | Pts | Status | One line |
| --- | --- | --- | --- |
| STORY-210 | 2 | **Done** | `ruff` moved to module form (preventive, PO-approved); `yt_gate.py` now classifies a policy block distinctly from a code failure — and provably cannot downgrade a red |
| STORY-199 | 3 | **Done** | **The live production defect.** Five persistence methods now paginate; `is_under_maintenance` no longer returns a silent `False` past the 1 MB page |
| STORY-202 | 3 | **Done** | Seven env-var **names** promoted to constants and imported instead of re-declared; `CONFIG_DIR` — which *is* the publish guard — no longer drifts silently |
| STORY-200 | 3 | **Done** | The proposal port takes `ProposalState`, not `str`; the adapter compares by enum identity; STORY-198 subsumed and its defect gone |

STORY-201 (1) was dropped post-lock with PO approval when STORY-202 absorbed a third file. No work
was started; it returns as `ready` and is the first candidate for sprint 68.

## The gate — evidence of record

Every story was gated by the orchestrator's own full 8/8 run, never on a self-report.

| At | Backend | Frontend | Other |
| --- | --- | --- | --- |
| `a528e25` (210) | 689 passed / **0 skipped** | 363/363 | 8 contracts, 247 formatted |
| `a7a1b96` (199) | 694 passed / **0 skipped** | 363/363 | green first attempt |
| `37b09a0` (202) | 695 passed / **0 skipped** | 363/363 | ZR-3 sweep 13 |
| `9bccac8` (200, **sprint close**) | **696 passed / 0 skipped** | 363/363 | `yt_selftest` 43/43, `yt_wiki` CLEAN |

Test count moved 689 → 696, entirely additive. **No test was deleted and none was weakened** — both
reviewers verified that independently on every story.

**Zero skips was load-bearing, not a formality.** STORY-199's five new tests cannot run against the
in-memory fakes, because a DynamoDB page boundary is not reproducible there. A skip would have
voided the sprint's headline story while the gate still read green.

## What the reviewers found — and why it matters more than the code

**Every story passed spec review. Every story failed quality review.** Four for four.

That is the fourth consecutive sprint in which the independent pass found something real, and this
sprint the pattern sharpened into something specific:

> **Eleven blocking findings across four stories. Ten were prose. The code was sound every time.**

Not documentation *drift* — documentation that **actively misinformed**, written by the same commit
that made it false:

- **A guard declaring its own fixed defects still live.** `test_zr7_pagination_guard.py`'s docstring
  still said five call sites were unfixed violations awaiting STORY-199 — twenty lines above the
  exemption block that had correctly been cut to one.
- **A `verified` wiki Fact stating a hot-path cost backwards.** It claimed `is_under_maintenance`
  avoids scanning the partition on the common path. The common path is precisely the one that must
  exhaust `LastEvaluatedKey`. Someone chasing `decide` latency would have read it and looked
  elsewhere.
- **Six citations copied from the AC text that warned to re-derive them.** Five pointed at `],`,
  `stdout=out_fh,`, a docstring, a comment.
- **A docstring asserting a Postgres CHECK constraint that has not existed since STORY-087.** After
  STORY-200 the core-service guard is the *only* enforcement — so that sentence was exactly the
  argument someone would use to delete the guard as redundant.

### The finding of the sprint

`zone-rules.md` marked ZR-6's row **`ENFORCED-BY`** a named test. The quality reviewer reverted the
**entire** ZR-6 fix — port back to `action: str`, fake back to `str`, adapter back to
`if action == "approved":` — and the suite stayed at **696 passed, identical to HEAD**.

The named test pins the *new* 2-member guard. **Nothing detects a ZR-6 regression.** And that table
defines `ENFORCED-BY`, twelve lines above, as requiring a guard "shown RED — never merely 'is
green'." ZR-3 and ZR-7 record their red demonstrations. This row recorded none, and none was
possible.

A future story could re-widen that port with a fully green gate, while the authoritative rule
catalogue told the reader it was guarded. The row now reads `FIXED — NO STANDING GUARD`, with the
mutation evidence in the row itself.

**The orchestrator re-derived that mutation independently** rather than accept it twice-removed: the
implementer disclosed it had restated the reviewer's number without re-measuring, and that number
was about to become a Fact in a `verified` article. Measured in an extracted copy with import
provenance confirmed — **696 passed**. The claim is true.

## Two blind spots found in the mechanical floor

Both are places where a false claim passed a green lint, and they are **different mechanisms**:

1. **Bare `:NNN` citations are invisible to the Facts lint** (STORY-202) — no filename for the regex
   to anchor on, so five wrong line numbers sailed through `facts: CLEAN`.
2. **Abbreviated paths are silently skipped** (STORY-200) — `yt_wiki.py:213` drops any citation that
   does not resolve from the repo root, so a Fact about `core/services/approval.py` passed while
   that file was absent from the article's `code_refs`. Future edits would never have flagged it
   stale.

Two independent ways a citation escaped the lint, in one sprint. Both are retro candidates at the
**script** rung. A third instance of the same abbreviated form already exists at
`canonical-types-and-ports.md:99`, predating this sprint — evidence it is a habit, not a one-off.

## Reality gates — what was actually executed

Nothing was accepted on promise:

- **STORY-210** — the gate ran end-to-end through its own new `python -m ruff` invocations; the
  detector was exercised against real subprocesses in both directions.
- **STORY-199** — the killer bug was *reproduced*: terminating on an empty-after-filter page instead
  of an absent `LastEvaluatedKey` turns the AC3 test RED (`assert False is True`).
- **STORY-202** — the publish guard was executed by the implementer **and both reviewers
  independently**: `statuspage_mapping() = {}`, publisher resolving to `LoggingPublisher` with
  real-looking credentials present.
- **STORY-200** — the persisted bytes were read back from real DynamoDB: `sk =
  'EVENT#…#approved'`, not `#ProposalState.APPROVED`.

### One honest nuance, recorded rather than smoothed over

STORY-200's AC7 mutation pins a **narrower** coupling than the story's blast-radius narrative
implies. The spec reviewer continued past the failure and found `approved_actor` is still written
correctly under the mutation — because AC4 compares by **object identity**, a `.value` drift cannot
break that branch. The hazard the story exists to prevent is now *structurally impossible* rather
than merely tested for.

The mutation is not vacuous; it pins the persisted sort-key byte format, and the test's lookup key
is authored independently of the mutated value. The important part: **the wiki does not overclaim
it** — it says the event becomes unreadable at its expected sort key, not that `approved_actor`
broke.

## Interruption and recovery

The sprint crossed an account session limit mid-STORY-202. The implementer died during a wiki
update. Its prose was coherent and was **preserved**; its `verified_sha` stamp was **refused**,
because it contained a false claim (both files import seven constants — one imports four) and
asserted an AC6 publish-guard check that had never run.

Both articles were left reading **stale** — readable, quarantined, barred from any subagent brief.
That is the wiki protocol's designed third state, and this is what it is for. A second implementer
fixed the claim, ran AC6 for real, and only then re-stamped, in a separate commit.

Reviewers were told the story crossed a handoff and to check the whole range, since a handoff is
where an AC gets dropped between two agents each assuming the other did it. **None was.**

## Blocked stories

None. No story was blocked at any point in this sprint.

## Follow-ups filed, with evidence attached

| Story | Why it exists |
| --- | --- |
| **STORY-213** (defect) | The `list_components` pagination test failed on 1 of 11 full runs. Filed not for frequency but because its message is **indistinguishable from "pagination is broken"** — the defect just fixed. It will cost someone a day. The test must not be weakened to silence it; it is load-bearing AC2 evidence. |
| **STORY-214** (chore) | Extract the shared pagination helper — with the trap recorded: the ZR-7 guard detects pagination **lexically**, so extraction flips all six compliant sites red and forces a guard rework in the same change. 2–3 points, not a refactor. |
| **STORY-215** (defect) | The env-var-name drift STORY-202 bounded out — including the one both reviewers found independently: `test_demo_fleet_config.py` hardcodes `"CONFIG_DIR"`, so the literal re-creating the drift risk sits **inside the test that guards the publish guard**. |

## For the PO — decisions requested

1. **Accept or reject each of the four stories.** All four are Done with recorded gate evidence and
   both reviewers' verdicts.
2. **Merge decision.** The standing directive is that sprint 66 stays unmerged and sprint 67 was cut
   from it. Sprint 67 remains unmerged unless you say otherwise — nothing has gone near `main`.
3. **Worth your attention at the retro:** ten of eleven blocking findings were prose, and two
   distinct blind spots in the Facts lint let false citations pass a green gate. My recommendation
   is to route both at the **script** rung rather than add another prose agreement — the sprint's
   own evidence is that prose about prose is what keeps failing.
