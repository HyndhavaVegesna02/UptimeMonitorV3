# Sprint 70 — review

**2026-08-13 · branch `sprint-70` (from `sprint-69` HEAD `a360e50`, tagged `sprint-70-start`)**
**11 of 11 points delivered. Gate 8/8 green at the final HEAD: 800 passed / 0 skipped, contracts 9 kept / 0 broken.**

Suite grew 743 → 800 (+57 tests). Four of the five stories added a standing guard; the fifth added
the tool that checks guards.

## Goal, and whether it was met

> Every guard the audit shipped is complete and self-checking, and no claim in the catalogue
> outruns its citation.

**Met, with one honest qualification you should hear before accepting.** The two hand-maintained
crutches under shipped guards are gone, ZR-8's residue is re-affirmed and dated, and citation
resolution is now enforced in the gate. The qualification is STORY-219's scope: it enforces **15 of
129** citation failures, and that is by design — see below.

## Story by story

| Story | Pts | What landed | Verdict |
| --- | --: | --- | --- |
| STORY-217 | 1 | ZR-8 Finding 1 re-affirmed and dated; expiry condition re-derived by port import | Done, no production code |
| STORY-220 | 2 | ZR-1's forbidden-module completeness is now a test (set equality vs. disk) | Done |
| STORY-218 | 2 | `Settings` declares each default once; ZR-3's blind spot stated | Done, spec PASS + quality fixed |
| STORY-219 | 3 | Citation resolution enforced in pytest with a per-article ratchet | Done, spec PASS + quality fixed |
| STORY-212 | 3 | `tools/evidence_check.py` — the evidence rule at the SCRIPT rung | Done, after a CRITICAL fix round |

### STORY-217 — the expiry condition has not fired

Closed as a dated re-affirmation with **no production code**, which is what the story was sized for.
`git diff -- backend/src/` is 0 lines, verified by the orchestrator rather than self-reported. No
core service imports `ComponentRepository` or `SignalRepository`, so option (b) stands and ZR-8
Finding 1 now records the re-check date alongside its expiry condition.

### STORY-220 — ZR-1's completeness is mechanical now

