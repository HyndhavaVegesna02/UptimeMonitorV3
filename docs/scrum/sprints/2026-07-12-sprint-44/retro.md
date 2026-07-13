# Sprint 44 Retro — YourTeam v2 PILOT

**Verdict on the pilot: v2 stays.** All five success criteria MET (scorecard in review.md).
Both stories accepted 2026-07-13; velocity 5/5.

## What went well (with the incidents)

- **Plan verifier killed an S32-class escape pre-lock**: round-1 GAPS on the int-typed
  fixtures vs the string-typed wire — the exact family that once survived 146 green tests and
  two reviewers. Cost: one extra dispatch. Historically this class cost whole sprints.
- **The git-guard hook fired once, correctly** — blocked the orchestrator's own mis-sequenced
  lock commit (checkout+commit chained while the board already named the new branch).
- **Crash recovery**: implementer connection-drop mid-wiki-pass cost one article's frontmatter
  (commit-per-green-step + commit-per-article + edge-case #13 tail completion).
- **Reviews had teeth on prose, not just code**: quality FIX_REQUIRED with 3 MAJORs on wiki
  ref-scoping; spec's AC-vs-hygiene ruling converged with quality on the same fix. Structured
  verdicts parsed cleanly; concurrent reviews on isolated DBs worked.
- **Reality gate**: live render-vs-wire exact match on 120 real observations.
- **Scripted evidence**: every gate fragment machine-written; the gate caught its own planning
  baseline red (unformatted v2 scripts; Device-Guard-blocked lint-imports exe → module-path
  DoD command).

## What dragged (root causes)

- **The enforcement floor shipped untested**: three script bugs surfaced only under live load —
  yt_gate cp1252 capture crash, yt_gate UTF-8 stdout crash after a fully green run, and
  yt_wiki's comment-blind parser SILENTLY skipping an article from the sweep (the exact
  trusted-and-wrong hole the sweep exists to close). Fixed in-sprint; the gap is process.
- **Manual multi-DB juggling** (:55432 demo / :55433 reviewer / :55434 gate) to honor the
  no-concurrent-DB rule; still tripped the STORY-080 hardcoded-port flake (defect filed with
  contention proof per the 2026-07-06 protocol).
- Full gate ≈ 5 minutes × 5 runs was the sprint's largest fixed time cost — acceptable,
  observed for trend-watching, no change proposed.

## Amendments — PO-approved 2026-07-13, each routed down the enforcement ladder

1. **Skill self-test suite** (rung: standing tests): pytest suite inside the skill covering
   yt_gate parsing/tails/dirty-tree, yt_wiki frontmatter/coverage/links, the hook's block/allow
   matrix, and template↔instance parity; run at standup via `yt_selftest`. The gate gets a gate.
2. **Lock-sequence fix** (rung: ceremonies.md): cut branch + tag FIRST, then write the board,
   then commit — never chain a checkout with a commit.
3. **Stateful-resource isolation pattern** (rung: reference text + brief boilerplate, written
   GENERICALLY): every concurrently dispatched agent that runs commands against a stateful
   resource (DB, container, port) gets its own isolated instance, named in its brief; the
   project's own tooling docs define how to provision one (this repo: `scripts/dev_db.py`).
4. **yt_wiki prints `SKIPPED (status=…)` for every non-verified article** (rung: script):
   silent exclusion from the sweep becomes impossible by construction.

**PO-stated rule (recorded immediately, working-agreements.md):** YourTeam skill changes stay
project-GENERIC — project specifics live only in generated/instantiated artifacts
(`.scrum/checklists/`, DoD, config), never in the skill's scripts/references/templates/agents.

**Rejected/deferred:** no changes to untested machinery (external mode, parallel-waves,
bootstrap) on speculation — next milestone is a bootstrap pilot into a fresh repo. The `.scrum`
write-protection hook stays a watch-item (harness doesn't expose agent identity to hooks).

## Watch-items for the next sprints

- Does retro-routing keep working-agreements.md small over many sprints (prose-regrowth check)?
- STORY-063 refinement needs the decide-time capture design decisions (severity semantics,
  triggering-signals shape).
- STORY-080 should enter the next sprint (a flaky gate is never left standing).
