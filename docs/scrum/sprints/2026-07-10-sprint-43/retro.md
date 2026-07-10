# Sprint 43 Retro — harden the gate + name the read side

- **Date:** 2026-07-11
- **Committed / accepted:** 8 / 8 pts. Three stories, no blocks, no hotfixes, no scope changes. Both 3-pt stories needed a one-round review fix loop; the 2-pt story was clean.

## What went well
- **STORY-073 retired a recurring tax.** The flaky Docker-lifecycle gate had degraded the DoD signal in sprints 41 AND 42 (forcing a manual contention-proof + `--ignore` carve-out each time). It's now genuinely deterministic — the orchestrator ran the canonical `pytest` (no `--ignore`) 3× at implementation and 2× at re-verify, all green including the lifecycle tests.
- **The two-Opus review caught two blocking MAJORs the green gates hid — again.** All six gates were green on the external agent's work, yet review found M1 (an import-time crash in the dev_db harness) and M2 (5 stale doc pointers contradicting STORY-078's own grep-proof claim). This is the third consecutive sprint (41 verify, 42, 43) where adversarial review added value beyond the mechanical floor.
- **Verifying the fix mechanism paid off twice.** For M1 the orchestrator *reproduced* the import crash before calling it blocking; for STORY-078 the "pure move" was confirmed byte-identical via `git show` old-vs-new. Neither was taken on faith.
- **The fix loop found MORE than asked.** Beyond M1/M2 + the folded MINORs (m3 docstring, m4 shared-helper, m5 test), it caught a pre-existing `migrations-and-db.md` wiki drift un-bumped since sprint 30.

## What was bumpy
- **Both external-implementation 3-pt stories shipped a MAJOR that gates couldn't catch** — same pattern as sprint 42's STORY-075. The external agent optimizes for a green suite; the gaps are (a) robustness on config/edge inputs it doesn't test (M1), and (b) completeness claims that a shallow grep "confirms" but doesn't actually satisfy (M2). Both are *self-review blind spots*, not capability gaps.
- **STORY-078's completion note asserted "grep-proof, no reference remains" while 5 references remained** — a claim stated more confidently than the evidence supported. The grep was run for the import form only.

## Amendments proposed
1. **A story whose AC or completion claim says "grep-proof / no X remains anywhere" must paste the EXACT grep command AND its (empty) output into the story History — for BOTH the dotted-import and slash-path forms where a path is involved.** A claim of exhaustiveness is only as good as the pattern behind it; STORY-078's grep matched imports but missed prose path references. (Motivated by Sprint 43, STORY-078 M2: the completion note claimed grep-proof removal while 5 slash-path doc references survived, because the grep used the dotted form only.) — *PO decision pending at next planning.*
2. **A story that introduces or changes a config knob parsed at import/module scope must (a) parse it defensively (never an unguarded cast) and (b) ship a test for the missing/empty/invalid case.** (Motivated by Sprint 43, STORY-073 M1: a module-scope `float(os.environ[...])` crashed pytest collection on a bad value — in the very harness the story hardens — and had zero coverage.) — *PO decision pending.*

## Working-agreement changes
The sprint-43 external-implementation continuation (2026-07-10) was again a per-sprint PO directive; it lapses now. The 2026-07-02 in-process implementer rule is the default for sprint 44 unless the PO renews external mode. The two amendments above are proposed for `working-agreements.md` on PO approval.

## Carry-forward
- No follow-up stories needed — the fix loop cleared every MINOR (m3/m4/m5) in-sprint.
- The `core/queries/` read side is now real and fenced; the FURTHER read-model steps (read-optimized query ports, C's read/write feature contracts, the `api/dependencies.py` ApprovalService decoupling) remain deferred per proposal §8 and are only triggered by a measured need / aggregation endpoint.
