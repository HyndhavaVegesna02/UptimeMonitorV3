# Ceremony Protocols

Read this file when entering any ceremony. Each section is the executable protocol; SKILL.md only orients.

## Table of Contents
1. Inception
2. Backlog Refinement
3. Sprint Planning
4. Sprint Execution Order Rules
5. Sprint Review
6. Retrospective
7. Sprint Abort
8. Hotfix Protocol

---

## 1. Inception

Runs once, when no `.scrum/` exists.

**For a fresh project:**
1. Ask about: target users, the core problem, must-have features, platform (web/mobile/CLI), stack preference, constraints. One question at a time; multiple choice where possible.
2. Inventory the environment: available MCP servers, CLIs, test runners, language toolchains. This becomes the CLAUDE.md tooling section.
3. Draft and present for approval, in this order:
   - **Initial backlog** — break the vision into stories. Fully refine the top 3–5 (AC + estimates); leave the rest as `status: draft` one-liners. Do NOT write an upfront mega-spec; depth lives in per-story refinement.
   - **Starter Definition of Done** — concrete commands for the chosen stack (test, lint, build), each with expected exit code 0. Include the CLAUDE.md-maintenance rule (see templates/definition-of-done.md).
   - **Default working agreements** (see templates/working-agreements.md).
4. On approval, commit the `.scrum/` files and proceed to Sprint 0.

**For an existing codebase:**
1. Explore first: README, structure, recent commits, existing CLAUDE.md, test setup.
2. Same interview, but grounded ("I see Express + Jest — keep that?"). Capture the observed coding conventions — naming, structure, error handling, test patterns — into a `wiki/conventions.md` article (with `code_refs` to representative files) so every future subagent brief carries them. Present it to the PO with the rest of the inception output.
3. **Conflict scan (mandatory):** read existing CLAUDE.md, AGENTS.md, and any agent config. List every instruction that contradicts YourTeam mechanics (e.g., "commit directly to main" vs branch-per-sprint, existing commit/PR conventions vs story commits, "always do X first" vs the standup). Because the PO's files outrank this skill, unresolved conflicts would silently disable parts of the methodology — so each one must be resolved explicitly at inception: the PO either amends the conflicting line or records a sanctioned exception in working-agreements.md. Never proceed to Sprint 0 with unresolved conflicts.
4. Offer one optional extra: **wiki seeding** — a pass writing initial verified articles for core modules (each with `code_refs` and current `verified_sha`). PO may skip; the wiki then grows organically from sprint 1.
5. CLAUDE.md handling: append the YourTeam section only. Never rewrite existing content. If AGENTS.md exists (other agents work on this repo), append the same pointer section there too — agents that don't know about `.scrum/` would otherwise commit outside the sprint flow.
6. **Bootstrap the project-local machinery** (both fresh and existing projects), from the skill's `templates/`:
   - Copy `templates/agents/yt-*.md` → `.claude/agents/` (confirm model tiers with the PO: default Sonnet implementer / Opus reviewers + verifier / Haiku scout).
   - Copy `templates/hooks/yt_git_guard.py` → `.claude/hooks/` and **merge** the hooks block from `templates/hooks/settings-fragment.json` into `.claude/settings.json` — never overwrite an existing file; the conflict scan (step 3) covers pre-existing agents and hooks. PO confirms, since hooks affect permission behavior.
   - Copy `templates/checklists/` → `.scrum/checklists/` (project-conventions sections start empty; they grow via retro routing).
   - Every generated file keeps its `yourteam_version` marker; the standup drift-check compares it against the skill version and offers a PO-approved re-sync after skill upgrades.
   - PO declines hooks, or the environment can't run them → prose rules are the fallback; note the degradation once.

**Sprint 0** follows immediately: scaffold, test harness, CI, `.scrum/` files, CLAUDE.md. It is a real sprint — branch `sprint-0`, DoD applies, ends with a review where the PO sees a running skeleton with green tests.

## 2. Backlog Refinement

