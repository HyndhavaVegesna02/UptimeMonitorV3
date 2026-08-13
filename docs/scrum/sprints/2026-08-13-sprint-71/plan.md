# Sprint 71 — plan

**Branch:** `sprint-71` off `sprint-70` HEAD `38d628f` · **Committed:** 11 points · **Mode:** in-process
**Status: DRAFT — awaiting PO approval. Not locked.**

## Goal

> Every check the DoD gate runs, and every document a session loads, is either true or visibly
> stale. Nothing in the floor reports a result it did not measure.

This is the **phase-0** set from the 2026-08-13 equilibrium pass: the work that is
**requirement-independent**. Real core requirements are inbound and may reshape the core; none of
them can invalidate a gate that lies about having run, a fixture that green-lights a dead
container, or a document describing infrastructure that no longer exists.

## Scope — 4 stories, 11 points

| # | Story | Pts | What it closes |
| --: | --- | --: | --- |
| 1 | **STORY-222** — record the stack decommission | 2 | `CLAUDE.md` + 2 wiki articles describe a stack that was brought down 2026-08-13 |
| 2 | **STORY-179** — dynamo_local port + readiness probe | 2 | A probe that proves connectability but not that the service answers |
| 3 | **STORY-173** — killed pytest leaks its container | 3 | Next run stalls 20 min with no diagnosis |
| 4 | **STORY-192** — wiki mojibake + re-verify | 4 | 218 corrupted sequences the encoding guard passes clean |

**STORY-192 is the DECLARED first-to-drop** if the sprint runs hot. It is last in the order, its
re-verification half is the sprint's largest unknown, and dropping it costs no other story.

Velocity baseline: sprints 67–70 accepted **10, 11, 11, 11**. This commits 11.

## Execution order, and why it is not negotiable

**222 → 179 → 173 → 192**

