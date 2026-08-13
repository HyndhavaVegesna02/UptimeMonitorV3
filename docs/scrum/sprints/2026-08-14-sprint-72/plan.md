# Sprint 72 — plan

**Branch:** `sprint-72` off `sprint-71` HEAD `fa5507d` · **Committed:** 11 points · **Mode:** in-process
**Status: DRAFT — pre-lock verification not yet run. Awaiting PO approval.**

## Goal

> The gate runs everything it claims to run, and it says the same thing twice.

Sprint 71 made the floor *honest* — every check reports what it measured. Sprint 72 makes it
**complete and deterministic**. Three things currently stop the eight-command gate from being a
floor:

1. **A command that answers differently on identical input.** `npm test` measured **2 red in 4** at
   a fixed commit with an empty frontend diff. A gate at a coin flip is something people re-roll,
   and re-rolling is how a *real* red eventually gets waved through. Sprint 71's own plan had to
   carry a two-limb attribution protocol to be applied before believing any red — that is the tax
   being paid, every run.
2. **An entire suite the gate does not execute.** 7 modules under
   `.claude/skills/yourteam/scripts/tests/`, including the two guards that have already caught real
   defects — both times by luck of someone running the script.
3. **State that survives a run and poisons the next one.** A killed pytest leaks its DynamoDB
   container; the next run stalls for 20 minutes with no diagnosis.

Then two stories that are not about the floor: one product-side slice, and one hygiene batch that
has been ready and cut for capacity twice.

## Scope — 5 stories, 11 points

| # | Story | Pts | State |
| --: | --- | --: | --- |
| 1 | **STORY-221** — `npm test` false-reds under load (MaintenancePage) | 3 | `draft` → **refined at this planning**, 7 AC |
| 2 | **STORY-224** — the 7 skill-test modules join the gate | 3 | `draft` → **refined at this planning**, 10 AC |
| 3 | **STORY-173** — reap the leaked DynamoDB container at session start | 2 | `draft` → **refined at this planning**, 7 AC |
| 4 | **STORY-147** — component `group` + `description` config → DTO | 2 | `ready` since sprint 62; **citations re-verified today** |
| 5 | **STORY-186** — demo-engine doc + test hygiene batch | 1 | `ready` since sprint 64; **citations re-verified today** |

Velocity: sprints 67–71 accepted **11, 10, 11, 11, 10**. This commits 11.

**STORY-186 is the declared first-to-drop** — smallest, last in order, blocks nothing, and has
already been cut twice for capacity without harm.

**Every one of the five is genuinely Ready.** Sprint 71 v1 committed 9 of 11 points with no
acceptance criteria at all and the verifier returned RE-PLAN for it; the three drafts here were
refined *before* this plan was written, not alongside it.

## What was measured at this planning, and what it changed

Planning decisions that rest on a measurement taken today rather than on the filing's guess:

- **STORY-224's shape is settled by blast radius, not preference.** `.scrum/definition-of-done.md`
  and `yt_gate.py` are in **no** article's `code_refs` (radius **0**); `pyproject.toml` — the
  filing's obvious one-line fix — is a `code_ref` in **four verified map articles**, each of which
  A18 would force re-verified inside the story. Shape (a) chosen. `yt_selftest.py` measured at
  **89 tests, 4.84s, exit 0** at HEAD, stdlib-only, so no tooling-freeze problem.
- **STORY-173's reaper placement is settled by STORY-179's lesson applied forward.**
  `resolve_dynamo` returns at `scripts/dynamo_local.py:335-337` when `DYNAMO_ENDPOINT_URL` is set —
  **which is the gate's own configuration** — so a reaper placed after that short-circuit would be
  dead code precisely where it is needed. It reaps *before* the short-circuit. This is the AC8 trap
  from last sprint, caught at planning this time instead of at review.
- **STORY-221's seam is contained.** The `datetime-local` typing path is **10 `user.type` calls
  across 5 tests, all in one file**; no other test file in the suite types one. That containment is
  what makes a narrow fix credible and holds the estimate at 3.
- **STORY-147's dependency is discharged and its citations had drifted.** STORY-146 is `done` and
  the `ConfigError` hierarchy exists (`config.py:97-123`); the pattern AC1 requires is now the
  documented idiom (`config.py:589-594`). But `ComponentConfig` moved `:57` → `:180` and the
  `try/except` moved `:343-357` → `:650-651`. Corrected in the story.
- **STORY-186 shrank on re-verification.** One of its four "wrong claims" is **discharged** — the
  `CLAUDE.md` `interval_seconds` sentence no longer exists (STORY-184 removed it, as the story
  predicted). A second targets a file now in `wiki/archive/`, which is a scope decision (new AC1a),
  not an edit. Its "seven rejection tests at `:295-405`" are **nine, at `:331`–`:458`**.

## Execution order

**221 → 224 → 173 → 147 → 186**

Two of these are real, and neither is a code dependency:

1. **221 first, because it taxes everything after it.** This sprint will run `npm test` many times.
   At the filed 2-in-4 rate, leaving it for later means every subsequent story's gate red must go
   through the two-limb attribution protocol before it can be believed. Fixing it first is the only
   ordering in this sprint that pays for itself.
2. **224 second, so the rest of the sprint exercises the 9th command for real.** Landing it early
   means stories 3–5 run the extended gate in anger rather than the new command being proven once
   and never used again.

3–5 are priority order, not dependency. **173, 147 and 186 touch disjoint files** and could run in
any order.

**One consequence to flag now so it is not read as an error:** once STORY-224 lands, gate evidence
reads **9/9**, not 8/8, for every story after it. The DoD file, `CLAUDE.md:194` and the emitted
evidence all move together (STORY-224 AC9).