Happens anytime, in any session, regardless of sprint state. A mid-sprint idea is captured instantly ("Added to the backlog") and refined now or later — refinement never touches sprint scope.

Per story:
1. Draft `docs/scrum/stories/STORY-NNN-slug.md` from the template: context, description, acceptance criteria, open questions.
2. AC must be **testable** — each criterion phrased so it can become a test or a checkable command. "Works well" is not AC; "GET /habits returns 200 with an empty list when none exist" is.
3. Estimate: fibonacci 1, 2, 3, 5, 8. Complexity, not hours. An 8 means "split me" — propose the split; an 8 can never enter a sprint.
4. High blast radius bumps the estimate: if the story's likely files are referenced by many wiki articles, that's load-bearing code — raise the points and note it (this also forces the full review pipeline).
5. Present to PO. Approved → `status: ready` in backlog.yaml. **Definition of Ready: approved AC + estimate + zero unresolved questions.**

Defect stories: repro steps in context, the fix expressed as AC ("given X, Y no longer happens"). Severity decides path — normal defects wait for planning; critical ones take the Hotfix Protocol.

## 3. Sprint Planning

1. Shape scope to one focused session: `velocity.json` is a sanity reference (what recent
   sprints actually delivered), never a formula. No history → under-commit deliberately
   (2–3 small stories). Never exceed a comfortable session's shape on hope.
2. Select `ready` stories by: PO priority order first, then dependency feasibility within the sprint.
3. Draft `docs/scrum/sprints/YYYY-MM-DD-sprint-N/plan.md`: per story, the task breakdown as
   checkbox steps (2–5 minutes each, TDD-shaped: write failing test / see it fail / minimal
   code / see it pass / commit), a "Verified API contracts" section for consumer stories, and
   the proposed execution mode (see references/execution-modes.md).
4. **Dispatch `yt-plan-verifier`** with the draft plan + story files. It refutes: units/scale
   uncited from producing code, unproven producer-gap claims, unstated edge behavior, missing
   fixture provenance, breakdown↔AC holes, informally deferred live ACs. Fix every GAP before
   the PO sees the plan; re-dispatch until LOCK_READY. (This kills the wrong-assumption class
   at the cheapest point — before anything is built on it.)
5. Propose to the PO in one message:
   - **Sprint goal** (one sentence)
   - **Stories** with points, and the **execution mode**
   - **Execution order with reasoning** (see section 4 below)
   - **Tooling gaps**, if any: "Story N would benefit from X MCP — install it, or I work around it?" This is one of only two moments tooling may change (the other is retro).
