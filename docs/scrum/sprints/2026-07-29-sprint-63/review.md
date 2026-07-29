# Sprint 63 review — the demo fleet is authored, the guard is proven, and the engine stopped lying about itself

**Branch `sprint-63`, final HEAD `05245fd`. Tag `sprint-63-start` at `e107811`. Nothing merged to
`main` — the standing PO instruction is "don't merge with main", so this sits unmerged pending your
verdict.**

7 points committed, 7 delivered, 3 of 3 stories Done. **Full 8-command DoD gate GREEN on the final
HEAD** (`.scrum/sprint-current.yaml` → `final_gate`): pytest **614**, 8/8 import contracts, `ruff`
×2, `cfn-lint`, `npm test` **363**, `npm run build`, `npm run lint`. Wiki sweep **CLEAN**,
`yt_selftest` **28/28**.

**No loop was started at any point this sprint**, by any story or any agent. That was the sprint's
central safety constraint: `decide` publishes recoveries with **no human gate** (`decide.py:122-126`
decides, `:171-172` publishes) and real Statuspage credentials sit in the gitignored repo-root
`.env`, which `load_dotenv()` picks up from any launch directory. The run is STORY-182, sprint 64.

---

## STORY-180 — demo-engine polish, 8 deferred minors (2 pts) → **Done** at `2ed3b57`

All eight minors closed. Scoped gate 5/5 (574 tests at the time).

**Reality gate PASS with a discrimination proof:** editing `vendor_health.py:37`'s
`_HEALTH_CHECK_WINDOW` from `"2h"` to `"3h"` turns AC2's new equality test **RED** (3/4 patched,
4/4 restored).

**Worth your attention — the first attempt at that proof FALSE-PASSED.** It reported green on
*both* sides, because the repo is installed editable (`package-dir = {"" = "backend"}`) and
setuptools' finder resolves `src.*` to the **main tree** from inside any git worktree; the patched
worktree file was never executed. "Green both sides" would have read as *"this constant doesn't
matter"* — the proof would have argued **against** a correct fix. Caught by printing the imported
module's `__file__`, fixed with `PYTHONPATH=<worktree>/backend`. The guard landed immediately at the
checklist rung (`.scrum/checklists/implementer.md`) plus a dated A1 refinement in
`working-agreements.md`, rather than waiting for this retro. **Landing a checklist amendment
mid-sprint is normally retro-routed — if you'd rather it went through the retro, it's a two-line
revert.**

## STORY-176 — part 2a: scenario player, demo fleet, time base, publish guard (3 pts) → **Done** at `e514c1d`

The sprint's risk peak. Delivered: `tools/demo_engine/scenario.py` (past-anchored player),
`config/demo/` with **13 components / 41 signals / 4 locations** across three fleet files plus five
scenario fixtures, and the publish guard.

- **Spec review: PASS** — 18 in-scope AC lines MET, full AC-to-test trace, no gaps, no scope
  additions. AC6/AC7 correctly absent (moved to STORY-182).
- **Quality review: FIX_REQUIRED** — 1 critical + 4 major. The critical was the important one: a
  mutant `expand_scenario` that **ignored `interval_seconds` and hardcoded 30 s passed all 30 new
  tests**. The story's headline behaviour was correct but pinned by nothing.
- **Fix round: 11 commits**, then verified.

