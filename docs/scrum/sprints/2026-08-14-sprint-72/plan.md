# Sprint 72 — plan

**Branch:** `sprint-72` off **`sprint-71` HEAD at lock** — the commit carrying this plan and all
five story refinements (first written at `cc88d78`, plus the pre-lock fix commit). **Not
`fa5507d`**: v1 named it, and it predates every artifact this sprint depends on — cutting there
would put the sprint on a commit where its own plan does not exist. · **Committed:** 9 points ·
**Mode:** in-process

**Status: v2 — pre-lock verification RAN and returned FIX-THEN-PROCEED (3 CRITICAL, 6 MAJOR,
9 MINOR). All are resolved below. Awaiting PO lock.**

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

Then one story that is not about the floor: a hygiene batch that has been ready and cut for capacity
twice, and whose every citation was re-derived at this planning.

## Scope — 4 stories, 9 points

| # | Story | Pts | State |
| --: | --- | --: | --- |
| 1 | **STORY-221** — `npm test` false-reds under load (MaintenancePage) | 3 | `draft` → **refined at this planning**, 7 AC |
| 2 | **STORY-224** — the 7 skill-test modules join the gate | 3 | `draft` → **refined at this planning**, 10 AC |
| 3 | **STORY-173** — reap the leaked DynamoDB container at session start | 2 | `draft` → **refined at this planning**, 7 AC |
| 4 | **STORY-186** — demo-engine doc + test hygiene batch | 1 | `ready` since sprint 64; **citations re-verified today** |

Velocity: sprints 67–71 accepted **11, 10, 11, 11, 10**. This commits **9** — below the band, on
purpose, and the reason is in the next paragraph.

**STORY-147 was cut at pre-lock verification, and the cut reverses v1's own drop order.** v1
committed 11 points and named STORY-186 first-to-drop. Verification then measured what v1 had
priced at zero: STORY-147's diff necessarily reaches **five `verified`/`tier: map` articles**
(`config-layer.md`, `zone-rules.md`, `canonical-types-and-ports.md`, `persistence-adapters.md`,
`api-five-file-convention.md`), each of which `.scrum/definition-of-done.md:110-114` forces
re-verified **inside the story** — the largest wiki radius in the whole candidate set, on the story
carrying the smallest estimate. Its estimate is corrected **2 → 3** in the backlog.

The verifier recommended cutting 186 and keeping 147 at 3 (11 points across 4). **That is not
followed, because it contradicts its own capacity evidence** — the same report says in plain terms
that the measurement tax is not the bottleneck and *"STORY-147 is."* Keeping the cost driver and
dropping the 1-pointer keeps the problem. Cutting 147 instead gives **9 points across 4 stories with
two review pairs**, against sprint 71's 10 points across 5 with the full loop, which **paused
mid-sprint on the session limit**. STORY-147 also has no consumer today: the frontend line is
archived and fleet expansion (STORY-175) is blocked behind STORY-151 and STORY-152. It goes to
sprint 73 honestly sized, with its citation table already re-derived.

**STORY-186 remains the declared first-to-drop** — smallest, last in order, blocks nothing, and
already cut twice for capacity without harm.

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
- **STORY-147's dependency is discharged and its citations had drifted — one of them dangerously.**
  STORY-146 is `done` and the `ConfigError` hierarchy exists (`config.py:97-123`); the pattern AC1
  requires is now the documented idiom (`config.py:589-594`). But `ComponentConfig` moved `:57` →
  `:180`, and the `try/except` moved `:343-357` → `:650-651` — and pre-lock verification found that
  **`:343-357` now points at `AppConfig`'s `mode="before"` `model_validator`, which is the exact
  implementation AC1 exists to forbid.** My re-verification table had the right numbers; I had not
  carried them into AC1's own prose. Both fixed. (Story deferred — see Scope.)
- **STORY-186 shrank on re-verification.** One of its four "wrong claims" is **discharged** — the
  `CLAUDE.md` `interval_seconds` sentence no longer exists (STORY-184 removed it, as the story
  predicted). A second targets a file now in `wiki/archive/`, which is a scope decision (new AC1a),
  not an edit. Its "seven rejection tests at `:295-405`" are **nine, at `:331`–`:458`**.

## Execution order

**221 → 224 → 173 → 186**

Two of these are real, and neither is a code dependency:

1. **221 first, because it taxes everything after it.** This sprint will run `npm test` many times.
   At the filed 2-in-4 rate, leaving it for later means every subsequent story's gate red must go
   through the two-limb attribution protocol before it can be believed. Fixing it first is the only
   ordering in this sprint that pays for itself.
2. **224 second, so the rest of the sprint exercises the 9th command for real.** Landing it early
   means stories 3–5 run the extended gate in anger rather than the new command being proven once
   and never used again.

