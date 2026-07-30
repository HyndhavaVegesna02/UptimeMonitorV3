# Sprint 65 — Retro

**Date:** 2026-07-30 · **Amendments A9 and A10 PO-approved and landed at their rungs.**

Process, not product. The product verdict is in `review.md`.

## Velocity

| Sprint | 62 | 63 | 64 | 65 |
| --- | --- | --- | --- | --- |
| Accepted | 9 | 7 | 8 | **13** |

13 was above the PO's stated ~9–11 baseline and **it showed — not in dropped scope, but in rework.**
Three of five stories needed a fix round and STORY-191's was large. The sprint still delivered 13/13,
so the honest read is that the size was absorbable but bought less margin than it looked: the fix
rounds happened to be tractable, not cheap.

## What worked, and is worth keeping

**The delivery contract's rule 2 paid for itself outright.** The external delivery reported
"implemented, verified with unit/integration tests, committed" and listed `pytest` plus two
reality-gate scripts. The orchestrator's own gate run was **RED**: 22 `ruff` errors including
`F821 Undefined name 'httpx'`, plus 12 unformatted files. The rule exists because sprint 47's
delivery self-reported "all nine gates clean" while carrying two MAJORs; this is the second time it
has caught the same shape. **Do not soften it.**

**Both reviewers caught defects the orchestrator had personally accepted.** That is the single
strongest piece of evidence for external mode's "both reviewers on EVERY story regardless of size",
which looked like pure overhead when the mode was chosen. Cutting it would have shipped a tautology
and a test that asserted nothing.

**The plan-verifier prevented a worse sprint than it appeared to.** Its 16 blocking GAPS included
that the plan's central publish mechanism was **impossible** (a `DOWN`→`UP` ladder cannot publish
from a seeded `OPERATIONAL` baseline) and that `build_live_loop` calls `run_periodic`, not
`run_cycle` — the latter would have wired quarantine into nothing while every test passed. Both were
caught before a single line was written.

**Cutting scope at verification, for structural reasons rather than sizing.** STORY-186 and
STORY-189 were removed because they collide with STORY-191 over the same files. That decision
removed two fix-round risks and kept the point total unchanged.

## What cost the most, in order

### 1. Dead code in a proof harness — the through-line of this sprint

STORY-191's delivery added an `extra_scenarios` seam to `harness.py` **that nothing called**, and in
the same commit deleted `import httpx` while 9 call sites remained. The harness could not run at all.
It failed **silently**: `NameError` is an `Exception`, so the polling helper's `except Exception: pass`
swallowed it and returned `False` after burning the timeout.

The two facts are causally linked: **the seam being uncalled is exactly why nobody noticed the broken
import.** A proof harness that is never executed is indistinguishable from one that works.

This is the same shape as sprint 64's STORY-182 round 1 ("the harness REPORTED rather than
ENFORCED"), which produced amendment A7. A7 was necessary but not sufficient — it governs what an
artifact must do *when run*, and says nothing about whether it is run.

### 2. Two defective tests, both past the orchestrator's own review

- STORY-190 AC3's "pre-fix stall" test built a `watermark_repo`, never passed it to anything, called
  `normalize_rows` directly, then asserted the watermark was still `None` — true whether or not
  anything raised. It reproduced nothing.
- STORY-191's backward-compat test asserted `len(scenarios) > 0` and `isinstance(rows, list)` on a
  function already annotated `-> list[dict]`. The quality reviewer exposed it by **mutation**:
  making the legacy branch emit `DOWN` — silently turning every existing scenario DOWN — left it
  green.

Both took a full review round to find and **minutes** to catch once someone asked "could this test
fail?". That gap is what A9 closes.

### 3. Orchestrator errors, at real cost

- **Two full ~4-minute runs lost** to a precondition that passed **vacuously**: it wrote a component
  status to a hand-rolled DynamoDB key and read it back from *the same hand-rolled key*. The key
  shape was wrong, so the write hit a phantom item and the read-back confirmed itself. Production
  correctly did nothing, and the gate blamed the feature.
- **A wrong first theory** (orchestrate-window timing) drove a component change before the real cause
  was found. Harmless, and its arithmetic is now documented as a genuine constraint — but it was not
  the bug, and diagnosing by hypothesis-then-change cost a run.
