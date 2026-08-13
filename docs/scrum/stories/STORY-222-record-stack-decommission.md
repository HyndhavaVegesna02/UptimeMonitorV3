---
id: STORY-222
title: Record the AWS stack decommission — CLAUDE.md and two wiki articles describe infrastructure that no longer exists
type: chore
points: 3
status: ready
filed: 2026-08-13
refined: 2026-08-13
sprint: null
---

> **Re-scoped at sprint-71 plan verification (2026-08-13).** Three surfaces were missing — one of
> them **executable** — and AC2 as originally written passed `integrity` while leaving AC6
> unsatisfied. Priced 2 → 3. The corrections are marked ⚑ below.

## Context

**The PO brought the AWS stack down on 2026-08-13.** Three documents still describe it as live, and
one of them is `CLAUDE.md` — the file every session loads and every subagent brief inherits.

This is the largest false claim currently in the repo. It belongs to the "the repo lies to you"
class that the equilibrium pass is organised around: a claim that costs nothing while someone is
watching, and misleads completely once nobody is.

## The three surfaces

**(a) `CLAUDE.md` → "Deployed topology (STORY-089)"**

Names a public CloudFront URL, the cluster `uptime-monitor-cluster`, services
`uptime-monitor-api` and `uptime-monitor-loop`, and two Secrets Manager secrets. It then instructs
the reader to *"Re-verify before trusting anything in this section"* and supplies two commands —
both of which now fail for a reason the text does not anticipate. The section's own hedge
("last verified healthy 2026-07-17 … cause unconfirmed") reads as *possibly degraded*, not
*deliberately retired*, which is a materially different fact.

**(b) `docs/scrum/wiki/deployment-and-infra.md`** — `tier: map`, `status: stale`

Under wiki-protocol 2.3.0 the correct end state is a **tombstone as `tier: reference`**, which means
**stripping `code_refs` AND the `## Facts` section** — `yt_wiki.py integrity` enforces both, and
that mechanical enforcement is exactly what makes a reference article's exemption from staleness
honest rather than an escape hatch. This is a conversion, not a prose edit.

This also **discharges one of the three stale articles** quarantined at sprint-69 close (`3303c6c`).

**(c) `docs/scrum/wiki/deployment-topology.md`** — already `tier: reference`, never swept, so it is
free to edit with no baseline consequence.

## *** Date the decommission. Do not delete the history. ***

A future redeploy needs to know what existed, what it cost, and why it came down. The protocol is
explicit that deletion should **add** knowledge:

> *"A tombstone is the archetypal `tier: reference` content: it explains a past decision and cites
> no live line."*

So the AWS migration epic reads 14/15 for a good reason: it was **delivered, then retired**. Both
halves are true and both belong in the record.

## Acceptance criteria

1. `CLAUDE.md`'s "Deployed topology" section states plainly that the stack was **decommissioned on
   2026-08-13 by PO decision**, with the date, and no longer instructs the reader to verify a live
   URL. The historical topology (what was deployed, and that it worked) is preserved as history,
   clearly marked as past.
2. `wiki/deployment-and-infra.md` is converted to a **tombstone**: `tier: reference`,
   `code_refs` removed, `## Facts` section removed, carrying `archived_reason` naming the
   decommission and its date. `yt_wiki.py integrity` passes on the result.
   ⚑ **The `status:` line is REMOVED** — the protocol declares it map-only. ⚑ **The file STAYS in
   `docs/scrum/wiki/`, not `wiki/archive/`.** Both are load-bearing and neither is caught by the
   tool: verification built a scratch wiki with `tier: reference` **and `status: stale` retained**
   and got `sweep CLEAN / integrity CLEAN / exit 0` — because `check_sweep` short-circuits on
   `tier == "reference"` at `yt_wiki.py:170-174` *before reading status*, and `check_integrity:366`
   flags only `status == "archived"`. Building literally to the old AC2 left three stale articles,
   silently failing AC7. Conversely, setting `status: archived` in place **fails** the gate.
3. `wiki/deployment-topology.md` is updated consistently and remains `tier: reference`.
4. ⚑ **Both deployment articles are free of cp1252 round-trip sequences at the final commit.**
   AC2's `## Facts` removal clears only 17 of `deployment-and-infra.md`'s 24 as a side effect; 7
   survive outside it, and **all 11 in `deployment-topology.md` survive**, including its own
   mojibake title (`Deployed topology â€" the live AWS instance`). Without this AC the ordering
   claim against STORY-192 is false and both stories end up editing these two files.
5. ⚑ **`tools/ui-sweep/` no longer points at the dead stack.** `sweep.mjs:23` hard-codes
   `BASE_URL = 'https://d3ukiib1iqmbxb.cloudfront.net'` and `package.json:5` describes sweeping
   "the LIVE deployed dashboard". **This is the highest-value surface in the story because it is
   executable, not prose** — a runnable tool aimed at a decommissioned host. Either point it at a
   configurable/local base URL or mark the tool decommissioned; do not leave the literal.
6. ⚑ **`CLAUDE.md:144-145` (the Stack table) is corrected too** — it asserts "FastAPI on **AWS ECS
   Fargate**" and "static build served by **CloudFront**". AC1 covers only the "Deployed topology"
   section, so without this the same file still claims a live AWS deployment two sections away.
7. ⚑ **`.scrum/backlog.yaml:1069`** — STORY-089's note "system LIVE at https://d3ukiib1iqmbxb…" is
   dated as past. **ORCHESTRATOR ACTION, NOT IMPLEMENTER WORK.** `.scrum/` is orchestrator-owned and
   subagents never write it (standing constraint); that line also sits inside STORY-089's entry, and
   the orchestrator is editing this same file for board state throughout the sprint. The
   implementer must **not** touch it. The orchestrator applies it at story close and records it in
   the story's board entry.
8. `docs/deploy-runbook.md` is checked and corrected if it *claims* a live stack. Note it is a
   *procedure* document; describing how to deploy is not the same as asserting something is
   running. Judgement call at implementation — say which way it went and why.
9. Any internal wiki link pointing at the converted article still resolves (`yt_wiki.py` link lint
   CLEAN).
10. The three stale articles are now two: `core-pipeline-and-availability.md` and
    `frontend-zone.md`. **Verify mechanically** — `grep -c "^status: stale" docs/scrum/wiki/*.md`
    returns 2, not 3 — rather than by reading AC2 and assuming.
11. The full wiki compile pass (`sweep`/`facts`/`links`/`integrity`) exits 0 at the final commit.

## Baseline note (wiki-protocol 2.3.0)

Editing (b) resets its derived staleness baseline. **That is harmless here and only here**, because
the article is being converted to `tier: reference` — never swept, so there is no verification claim
left to falsify. Contrast STORY-192, where the same edit against a `verified` map article would be
a false claim. Do not generalise this exemption.

## Side effect worth sequencing on

⚑ **Corrected 2026-08-13.** AC4 makes this story clear **35 sequences** (24 in
`deployment-and-infra.md` + 11 in `deployment-topology.md`) out of a corrected repo-wide total of
**293**, not the 24-of-218 originally claimed. Both figures were wrong: 218 counted em- and en-dash
only, missing arrows (57), section signs (15) and others of the identical cp1252 round-trip class.
With AC4 in place this story genuinely removes both files from STORY-192's scope. Without it, it
does not — which was the finding.

## Not in scope

Any decision about redeploying. STORY-090 (CI/CD) was archived on this same fact and stays archived
until a redeploy decision exists. Rehabilitating the other two stale articles.
