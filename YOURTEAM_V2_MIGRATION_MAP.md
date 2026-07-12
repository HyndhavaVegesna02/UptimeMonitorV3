# YourTeam v2 — Working-Agreements Migration Map

**Status: APPROVED by the PO 2026-07-12 and EXECUTED** — the prune landed on `yourteam-v2`
(retired entries live in git history: `git show b025b3c:.scrum/working-agreements.md`; a prune
record documents the routing). `.scrum/checklists/` are now the binding home for routed items;
`working-agreements.md` holds only the defaults, the PO inception rules, and the contention
protocol. The map below is the approved routing record.

Enforcement ladder: **gate/test → script → hook → agent definition → checklist → prose agreement.**

## Defaults (5 entries) — stay

| Entry | New home | Action |
|---|---|---|
| Pipeline split (1–2 pt vs 3+) | SKILL.md (already) | Keep default; prune duplicate prose |
| Effort cap 3× | SKILL.md (already) | Keep |
| 8-point split rule | SKILL.md / ceremonies (already) | Keep |
| Tooling frozen mid-sprint | SKILL.md (already) | Keep |
| One active session (lock) | SKILL.md / state-files (already) | Keep |

## PO-stated rules — retire into configuration

| Entry | New home | Action |
|---|---|---|
| 2026-06-24 model assignment (Sonnet impl / Opus reviewers) | `model:` frontmatter in `.claude/agents/yt-*.md` | RETIRE |
| 2026-07-02 in-process implementation returns | `mode: in-process` default + agent definitions | RETIRE |
| 2026-07-09 model tiering for non-pipeline subagents | yt-scout (haiku) definition + SKILL.md dispatch guidance | RETIRE |
| 2026-07-10 sprint-42 external exception | Spent one-shot; `mode: external` covers the future | RETIRE |
| 2026-07-10 sprint-43 external exception | Spent one-shot; same | RETIRE |

## PO inception rules — stay as agreements (true project rules)

Dossier-is-the-spec · boundary-violations-are-build-failures (the no-override clause; the check
itself is already a gate) · pure-core-mockable-edges · measure-before-optimizing-reads ·
defer-auth-cleanly — **all KEEP**, unchanged.

## Amendments — routed

| Agreement (date, short name) | New rung / home | Action |
|---|---|---|
| 06-23 command-sync in brief | Checklist: implementer (process) | RETIRE |
| 06-23 single canonical DoD | `yt_gate.py` reads only `.scrum/definition-of-done.md` | RETIRE |
| 06-24 clean tree at dispatch; scoped staging | Hook (`yt_git_guard.py`) for staging; SKILL.md keeps clean-tree-at-dispatch line | RETIRE |
| 06-24 shared throwaway-DB harness | CLAUDE.md + `dev-setup-and-dod` wiki article (already) | RETIRE |
| 06-25 fresh-agent fix loops; verify tree after crash | SKILL.md sprint section + standup (already summarized) | RETIRE |
| 06-25 teardown-on-failure in brief | Checklist: implementer (test discipline) | RETIRE |
| 06-25 share-the-assembly | Checklist: implementer (conventions) | RETIRE |
| 06-25 implementers never write board | Agent definition (yt-implementer rule 5) + SKILL.md "sole writer" | RETIRE |
| 06-25 code_refs = defining files | Checklist: implementer (wiki) + wiki-protocol.md | RETIRE |
| 06-25 orchestrator may finish trivial tails | edge-cases.md (new #13 on approval) | MOVE |
| 06-25 empty-input behavior tested | Checklist: implementer | RETIRE |
| 06-25 Fact coverage in code_refs | **Script:** `yt_wiki.py facts` lint | RETIRE |
| 06-25 non-aligned boundary test | Checklist: implementer | RETIRE |
| 06-26 invariants enforced at construction | Checklist: implementer (project conventions) | RETIRE |
| 06-26 fake/adapter parity | Checklist: implementer | RETIRE |
| 06-26 plan specifies edge behavior | Checklist: plan-verification | RETIRE |
| 06-27 external plans carry conventions checklist | execution-modes.md (external) + plan-verification | RETIRE |
| 06-27 symbol citations in wiki Facts | Checklist: implementer (wiki) + wiki-protocol.md | RETIRE |
| 06-28 TOCTOU → named error + forced race | Checklist: implementer | RETIRE |
| 06-28 five-file shape test per feature | Checklist: implementer — **candidate for a standing meta-test (better rung); propose as a chore story** | RETIRE |
| 06-28 no sentinel id fallback | Checklist: implementer | RETIRE |
| 06-28 tz-naive → 422 at edge | Checklist: implementer | RETIRE |
| 06-28 blast radius = mechanical sweep | **Script:** `yt_wiki.py sweep` | RETIRE |
| 06-29 spec review: test drives the AC | Agent definition (yt-spec-reviewer) + checklist: spec-review | RETIRE |
| 06-29 merge-last at sprint close | ceremonies.md §5 (already encoded) | RETIRE |
| 06-29 gate only on clean committed tree | **Script:** `yt_gate.py` refuses dirty trees | RETIRE |
| 06-29 assembly tests construct real objects | Checklist: implementer + quality-review taxonomy | RETIRE |
| 06-29 contract change rewrites tests | Checklists: implementer + spec-review | RETIRE |
| 06-29 live step gates or is carved out | **Reality gate** (SKILL.md + ceremonies §5 + spec checklist) | RETIRE |
| 06-29 probes enumerate full type distribution | Reality gate (adapter stories) | RETIRE |
| 07-02 consumer AC vs DTO at planning | Checklist: plan-verification (yt-plan-verifier) | RETIRE |
| 07-02 single non-concurrent DB-gated invocation | **Script:** `yt_gate.py` runs sequentially by construction | RETIRE |
| 07-03 AC never pre-declare blast radius | Checklists: plan-verification + spec-review | RETIRE |
| 07-03 wiki pass commits article-by-article | Checklist: implementer (process) + agent definition | RETIRE |
| 07-04 units/scale pinned; fixtures from real samples | Checklists: plan-verification + implementer | RETIRE |
| 07-04 live render-vs-wire spot check | **Reality gate** (consumer stories) | RETIRE |
| 07-06 producer gaps proven by failure-path probe | Checklist: plan-verification | RETIRE |
| 07-06 entrypoint side-effect audit | Checklist: implementer | RETIRE |
| 07-06 contention false-red: prove, isolate, file defect | **KEEP** as agreement (judgment protocol; `yt_gate.py` prints the reminder on red) | KEEP |
| 07-08 worktree syncs integration branch first | execution-modes.md (parallel-waves step 0) + yt-implementer definition | RETIRE |
| 07-08 vendor-id config carries drift check | Checklists: implementer + plan-verification | RETIRE |

## Net result on approval

`working-agreements.md` shrinks to: the 5 defaults, the 5 PO inception rules, the contention
protocol, and future true-process amendments — roughly 60–80 lines. Everything else is enforced
by a script, a hook, an agent definition, or a role checklist, each carrying its provenance.
