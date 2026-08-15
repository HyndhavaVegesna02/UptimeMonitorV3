# Sprint 72 — review

**Branch:** `sprint-72` (off `sprint-71` HEAD `9c68b97`, tag `sprint-72-start`) · **Final HEAD:** `f29f99b`
**Committed:** 9 points / 4 stories · **Delivered for acceptance:** 8 points / 3 stories · **Dropped:** 1 point / 1 story
**Mode:** in-process · **Status:** awaiting PO verdict — nothing merged, sprints 66–72 all stay unmerged

> **Goal:** *The gate runs everything it claims to run, and it says the same thing twice.*

## The one-line result

The gate went from 8 commands to **9**, and in the process the sprint found and fixed a **soundness
break in the gate runner itself** — one that could emit green DoD evidence stamped at a commit whose
HEAD was red. That defect was created by the interaction of two of this project's own amendments and
had nothing to do with the story that exposed it.

## Final gate — the evidence of record

Full 9-command run at `f29f99b`, `DYNAMO_ENDPOINT_URL=http://127.0.0.1:8021`, `REQUIRE_DYNAMO=1`:

| # | Command | Result |
| --: | --- | --- |
| 1 | `python -m pytest` | **835 passed, 0 SKIPPED**, 71.22s |
| 2 | import-linter | 151 files, 432 deps, **9 kept / 0 broken** |
| 3 | `ruff check .` | clean |
| 4 | `ruff format --check .` | 263 files already formatted |
| 5 | cfn-lint `infra/stack.yaml` | clean |
| 6 | `npm test` | 51 files / 363 tests |
| 7 | `npm run build` | clean |
| 8 | `npm run lint` | clean |
| 9 | **`yt_selftest.py`** *(new this sprint)* | **108 tests, OK** |

**Gate exit 0.** Backend test count moved **816 → 835** (+19, all STORY-173). The skill self-test
suite moved **89 → 108** tests and now gates every story.

Wiki compile pass: **sweep CLEAN, facts CLEAN, links CLEAN, integrity CLEAN.** Map tier held at
**13 articles — no growth this sprint**, which is the protocol's own signal that knowledge routing is
being used instead of defaulting to new map articles.

---

## STORY-221 — `npm test` false-reds under gate load (3 pts)

**Spec: PASS (7/7). Quality: APPROVE (0 critical, 0 major, 3 minor — all fixed).**

Changed the 5 `userEvent.setup()` call sites that precede the 10 `datetime-local` `user.type` calls
to `{ delay: null }`, removing 32 awaited macrotasks per affected test.

**State this honestly, because the story requires it: the flake was never reproduced.**
0-in-8 before the fix, 0-in-8 after, on top of 0-in-4 across sprint 71 and 0-in-1 at this sprint's
baseline — against the filed 2-in-4. **Determinism is not demonstrated.** AC1 explicitly permits an
honest negative and AC4 forbids dressing an uncomparable before/after as an improvement; both were
honoured.

**What IS demonstrated, measured twice by two independent routes:** the affected file's tests got
**~63% faster** and the suspect test **4.7× faster** (1296ms → 273ms), with **no loss of assertion
power** — proven by a 7-mutation battery breaking six different product paths, plus an independent
worktree re-run of the AC3 mutation. The code comment now says the load mechanism is the likeliest
explanation rather than a demonstrated cause.

A counter-intuitive +11% suite wall-clock resolved in the fix's favour: the `tests` phase went *down*
(~53.5s → ~52.3s) while unrelated jsdom `environment` spin-up rose ~160s → ~185s. Contention, not cost.

## STORY-224 — the 7 skill-test modules join the gate (3 pts)

**Spec: FAIL round 1 → fixed. Quality: FIX_REQUIRED round 1 (1 CRITICAL, 3 MAJOR, 8 MINOR) → fixed.**
**One AC remains unmet and needs your ruling — see below.**

The DoD gained a third section and the self-test is now command 9 of 9, running at repo root.

**The CRITICAL, and it is the sprint's most valuable finding.** A20 (landed last sprint) exempts
`.scrum/` from `yt_gate`'s dirty-tree refusal, justified in code by the claim that those paths are
*"read by NO gate command."* This story added a gate command that reads them. Demonstrated end-to-end,
not argued: an uncommitted `.scrum/` edit made the gate **emit `exit_code: 0` evidence stamped at a
commit whose HEAD was red**, with no warning anything was skipped — and the inverse reddened any
agent's gate for reasons unrelated to its code.

**The fix satisfies both horns instead of choosing one:** the `.scrum/`-reading suites now read
**committed HEAD** (`git show HEAD:<path>`), so the gate's inputs are the commit it stamps.
Re-verified by the orchestrator in a scratch clone, both properties simultaneously:

