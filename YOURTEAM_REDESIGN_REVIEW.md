# YourTeam Skill — Architecture Review & Redesign Proposal

**Date:** 2026-07-12
**Scope:** `.claude/skills/yourteam/` (14 files) evaluated against 43 sprints of live evidence
(`docs/scrum/sprints/`, `.scrum/working-agreements.md`) and current official Anthropic guidance
(Agent Skills, subagents, hooks, multi-agent orchestration, context management).
**Status:** Approved direction; the P0/P1 core (+ plan verifier) is built on branch `yourteam-v2`
— see `YOURTEAM_V2_MIGRATION_MAP.md` for the agreements reclassification awaiting entry-by-entry
PO approval. Not merged to main.

---

## 1. Current Architecture Assessment

### What it is

A single Agent Skill implementing a complete Scrum methodology:

| Layer | Artifact | Mechanism |
|---|---|---|
| Orchestrator playbook | `SKILL.md` (143 lines) + 4 references (ceremonies, edge-cases, wiki-protocol, state-files) | Prose instructions, progressive disclosure per ceremony |
| Worker roles | `agents/*.md` — implementer, spec reviewer, quality reviewer | Markdown prompt **templates with `{PLACEHOLDERS}`** the orchestrator hand-interpolates into generic Agent dispatches |
| State | `.scrum/` YAML (backlog, sprint board, velocity, DoD, agreements, lock) | Orchestrator-maintained; git-committed for recoverability |
| History | `docs/scrum/stories/`, `sprints/` | Append-only |
| Knowledge | `docs/scrum/wiki/` (13 articles) | Provenance frontmatter (`code_refs`, `verified_sha`), git-arithmetic staleness, quarantine, blast-radius sweeps |
| Guardrails | Mechanical DoD gate (9 commands), import-linter, FK check | Real commands — but **run and transcribed manually** by the orchestrator |
| Memory | `working-agreements.md` (append-only retro amendments) | Now ~557 lines, all of it binding on every session and every brief |

### Scorecard

| Dimension | Verdict | Evidence |
|---|---|---|
| Overall architecture | **Strong core, weak enforcement layer** | Methodology is coherent and battle-tested; nearly all invariants live in prose |
| Prompt organization | Good disclosure, outdated mechanics | References load per-ceremony (correct); agent prompts are paste-templates, not real agent definitions |
| Agent responsibilities | Clear on paper, unenforced in practice | Reviewer lanes well-separated; but nothing *prevents* an implementer writing board state (S4 incident) or a reviewer editing code |
| Orchestration & delegation | Sound sequential pipeline; no parallelism model | S38 ran 31 pts via ad-hoc parallel worktrees and needed a corrective agreement after the fact |
| Memory strategy | **Does not scale** | Agreements grew 0→557 lines in 3 weeks, monotonic, all injected into briefs; conventions/process/exceptions conflated |
| Guardrails | Right philosophy, wrong substrate | "Mechanical gates over promises" — yet branch-guarding, staging scope, board ownership, gate-on-clean-tree are all prose rules that each failed once first |
| Evaluation & testing | Product: excellent. Process: none | No self-test for the skill; changes to it ship unvalidated |
| Maintainability | Degrading | Every incident adds prose someone (an LLM) must remember; prune has happened once, PO-directed |
| Scalability | Ceremony is per-sprint, not per-point | S38 proved 31 pts flow through the same ceremony as 3 pts; sprint granularity, not ceremony content, is the cost driver |
| Developer experience | High-trust, high-toil | 40 sprints of 100% commit-to-accept; but orchestrator hand-runs gates, transcribes evidence, sweeps the wiki every close |

### What 43 sprints prove works (keep, unchanged in spirit)

