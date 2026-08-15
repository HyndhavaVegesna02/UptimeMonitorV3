# Sprint 73 — plan

**Branch:** `sprint-73` off `sprint-72` HEAD at lock · **Committed:** 11 points / 3 stories ·
**Mode:** in-process

**Status: DRAFT — awaiting PO lock.** Plan verification not yet dispatched (see Verification below).

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

## Scope — 3 stories, 11 points

| # | Story | Pts | State |
| --: | --- | --: | --- |
| 1 | **STORY-155a** — remove `sample_mode` from the frontend | 3 | `draft` → **split + refined at this planning**, 6 AC |
| 2 | **STORY-155b** — remove `sample_mode` from the backend, tombstone its article | 5 | `draft` → **split + refined at this planning**, 8 AC |
| 3 | **STORY-147** — component `group` + `description` | 3 | `ready` since sprint 62; re-verified 2026-08-14 |

Velocity: 11, 10, 11, 11, 10, **8**. This commits **11** — the top of the band, deliberately, because
sprint 72's 8 was one dropped story on a session limit and **A21 (the window-check hook) now blocks a
dispatch above 95%**, which is the specific failure that cost that point.

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

**STORY-147 is here to stop it becoming another STORY-186.** It has been deferred from sprint 62 and
sprint 72. STORY-186 was deferred three times, never once started, and was archived at the sprint-72
review. The lesson was explicit: *a story that loses every prioritisation contest is telling you its
real priority.* STORY-147 either goes in now or it should be archived — and it is `ready`, its
citations were re-derived on 2026-08-14, and its own rationale sequences it **before** fleet
expansion (whoever authors the coming components fills `group`/`description` in the same edit rather
than every entry being touched twice). So it goes in, first-to-drop.

## Backlog arithmetic — the point of the sprint

| | Open |
| --- | --: |
| At the equilibrium pass (2026-08-13) | 21 |
| At this planning, before changes | 14 |
| STORY-225 **archived** (below) | 13 |
| STORY-155 **split** into 155a + 155b (`split` closes, two open) | 14 |
| **After sprint 73 completes all three** | **11** |

Trajectory: **42 → 21 → 14 → 11.**

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

**155a → 155b → 147**

1. **155a before 155b is a hard dependency, not a preference.** Removing the backend endpoint first
   leaves the SPA calling a route that 404s, on a branch that may sit unmerged for sprints.
2. **147 last** because it is additive and off-goal; it is the **declared first-to-drop**. If it
   drops, it is archived rather than deferred a fourth time — see above.

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

## Verification

**This sprint IS contract-sensitive** — 155b touches the live ingest seam and the API route table,
and both removal stories consume a wiki-held recipe that is already known to have drifted. The
`yt-plan-verifier` should be dispatched before lock.