A test asserts set equality between the `inbound-adapters-dont-persist` contract's nine forbidden
modules and the persistence ports discovered on disk. The prose sentence STORY-206 left ("maintained
by hand until STORY-220 lands") is gone.

**Reality gate finding:** the implementer's two shown-RED mutations both landed in the *same* branch
of the assertion — removing a contract entry while its file stays on disk produces the identical
message as adding a file, so `In the contract but not on disk` had never fired. The implementer
disclosed the collision rather than presenting two proofs. The orchestrator proved the second branch
separately.

### STORY-218 — the drift path is closed, and now pinned

Each default literal appears exactly once; `load_settings()` reads `Settings.<field>`. The forbidden
shapes were correctly avoided — both would have removed the class attribute `harness.py` depends on.
Per-field empty-string decisions are recorded in the code, and `CONFIG_DIR=""` deliberately stays
empty rather than falling back, so an operator gets a loud failure instead of a silent redirect to
the config carrying a **real** Statuspage component id.

Quality review returned one MAJOR (a line span citing `:755-768` when the block runs to `:771`,
truncating mid-sentence) and, more valuably, **found that nothing pinned the story's own central
invariant** — re-typing the literal back would have kept every test green until the next rename. The
new test is mutation-proven to be the only one that catches it.

### STORY-219 — enforced, and honest about how much

**It enforces 15 of 129 citation failures.** 113 are bare-filename citations routed to an advisory
list; 1 sits in a `tier: reference` article that is mechanically exempt. Content is verified only for
the 13 of 198 citations carrying an excerpt anchor, so **a wrong-but-in-range line number passes** —
the story's own motivating occurrence, `scripts/seed_topology.py:44`, is reported OK today and is
named in the test's docstring as the worked example.

Both reductions were approved at planning. The pre-lock verifier had already killed the story's
original mitigation, which was a no-op: it filtered on "has a line number" when the tool's regex makes
line numbers mandatory, so it removed 0 of 129.

Quality review then found the sharpest thing in the sprint: the docstring stating that scope carried
**a number this story's own edits had invalidated** (195 → 198), and it counted the passing subset
while describing the checked set. Fixed not with a better number but with a test that re-derives all
three live and reds on drift.

### STORY-212 — the tool that would have caught all of the above

`tools/evidence_check.py` with three subcommands: `falsify`, `two-sided`, `mutate`. Six retros named
this rung and declined it; both stated reasons were gone.

**It needed a fix round, and the finding was severe: the evidence checker had a false-GREEN.**
`mutate` scanned pytest output for lines whose second token is `FAILED`/`ERROR` — and pytest's
collection banner (`____ ERROR collecting test_x.py ____`) matches. So the most ordinary mutation
there is, renaming the symbol a test imports, reported `OK: mutation turned RED` with **zero tests
executed**, exit 0. Pytest's exit code was discarded, the one signal that would have caught it.

Five more MAJORs, every one probed rather than inferred: no baseline run, so "turned RED" could not be
told from "was already red"; the restore backstop vacuous for creation patches (`git diff` cannot see
untracked files); empty `--bad-input` a vacuous pass; and the isolation guard blind to the bare import
shape this repo uses everywhere, including inside the new tool.

All closed. **Re-proven by the orchestrator against the real tool, not its test suite:** the same
import-breaking mutation now returns `SELECTOR DID NOT RUN (pytest exit 2) … NOT a RED proof, and
distinct from ZERO RED`, exit 1.

The fix round also surfaced a defect nobody was looking for: running pytest twice against the same
files hit CPython's second-granularity `.pyc` mtime cache and silently reused **stale bytecode** — a
false result inside the proof mechanism itself.

## The one you should push back on if you disagree

**AC7's checklist edit, and the fact that I passed it.** STORY-212 was required to shrink the two
checklists because the tool now covers part of them. I reviewed that diff, saw every mechanic
preserved, and passed it. The quality reviewer found what I missed: the old rule said *mutate it
yourself*; the new one said *confirm the implementer pasted a tail*. That converts an independent
action into confirmation of someone else's artifact — a rule cut with no mechanical replacement,
which is the one thing AC7 forbids.

The review is its own proof: had it only confirmed a pasted tail, the CRITICAL and two MAJORs would
all have read as green tails. The clause is restored and came back stronger — *"a pasted tail is the
implementer's evidence, not yours."* Net shrink 241 → 235 lines, with independence intact.

## Deferred, unchanged from the plan

- **STORY-214** — the last ZR finding-residue (ZR-7's six duplicated pagination loops). Still has no
  story file; still trapped (extracting the helper turns all six compliant sites red). Write the file
  at sprint-71 refinement, size 3, and do not put it in a sprint that adds a new persistence call site.
- **STORY-211**, **STORY-213**, **STORY-221**, **STORY-179** — unchanged, reasons in `plan.md`.

## Filed during the sprint, for sprint-71 refinement

1. **Content-anchor coverage** — only 13 of 198 citations carry the excerpt anchor needed to check
   content. This is the real fix for the drift class STORY-219 was filed against, and it is bigger
   than STORY-219 was.
2. **`citation_gate.py:53`'s bare literal `3`** → `len(_FM_DELIM)`. Declined mid-sprint only because
   it cascades into the ZR-3 ledger and the catalogue count. It would shrink a permanent exemption list.
3. **Rehabilitate or tombstone the three stale articles** — `core-pipeline-and-availability.md`,
   `deployment-and-infra.md`, `frontend-zone.md`. Deliberately quarantined at sprint-69 close
   (`3303c6c`) as honestly unverified, not fresh rot. Re-verifying their Facts is its own story.
4. **A `count` check for evidence** — see the retro; a count used as evidence must name its exclusions.

## Wiki

Sweep, facts, links and integrity all CLEAN at the final HEAD. **14 map-tier articles, 3 reference.**
The map tier did not grow this sprint — new knowledge went to tests (`test_citation_gate.py`,
`test_zr1_forbidden_list_completeness.py`, `test_evidence_check.py`) and to the two checklists, which
is routing row 1 working as intended.