3–4 are priority order, not dependency. **173 and 186 touch disjoint files** and could run in
either order — but *disjoint at the file level is not disjoint at the article level*: if STORY-173's
reaper lands in `backend/tests/conftest.py` rather than `scripts/dynamo_local.py`, both stories
reach `demo-engine.md`. Whichever runs second takes the sweep's answer as it finds it.

**One consequence to flag now so it is not read as an error:** once STORY-224 lands, gate evidence
reads **9/9**, not 8/8, for every story after it. The DoD file, `CLAUDE.md:194` and the emitted
evidence all move together (STORY-224 AC9).

## Deferred — with reasons

- **STORY-147** (component `group` + `description`) — cut at pre-lock verification on its
  re-measured cost, not its value. Five-article wiki radius, estimate corrected **2 → 3**, and no
  consumer until the frontend line or fleet expansion moves. Full reasoning under Scope.
  **Sprint-73 candidate, already re-verified.**
- **STORY-225** (infra files outside wiki coverage) — **the sweep its own refinement demanded was
  run today and refuted two of its premises.** The gap is **68 unhooked files**, not the 4 it names;
  and `infra/stack.yaml` has not been touched **since 2026-07-17 (~4 weeks)**, so "actively
  maintained" does not hold. *(A first draft of this line said "zero commits in 60 days" and the
  verifier refuted it — all five commits fall inside that window. Corrected here rather than
  quietly dropped; the surviving point is how short the file's history is, not recent inactivity.)*
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
   **pause mid-sprint** on the session limit, with a committed handoff. This sprint is **9 points
   across 4 stories with two review pairs** — deliberately lighter, after verification showed 11
   was over-committed. Still pre-empt the limit: pause with a committed handoff rather than
   dispatching a review pair that may die mid-task.
   *The measurement work is not the tax it looks like:* pytest is 50s and `npm test` 37s, so
   STORY-221's AC1 + AC4 at 8 runs each is **≈23 minutes**, not an hour.
6. **Do not pre-declare wiki blast radius** (`plan-verification.md:19`). Run the sweep after each
   story's last commit and take what it returns. Informational only, not priced in:
   `MaintenancePage.test.tsx` and `scripts/dynamo_local.py` are in no `code_refs`;
   `backend/tests/conftest.py` is a `code_ref` of two `verified` map articles; `frontend-zone.md` is
   already `stale` and therefore not swept.
7. **Re-verify each story at dispatch.** This planning found a discharged claim in STORY-186, a
   discharged dependency in STORY-147, and drifted citations in both. The gap between planning and
   dispatch is where claims die.

## Environment preconditions — VERIFIED, not assumed

Measured at pre-lock verification, 2026-08-14, at `cc88d78`:

| Check | Result |
| --- | --- |
| Working tree | **clean** |
| `python -m pytest` (`DYNAMO_ENDPOINT_URL=http://127.0.0.1:8021`, `REQUIRE_DYNAMO=1`) | **816 passed, 0 skipped, 50.12s, exit 0** |
| `npm test` | **51 files / 363 tests, 37.02s, exit 0** |
| Container `uptime_dynamo_8021` | **Up**, `127.0.0.1:8021->8000/tcp` |
| Wiki sweep / facts / links / integrity | **CLEAN** |

That is the green baseline any later red is compared against — which matters most for STORY-224 and
STORY-173, both of which change the harness the gate itself runs on.

- **A nonzero pytest skip count is an incomplete gate, not a pass.**
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

## Pre-lock verification — RAN, verdict **FIX-THEN-PROCEED**

Dispatched because the sprint is contract-sensitive: STORY-147 carried a config→seed→repository→DTO
slice across four zones, and STORY-224 changes the DoD contract that every other story's evidence is
recorded against. **3 CRITICAL, 6 MAJOR, 9 MINOR. All resolved; every fix is in this v2.**

### The three CRITICALs — all in STORY-224, all would have produced false work

1. **AC1 and AC2 specified incompatible placements, and "the 9th" was unsatisfiable as written.**
   Run through the real `yt_gate.parse_dod`: appending to `## Commands (backend)` makes the
   self-test command **6 of 9**, not the 9th, and turns `CLAUDE.md`'s "Backend (5)" into six. Only a
   **new `## Commands (skill self-test)` section after the frontend section, with no `run from`
   phrase**, yields the 9th at repo-root cwd. AC1 now names that placement literally. Nobody owned
   this decision before — the DoD edit is the orchestrator's, the consequences landed in the
   implementer's AC9.
2. **AC8's assertion is RED at HEAD and would have reddened the gate for every later story.**
   `next_story_id: 225` against a maximum id of `STORY-225` → `225 > 225` is **False**. Once AC1
   makes the self-test a gate command, writing that assertion breaks the gate immediately — and the
   only fix lives in `.scrum/backlog.yaml`, which the implementer may not touch. **The orchestrator
   bumps `next_story_id` to 226 in the same commit as the DoD line**; AC8's shown-RED is taken
   against the pre-bump state.