1. **222 first.** It is docs-only with zero gate risk, and it **tombstones the two deployment
   articles that STORY-192 would otherwise also edit** (`deployment-and-infra.md`,
   `deployment-topology.md` — 24 of 192's 218 sequences). Running it second would put two stories
   in the same two files.
2. **179 before 173.** Both touch the DynamoDB Local container lifecycle. 179 may change the port
   strategy and therefore the container **name pattern**, which is precisely what 173's reaper
   matches on. Reversed, 173's reaper is written against a pattern 179 then changes.
3. **192 last.** It depends on 222 (above), and it is the drop candidate — the tail is where a
   drop costs least.

## Deferred, with reasons

- **STORY-213 (backend flake, 2) and STORY-221 (frontend flake)** — deliberately held for sprint 72,
  *together*. **STORY-179 and STORY-173 both modify the container lifecycle STORY-213 runs on.**
  Measuring a 1-in-11 hit rate against a substrate being changed in the same sprint produces
  numbers that mean nothing. Measure both flakes **after** this sprint lands, on a stable fixture.
  They pair naturally — one backend, one frontend, both "the gate false-reds," both requiring a
  measured hit rate before and after. *Do not assume 179 fixes 213* (its hypothesis is a lost write,
  a different mechanism); re-measure and let the number decide, the way STORY-178 was decided.
- **STORY-186 / 189 / 201** — three 1-pointers, `ready`, pure accuracy. They gate nothing and make
  natural sprint-72 filler alongside the flakes. STORY-189 must have its (b)/(c) citations
  re-derived first (both drifted; see the refinement pass).
- **STORY-223** — unestimated by design: refinement must first settle whether it rehabilitates the
  two `status: stale` articles or excludes them. That decision separates a ~3 from a ~8.
- Everything `blocked` (150, 154, 172, 175) — gated on the vendor or on the inbound requirements.

## Pre-sprint housekeeping — **PO-APPROVED 2026-08-13**

A **stale git worktree** sits at `.claude/worktrees/yourteam-skill-analysis-a29bf1` — 12 MB, from
2026-08-01, detached at `2f31ec9`.

**Verified safe to remove:** working tree is clean, and `2f31ec9` is reachable from five branches
(`sprint-66`…`sprint-69`, `process/ratchet-brake-from-sprint-66`), so it holds **zero unique work**.

**Why it matters beyond disk:** it is a full second copy of `backend/`, `docs/scrum/wiki/`, and
`.scrum/`, and it **pollutes recursive searches**. It was found during this planning session by a
`grep -rln` that returned 8 hits from the worktree and 2 from the real tree. That is exactly the
RC-1 defect class from sprint 70 — a count contaminated by a directory nobody remembered — and it
will corrupt any measurement STORY-192 or STORY-223 takes.

Proposed: `git worktree remove` at sprint start, recorded in the plan rather than made a story.

## Risks

1. **This sprint modifies the test harness the DoD gate itself runs on.** Stories 2 and 3 both
   change `dynamo_local` behaviour, so every gate run during them is exercising the thing under
   change. **Mitigation:** establish the green baseline against a *fixed-port* container
   (`DYNAMO_ENDPOINT_URL=http://127.0.0.1:8021`, `REQUIRE_DYNAMO=1`) before story 2 starts, and
   re-run it unchanged after story 3. A red during 2–3 must be attributed before it is believed.
2. **STORY-192's re-verification is the sprint's largest unknown** — **67 Facts across 1068 lines**
   (`sample-mode.md` 23 / `ingest-service-and-pull-loop.md` 28 / `statuspage-publish.md` 16), each
   to be read against the code it cites. This is why 192 is priced 4 and declared first-to-drop.
3. **STORY-173 carries a two-article wiki blast radius.** `backend/tests/conftest.py` is a
   `code_ref` in **`demo-engine.md` and `persistence-adapters.md`, both `verified`** — so under
   A18 the story must update or genuinely re-verify both, in-story. This is why it is 3, not 2.
   (`scripts/dynamo_local.py` is a `code_ref` in **no** article, so STORY-179 has zero blast radius.)
4. **Environment:** container `uptime_dynamo_8021` is currently **exited**. Restart it before
   anything, or `REQUIRE_DYNAMO=1` will ERROR — which reads as a code red and is a setup error.
5. **Two of these stories were nearly filed stale.** The refinement pass found STORY-178 already
   fixed and STORY-189(a) already fixed. Every story here was re-verified against the live tree on
   2026-08-13 — but **re-verify again at dispatch**; the gap between planning and dispatch is where
   the last two died.

## Verified green baseline

Sprint 70 final HEAD: **8/8 gate green — 800 passed / 0 skipped** under `REQUIRE_DYNAMO=1`,
contracts 9 kept / 0 broken, ruff clean, cfn-lint clean, npm test 363 / build / lint.
Post-refinement HEAD `38d628f`: `yt_selftest` OK, ruff clean (260 files), `yt_wiki` exit 0 with the
citation advisory unchanged at 146.

## Definition of Done

Unchanged — `.scrum/definition-of-done.md`, 8 commands, all exit 0, run via `yt_gate.py`.
A nonzero skip count is an incomplete gate, not a pass.

## Execution shape — **PO-DECIDED 2026-08-13: FULL YOURTEAM LOOP**

The PO re-confirmed subagent dispatch for this sprint: **implementer + spec reviewer + quality
reviewer per story**, as sprints 66–70 ran. This resolves the session-level "no subagents unless
requested" constraint against the standing 2026-08-03 authority — **requested, explicitly, here.**

The reason it mattered enough to ask: **sprint 70's own review recorded that the orchestrator's
self-check was the weaker one.** I reviewed STORY-212's AC7 checklist diff, confirmed every
mechanic was preserved, and passed it; the quality reviewer found that reviewer *independence*
was the casualty. Three of this sprint's four stories turn on a proof — two shown-RED mutations
and one 67-Fact re-verification — and "I checked it myself" is the weakest available evidence for
exactly that shape of claim.

Standing constraints that ride on every brief (unchanged from sprint 70):
- **NEVER run `python -m src.composition.run`** — `decide` publishes recoveries with NO human gate
  to the LIVE public Statuspage. If `create_app()` is constructed, **PIN `CONFIG_DIR=config/demo`**.
- Console-script shims are Device-Guard blocked — **module form only**.
- Checkpoint agent evidence **outside the repo**, to the session scratchpad.
- **A19:** every scratch `cd` is written `cd X || exit 1`, and no tool relies on a `--repo-root`
  default pointing at the working tree.
- `.scrum/` is orchestrator-owned; subagents never write it.
- Sprints 66–71 all stay **UNMERGED**. Nothing touches `main`.
