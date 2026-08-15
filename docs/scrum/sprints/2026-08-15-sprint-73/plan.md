# Sprint 73 — plan

**Branch:** `sprint-73` off `sprint-72` HEAD at lock · **Committed:** 13 points / 3 stories ·
**Mode:** in-process

**Status: v3 — pre-lock verification RAN (FIX-THEN-PROCEED, 16 findings, all applied). PO then ruled
on the one question v2 raised: *"i want 147"*. STORY-147 is back in and the sprint is 13 points.
Awaiting PO lock.**

## Goal

> **Equilibrium: the dead feature is gone, and the backlog shrinks.**

This sprint is scoped against the PO's equilibrium directive (`38d628f`, 2026-08-13) rather than
against feature delivery. That directive defines equilibrium as **(1) nothing lies, (2) nothing is
half-landed, (3) what remains is chosen**, and states plainly: ***most of the value is in the
archiving, not the building.***

**Confirmed with the PO at this planning: fleet readiness is NOT the goal for sprint 73.** That is a
deliberate choice, not an oversight — 8 of the 14 open stories are fleet-path work and every one of
them is unestimated, so the fleet critical path stays where the equilibrium pass left it. Recorded
here so a later reader does not mistake it for drift.

## Scope — 3 stories, 13 points

| # | Story | Pts | State |
| --: | --- | --: | --- |
| 1 | **STORY-155a** — remove `sample_mode` from the frontend | 3 | `draft` → **split + refined**, 6 AC |
| 2 | **STORY-155b** — remove `sample_mode` from the backend, tombstone its article | **7** | `draft` → **split + refined**, 11 AC |
| 3 | **STORY-147** — component `group` + `description` | 3 | `ready` since sprint 62; citations verified exact at v2 verification |

Velocity: 11, 10, 11, 11, 10, **8**. This commits **13** — **two points above the highest figure this
team has ever delivered**, and that is stated plainly rather than smoothed over.

### STORY-147 was cut at verification, and STORY-155b re-priced 5 → 7

**The re-pricing indicts my own method.** v1 bumped STORY-147 from 2 to 3 *specifically because* its
diff reaches five `verified`/`tier: map` articles that A18 forces re-verified in-story — then priced
STORY-155b's **nine** such articles at zero and called them "informational only." The same rule,
applied to the small story and withheld from the big one. Verification computed the overlap
(`api-five-file-convention`, `architecture-boundary`, `canonical-types-and-ports`, `config-layer`,
`ingest-service-and-pull-loop`, `persistence-adapters`, `statuspage-publish`, `zone-rules`,
`sample-mode`) and **that scope cannot be split into a follow-up — A18 makes it in-story by rule.**

With 155b honestly at 7, the sprint is a 13.

**v2 cut STORY-147 and put its fate to the PO — archive, or commit it. The PO ruled: *"i want 147"*.**
It is in, and it goes **first**.

**That ruling is what sets the ordering, and the reasoning is worth recording.** 147 is the only
story here that is independent, already `ready`, and small. Running it first **banks it** — the PO
asked for it specifically, and a story scheduled last is a story that gets dropped, which is the
mechanism that produced STORY-186 over three sprints. Running it first removes that risk entirely.

**The cost of that choice, stated honestly: it moves the risk onto the `sample_mode` pair.** If the
sprint runs short, the pair is what remains, and the pair is atomic (below). So the realistic bad
outcome is a sprint that delivers 3 points instead of 13 — not a sprint that delivers 10 and drops a
3. I judge that the right trade because the PO named 147 explicitly and the pair is worthless
half-done, but it is a trade and it should be visible at review if it lands badly.

## Why this is the equilibrium sprint

**STORY-155 is the largest single piece of dead weight in the codebase.** Measured at this planning:
`sample_mode` spans **41 code files across two toolchains** (27 backend, 14 frontend), a live seam in
both composition roots, and a `tier: map` / `status: verified` wiki article. It was declared
**TEMPORARY by PO directive on 2026-07-03**, is superseded by the Grail demo engine, and `CLAUDE.md`
already names STORY-155 as its removal. Deleting it is equilibrium applied to code, with the reason
on record — exactly what the directive asks for.

**It also shrinks another story by half.** Archiving `sample-mode.md` removes **~110 of STORY-192's
224 mojibake sequences** (re-measured 2026-08-15; filed as 218, the sprint-71 verifier said 293).
STORY-192 must be re-measured after this sprint rather than carried at its current size.

## Backlog arithmetic — the point of the sprint