## Deferred — with reasons

- **STORY-225** (infra files outside wiki coverage) — **the sweep its own refinement demanded was
  run today and refuted two of its premises.** The gap is **68 unhooked files**, not the 4 it names,
  and `infra/stack.yaml` has **zero commits in 60 days**, so "actively maintained" does not hold.
  The real question is a policy one about what `code_refs` coverage means repo-wide. Re-scoped in
  the story file; not sized on a refuted premise.
- **STORY-223** (146 unresolvable Fact citations) — real, but its own refinement says the
  stale-article decision separates *a ~3 from a ~8*, and two of the eleven articles are `stale` and
  quarantined. It also wants a per-article ratchet reusing STORY-219's machinery. Too big to carry
  beside three refined defects; **and it is not growing** — the advisory held flat at 146 across
  sprint 71's 51 commits and the ratchet caught the one attempt to add to it. Contained debt, not
  compounding debt.
- **STORY-192** (wiki mojibake) — depends on STORY-224's answer for where its new guard lands, and
  that answer arrives *during* this sprint. Running both is a guaranteed conflict of exactly the
  kind that cut STORY-186 from sprint 65. Its count also needs re-measuring (218 filed, 293 per the
  sprint-71 verifier).
- **STORY-154** (map the real Dynatrace failure codes) — still `blocked`. The PO reported on
  2026-08-13 that access is returning; it has not arrived. **When it does, 154 runs first and
  alone**, and STORY-175 cannot enter a sprint before STORY-151 and STORY-152 land.
- **STORY-174, STORY-193** — unrefined, no AC, and neither is load-bearing this sprint.

## Risks

1. **STORY-221 may not reproduce.** It went 2-in-4 on 2026-08-06 and **0-in-3 across sprint 71's
   full gate runs**. Two flakes in this repo have already evaporated before their fix (STORY-178;
   STORY-213 at 0-in-12). **Mitigation: AC1 explicitly permits an honest negative and does not let
   it block the story**, and AC4 forbids presenting an uncomparable before/after as if it were one.
   The seam analysis stands on its own. What the story must not do is manufacture a failure.
2. **STORY-224 puts a new command in front of every future gate run.** If it is slow, flaky, or
   sensitive to routine board bookkeeping, the cure is worse than the disease. **Mitigation: AC5
   proves both directions** — a fresh draft entry with no story file leaves the gate green, a real
   parity breach still reds it — and **AC6 bounds runtime** with a stated threshold rather than
   absorbing whatever it costs.
3. **STORY-173's reaper can destroy the gate's own container.** The gate runs against a
   long-lived, fixed-port container (`uptime_dynamo_8021`) that is *outside* the fixture's name
   pattern. A prefix-only or over-broad reaper would remove it mid-run. **Mitigation: AC2 makes the
   three negatives — live PID, non-matching name, no broad `rm -f` — shown-RED requirements, not
   assertions in prose.** This is the half of the story that matters.
4. **Two of the five stories change the test harness the gate itself runs on** (224, 173). A
   baseline gate run at `sprint-72-start` is required **before** either lands, so a later red has
   something to be compared against.
5. **Session capacity.** Sprint 71 ran 10 points across 5 stories with the full loop and had to
   **pause mid-sprint** on the session limit, with a committed handoff. This sprint is 11 points
   across 5 stories with the same shape. Expect the same, and pre-empt it: pause with a committed
   handoff rather than dispatching a review pair that may die mid-task.
6. **Do not pre-declare wiki blast radius** (`plan-verification.md:19`). Run the sweep after each
   story's last commit and take what it returns. Informational only, not priced in:
   `MaintenancePage.test.tsx` and `scripts/dynamo_local.py` are in no `code_refs`;
   `backend/tests/conftest.py` is a `code_ref` of two `verified` map articles; `frontend-zone.md` is
   already `stale` and therefore not swept.
7. **Re-verify each story at dispatch.** This planning found a discharged claim in STORY-186, a
   discharged dependency in STORY-147, and drifted citations in both. The gap between planning and
   dispatch is where claims die.

## Environment preconditions

- Container `uptime_dynamo_8021` **up and answering** before anything; gate env
  `DYNAMO_ENDPOINT_URL=http://127.0.0.1:8021` and `REQUIRE_DYNAMO=1`. **A nonzero skip count is an
  incomplete gate, not a pass.**
- STORY-179's fixed port range **18000–18099** is live for fixture-spawned containers; occupied
  ports there are now a real failure mode (bounded 20-attempt retry, then a message naming the
  range).
- **Never run `python -m src.composition.run`.** `decide` publishes recoveries with **no human
  gate** to the live public Statuspage. Any composition root that builds a publisher needs
  `CONFIG_DIR=config/demo` — on **both** the loop and the API process.

## Execution shape

**In-process, full YourTeam loop** — implementer, then spec reviewer ∥ quality reviewer for every
3+ point story, then the mechanical DoD gate, then the reality gate. The 1- and 2-point stories
(173, 147, 186) take the loop as their points dictate: 2-pointers get implementer → gate → reality
gate; 3-pointers get the full pair. The PO granted the full loop on 2026-08-13 and said "don't stop
after each story" — this sprint runs autonomously to review.

**Sprints 66–72 all stay unmerged. Nothing touches main.**

## Pre-lock verification

Dispatched — this sprint is contract-sensitive: STORY-147 carries a config→seed→repository→DTO
vertical slice across four zones, and STORY-224 changes the DoD contract that every other story's
evidence is recorded against. Findings and their resolution are appended below before the PO is
asked to lock.
