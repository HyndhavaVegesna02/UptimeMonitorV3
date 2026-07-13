# Sprint 45 Retro — 2026-07-13

Process inspection (not product). Sprint accepted 6/6.

## What went well
- The **reality gate earned its keep**: it exercised the genuinely un-mocked paths that unit tests
  structurally can't — the codebase's first `DELETE` verb (204/404 live) and the derive-on-read
  author join (live `author` == DB `approval_events.actor`). Nothing was broken, but "never ships on
  promise" held.
- **Plan-verifier round-1 hardening paid off**: the correlated-scalar-subquery mandate (no LEFT JOIN
  row multiplication) and the "title must actually RENDER on the row" assertion meant zero rework on
  those axes.

## Friction + root causes
1. **`dev_db` container-contention flake recurred** (1/570 on the first gate run) — now a per-sprint
   tax (43/44/45). Root cause: open **STORY-080** (dev_db CLI hardcoded port); dev_db-lifecycle tests
   spawn their own containers and contend when another DB is up. Proven benign each time (empty diff
   since cut + isolation pass), but it costs real close-out effort.
2. **`PYTHONUTF8=1` not baked into `yt_gate.py`** — import-linter's rich banner crashed the Windows
   cp1252 pipe writer; the orchestrator had to remember to export it. Flagged in a prior retro; still
   manual.
3. **git-guard hook shipped a bare relative path** (`python .claude/hooks/yt_git_guard.py`) — broke
   every shell after a CWD moved off the repo root (`cd frontend`) and blocked the close-out mid-flight.
4. **`origin/HEAD` stale** — points at `debug/ingest-stall-sample-mode` (293 commits behind `main`),
   which is why the harness mislabeled the PR base. `main` is the true YourTeam mainline (sprint-45
   forked from its tip).

## Amendments (routed down the enforcement ladder)
| # | Rung | Amendment | PO verdict |
|---|------|-----------|-----------|
| A | script | Bake `PYTHONUTF8=1` into `yt_gate.py`'s subprocess env (`env.setdefault`) | **APPROVED — landed** (this retro) |
| B | script/test | Auto-skip/serialize dev_db-lifecycle tests when an external dev_db is present + bump STORY-080 | Deferred (not approved this retro) |
| C | template | Carry the `$CLAUDE_PROJECT_DIR` git-guard fix into the skill `templates/` | Deferred |
| D | housekeeping | `git remote set-head origin main` to repoint the stale default | Deferred |

### A — landed
`.claude/skills/yourteam/scripts/yt_gate.py`: after building the subprocess `env`, add
`env.setdefault("PYTHONUTF8", "1")` (an explicit export still wins). Verified: with `PYTHONUTF8`
unset, `yt_gate.py --only lint_imports` now PASSES (8 contracts kept) where it previously crashed;
`yt_selftest.py` 28/28 green.

### Notes on deferred items
- **B/STORY-080** remains open in the backlog; the flake stays "prove-benign per the 2026-07-06
  agreement" until then.
- **C** was already fixed in THIS project at `f53819e`; only the skill-template propagation is deferred.
- **D** is a one-command housekeeping fix the PO can run anytime.