- **The "13 damaged sites" figure was a double-count**, from measuring with `errors="replace"` (which
  converts each invalid byte *into* a `U+FFFD`). The plan verifier "independently reproduced" the bad
  table by repeating the same method. **Reproducing a measurement is not validating it** — worth
  remembering the next time a verifier confirms a number.
- **I corrupted the sprint board** by doing exactly what the skill instructs: pasting `yt_gate.py`'s
  evidence fragment verbatim. That is a tooling defect, and A10 fixes it.

### 4. Wiki re-stamping churn

The blast-radius protocol worked, but required **two** rounds of re-verification because later fix
commits touched the same `code_refs`. Not a defect — the cost of doing it correctly mid-fix-round.
Noted so it is expected rather than surprising.

## Amendments (PO-approved 2026-07-30)

### A9 — the "shown failing" rule extends from artifacts to TESTS · rung: CHECKLIST

Landed in `.scrum/checklists/implementer.md` and `.scrum/checklists/spec-review.md`.

A test that is a story's primary evidence for a defect fix must be **demonstrated failing** — against
the pre-fix behaviour or a deliberate mutation of the code it guards — and that demonstration
recorded. Two concrete smells are named: a fixture that is constructed but never wired up (the test
asserts on a value it supplied itself), and "if I broke the guarded behaviour, would this go red?".
The spec-review side makes the answer a **verdict condition**: if you cannot say yes, it is `NOT_MET`,
not `MET`-with-a-note.

A9 also carries a second, narrower rule from the vacuous precondition: **if a proof sets up state, it
must set that state up and read it back through the same production interface the system under test
uses**, never a parallel hand-rolled implementation.

**Why checklist and not lower:** no script can detect a tautological assertion — it requires knowing
what the test is *for*. Both defective tests would have been caught in minutes by a human applying
this. It sits directly alongside A7, which it widens.

### A10 — `yt_gate.py` sanitises its emitted evidence · rung: SCRIPT

`one_line_tail` now strips ANSI escape sequences and C0 control characters before slicing, so the
`dod_evidence` fragment the skill tells you to merge **verbatim** is always valid YAML. Two guards
added to `test_yt_gate.py`, and both were **shown failing** with the fix reverted (`yt_selftest`
28→**32** across the sprint).

**Why script and not a checklist warning:** the hazard is created by the skill's own instruction, and
it is fully generic — any project whose build tool colourises output hits it. Removing the failure
beats warning each project about it.

## Deliberately NOT amended

- **The external-delivery contract.** It worked exactly as designed. The cost was one fix round,
  which is the expected price, not a process failure.
- **Anything about proof-harness invocation.** Tempting after finding #1, but A9 plus the existing A7
  cover the observable symptom, and a rule like "every artifact must be executed" would need a
  project-specific registry to enforce — the wrong rung for a generic skill. Revisit if it recurs.
- **The 13-point sizing.** The PO chose it knowingly with a pre-agreed drop order. Recorded as a
  data point for planning, not legislated.

## Carried into sprint-66 planning

1. **⚠ RAISE THE BOUNDARY/CODE-DISCIPLINE AUDIT SPRINT.** The PO asked explicitly to be reminded
   (memory: `wanted-architecture-audit-sprint`). It came directly out of learning that an inbound
   adapter persisting via a core port passes all eight contracts while being wrong — so if one such
   gap exists, others are probably already in the tree. Its deliverable is findings plus mechanical
   guards, with any non-trivial fix filed as its own story. **Raise it every planning until it is
   scheduled or explicitly dropped.**
2. **STORY-186** and **STORY-189** — cut from this sprint for collision with STORY-191; both carry
   recorded corrections to fold in when refined (186's "seven rejection tests" is 11; 189's
   `missing_cycles` is `gap_verdicts`, and its `demo-engine.md` finding is a Fact rewrite, not a
   `code_refs` addition).
3. **STORY-192** — `docs/scrum/wiki/` carries the same em-dash corruption in a shape STORY-188's
   guard cannot detect (valid UTF-8 carrying mojibake). 246 sequences, 6 files.
4. **STORY-193** — proposal formation is not reliably assertable in a loop run; the fix direction is
   a longer-interval failure scenario or a deterministic anchor, explicitly **not** widening the
   anti-flap window (that is production logic).
5. **STORY-178** (`yt_gate.py` exits 0 when `--only` matches nothing) stayed unscheduled and was a
   standing caveat on every scoped run this sprint. It is now the only known false-green on the DoD
   floor.