3. **AC3's second suggested proof yields a false RED.** `yt_gate.py` exits **3** on a dirty tree
   before running any command (`:427-437`), and A20 exempts only `.scrum/` (`:125`) — so mutating
   `.claude/agents/*.md` *uncommitted* reds the gate for a reason unrelated to the ninth command.
   AC3 now requires the mutation to be **committed** in the scratch clone, and the evidence to name
   the failing command's label and distinguish **exit 1 from exit 3**.

### The MAJORs

| # | Finding | Resolution |
| --: | --- | --- |
| M1 | STORY-147 priced at 2 with a **five-article** wiki radius — the largest in the set, on the smallest estimate, using the very measurement that rejected STORY-224's shape (b) at four | Estimate corrected **2 → 3**; story **cut from the sprint** (see Scope — the cut differs from the verifier's recommendation, with reasons) |
| M2 | STORY-147 AC1's stale citation `config.py:343-357` now points at a pydantic `model_validator` — **the exact implementation AC1 forbids** | AC1 rewritten to `:650-651`, with the trap recorded |
| M3 | STORY-221 AC2 prohibited serialization **by location**; `vite.config.ts` declares no pool settings, so `test.fileParallelism: false` there serializes identically, satisfies AC2's wording, and escapes AC6's `frontend/src/` scope | AC2 now prohibits the **effect** by any route (script, CLI, `vite.config.ts` pool keys); AC6's diff check extended to `frontend/` root config files |
| M4 | STORY-224 AC5 proved only the **advisory** half — `test_backlog_story_parity` also has two **hard** assertions (`:101`, `:119`), so a story file committed before its backlog entry reds the gate for an unrelated story | AC5 gains proof (c) against both hard assertions, and states the rule: a mid-sprint filing lands its backlog entry and story file in **one commit** |
| M5 | "`infra/stack.yaml` has zero commits in 60 days" — refuted; all five are dated 2026-07-16/17, **inside** the window | Corrected to "nothing since 2026-07-17 (~4 weeks)" in the plan, the story and the backlog. The 68-unhooked-file half reproduced **exactly** |
| M6 | Branch point `fa5507d` **predates this plan and every story refinement** | Corrected to the `sprint-71` HEAD carrying them |

### The MINORs — all applied

`userEvent.setup()` is **66 sites across 20 files**, not 20 sites · `frontend-zone.md` has **14**
top-level Facts, not 35 · **`demo-engine.md:617` and `:636` record historical "DoD gate 8/8"
evidence that must NOT become 9/9** — a literal grep-and-replace would corrupt sprint history;
AC9 now says so · `CLAUDE.md:78` ("the five backend DoD commands") stays correct under the new
placement, and AC9 notes it moves if the placement ever does · STORY-147 frontmatter gained
`points`/`status`/`refined` — the same Definition-of-Ready bookkeeping miss the sprint-65 verifier
caught on STORY-186 · STORY-147's `models.py:12` corrected to `:14-16` · **STORY-173 AC3 now names
the reaper injection parameter** — `resolve_dynamo` has no such seam today, so "an injected reaper"
was unbuildable as specified · baselines recorded above · the "disjoint files" claim qualified at
the article level.

### Two findings worth carrying into dispatch, from the verifier's own probes

- **STORY-173, Windows liveness:** `os.kill(pid, 0)` on a dead PID raises a bare **`OSError` with
  `winerror == 87`, NOT `ProcessLookupError`** — a reaper catching only `ProcessLookupError` raises
  and violates AC4. And a still-open process handle makes a dead PID read **alive**. Both written
  into AC5, measured rather than assumed.
- **STORY-147 (deferred, for its next sprint):** `_map_item` uses bracket access
  (`dynamo_component_repository.py:24-30`), so new fields need `.get()` or already-seeded items
  raise `KeyError`. AC4's "neither field reaches Statuspage" was confirmed **structurally**
  guaranteed — the payload is built only from `change.status` and the id map
  (`adapters/outbound/statuspage/__init__.py:54`).

### What verification could not break

STORY-224's blast-radius comparison (both halves exact: 0 articles vs 4) · STORY-173's every
citation, **including that the gate's own `uptime_dynamo_8021` falls outside the fixture's
`uptime_dynamo_pytest_` pattern**, so AC2(b) is safe · STORY-221's containment and its mechanism,
confirmed down to the installed `user-event` source · **that AC2 does not block the story by
construction** — `delay: null` and `fireEvent.change` are both viable · all eleven of STORY-186's
re-derived citations · the 68-file sweep (281/213/68, same bucket shape) · and that the plan's
`code_refs` notes are honestly labelled rather than blast-radius pre-declaration in disguise.