| | Open |
| --- | --: |
| At the equilibrium pass (2026-08-13) | 21 |
| At this planning, before changes | 14 |
| STORY-225 **archived** (below) | 13 |
| STORY-155 **split** into 155a + 155b (`split` closes, two open) | 14 |
| **After sprint 73 completes both** | **12** |

Trajectory: **42 → 21 → 14 → 12.** (v1 projected 11 with STORY-147 included; it is cut, so the
sprint returns one fewer. If the PO archives 147, it is 11.)

**One archive, and it is archived on its own evidence.** STORY-225's refinement question 4 *demanded*
a sweep before choosing a shape. The sweep was run at sprint-72 planning and **refuted both of its
premises**: the gap is repo-wide (281 files checked, 213 hooked, **68 unhooked** — its four files are
4 of 68) and `infra/stack.yaml` has been untouched since 2026-07-17, so "actively maintained" fails
and option (a)'s own test answers *no*. What survives is a policy question that is a different story.
It fails equilibrium test 3 — it had no path to `ready` and was not chosen.

**Two candidates I proposed and then withdrew, having checked their content rather than their
titles:**
- **STORY-174** — fleet-path work (`deferred-by-po`), consciously kept by the equilibrium pass.
- **STORY-193** — a **measured** defect: two consecutive real runs of `failure_path_reality_gate.py`
  with identical scenarios disagreed, root cause verified as arithmetic. Archiving it would destroy
  real information.

Withdrawing them is recorded because proposing them was the error the directive warns against —
judging from status and title instead of content.

## Landed at this planning, deliberately NOT as a story

**A board/backlog status parity guard** (`67c5095`). On 2026-08-15 the board recorded STORY-221,
STORY-224 and STORY-173 as `done` and PO-accepted while `backlog.yaml` — *"the source of truth for
story status"* — still said `ready`. The 9-command gate was green throughout, and planning then
offered all three as candidates. Fixed at `ea62f28`; the guard landed as **enforcement-ladder work
under A14**, shown RED against the exact occurrence at exit 1.

**It is not a story on purpose.** One assertion at a rung that already runs in the gate is an owed
one-liner; filing it would have grown the open set to do work that could simply be done — the
opposite of *"most of the value is in the archiving, not the building."* `next_story_id` stays 226.

## Execution order

**147 → 155a → 155b**

**147 first** — see Scope. It is independent of both removal stories (its diff touches
`composition/config.py`, `seed_dynamo.py`, `core/domain/component.py`, the component repository and
the components API feature; none is a `sample_mode` file), so nothing about the removal changes it.

**⚠ 155a and 155b are ATOMIC — both land, or neither does.** A half-removed feature is exactly what
equilibrium test 2 ("nothing is half-landed") forbids. If the window closes mid-155b, **pause with a
committed handoff** rather than closing the sprint with 155a merged and 155b outstanding; if 155b
proves undeliverable, 155a's commits stay unmerged with it. The declared drop unit is **the pair**,
never one half.

**The ordering rationale stated in v1 was WRONG and is replaced.** I claimed removing the backend
first would leave the SPA "calling a 404" in a broken intermediate state. Verification refuted it by
reading the code: the SPA **degrades gracefully** — `client.ts:73-79` throws `ApiError(status=404)`,
`TopBar.tsx:52-58` renders *"Sample mode unavailable — retry"*, and `TopBar.test.tsx:126` already
covers that path.

**The order still stands, on a reason that survives:** 155a's diff **stales `sample-mode.md`** (nine
of the article's `code_refs` are files 155a deletes or edits) and 155b **archives** it. Consumer-first
archives the article once instead of updating-then-archiving.

**Neither half may ship alone.** A half-removed feature is precisely what equilibrium test 2
("nothing is half-landed") forbids. If 155b cannot complete, 155a's commits stay unmerged with it.

## Risks

1. **`sample_mode` is NOT unwired, only flagged off.** `SampleModeIngest` is a live decorator over
   the ingest front door (`run.py:101`, `app.py:47`). Removal changes the wiring of the live ingest
   path. **Mitigation: 155b AC1 requires the unchanged behaviour be proven against observations, not
   argued from the flag being false** — and says to split or block rather than ship on the argument.
2. **The deletion recipe is authoritative-looking and has drifted.** `sample-mode.md:226` names
   `adapters/persistence/sample_mode_repository.py`, which does not exist. Both stories carry the
   correction. Verify every line before following it.
3. **A user-visible change.** 155a removes a banner and its trigger from the operator cockpit. That
   is intended, but it is not a silent refactor.
4. **Two toolchains in one sprint.** 155a is frontend-only, 155b backend-only, and **AC4/AC-scope in
   each forbids a mixed diff** — so each half stays independently reviewable and revertible.
