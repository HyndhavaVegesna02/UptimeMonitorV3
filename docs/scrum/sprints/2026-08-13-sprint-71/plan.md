# Sprint 71 — plan

**Branch:** `sprint-71` off `sprint-70` HEAD `bfec505` · **Committed:** 10 points · **Mode:** in-process
**Status: v2 — RE-PLANNED after pre-lock verification returned RE-PLAN. Awaiting PO lock.**

## Goal

> Every check the DoD gate runs, and every document a session loads, is either true or visibly
> stale. Nothing in the floor reports a result it did not measure.

The **phase-0**, requirement-independent set. Real core requirements are inbound and may reshape
the core; none of them can invalidate a fixture that green-lights a dead container, a gate command
whose failure message is indistinguishable from a real defect, or a document describing
infrastructure that no longer exists.

## What v1 got wrong

The pre-lock verifier returned **RE-PLAN**: 3 CRITICAL, 8 MAJOR. The three that reshaped this plan:

1. **9 of 11 committed points had no acceptance criteria.** STORY-179/173/192 were all
   `points: null`, `status: draft`, with 12 open refinement questions. They were written in
   *filing* shape during the equilibrium pass and put into a sprint without being refined.
   Definition of Ready exists to prevent exactly this.
2. **STORY-192's `~2 → ~4` rested on a void premise** — the three articles' staleness baseline was
   already reset to `d9319d8` (2026-08-12, a bulk migration that re-read zero Facts), and the diff
   over their `code_refs` is empty. The re-pricing was discretionary, not protocol-forced.
3. **STORY-173's `3` pre-declared a wiki blast radius**, which `plan-verification.md:19` forbids —
   the radius depends on an implementation choice the story defers.

Two ordering rationales were also refuted outright and have been removed, not rewritten.

## Scope — 5 stories, 10 points

| # | Story | Pts | State |
| --: | --- | --: | --- |
| 1 | **STORY-222** — record the stack decommission | 3 | `ready`, re-scoped + AC corrected |
| 2 | **STORY-179** — dynamo_local port + readiness probe | 3 | `ready`, **refined at this planning** — 8 AC |
| 3 | **STORY-213** — self-diagnosing pagination assertion | 2 | `ready`, 6 AC (was already refined) |
| 4 | **STORY-201** — clickpath `require_field` hygiene | 1 | `ready` |
| 5 | **STORY-189** — two doc/wiki gaps | 1 | `ready`, re-scoped 3 findings → 2 |

Velocity: sprints 67–70 accepted **10, 11, 11, 11**. This commits 10 — all of it genuinely Ready.

**STORY-189 is the declared first-to-drop.** It is the smallest, last in order, and blocks nothing.

## Execution order

**222 → 179 → 213 → 201 → 189**

Only one ordering constraint is real, and it is weak: **222 before anything that touches the wiki**,
because it converts `deployment-and-infra.md` to a tombstone and discharges one of the three stale
articles. The rest is priority order, not dependency. **v1's "not negotiable" framing was wrong**
and is dropped:

- ~~179 before 173~~ — refuted. `_free_tcp_port()` (`:39-45`) and `unique_container_name()`
  (`:48-50`) take no shared input and are called independently at `:123-124`. 173 is not in this
  sprint regardless.
- ~~222 before 192~~ — 192 is not in this sprint. STORY-222's new AC4 now genuinely clears both
  deployment articles of mojibake, which is what that ordering was supposed to achieve and didn't.

## Deferred — with honest reasons this time

- **STORY-192** — not Ready, and re-priced on findings (count is **293, not 218**; the re-baseline
  premise is void; its guard-placement choice is a false choice pending STORY-224). Re-refine first.
- **STORY-173** — not Ready; 4 open refinement questions, including where the reaper is invoked
  relative to `resolve_dynamo`'s env short-circuit, and the reap match-pattern.
- **STORY-224** — filed *by* this verification (see below); unestimated.
- **STORY-186** — `ready` at 1pt, cut purely for **capacity**. Not a judgement about its value.
- **STORY-221** — capacity, not substrate. v1 deferred it on a shared-substrate argument that was
  simply wrong: it lives entirely in `frontend/`, a zone this sprint does not touch. **But see
  Risk 2 — it will fire during this sprint anyway.**

## Filed by this verification