| Scenario | Result | Property |
| --- | --- | --- |
| Violation committed, hidden by a working-tree revert | **exit 1** | soundness restored |
| Violation uncommitted (orchestrator mid-edit) | **exit 0** | A20's intent preserved, no exit-3 box |
| `test_yt_selftest.py` dropped against the real tree | **exit 1** | was exit 0 before the fix |

Also fixed: `MIN_TEST_MODULES` 7 → 8 (the guard was green for exactly the first silent module drop it
existed to catch — found independently by *both* reviewers); "seven modules" → "eight" in the DoD note
and `CLAUDE.md`; and `zone-rules.md:907`'s now-false "eight DoD commands".

### ⚠ AC1 is NOT MET, it is my fault, and it needs a PO decision

AC1 says *"The implementer does not edit `.scrum/`"* and assigns that edit to the orchestrator, citing
the STORY-222 precedent. **My dispatch brief told the implementer to make the edit** — in the same
message that told it the story file wins on any disagreement. The implementer spotted the
contradiction, resolved it toward the brief, and **disclosed it explicitly rather than silently
choosing a side**, which is exactly the behaviour we want.

Mitigating facts: only `definition-of-done.md` was touched; no `git stash`; `backlog.yaml` and
`sprint-current.yaml` untouched; every `.scrum/` edit after the finding was made by me.
**The risk AC1 guards against did not materialise.**

**Your options:** accept with the disclosure on record, or require AC1 amended. The spec reviewer's
point stands either way — such an amendment must be made to the AC, not assumed by a brief.

## STORY-173 — reap the leaked DynamoDB container (2 pts)

**All 7 AC met, four with mutation proofs. No review pair at 2 points; verified by the orchestrator.**

`resolve_dynamo` now reaps dead-PID `uptime_dynamo_pytest_*` containers as its **first statement** —
before the `DYNAMO_ENDPOINT_URL` short-circuit, because the gate always sets that variable and a
reaper placed after it would be dead code exactly where it is needed (STORY-179's AC8 trap applied
forward). Gate green in **both** configurations: 835 passed / 0 skipped with the variable set (56s)
and unset (85s, spawning its own container with no 20-minute stall).

**AC2's negatives are the half that mattered, and this machine made them concrete:** the box holds a
dozen unrelated `gateway-poc-*` containers plus the gate's own `uptime_dynamo_8021`. The name regex is
anchored `^uptime_dynamo_pytest_(\d+)_[0-9a-f]{8}$`; run against all of them plus a `my_`-prefixed
lookalike, **only the exact fixture shape matches.** AC2(c) is a *static source check* that greps for
`prune`, `"*"`, and any `docker rm` lacking a name argument — a mechanism, not a promise.

The implementer also found something outside its brief: `os.kill(pid, 0)` reads **still-alive** for a
child this same process spawned and already `wait()`ed on. It then proved that shape cannot affect the
reaper (which never holds a handle to the PID it checks) and pinned **both** shapes as named tests.

## STORY-186 — demo-engine hygiene (1 pt) — **DROPPED, never started**

Its implementer died on the session limit before touching a file; tree verified clean, no code written.
This was the **declared first-to-drop**, named at planning for exactly this case.

**Raising it rather than rescheduling it silently: this is the third capacity cut (sprints 64, 65, 72)
and it has still never been started once.** Its content has only shrunk on each re-verification — one
of its four original items is already discharged by another story. That is a decision, not a
scheduling accident: either it goes **first** in some sprint, or it should be archived.

---

## Blockers

None. No story was blocked on ambiguity; the one incomplete story was cut on capacity by prior plan.

## Two incidents, both disclosed

1. **`frontend/node_modules` was destroyed during STORY-221's concurrent review window** and repaired
   with `npm ci`. Healthy is **216** top-level entries; the broken state was **199** — and the spec
   reviewer verified its own cleanup by confirming "199 entries intact", i.e. compared the damage
   against itself. `git status` stays clean through this because `node_modules` is untracked, which is
   what makes it a hazard no existing guard can see.
2. **Two orchestrator brief defects, same root cause — I restated contract material instead of
   pointing at it.** STORY-221: a paraphrased mutation description that manufactured a disagreement
   between two correct reviewers. STORY-224: a `.scrum/` instruction contradicting the AC. Both are
   retro items with a real rung available.

## Verdicts requested

| Story | Pts | Ask |
| --- | --: | --- |
| STORY-221 | 3 | accept / reject |
| STORY-224 | 3 | accept **with the AC1 disclosure**, or require AC1 amended |
| STORY-173 | 2 | accept / reject |
| STORY-186 | 1 | **decide its fate** — first in a future sprint, or archive |