5. **STORY-147's citations drifted once already** and one drifted *dangerously*: `config.py:343-357`
   now points at `AppConfig`'s `model_validator`, the exact implementation its AC1 forbids. The story
   file carries the corrected table; follow it, not the inline numbers elsewhere in that file.
6. **Do not pre-declare wiki blast radius** (`plan-verification.md:19`). Run the sweep after each
   story's last commit. Informational only: `sample-mode.md` is `tier: map` / `status: verified` and
   155b tombstones it; STORY-147's diff reaches five verified map articles, which is why it is a 3.
7. **Re-verify each story at dispatch.** This planning found a drifted recipe, a stale backlog
   status, and two archive candidates that did not survive contact with their own content.

## Environment preconditions

To be measured at lock, not assumed. Expected baseline from sprint-72 close: **9-command gate 9/9**,
pytest **835 passed / 0 skipped**, `npm test` 51 files / 363 tests, `yt_selftest` **113 tests** (108
plus the five added by the parity guard), wiki sweep CLEAN.

## Pre-lock verification — RAN, verdict **FIX-THEN-PROCEED**

4 CRITICAL, 4 HIGH, 3 MEDIUM, 5 LOW. All applied. Several probed by **execution**, not reading.

**What it confirmed I got right:** `SampleModeIngest` really is a live decorator (and I *understated*
it — `sample_mode.py:61` also does a per-cycle control-table read); the ZR1 citations and their `8`;
STORY-147's entire corrected citation table, exact at HEAD; the backlog arithmetic; and that
`putJson` has exactly one caller so it is safe to delete.

### The four CRITICALs — every one would have reddened the gate at a story's final commit

| | Finding | Fix |
| --- | --- | --- |
| **C1** | `pyproject.toml` is in **neither story**, and names sample-mode modules in **three** import-linter contracts (`:79`, `:105`, `:141`). Probed: an *independence* contract naming a deleted module → **exit 1**; a *forbidden* contract → **silent exit 0**. So `:79` reds DoD command 2 and `:105` rots invisibly. 155b's grep was scoped `backend/` and never reaches the file. | 155b **AC2**, naming all three |
| **C2** | `test_citation_gate.py:242-251` asserts `found == set(BASELINE)` over the literal glob `wiki/*.md`; `BASELINE:212` holds a `"sample-mode.md"` key. Archiving the article guarantees a red pytest — and 155b's underscore grep cannot see a hyphenated filename. | 155b **AC4** |
| **C3** | **155b AC1 was unsatisfiable as written.** `build_live_loop` cannot prove it — `test_run_live_loop.py:94` patches `run_periodic` away and asserts an `isinstance`, so removal becomes a one-word edit proving nothing. Worse, the "before" arm cannot live in the suite because AC2 deletes the before-object, and the one existing behavioural proof (`test_sample_mode_end_to_end.py:116`) is on the delete list. | AC1 rewritten: `run_periodic` + `test_pull_loop.py`'s harness, before-arm as **captured evidence**, compared at observation level |
| **C4** | **155a stales `sample-mode.md`** — nine of its `code_refs` are files 155a touches — while 155a's own "Not in scope" forbade touching it and DoD `:133-136` required acting. Three rules, no legal move. | 155a demotes it to `status: stale` with a reason pointing at 155b — the protocol's designed safe state |

### The HIGHs

**H1 re-priced the sprint** (see Scope). **H2:** 155a's AC5 was *false by construction* — ~18 of ~30
lost tests are in **edited** files, so the AC flagged its own correct outcome as a regression.
**H3:** both AC2 greps were holed — 155a's underscore pattern missed `AppShell.test.tsx` and
`SampleModeBanner.css`; 155b's could **never** return zero because it matches
`uptime_monitor_v3.egg-info/SOURCES.txt`. **H4:** `tools/demo_loop_gate/harness.py:800` asserts
`GET /sample-mode == {"enabled": False}` and **no DoD command runs it** — it would have silently
broken the only proven end-to-end verification left since the vendor trial expired.

### MEDIUM / LOW

Further recipe drift beyond the one I found (`PostgresSampleModeRepository`, a `TopBar.css` with no
sample-mode content, and the recipe's own discovery grep finding **4 of 16** files); the file counts
were wrong in both directions (actual **23 backend / 16 frontend / 3 cross-cutting = 42**); 155a's
AC3 offered a false binary when `useMaintenance` carries only a **docstring** reference; STORY-147's
DoD citation corrected `:110-114` → `:133-136`; `archived_sprint`/`archived_reason` named in AC8; and
`BOARD.md` regenerated — it still showed STORY-155 as an unestimated draft, contradicting the very
parity guard this planning landed.
