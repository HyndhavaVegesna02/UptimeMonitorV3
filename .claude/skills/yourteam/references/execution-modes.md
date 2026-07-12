# Execution Modes

<!-- yourteam_version: 2.0.0 -->

Who implements this sprint, and how the pipeline adapts around that. The mode is declared
per sprint in `sprint-current.yaml` (`mode:` field) as part of what the PO approves at lock —
one line, never a working-agreement amendment. Default: `in-process`.

**Invariant across ALL modes:** the DoD gate (`scripts/yt_gate.py`), PO acceptance at review,
main-is-sacred, story files + append-only history, wiki blast radius, and the reality gate.
Modes change who writes code and how reviews are scheduled — never what Done means.

## 1. `in-process` (default)

The orchestrator dispatches **yt-implementer** per story; 3+ pt stories get **yt-spec-reviewer**
and **yt-quality-reviewer** (the two reviews are independent and may run concurrently). Briefs
are thin: the story file, plan steps, verified wiki Facts, sprint branch, mode flags — the agent
definitions carry the roles.

## 2. `external`

The PO implements via an external AI agent building to `plan.md` alone.

- `plan.md` is the full contract: self-contained, conventions checklist embedded, edge behavior
  per method explicit, docstring deliverables named. **yt-plan-verifier** checks exactly this
  before lock (external implementers build literally and infer nothing).
- The external agent works ONLY on the sprint branch and never merges to main.
- The orchestrator does planning, board-keeping, and **post-implementation verification**:
  yt-spec-reviewer + yt-quality-reviewer per story regardless of size, plus an independent
  `yt_gate.py` re-run, before any story goes `board: done`. (History: external mode reliably
  ships ~1 MAJOR per 3-pt story — self-review blind spots; the review stage is never skipped.)

## 3. `parallel-waves`

For sprints with several independent stories (no shared files, no dependency edges).

- Group independent stories into waves. Per wave, dispatch worktree-isolated **yt-implementer**
  agents concurrently.
- **Step 0 in every worktree brief: `git merge <sprint-branch>`** — a worktree is cut from the
  branch BASE, not its tip; skipping the sync builds on a stale foundation.
- Integration is serial: one story merges to the sprint branch at a time; `yt_gate.py` runs at
  each integration. Reviews for different stories run concurrently.
- Never run two DB-gated gate invocations at once (agreement 2026-07-02) — the serial
  integration point is where the gate runs.

## 4. `debug` (no-points record)

For investigation/firefighting that isn't a story: create
`docs/scrum/sprints/YYYY-MM-DD-debug-<slug>/report.md` — one file holding intent, findings, and
outcome; no points, no velocity entry, no plan/review/retro triple. Code changes that emerge
become stories or a hotfix — the debug record itself never ships production code.

## 5. `parked`

PO pauses a sprint mid-flight (not an abort):

1. Snapshot the board to `paused-board.yaml` in the sprint folder with the pause reason.
2. Set `status: parked` in `sprint-current.yaml`; the sprint branch stays as-is.
3. Other work may proceed from main. Resume = restore the board, re-run the standup
   reconciliation (edge-case #2 applies if main moved), continue.