1. **Mechanical DoD gate + recorded evidence.** The non-LLM floor caught real regressions every sprint. Exit codes over promises is the skill's best idea.
2. **Git-arithmetic wiki staleness + quarantine.** Drift held at ~zero across 43 sprints; "incomplete but never trusted-and-wrong" held (one leak in ~13 sweeps, S43).
3. **Four PO touchpoints, hard-locked sprints, main-is-sacred, blocked-not-guessed.** Zero scope disputes, zero unwanted merges, fully reversible sprints.
4. **Commit-after-green as crash recovery.** ~15 subagent/session deaths across the project; all but one (S41) recovered at the cost of ≤1 step.
5. **The retro → amendment loop itself.** Agreements demonstrably changed downstream behavior (S9 proactive validator; S22 "cleanest execution to date"). The loop is right; where amendments *land* is wrong (see Issue 2).
6. **Scale-ceremony-by-points.** No gate-only (1–2 pt) story ever produced an escape; all serious findings came from full-pipeline stories. The split is correctly calibrated.
7. **Dual review on 3+ pt stories.** Not rubber stamps: ~13 of the first 22 sprints had ≥1 blocking finding; quality review was the single most valuable stage in the system.

---

## 2. Key Issues (ranked by cost incurred)

### Issue 1 — Verification verifies artifacts, not reality
The marquee failure class: **"green tests, wrong contract"** — 7+ incidents (S14, S17 rigged test, S19 uncommitted format, S20 over-mocked assembly, S21 deleted tests, S32 percent-scale, S42 catch-all 422). In S32, 146 green tests **and both Opus reviewers** validated the wrong scale, because plan, fixtures, and tests all encoded the same wrong assumption. Every major escape (S21→22, S32, S38 silent zero-ingest, S39) was ultimately caught only by a **live** check — and live checks exist today only as accreted amendments (2026-07-04, 2026-07-08), not as a pipeline stage. Reviewers verify internal consistency; nothing in the core pipeline verifies against reality.

### Issue 2 — The rulebook doesn't scale, and it violates the skill's own first principle
557 lines of append-only agreements bind every session and every subagent brief. Three distinct kinds are conflated:
- **Engineering conventions** (empty-input tests, `model_validator` invariants, five-file shape test, tz-aware 422s) — most of the file;
- **Process mechanics** (clean tree at dispatch, merge-last, fresh-agent fix loops) — patches for gaps in the skill itself;
- **One-shot exceptions** (sprint-42/43 external mode) — spent immediately.

The evidence is decisive that *prose rules under-perform mechanical ones here*: the five-file shape test was missed twice **despite explicit AC**; the identical unenforced-invariant MAJOR recurred three sprints running until a standing rule landed. The system's response to incidents is to write more prose an LLM must remember — the exact failure mode "mechanical gates over promises" was designed against.