**STORY-224 — an entire second test suite exists and the DoD gate does not run it.**
`testpaths = ["backend/tests"]`; `pytest --collect-only` returns 800 tests, **zero from `.claude/`**.
The 7 modules under `.claude/skills/yourteam/scripts/tests/` run only when someone invokes
`yt_selftest` — a habit, not a floor. Two of them have already caught real defects by luck:
`test_template_parity` caught A19 silently reverting, and `test_scrum_encoding` is STORY-188's
guard. Same class as STORY-178, except these never run at all. Unestimated; the obvious fix
(extending `testpaths`) edits `pyproject.toml`, an amplifier `code_ref` in four articles.

## Risks

1. **STORY-179 modifies the harness the gate itself runs on — and the gate env HIDES it.**
   With `DYNAMO_ENDPOINT_URL` set, `resolve_dynamo` short-circuits at `dynamo_local.py:113-115`
   and **none** of the functions STORY-179 changes is ever called; `REQUIRE_DYNAMO` is inert too
   (`conftest.py:52-86` is only reached when `plan.source == "skip"`). A URL-set baseline stays
   green through total breakage. **Mitigation: STORY-179's AC8 requires the gate green in BOTH
   configurations** — URL set, and URL unset with Docker up. v1's single-config mitigation proved
   nothing; this is the correction.
2. **STORY-221's flake will fire during this sprint.** Measured **2 red in 4** at `56491a8` with
   zero frontend diff — including one failure when run *alone*, which breaks the "passes in
   isolation" limb. `npm test` is gate command 6 of 8, and this sprint runs the full gate at least
   6 times. **Attribution protocol before any red is believed:** (a) confirm an empty
   `git diff sprint-71-start..HEAD -- frontend/`, (b) re-run serialized
   (`--no-file-parallelism`; ~205s vs ~93s). Both limbs, every time. Record the discount on the
   board — never silently.
3. **Do not pre-declare wiki blast radius** (`plan-verification.md:19`). Run the sweep after each
   story's last commit and take whatever it returns. `backend/tests/conftest.py` *is* a `code_ref`
   in `demo-engine.md` and `persistence-adapters.md` (both `verified`), so if STORY-179's AC5
   surfaces through the fixture, that radius is real — but it is not assumed here, and it is not
   priced in.
4. **Environment:** container `uptime_dynamo_8021` is **exited**. Restart it before anything, or
   `REQUIRE_DYNAMO=1` errors in a way that reads as a code red.
5. **Re-verify each story at dispatch.** This session found STORY-178 and STORY-189(a) already
   fixed, and the verifier then found two of v1's own price justifications refuted by measurement.
   The gap between planning and dispatch is where claims die.

## Pre-sprint housekeeping — PO-APPROVED

Remove the stale worktree `.claude/worktrees/yourteam-skill-analysis-a29bf1` (12 MB, 2026-08-01,
detached at `2f31ec9`). **Verified safe twice**: clean tree, 0 tracked files, ignored via
`.git/info/exclude:12`, and `2f31ec9` reachable from **6** branches (the plan previously said 5 —
conservative in the safe direction). It pollutes recursive searches and will corrupt any
measurement STORY-192 or STORY-223 takes.

## Execution shape — PO-DECIDED

**Full YourTeam loop:** implementer + spec reviewer + quality reviewer per story. The PO
re-confirmed dispatch on 2026-08-13, resolving this session's "no subagents unless requested"
constraint against the standing 2026-08-03 authority.

Standing constraints on every brief: **never run `python -m src.composition.run`** (`decide`
publishes recoveries with NO human gate to the LIVE Statuspage); pin `CONFIG_DIR=config/demo` if
`create_app()` is constructed; Device-Guard shims are module-form only; **A19** — every scratch
`cd` written `cd X || exit 1`; checkpoint evidence outside the repo; `.scrum/` is orchestrator-owned;
sprints 66–71 all stay **UNMERGED**.

## Verified green baseline

`bfec505`: `yt_selftest` OK, ruff clean (260 files), `yt_wiki` sweep/facts/links/integrity CLEAN
exit 0 with the citation advisory at **146**. Sprint-70 final gate: 8/8, **800 passed / 0 skipped**
under `REQUIRE_DYNAMO=1`, contracts 9 kept / 0 broken.

## Definition of Done

Unchanged — `.scrum/definition-of-done.md`, 8 commands, all exit 0 via `yt_gate.py`. A nonzero skip
count is an incomplete gate, not a pass.
