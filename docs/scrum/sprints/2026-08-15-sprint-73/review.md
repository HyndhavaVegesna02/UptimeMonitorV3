# Sprint 73 — Review

**Goal:** *Equilibrium: the dead feature is gone, and the backlog shrinks.*

**Committed 13 points. Delivered 13 points, 3 of 3 stories.** Branch `sprint-73`, final HEAD
`b55cc74`, gate **9/9 green**, tree clean.

This is the highest figure this team has delivered. Velocity was 11, 10, 11, 11, 10, 8 — and the
plan said plainly at lock that 13 was *"two points above the highest figure this team has ever
delivered."* That risk was stated before the sprint, not discovered here.

**Nothing is merged.** Sprints 66–73 all stay unmerged; acceptance at this review is acceptance of
the *work*, not authorisation to touch `main`.

---

## The goal, measured

| Equilibrium test (PO directive `38d628f`) | Result |
| --- | --- |
| 1. Nothing lies | **Six false claims corrected**, five of them found by review, not by the author |
| 2. Nothing is half-landed | **The atomic pair landed WHOLE** — see the pause below |
| 3. What remains is chosen | Backlog **14 open → 11** |

`sample_mode` — the largest single piece of dead weight in the codebase, 41 code files across two
toolchains, declared TEMPORARY by PO directive on 2026-07-03 — **is gone**, and its wiki article is
a tombstone rather than a deletion.

---

## Story 1 — STORY-147 (3 pts): component `group` + `description`

The story the PO asked for by name (*"i want 147"*), scheduled first for exactly that reason.

- **Spec: PASS** — six AC, every one traced to a test the reviewer *ran*, none inspection-only.
- **Quality: REQUEST CHANGES → one MAJOR, fixed.** The code itself was called clean and
  zone-correct with no changes asked.
- **Gate: 9/9 at `4b8501e`**, pytest 851 passed / 0 skipped.

**The MAJOR is worth reading.** `test_citation_gate.py` — the guard that exists to stop wiki numbers
rotting — carried a stale count of its own (186, live value 178), *and* a sentence claiming
*"re-derives all three live, so this sentence cannot go stale silently again"* while that fourth
number was the one thing nothing asserted. A staleness guard lying about its own coverage is worse
than no guard. The fix made the claim **true** (the test now asserts all four) rather than narrowing
it.

**Reality gate.** The HTTP tests use `FakeComponentRepository`, so the full chain had never run in
one process. Against the real composition root and real DynamoDB Local: `group: "Commerce"` in YAML
arrived as `"commerce"` over HTTP, and a component declaring neither field returned `null`, not
`""`. Both AC2 and AC3's negative clause proven past the fake seam.

## Story 2 — STORY-155a (3 pts): `sample_mode` out of the frontend

- **Spec: PASS** — six AC. The reviewer **re-derived the test-count delta itself** (30 removed /
  1 added) rather than trusting the report.
- **Quality: REQUEST CHANGES → one MAJOR, fixed.**
- **Gate: 9/9 at `f6ce2c6`**, npm 51 files/363 tests → 49/334, delta itemised.

**The MAJOR:** dead CSS the removal itself created. `top-bar__` was left with exactly one live
consumer while four rule blocks survived — including one the implementer's own candidates list
missed. It had knowingly left them, arguing they were outside AC2's grep; that is the argument *for*
removing them, since nothing later could ever find them.

**Reality gate.** For a removal story the real question is the shipped artifact: the **built bundle**
(`dist/*.js` and `*.css`) contains **zero** sample-mode references.

## Story 3 — STORY-155b (7 pts): `sample_mode` out of the backend, article tombstoned

The largest story in the sprint — 11 AC, 29 commits, nine `tier: map` articles that A18 forced
re-verified in-story.

- **Spec: FAIL → MET after the fix round.** Ten AC met on the first pass; **AC11 not met on its
  second clause.**
- **Quality: REQUEST CHANGES → one MAJOR, fixed.**
- **Gate: 9/9 at `b55cc74`**, pytest **831 passed / 0 skipped** (from 851; −20, accounted exactly).

