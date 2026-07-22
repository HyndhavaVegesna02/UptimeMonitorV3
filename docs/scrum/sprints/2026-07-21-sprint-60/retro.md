# Sprint 60 — Retro

**Outcome:** 5/5 stories accepted, 20/20 pts (velocity +20 — the highest single-sprint accepted total
on record, vs ~9 prior). Mode pivoted external→in-process after the PO rejected the external
delivery; the in-process pipeline held. Accepted unmerged (ui-prototype line).

## What went well
- **In-process pipeline caught real defects.** Every 3-pointer ran implementer → spec ∥ quality →
  DoD gate → reality gate. The reality gate earned its cost twice: it caught the STORY-130 duplicate
  row-key corruption (below) and drove the full live create→delete cycle on STORY-132.
- **Crash/limit recovery was lossless.** A mid-sprint session usage-cap kill (STORY-133) lost nothing —
  board + git state let work resume cleanly after reset. Commit-per-green-step + board-as-truth worked.
- **Reviewers were genuinely adversarial** (forced 409/404/422 tests, order-sensitive mapping proven
  3 ways, tests-that-lie taxonomy applied) — 0 critical / 0 major across all reviewed stories.

## What didn't (incidents → lessons)
1. **The reality gate caught what BOTH reviewers missed (STORY-130).** Spec PASS + quality APPROVE,
   yet the quality review explicitly dismissed the merged-row-key collision as *"not realistic on the
   wire."* It WAS on the wire — live `/history` has duplicate `(signal_key, observed_at, location)`
   triples → React key collision → visibly corrupted filtered rendering (168 rows, wrong per-location
   counts). Reviewers reason about internal consistency; only the live gate saw reality. This is the
   single most important process signal of the sprint.
2. **`yt_gate.py` reports a false RED on this machine.** The Windows Device Guard / Application Control
   policy that has blocked `lint-imports.exe` since 2026-07-12 also blocks `pytest.exe` and
   `cfn-lint.exe`. The full sprint-close gate came back RED purely from those two blocked shims —
   the code was green (proven via `python -m pytest` → 529 passed, `cfnlint.runner:main` → exit 0).
   A gate that cries wolf erodes the "exit codes cannot be rationalized" principle.
3. **The greenfield rebuild silently dropped a feature (sample mode).** Noticed only by the PO at
   review, not by any story or checklist. Filed as STORY-135 (draft, next sprint) — but the *process*
   let a removed consumer go unrecorded until a human spotted it.

## Estimate accuracy
Estimates held (5/3/5/5/2 all delivered). The 20-pt scope (vs ~9 velocity) was the PO's explicit
owned choice and was met — but note it required an in-process re-implementation after an external
reject, so raw throughput was higher than one delivery cycle implies.

---

## Proposed amendments (each routed down the enforcement ladder — PO approval needed)

### A1 — Route the DoD's blocked `.exe` commands to their module/callable form *(rung: gate command / DoD file — mechanical)*
`.scrum/definition-of-done.md` currently runs `pytest` and `cfn-lint infra/stack.yaml` via the `.exe`
shims, which Device Guard blocks → false RED. Change them to the invocation forms that already work
(mirroring the documented `lint-imports` workaround):
- `pytest` → `python -m pytest`
- `cfn-lint infra/stack.yaml` → `python -c "import sys; sys.argv=['cfn-lint','infra/stack.yaml']; from cfnlint.runner import main; sys.exit(main())"`

This makes `yt_gate.py` green-on-green-code on this machine and removes a recurring false RED. Lowest
rung that holds it (a command string change), highest leverage. **This is the priority amendment.**

### A2 — Reality-gate checklist: verify keyed/list rendering against REAL wire cardinality *(rung: checklist item)*
Add to `.scrum/checklists/` (reality-gate section, cross-ref the tests-that-lie taxonomy): *"For any
list/table/keyed rendering, verify identity/uniqueness against REAL wire data at real cardinality —
duplicates are possible even when a field looks unique. A review claim that a collision is 'not
realistic on the wire' is not evidence; the reality gate must confirm on live data (real duplicates,
real row counts), not just fixtures."* Motivating incident: STORY-130 (above). Turns a near-miss into
a standing check without adding a gate command.

*(Considered a third — a rebuild-dropped-feature inventory checklist item for greenfield rewrites —
but that lesson is narrow to this one initiative; leaving it as an observation, not an amendment,
unless the PO wants it landed.)*

## PO decision (2026-07-22): ALL THREE APPROVED — landed
- **A1** → `.scrum/definition-of-done.md`: `pytest`→`python -m pytest`; `cfn-lint …`→ the
  `cfnlint.runner:main` callable form (Device-Guard `.exe`-block workaround, dated notes).
- **A2** → `.scrum/checklists/quality-review.md`: new tests-that-lie taxonomy member #8
  "Fixture-cardinality gap / 'not realistic on the wire'".
- **A3** → `.scrum/checklists/implementer.md`: Process-discipline item — a rebuild that drops a
  user-facing consumer records it + files a follow-up (backing feature existing is not an excuse).
Each carries its date + motivating incident. Sprint 60 closed.