### Issue 3 — Enforcement lives in prose, not machinery
Roughly a third of all amendments exist because the skill left orchestration mechanics unspecified, and each was written *after* the invariant failed once: implementer swept board state into a code commit (S1), implementer rewrote `sprint-current.yaml` (S4), commits landed on the default branch after a silent checkout failure (edge-case #12), merge preceded the compile pass (S18), gate ran on a dirty tree (S19). Every one of these is mechanically preventable with today's Claude Code primitives (hooks, per-agent tool allowlists) — none of which the skill uses.

### Issue 4 — Roles are informal: no model, tool, or output enforcement
The PO had to *mandate model tiering as a working agreement* (Sonnet implementers / Opus reviewers, 2026-06-24; Haiku scouts, 2026-07-09) because prompt-template dispatch carries no model binding. Reviewer verdicts are free text the orchestrator parses. The spec reviewer was the weak lane (PASSed S17's rigged test by name-matching) until prose rules hardened it. Real `.claude/agents/*.md` definitions with `model:`, `tools:` allowlists, and structured verdict schemas make all of this configuration instead of vigilance.

### Issue 5 — Mechanical work is done by hand
The orchestrator manually: runs 9 DoD commands and transcribes output tails/exit codes/SHAs into YAML; runs the staleness sweep (an agreement literally says "a small script over `docs/scrum/wiki/*.md`" — the script doesn't exist); lint-checks wiki links; adjudicates gate false-reds (6 contention incidents, each requiring a hand-crafted isolation proof). This is toil, a transcription-error risk, and context burned on bookkeeping.

### Issue 6 — Crash tolerance depends on unenforced discipline
Commit cadence is briefed, not enforced. S41: an implementer ran 1h28m with zero commits and lost everything. The twin wiki-pass stalls (S29, S31 — identical spot) had the same root cause: the cadence rule wasn't operative where it mattered.

### Issue 7 — One hardwired pipeline vs. observed reality
The project actually ran in at least five modes: in-process subagents, external implementer (S9–14 Gemini era, S42–43), parallel worktree waves (S38), a parked sprint (S35), and no-points debug sprints. All were bolted on via agreements or improvisation. PO-directive volatility (external ↔ in-process, twice) shows mode-switching must be cheap and first-class.

### Issue 8 — Ceremony weight is decoupled from value at the edges
Full plan/review/retro + wiki pass + evidence recording ran for single-3-pt-story sprints, while S38 pushed 31 points through the identical ceremony. Meanwhile capacity planning (mean-of-3 velocity) is theater — committed == accepted in 40 of 40 sprints because "sprint" is really "session," and the effort cap and `attempts` bookkeeping never once triggered in 43 sprints.

### Issue 9 — Minor frictions
Wiki no-op re-verifies via shared `code_refs` (`pyproject.toml` drift flags 3+ articles per touch); sprint records S23/24 erased entirely by a product revert (history should be revert-proof); `session.lock` and standup work fine but are unassisted.

---

## 3. Recommended Architecture

**Design principle: apply "mechanical gates over promises" to the process itself.**
Every lesson gets pushed *down* this enforcement ladder as far as it will go, and only the residue stays prose:

```
1. DoD gate command / CI contract      (import-linter, a standing pytest)
2. Script                              (gate runner, wiki sweep)
3. Hook                                (PreToolUse branch guard, path protection)
4. Agent definition                    (model, tool allowlist, output schema)
5. Reviewer checklist                  (versioned reference file, loaded by role)
6. Working agreement                   (true process rules only — the residue)
```

### Target layout

The skill relocates to **user level** (`~/.claude/skills/yourteam/`) so every project can use it;
project-local artifacts are **generated at inception** from templates inside the skill (move G).

```
~/.claude/skills/yourteam/
├── SKILL.md                     # orientation + lifecycle (stays ~150 lines)
├── references/
│   ├── ceremonies.md            # kept (minor updates)
│   ├── edge-cases.md            # kept, pruned of hook-covered items
│   ├── wiki-protocol.md         # kept
│   ├── state-files.md           # kept
│   ├── execution-modes.md       # NEW: in-process | external | parallel-waves | debug | parked
│   └── checklists/
│       ├── implementer.md       # NEW: conventions checklist (from agreements)
│       ├── spec-review.md       # NEW: incl. AC↔test trace requirements
│       └── quality-review.md    # NEW: incl. tests-that-lie taxonomy
├── scripts/
│   ├── yt_gate.py               # NEW: runs DoD, writes evidence YAML, contention protocol
│   └── yt_wiki.py               # NEW: staleness sweep + code_refs coverage lint + link lint
└── templates/                   # kept, plus:
    ├── agents/                  # NEW: source templates for the four yt-* definitions
    └── hooks/                   # NEW: hook scripts + settings.json fragments

# Per project, GENERATED at inception (versioned in the project's git):
.claude/agents/                  # NEW — real agent definitions
├── yt-implementer.md            #   model: sonnet, full tools, TDD + cadence rules
├── yt-spec-reviewer.md          #   model: opus, read-only + test execution
├── yt-quality-reviewer.md       #   model: opus, read-only + test execution
└── yt-scout.md                  #   model: haiku, read-only exploration

.claude/settings.json            # NEW hooks (merged in, never overwritten):
                                 #   branch guard (git commit only on sprint/hotfix branch)
                                 #   block `git add -A` / `-add .` in sprint context
                                 #   .scrum/ writes restricted to orchestrator

.scrum/                          # UNCHANGED schema; agreements file slimmed (see migration)
docs/scrum/                      # UNCHANGED
```

### The seven redesign moves

**A. Formalize the agents (Issue 4).** Convert the three prompt templates into `.claude/agents/` definitions carrying model, tool allowlist, and role instructions. Reviewers get read-only file tools + Bash for running tests — a reviewer *cannot* edit code, an implementer *cannot* write `.scrum/`. Briefs shrink to the variable part only (story file, plan steps, selected wiki facts, mode flags). Reviewer verdicts and implementer completion reports become **structured output** (schema-validated), ending free-text verdict parsing. The PO's model-tiering directives become configuration and leave the agreements file.

**B. Script the mechanical floor (Issue 5).** `yt_gate.py` runs every DoD command, captures exit codes/output tails, and writes the `dod_evidence` block itself — including the codified contention protocol (empty-diff proof + isolated re-run + flake ledger entry) that today requires judgment each time. `yt_wiki.py` implements the staleness sweep, the Fact-coverage lint (every cited file ∈ `code_refs` — currently a prose rule), and the link lint. Both are also DoD-visible commands, so the process's own checks live on the same floor as the product's.

**C. Convert prose invariants to hooks (Issue 3).** PreToolUse hooks enforce: commits only on the sprint/hotfix branch named in `sprint-current.yaml` (kills edge-case #12 permanently), no bulk staging, `.scrum/` writes only from the orchestrator session. Edge-cases that hooks now cover get pruned from prose. Hooks fail closed — they work even when a subagent never read the rule.

**D. Re-architect the rulebook (Issue 2).** One-time reclassification of all ~40 agreements down the enforcement ladder:
- Conventions with testable shape → standing tests/lints where possible (five-file shape, src-no-tests already prove this path works);
- Remaining conventions → the three role **checklists** (versioned, loaded by the agent that enforces them — this is where the S12/S13 evidence points: standing checklists beat per-story AC);
- Codebase facts → wiki articles (which already have `code_refs`-based relevance routing into briefs);
- Process mechanics → skill/reference text or hooks;
- True process agreements → a slim `working-agreements.md` (target: under ~80 lines).
The **retro protocol changes accordingly**: each proposed amendment must name its ladder rung; "append prose" becomes the last resort, not the default. This preserves "the process amends itself" while capping context growth.

**E. Make reality verification a pipeline stage (Issue 1 — the highest-value change).** A story is not Done until its **reality gate** passes, scaled by story type:
- Consumer/rendering stories: live render-vs-wire spot check (already an agreement; becomes a stage);
- Adapter/integration stories: live probe of the real vendor path, with full event-type distribution enumeration;
- Any story whose AC cannot execute inside review: **blocks or splits** — never ships on promise (the S21→S22 lesson, promoted from amendment to core rule);
- Fixtures must derive from a captured real sample, recorded alongside the story.
This closes the structural gap that dual Opus review cannot: reviewers check internal consistency; the reality gate checks the world.

**F. First-class execution modes and parallelism (Issues 6, 7, 8).**
- `execution-modes.md` defines in-process (default), external (plan-as-contract + post-hoc verification pipeline — exactly what S42/43 improvised), parallel-waves (worktree-isolated implementers with the mandatory branch-sync step 0; review fan-out runs concurrently), debug sprint (single-file record, no points), and parked sprint (board snapshot). Mode is declared per-sprint in `sprint-current.yaml` — one line, not a working agreement.
- Commit cadence becomes enforced: the implementer agent definition requires a commit per green step *and* the orchestrator checks `git log` recency at every board touch; a >30-min silent gap is treated as a stalled agent (kill, verify tree, fresh dispatch) — the S41 loss becomes impossible by construction.
- Capacity: drop mean-of-3 velocity as a planning input (it measured cadence, not capacity). Planning proposes scope by dependency/risk shape; `velocity.json` remains as a record. Drop `attempts` bookkeeping; keep the effort cap as a simple prose backstop.

**G. Self-bootstrapping installer (multi-project portability).** The skill lives at user level
and installs itself into any new project, extending the pattern inception already uses for
`.scrum/`:
- **Stays in the skill, never copied:** scripts and references. They are generic by
  construction — `yt_gate.py` reads the *project's* `.scrum/definition-of-done.md` at runtime —
  so one copy serves all projects and fixes propagate instantly.
- **Generated per project at inception:** `.claude/agents/yt-*.md` and the settings.json hook
  wiring, materialized from `templates/agents/` + `templates/hooks/`. Project-level copies are
  versioned in the project's git and parameterizable (model tiers, gate surfaces, hook
  strictness).
- **Bootstrap interview:** minimal — confirm model tiering defaults (Sonnet/Opus/Haiku) and hook
  strictness; everything else is defaults + the existing inception interview/conflict scan. The
  conflict scan extends to pre-existing `.claude/agents/` and hooks; settings.json is merged,
  never overwritten (same rule as CLAUDE.md).
- **Version stamps + drift check:** every generated file carries a `yourteam_version` marker; the
  standup compares it against the skill version and offers a PO-approved re-sync on upgrade —
  otherwise N projects means N silently divergent copies (the process-level "trusted-and-wrong").
- **Degradation:** PO declines settings changes or hooks unavailable → prose rules remain the
  fallback, noted once (mirrors edge-case #9).

### Concept adoption verdicts (as requested)

| Concept | Verdict |
|---|---|
| Orchestrator + specialist agents | **Adopt formally** — already de facto; make it real via agent definitions |
| Planner / executor / reviewer | **Already present** (planning ceremony / implementer / dual review). Keep. Do **not** add a ceremony-owning planner agent — planning is a PO dialogue, and the judgment half (selection, order, goal) never failed in 43 sprints. **Do add a plan verifier** (see agent table): every real planning failure (S32 units/scale, S34 false gap, S9/S10 edge under-spec) was a precision failure an adversarial pre-lock check would have caught |
| Memory files | **Restructure, don't multiply** — route lessons down the ladder; wiki keeps long-term knowledge (its provenance model is better than anything to replace it with) |
| Prompt modularization | **Adopt** — agent definitions + role checklists + thin variable briefs |
| Verification loops | **Adopt, aimed at reality** — the missing loop is live verification, not a third LLM reviewer; keep dual review as-is |
| Reusable components | **Adopt** — the two scripts + checklists + agent definitions make the skill portable to the next project |
| Autonomous workflows | **Qualified adopt** — Workflow-tool fan-out for parallel waves and concurrent reviews; the core story pipeline stays sequential (dependencies are real). No cron/background loops needed |
| Debate/consensus panels | **Reject for now** — dual review already catches internal-consistency issues; the escapes were reality-gaps, which panels don't close. Revisit only with evidence |

---

## 4. Proposed Agent Structure & Responsibilities

| Agent | Model | Tools | Responsibility | Output |
|---|---|---|---|---|
| **Orchestrator** (main session) | Session model (Opus-tier+) | All | Ceremonies, board & state ownership (sole `.scrum/` writer), brief assembly, dispatch, gate & reality-gate execution, wiki compile pass, PO interface | — |
| **yt-implementer** | Sonnet | Full (Edit/Write/Bash/…), worktree-capable | One story: TDD, commit-per-green-step, plan checkbox ticks, wiki blast-radius updates, self-run DoD before reporting | Structured report: steps+SHAs, gate results, wiki updates, candidate backlog items, or exact blocking question |
| **yt-spec-reviewer** | Opus | Read-only + Bash (run tests) | AC compliance only. Mandatory **AC↔test trace table**: per AC, the test that drives its named scenario and asserts its outcome (name-matching is not evidence — S17 rule, now structural) | Structured verdict: PASS/FAIL + per-AC {MET/NOT-MET/PARTIAL, evidence}, scope additions |
| **yt-quality-reviewer** | Opus | Read-only + Bash (run tests) | Code quality vs. `checklists/quality-review.md` (incl. the tests-that-lie taxonomy: rigged paths, over-mocking, silent deletion, fixture invention) | Structured verdict: APPROVE/FIX-REQUIRED + Critical/Major/Minor findings |
| **yt-scout** | Haiku | Read-only | Exploration/inventory for planning & refinement (codifies the 2026-07-09 tiering directive) | Findings summary |
| **yt-plan-verifier** | Opus | Read-only + Bash (live probes) | Adversarial pre-lock check of the drafted plan: units/scale cited from producing code per rendered numeric field; edge/error behavior stated per port method; claimed producer gaps proven by live failure-path probe; breakdown↔AC trace; external-mode plans carry the full conventions checklist. Converts the 2026-07-02/07-04/07-06 agreements into a role | Structured verdict: LOCK-READY/GAPS + per-check findings |

The plan verifier runs once per sprint at planning (after drafting, before the PO lock), not per
story. It is deliberately **not** a plan author: planning judgment stays with the orchestrator +
PO; the verifier only refutes. (Optional, low priority: in external mode, plan.md *drafting* may
be delegated to save orchestrator context — a convenience, not a quality gate.)

Pipeline per story (unchanged shape, hardened substance):
`implementer → [3+ pts: spec review ∥ quality review] → yt_gate.py → reality gate → board=done`.
Fix loops keep the fresh-agent rule and the 3-cycle ping-pong cap. Reviews of independent concerns run concurrently. Parallel-wave mode dispatches independent stories to worktree-isolated implementers with serial integration and a single gate at merge.

---

## 5. Migration Strategy

The redesign is skill-work, not product code — it runs outside product sprints, but versioned in git with the same evidence discipline.

1. **No state migration.** `.scrum/` schemas, story files, wiki, and history are untouched (drop `attempts` on the next sprint's board file only). Rollback = revert the skill directory; the running project never notices.
2. **Build v2 alongside v1.** Agent definitions, hooks, scripts, and checklists are additive files. SKILL.md edits come last. The relocation to `~/.claude/skills/` happens once v2 is stable in this repo; this project then becomes the first "already-bootstrapped" project (its generated files get version stamps retroactively).
3. **The reclassification pass** (agreements → ladder rungs) is the one delicate step: do it as an explicit mapping document the PO approves entry-by-entry (each of ~40 agreements → its new home or retirement), then execute. Removed text stays in git history per the existing prune convention.
4. **Pilot sprint.** Run one normal sprint on v2 in this repo. From the PO's seat, ceremonies are identical; what changes is enforcement substrate. The pilot's retro judges the redesign.
5. **Success criteria for the pilot:** zero prose-rule violations that a hook/allowlist should have caught; gate evidence written by script, byte-accurate; brief size measurably down (agreements payload replaced by checklists + routed wiki facts); one reality-gate execution recorded.

## 6. Prioritized Implementation Roadmap

| # | Work | Addresses | Effort | Why this order |
|---|---|---|---|---|
| **P0** | Agent definitions (4) + structured verdict/report schemas + thin-brief format | Issues 3, 4 | S | Highest leverage, purely additive, everything else builds on real roles |
| **P0** | `yt_gate.py` (DoD runner + evidence writer + contention protocol) | Issue 5 | M | Kills the largest toil + transcription risk; codifies flake handling |
| **P0** | Hooks: branch guard, staging scope, `.scrum/` write protection | Issues 3, 6 | S | Converts the three worst prose invariants into fail-closed machinery |
| **P1** | Rulebook reclassification (PO-approved mapping) + role checklists + retro-router protocol | Issue 2 | M | Needs P0 homes (checklists, hooks) to exist first |
| **P1** | Reality gate as a standing pipeline stage + fixtures-from-real-samples rule | Issue 1 | S–M | Biggest quality win; mostly promotion of proven amendments into core |
| **P1** | `yt_wiki.py` (sweep + coverage lint + link lint) + no-op re-verify fast path | Issues 5, 9 | S | Sweep is already specified by agreement; this just makes it real |
| **P1** | Self-bootstrapping installer: skill to user level, agent/hook templates, inception bootstrap, version stamps + standup drift check | Move G (multi-project goal) | M | Depends on P0 artifacts existing; makes the skill portable to the next project |
| **P2** | `yt-plan-verifier` agent + pre-lock planning stage | Issue 1 (front-of-pipe) | S | Checklist-driven; depends on P1 checklists; kills S32-class escapes before the sprint locks |
| **P2** | `execution-modes.md` (external / parallel-waves / debug / parked) + per-sprint mode flag | Issue 7 | M | Formalizes what S38/S42-43 improvised; includes worktree sync step-0 |
| **P2** | Commit-cadence enforcement (agent rule + orchestrator staleness check) | Issue 6 | S | Prevents the S41 class of loss |
| **P2** | Ceremony scaling: drop velocity-as-input, drop `attempts`, micro-sprint record format | Issue 8 | S | Low risk, removes theater |
| **P3** | Process self-test (skill smoke checklist + changelog), revert-proof ceremony records | Issue 9, evals gap | S | Nice-to-have hardening |

Estimated total: P0+P1 is the meaningful redesign (~1–2 focused sessions); P2–P3 are incremental.

---

*Implementation begins only after PO review and approval of this document.*