6. PO may reorder, swap, or trim. Approval is required; planning is selection, never authoring — un-ready stories cannot be added on the spot (refine them first, even if that takes five minutes right now).
7. On approval, verify preconditions: working tree clean (else commit/stash with the PO) and DoD commands green on main via `yt_gate.py` (else "restore green baseline" is the mandatory first story — see edge-cases.md #1, #9). Then, **in this order — cut the branch BEFORE writing the board, and never chain a checkout with a commit** (the git-guard hook reads `sprint-current.yaml` and blocks commits made off the named branch; writing `branch:` first then chaining checkout+commit triggers it — found live at the sprint-44 lock):
   - `git checkout main && git checkout -b sprint-N && git tag sprint-N-start` (no commit in this chain)
   - Write `sprint-current.yaml` (goal, mode, stories, board all `todo`, lock metadata)
   - Commit the lock records as a separate command, already on `sprint-N`
   - Announce the lock: "Sprint N is locked. See you at review."

## 4. Sprint Execution Order Rules

Order stories by, in priority:
1. **Dependencies** — prerequisites first, always.
2. **Risk** — high-blast-radius or uncertain stories early, so a blocker leaves time to finish the rest.
3. **Momentum** — stories touching files just worked on are cheaper while context is fresh (reverse blast radius makes this visible).
4. **Size** — smaller first among equals; early Done states improve crash recovery.

## 5. Sprint Review

Preconditions: every story Done or Blocked; each Done story's **reality-gate evidence recorded** (live render-vs-wire spot check for consumer/rendering stories, live vendor-path probe for adapter stories, no AC deferred informally — a story whose live path never ran is not Done); the sprint branch rebased onto current main with full DoD re-run if main moved (edge-cases.md #2); inter-story commit dependencies checked so mixed verdicts don't cherry-pick through a dependency (edge-cases.md #3); AND the wiki compile pass has run (it blocks review — see wiki-protocol.md; `yt_wiki.py` must exit 0).

1. Prepare `review.md` in the sprint folder: per story — what was built, AC checklist with evidence (test output, DoD records from sprint-current.yaml), demo steps.
2. Demo live where possible: run the app, execute the commands, show output. Evidence over claims.
3. Per story, the PO gives one of exactly two verdicts:
   - **Accept** → merge its commits to main. Minor nitpicks → still accept, capture nitpicks as a follow-up story. There is no partial-accept state.
   - **Reject** → story returns to backlog `status: ready` with the PO's feedback appended to the story file; its commits stay on the sprint branch, off main.
4. Present Blocked stories with their exact questions; answers go into the story file; story returns to backlog, re-estimated if the answer changed scope.
5. Record accepted points into velocity.json. Returned stories get re-estimated with what was learned.
6. After all verdicts: merge accepted work to main (whole branch if everything accepted; cherry-pick story commits if mixed — new SHAs! — and ALSO apply the ceremony/state commits, which are records exempt from verdicts; verify the sprint folder exists on the default branch — edge-cases.md #11), then re-stamp the verified_sha of every wiki article verified this sprint to the resulting main commit (edge-cases.md #4), delete or keep the sprint branch per PO preference, freeze the sprint folder.

## 6. Retrospective

Runs immediately after review. Inputs: blockers hit, effort-cap trips, estimate vs actual per story, reviewer rejection loops, hotfixes taken, wiki drift stats (articles stale ≥3 sprints), recurring tooling friction.

1. Report honestly: what went well, what dragged, with the specific incidents.
2. Propose **1–2** concrete amendments — not five. Each must be actionable and checkable. ("AC for list features must include the empty state" — good. "Be more careful" — useless.)
3. **Route each proposal down the enforcement ladder and name its rung:** DoD command / standing test → script (`yt_gate.py` / `yt_wiki.py` change) → hook → agent definition → `.scrum/checklists/` item → prose in `working-agreements.md`. Prose is the last resort — a lesson that can be a mechanical check becomes one. Checklist items carry the same date + motivating-incident provenance as agreements.
4. Recurring tooling friction → propose an install here (the second of the two allowed moments).
5. PO approves/rejects each. Approved → land it at its named rung. Rejected → note it; don't re-propose next sprint unless new evidence.
6. Write `retro.md`, freeze the sprint folder. Future sessions obey the new rules from their next standup.

## 7. Sprint Abort

Only the PO triggers this, explicitly. Confirm before acting — this is destructive.

Present the three options with what each means concretely:
1. **Discard everything** — `git checkout main; git branch -D sprint-N`. Main untouched, total undo.
2. **Keep done stories only** — cherry-pick Done stories' commits to main (their separate commits make this clean), drop the rest.
3. **Keep all work unmerged** — branch stays for reference.

Then: all non-merged stories return to the backlog, sprint folder gets an `aborted.md` noting the reason, velocity records only merged points. The abort reason is mandatory retro input.

## 8. Hotfix Protocol

For critical breakage only (production down, or the current sprint is built on the broken code). Normal bugs become defect stories and wait for planning.

1. Pause the in-progress story at its last green commit; note the pause in sprint-current.yaml.
2. `git checkout main && git checkout -b hotfix/slug`
3. Fix with TDD; the full DoD gate applies — a hotfix is not an excuse to skip the floor.
4. Merge to main. Rebase the sprint branch onto main. Resume the paused story.
5. Log the hotfix in sprint-current.yaml. The retro must address why it escaped: `git bisect` against story commits identifies which story introduced it, and whether its AC had a gap ("no error-path AC") becomes amendment material.