**AC1 is the one to be pleased about.** It justified the 7-point estimate, and the story named its
own cheap fake in advance: after removal, the existing `isinstance` assertion becomes a one-word
edit proving nothing. That path was not taken. Quality **reconstructed the deleted module from the
pre-removal commit in a scratch directory**, re-ran the same harness with the decorator in place,
and confirmed the committed "before" literal matches **field-for-field**. Spec separately mutated
`health_mapping` to flip `UP`→`DOWN` and watched the test go red. Real captured evidence,
independently falsified.

**The spec FAIL:** AC11 requires *"state before/after and account for the delta exactly."* The
number was right and the gate green, but the statement did not exist — `851` and `831` appeared
nowhere in the story file. A commit deferred it, nothing delivered it, and the checkbox was ticked
anyway. On a deletion story that narrative is the artifact proving coverage did not quietly vanish.

**The quality MAJOR:** `docs/project-history.md` still called `sample_mode` *"inert"* with
*"Removal is STORY-155"* — and `CLAUDE.md` routes readers to that file **naming `sample_mode`**,
while this same story had already fixed the identical sentence in `CLAUDE.md` itself.

**Reality gate.** Against the real composition root and real DynamoDB, `CONFIG_DIR=config/demo`,
without launching the loop: `GET` and `PUT /api/v1/sample-mode` → **404**, `/components` and
`/health` → **200**. The route is genuinely gone at the real HTTP surface, and the app boots now
that the composition root no longer builds the removed repository — which is the actual risk, since
`SampleModeIngest` was a **live decorator over the ingest front door** in both composition roots.

---

## The pause, and why the pair landed whole

Mid-sprint the session window hit 82%. STORY-155b was untouched. Rather than start a 7-point story
that certainly could not finish, the sprint **paused with a committed handoff** — which is what the
board's atomicity rule required, because closing with 155a done and 155b outstanding would have left
`sample_mode` half-removed, failing the sprint's own goal. The window reset, 155b was dispatched,
and **the pair landed together**. The rule did its job.

## What review caught that the authors did not

Every story needed exactly one fix round, and **each MAJOR was something the implementer's own
self-report missed or misjudged**. Concurrent spec + quality is paying for itself:

- a staleness guard carrying a stale number *and* a false "cannot go stale" label
- dead CSS created by the removal, one rule of which the author's own list omitted
- a stale claim in the doc `CLAUDE.md` names as the authority, whose sibling the same story had fixed
- a ticked AC checkbox with no deliverable behind it
- a false port count (`ten`, actually eleven) restated by a re-verification, which converts inherited
  drift into a claim this story owns

Two corrections went the other way, which is worth recording: **the work corrected the story files.**
155a's demotion reason established that **eight** `code_refs` moved, not the nine the story claimed;
and the orchestrator's pre-dispatch measurement found the story's own citation (`:212`) stale before
155b started.

---

## Blockers

**None.** No story was blocked at any point.

## Decisions for the PO

1. **Accept / reject each story.**
2. **Eleven quality minors are carried, unfixed and unfiled** — they are design questions, not
   defects, and the equilibrium directive is explicit that filing is not free. They are recorded
   per-story under `carried_to_po_at_review` in `.scrum/sprint-current.yaml`. The three most
   substantive:
   - the validation error echoes the **normalized** group, so an author who typed `"Not Valid!"` is
     shown `"not valid!"` and cannot grep their own YAML;
   - `description: ""` is accepted while `group: ""` is rejected — an asymmetry the UI must
     special-case;
   - `_EXPECTED_ROUTE_TABLE` pins route paths but **not HTTP methods**, so a method change on a
     surviving route would pass unnoticed.
3. **Merging.** Sprints 66–73 remain unmerged. That is now eight sprints of work off `main` and it
   is a standing decision only the PO can change.

## Two facts for the next planning

- **No story is `ready`.** All 11 open items are 7 `draft` + 4 `blocked`. **Sprint 74 cannot be
  planned without a refinement pass first** — there is currently nothing that satisfies the
  Definition of Ready.
- **STORY-192 must be re-measured before it is sized.** Archiving `sample-mode.md` removed roughly
  110–142 of its mojibake sequences; carrying it at its filed size would overstate it.