**Reality gate PASS, two-sided** (the run isn't in this story, so the guard *is* the gate):

| Side | Result |
|---|---|
| Safe — `config/demo`, **with** real-looking credentials | `statuspage_mapping() == {}`, chain `StatusWritebackPublisher → LoggingPublisher` |
| Unsafe — a throwaway config declaring a `statuspage_component_id` | non-empty mapping, chain `… → BestEffortPublisher → RecordingPublisher → StatuspagePublisher` (**type asserted, no network call**) |
| Collision — a planted `http-check` | caught by AC3(c)'s disjointness check |

**C1 discrimination proof PASS:** hardcoding the interval inside `expand_scenario` now turns exactly
the two new tests RED (2 failed / 28 passed), restored clean. The same mutant previously survived the
entire suite.

### Two things this story carries into review, stated plainly

1. **Review debt.** The fix-round re-reviewer died on an upstream **529 three times** (once fresh,
   twice on resume) and returned nothing. I replaced it with mechanical verification — the mutation
   proof above, an M3 mutation (a typo'd `monitor_id` turns the coherence test RED), an S2 check (the
   demo-side guard test passes with `DYNAMO_ENDPOINT_URL` **unset**, so it can no longer silently
   skip), and an M2 probe (all six malformed scenario shapes raise the named error). **But no
   independent reviewer has read those 11 fix commits as code.** That's a real gap and it's your call
   whether to accept it.
2. **The S2 fix is half a fix.** Only the *safe* side was un-gated from Docker; the unsafe
   counterpart still takes `dynamo_local`, so the **in-test** two-sided proof degrades to one-sided
   on a machine without Docker. It doesn't affect this sprint's evidence — my out-of-test harness
   proves the unsafe side with no Docker at all — but it's a residual worth a follow-up.

## STORY-181 — retire 16 stale code references (2 pts) → **Done** at `05245fd`

All 16 sites across families A–D corrected, plus one defect-driven rewording. Comment-only: **test
count 614, unchanged**, as AC8 requires.

**Reality gate PASS:** the AC6 scan returns **15 hits at the parent** `16143d1` and **0 at the story
head**, same `git grep` command and pathspec at both revisions (so neither side depends on the
working tree). Bare case-insensitive cross-check: **9 → 3**, and the 3 are exactly the permitted
sites.

**AC5 proven by AST, not by reading.** All 11 changed `.py` files have **byte-identical
docstring-stripped ASTs** between the parent and HEAD — comments never enter the AST, and docstrings
are the only comment-shaped thing that does — and every changed line in the 4 non-Python files is
comment-shaped. That is strictly stronger than the AC's own "review the diff line by line".

**AC7 was not the no-op it was expected to be.** `CLAUDE.md`'s own "History — superseded" bullets
asserted that two code comments "still name" Railway/Vercel/STORY-017 — true when written, made
false by this very story, corrected in it. The rot appeared in the document that describes the rot.

---

## The three plan-accuracy defects execution found (appended to `plan.md` at close)

1. **`config.py:585-587`'s "silent discard" trap no longer exists** — sprint 62's `7648d74` made it a
   raised `DuplicateAppIdError` (`config.py:716`). Both the plan and STORY-176 AC8 described stale
   behaviour; the delivered test proves the positive case instead, which is correct.
2. **AC6's scan definition had three defects, not one.** Beyond the `__pycache__` inflation the
   verifier caught pre-lock: `asgi.py:12`'s legitimate `DATABASE_URL` mention made the scan unable to
   come back empty; `windowState.ts:8`'s bare `Postgres` would have been missed; and
   `persistence/__init__.py:1`'s **lowercase** `neon` meant AC6's literal scan saw **15 of 16** real
   sites. All were fixed because families A–D name them — the grep was never the scope.
3. **Points arithmetic** — the drafting commit said 8; the table sums to **7**. Seven was locked and
   is what velocity should record.

## Verdict requested

Per story: **accept** (merges to `main`) / **reject** (back to backlog, commits stay off `main`) /
**accept + follow-up story**.

Follow-ups already filed or ready to file:

- **STORY-183** (filed, `draft`, 1 pt) — bound the demo-engine token cache by **retention** rather
  than consume-on-first-poll. STORY-180 AC4's `pop` closed the common path but leaks an
  abandoned token for the process lifetime and made a repeat poll 404, which real Grail does not do.
  Recommended to land **with or before STORY-182**, whose long-running loop is the first time either
  problem can bite.
- **Ready to file if you want them:** the S2 residual (un-gate the unsafe-side guard test from
  Docker); the two pre-existing wiki rot sites STORY-181 flagged but did not fix
  (`api-five-file-convention.md` and `sample-mode.md` still describe `Postgres*Repository` as the
  live wiring — the latter probably dies with STORY-155).

---

## PO verdict — 2026-07-30

**All three stories ACCEPTED** (STORY-180, STORY-176, STORY-181). 7 committed / **7 accepted**,
recorded in `.scrum/velocity.json` as sprint 63.

**On the two items raised for decision:**

1. **STORY-176's review debt — accepted, and the review authorised to run after acceptance.** The PO
   said: *"i accept, and if any reviews are to be done, you can go ahead and do them."* So the
   fix-round quality re-review was dispatched post-acceptance. Because the story is already accepted,
   anything it finds becomes a **follow-up story**, never a re-opening of STORY-176 — and it matters
   anyway, since STORY-182's live loop run next sprint depends on exactly this code.
2. **The mid-sprint checklist amendment stands.** The PO did not ask for the revert that was offered,
   so the worktree/editable-install guard stays at the checklist rung in
   `.scrum/checklists/implementer.md` plus its dated A1 refinement in `working-agreements.md`.

**`main` is NOT touched.** The standing PO instruction is "don't merge with main", so `sprint-63`
stays unmerged at `05245fd` (plus `.scrum/`/docs commits) exactly as sprints 59–62 did. Acceptance
here means the work is approved, not that it lands on the default branch — say the word if you want
the merge.

**Retro amendments A3/A4/A5 are still awaiting approval** — the retro is its own ceremony and the
acceptance above was of the stories. They are written up in `retro.md` and not yet landed at any
rung.
