# Edge Cases & Failure Modes

Read this when something doesn't fit the happy path. Each rule exists because the naive behavior corrupts state, blocks forever, or silently breaks an invariant.

## 1. Red baseline (the DoD can never pass)

A sprint must start from green. At **planning**, before creating the branch: run the DoD commands on main. Any failure → the sprint cannot start; "restore green baseline" becomes the mandatory first story (or the PO explicitly amends the DoD).

At **inception on an existing project** with failing tests: do not write a DoD the project can't meet. Options to present: (a) Sprint 0 includes a fix-the-suite story, (b) temporarily scope the test gate to files the story touches, with a backlog story to restore the full gate. Never silently ignore failures — that trains everyone that red is normal.

## 2. Main moved during the sprint

Someone (the PO, another human, a hotfix) pushed to main mid-sprint. Before the review: rebase the sprint branch onto main. Conflicts are resolved by the team, then **re-run the full DoD for every Done story** — a clean rebase can still break behavior. Evidence in sprint-current.yaml is refreshed. Only then call the review. A review against a stale main produces merges that break.

## 3. Mixed verdicts with dependent commits

PO accepts story B but rejects story A, and B's commits build on A's changes. Cherry-picking B alone will conflict or silently carry A's code. At review, before asking for verdicts, check inter-story commit dependencies (`git log --stat` overlap). If B depends on A, tell the PO *before* they decide: "B is built on A — reject both, accept both, or I rework B standalone next sprint." Never cherry-pick through a dependency silently.

## 4. Cherry-picks invalidate wiki SHAs

Cherry-picked commits get **new SHAs on main**; if the sprint branch is then deleted, every `verified_sha` stamped during the sprint may point at a commit that no longer exists — and the staleness check (`git diff <sha>..HEAD`) errors out. At **sprint close**, after the merge: re-stamp every article verified this sprint with the resulting main commit. An unresolvable `verified_sha` is treated as `stale` (quarantine), never as verified.

## 5. Scope explosion mid-story

The implementer discovers a 2-pointer is really an 8 (missing schema, hidden coupling). Do not grind against the effort cap. The implementer reports the discovery; the orchestrator immediately marks the story Blocked with reason "needs re-split: <what was found>", reverts to the story's start commit if partial work doesn't stand alone, and moves on. At review the story returns for re-refinement. Burning attempts on a mis-sized story wastes the sprint.

## 6. Cascading blocks

Story C depends on blocked story B → C is Blocked too, reason "depends on STORY-B". The all-blocked escape hatch counts cascades: if every remaining story is blocked (directly or by cascade), ask the PO now.

## 7. PO volunteers a blocker answer mid-sprint

The blocked protocol defers questions to review — but if the PO *initiates* an answer mid-sprint (they saw the board, they interrupt with the decision), that is not a scope change: record the answer in the story file, unblock, resume. The lock keeps the team from *pulling* the PO in; it never blocks the PO from *pushing* a decision.

## 8. Review ping-pong cap

Implementer ↔ reviewer disagreement can loop. Hard cap: **3 review cycles per story per reviewer stage.** Hitting the cap → story is Blocked with both positions summarized; the PO arbitrates at review (or immediately if it's the last story). A fourth identical review round never converges.

## 9. Environment prerequisites

- **No git repo** (existing project not under version control): inception must `git init` + initial commit before anything else, with PO confirmation. YourTeam without git has no undo, no blast radius, no recovery — refuse to run without it.
- **Dirty working tree at planning**: require clean (commit or stash with the PO) before cutting the sprint branch. A dirty tree contaminates story commits and breaks abort guarantees.
- **No subagent capability** (environment without a Task/agent tool): run the same pipeline inline — read each `.claude/agents/yt-*.md` role definition and its `.scrum/checklists/` file as your own checklist for that stage, same DoD gate, same evidence. The roles survive even when the isolation doesn't; note the degradation to the PO once.
- **Corrupted/unparseable state YAML at standup**: reconstruct from the durable sources — git log (story commits), plan.md checkboxes, and the last valid git-committed version of the YAML. State files are committed precisely so corruption is always recoverable.

## 10. Default branch is not "main"

Older repos use `master`; some use `trunk` or `develop`. Detect once at inception — `git symbolic-ref refs/remotes/origin/HEAD` or the current branch on a fresh clone — record it in CLAUDE.md ("Default branch: master"), and use it everywhere this methodology says "main." Hardcoding "main" silently breaks merge, rebase, hotfix, and abort on such repos. (Found live while testing on TinyDB.)

## 11. Mixed-verdict close loses the sprint records

Cherry-picking only accepted stories means the sprint's ceremony commits — plan.md, review.md, retro.md, state file updates — stay on the sprint branch and never reach the default branch. Whole-branch merges carry them automatically; cherry-picks do not. At sprint close under mixed verdicts: after cherry-picking accepted story commits, also apply the ceremony/state commits (they are records, not code — they are never subject to verdicts). Verify `docs/scrum/sprints/<this-sprint>/` exists on the default branch before deleting the sprint branch. (Found live during testing.)

## 12. Silent branch failure → commits land on the default branch

A failed `git checkout -b` (scripting error, hook failure, detached HEAD) followed by commits violates main-is-sacred without any error surfacing. Rule: **verify the current branch before every commit** — `git branch --show-current` must equal the sprint (or hotfix) branch named in sprint-current.yaml; mismatch → stop, do not commit, repair state first. **v2: `.claude/hooks/yt_git_guard.py` enforces this mechanically** (blocks wrong-branch commits and bulk staging during an active sprint) — the prose rule remains as the fallback for environments without hooks. Recovery if violated: create the sprint branch at current HEAD (preserving work), hard-reset the default branch to its pre-sprint commit, continue on the branch. (Found live: a test-runner's progress output broke a shell chain, branch creation silently skipped, an entire story committed to master.)
