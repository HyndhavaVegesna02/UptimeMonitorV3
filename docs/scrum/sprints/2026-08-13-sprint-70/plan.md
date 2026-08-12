# Sprint 70 — plan (PROPOSED, not locked)

**Dates:** 2026-08-13 · **Branch:** `sprint-70` from `sprint-69` HEAD (`a360e50`) · **Mode:** in-process
**Committed:** 11 points, 5 stories · **Baseline velocity:** 11, 11, 10, 11 over sprints 66–69

## Goal

Every guard the audit shipped is complete and self-checking, and no claim in the catalogue outruns
its citation. Sprint 69 gave all eight zone rules a terminal verdict; this sprint closes the
*residue* those verdicts left behind — the two places where a shipped guard still rests on a
sentence a human must remember, and the one place where the catalogue's own `file:line` citations
are unenforced. It also lands the evidence-artifact rule at the SCRIPT rung, which the PO directed
at the sprint-69 review after six retros named that rung and declined it.

At close, the `process-ratchet-brake` epic drops from 9 open to 4, and no ZR finding-residue remains
except ZR-7's pagination extraction (STORY-214), which is deferred with a reason below.

## Scope

| # | Story | Pts | Type | What it closes |
| - | ----- | --: | ---- | -------------- |
| 1 | STORY-217 — topology write port: re-affirm or expire | 1 | chore | ZR-8 Finding 1 residue |
| 2 | STORY-220 — ZR-1 forbidden-list completeness test | 2 | chore | ZR-1's prose maintenance note |
| 3 | STORY-218 — Settings declares every default twice | 2 | chore | ZR-3's `src`-internal blind spot |
| 4 | STORY-219 — wire citation resolution into the gate | 3 | chore | five sprint-68 occurrences; 129 unenforced citations |
| 5 | STORY-212 — evidence-artifact rule at the SCRIPT rung | 3 | chore | RC-1/RC-7, three occurrences in sprint 69 |

**Total 11 points** — inside the PO's 9–11 pacing band, matching four consecutive sprints.

## Execution order, and why it is not negotiable

Ordered cheapest-first *looks* like momentum sequencing; it is not. The binding constraint is that
**three stories edit `docs/scrum/wiki/zone-rules.md`, and STORY-219 freezes that file's citation
count into a committed baseline.**

- STORY-217 AC2 appends a dated re-affirmation to ZR-8 Finding 1.
- STORY-220 AC7 rewrites the ZR-1 row and deletes STORY-206's "maintained by hand" sentence.
- STORY-219 AC3 commits a per-article citation baseline, `zone-rules.md` included.

If 219 ran first, 217 and 220 would each move `zone-rules.md`'s count and fail 219's own ratchet —
each would then have to lower a baseline it did not author, which is exactly the "edit the guard to
satisfy the change" shape sprint 69's AC6 forbade. **So all `zone-rules.md` edits land before the
baseline is measured.** 217 → 220 → 218 → 219.

STORY-212 runs **last** for a different reason: its AC7 amends
`.scrum/checklists/implementer.md` and `quality-review.md`. Landing it mid-sprint would change the
rules under this sprint's own remaining stories, so it goes after the last story that must obey the
current ones.

STORY-218 sits at position 3 for a reason the first draft of this plan got **wrong**. It is not
"independent of the wiki chain" — plan verification proved the opposite. STORY-218 edits three files
that are cited BY LINE from the wiki: `settings.py:21-22` (cited at `zone-rules.md:309, :415` and
`zone-rules-history.md:518, :532, :564`) where AC1 edits exactly lines 20-22; `harness.py` (cited at
`zone-rules.md:517, :913` and five places in `zone-rules-history.md`) where AC6 edits the comment at
`:755-761`, directly above them; and `test_settings.py:30`, which carries one of only **eight
anchor-checked citations repo-wide** (`zone-rules-history.md:185`) — and AC3 adds tests to that file.
`settings.py` and `harness.py` are both in `zone-rules.md`'s `code_refs`.

So 218 is squarely inside the chain, and the real constraint is: **it shifts lines in three
line-cited files, one of them anchor-checked, so it must land before STORY-219 measures the
baseline.** Position 3 is correct; the original justification was not.

## Deferred, with reasons — so nobody re-litigates them mid-sprint

- **STORY-214** (extract the pagination loop, rework the ZR-7 guard) — the last ZR finding-residue,
  and deliberately not here. It has **no story file at all**, so it is not Definition-of-Ready. It is
  also trapped: extracting the helper turns all six compliant call sites RED, forcing the guard
  rework into the same change. The risk is latent, not realised — STORY-199's reviewer diffed all
  five copies against the reference character by character and found zero divergence. Write the story
  file at sprint-71 refinement and size it 3. **It must not share a sprint with any story adding a
  new persistence call site**, or the guard rework and the new site will mask each other. Sprint 70
  adds none.
- **STORY-211** (plan on context and token budget) — PO-deferred explicitly ("i will take it up
  later"), unchanged.
- **STORY-213** (1-in-11 pagination flake) — did not fire in sprint 68 **or** sprint 69. Per the
  sprint-69 board, re-price against the measured 1-in-11, never against the quiet streak. Still
  filed, still 2, not scheduled.
- **STORY-221** (frontend gate flake) — unestimated; refinement must first reproduce it on demand and
  measure a hit rate, the way STORY-213's was measured. Pinning `--no-file-parallelism` is not free:
  measured 205s serialized vs 93s parallel.
- **STORY-179** (`dynamo_local` ephemeral port) — **mis-scoped, flagged at sprint-69 park.** Its
  documented workaround (point `DYNAMO_ENDPOINT_URL` at a fixed-port container) cannot help
  `test_provide_dynamo_local_teardown_on_failure`, which deliberately unsets that variable to force a
  container spawn. Re-scope before it is ever scheduled.

## Refinement performed at this planning (2026-08-13)

Three of the five stories had no acceptance criteria — "Refinement should settle" sections only, so
none was Definition-of-Ready. AC were authored today and are **pending PO approval**:

- **STORY-217** — AC1–AC6. AC1 re-derives the expiry condition mechanically at sprint-70 HEAD rather
  than trusting the 2026-08-05 answer; **AC3 makes a positive result a BLOCK, not a silent conversion**
  into a 3+ point port story inside a locked sprint.
- **STORY-218** — AC1–AC8. AC4 is the interesting one: the proof is the defect itself, run forwards —
  rename the single surviving default and show the blocklist follows, where before the fix the same
  rename left the suite green and the blocklist guarding a dead name.
- **STORY-219** — AC1–AC9, estimate 3 confirmed. See the re-measurement below.

**STORY-212 sized 3** (eight AC, a new tool with three subcommands, self-application under AC5, plus
the checklist amendments) — and **both its open questions resolved**, which plan verification showed
was not optional: it was not Definition-of-Ready, because `mutate`'s mutation format is the entire
interface of one of the three subcommands and was unresolved in the story, the backlog *and* the
plan. Settled: **a patch file** applied and reverted with `git apply` / `git apply -R`, chosen
because it is the only one of the three options that cannot half-apply silently and the only one
that expresses the multi-line mutations this project's proofs actually use; and **`tools/`, not the
skill's `scripts/`**, settled by AC6's requirement to reuse the project-local
`import_provenance.py::assert_import_root`.

**STORY-220** already carried AC1–AC7 from sprint-69 plan verification — but two of them had gone
stale in the eight days since, which is the argument for re-verifying rather than trusting a prior
pass. See the verification section.

### New measurement that changes STORY-219's shape

Re-measured all 17 wiki articles at `a360e50`: **129 citation failures, up from 124 at sprint-69
planning.** The rise is not new drift — it is the yourteam-2.3.0 wiki split: `zone-rules.md` fell
28 → 18 and the new `zone-rules-history.md` carries 15. The split moved citations rather than
resolving them.

That surfaces a question nobody has answered: `zone-rules-history.md` is `tier: reference`, and
reference articles are exempt from the staleness sweep because they carry no `code_refs`. Whether
they are also exempt from *citation resolution* is a separate question, and it binds immediately —
reference tier is where this project now puts its History sections, and 15 of the 129 are already
there.

**Plan verification then answered the question rather than leaving it open.** The first draft of
AC6 said "either answer is acceptable". That was wrong: `references/wiki-protocol.md:21` already
defines reference tier as "append-only, cites no live line", and `:56` says an article that wants to
cite code IS a map article. All 15 failures are citations into *history* — claims about past state,
which a tool resolving against HEAD cannot judge. And AC4's ratchet on an append-only article would
go RED on the next appended entry, forcing its author to move a baseline they did not set — the exact
shape this sprint's ordering exists to prevent. **AC6 now exempts `tier: reference` mechanically,
read from frontmatter, never a hand-listed filename.**

## Risks

1. **STORY-219 is red on arrival if the shape is wrong, and its first mitigation was a no-op.**
   Enforcing all 129 absolutely would fail the gate the moment it lands. The original AC2 claimed
   that enforcing only line-numbered citations would quarantine the tool's three documented
   false-positive classes; **plan verification proved that false** — `citation_sweep.py:41-44` makes
   the line number mandatory in `CITATION_RE`, so 129 of 129 failures carry one and the filter
   removed nothing. AC2 has been rewritten to filter on **path resolvability**, which is what
   actually discriminates (124 of the 129 are bare filenames that do carry line numbers).
   **What keeps this story green is the AC3/AC4 per-article ratchet, not AC2.** If the shape still
   cannot go green, the story blocks — it does not ship with the tool disabled.

   **Related scope correction, and the more important one.** The verifier established that the tool
   enforces less than the story assumed: content is checked only where a parenthesized excerpt anchor
   exists — **8 of 195 citations repo-wide** — so a wrong-but-in-range line number PASSES. The
   decisive proof is that the story's own motivating occurrence (v), `scripts/seed_topology.py:44`,
   is reported OK today. STORY-219 therefore buys a real floor against the dominant class (124
   unresolvable paths, matching the 146 unchecked Facts `yt_wiki.py` independently reports) but is
   **not** the fix for in-range line drift. AC1 now says so in the test's own docstring, and
   content-anchor coverage is filed as a sprint-71 follow-up rather than smuggled in at 3 points.
2. **STORY-217 may find the expiry condition fired.** Then it is a 3+ point core-owned port story,
   not a 1. AC3 handles this by blocking rather than growing. Sprint loses 1 point, not 3.
3. **STORY-218 touches the boot path of both composition roots** — `run.py::main` and
   `app.py::create_app`'s lifespan seed. A regression is a startup regression in two processes.
   `test_settings.py` already pins the resolved values before the change starts.
4. **STORY-212's AC5 (the tool subjected to its own rule) can spiral.** Cap it at the three
   non-bespoke checks named in the story — exit-non-zero-on-bad-input, sides-differ,
   mutation-turns-something-red. It does not claim to judge a reality gate.

## Definition of Done

Unchanged — the 8-command gate in `.scrum/definition-of-done.md`, run by
`python .claude/skills/yourteam/scripts/yt_gate.py`. Per-story gates MAY be `--only` scoped
mid-sprint; the **full** 8/8 gate at the final HEAD is the evidence of record.

Gate preconditions for this sprint: `DYNAMO_ENDPOINT_URL=http://127.0.0.1:8021` and
`REQUIRE_DYNAMO=1` on every run. A wrong endpoint under `REQUIRE_DYNAMO=1` ERRORS rather than skips —
it looks like a code red and is a setup error.

## Green baseline, verified 2026-08-13 at `a360e50`

Recorded because the checklist requires a plan to state it rather than assume it. Measured during
plan verification, not asserted:

- `python -m pytest` — **743 passed, 0 skipped** (65.9s) under `REQUIRE_DYNAMO=1` and
  `DYNAMO_ENDPOINT_URL=http://127.0.0.1:8021`. Zero skips is the point: a nonzero skip count is an
  incomplete gate, not a pass.
- import-linter — **9 contracts kept, 0 broken**.
- `ruff check .` clean; `ruff format --check .` — 254 files already formatted.
- Not run at planning: the three frontend commands and cfn-lint. The full 8/8 gate is the evidence of
  record at sprint close.

**Clean-tree precondition:** `yt_gate.py` refuses a dirty tree by design (agreement 2026-06-29). The
planning artifacts — this file, the four story files, `backlog.yaml` — are committed at lock, before
the first dispatch.

## Plan verification — verdict GAPS, 20 findings, all closed before the PO saw this plan

Dispatched because the sprint is contract-sensitive: STORY-219 changes what the DoD gate accepts and
STORY-218 changes env-var resolution on two boot paths. **The third reason originally given —
"STORY-217 edits an adjudication row that STORY-216's parser guards" — was itself wrong** and is
withdrawn: AC2 appends to ZR-8's body at `:736-767`, and the Adjudication row is at `:878`.

Two findings would have cost real time, and both are cases of a story's own evidence being weaker
than its prose:

- **F1 — STORY-219 AC2 was a no-op** (129 → 129), and Risk 1 asserted it as the mitigation. An
  implementer would have written the filter, measured no change, and had to redesign the story
  mid-sprint against a locked estimate.
- **F4/F2 — STORY-219 AC7 was unsatisfiable.** It required fixing two known-real drifts to LOWER
  `config-layer.md`'s baseline; both report **OK** today (the em-dash excerpt form at `:271-272` is
  not read as an anchor), so the fix moves the count by zero. The AC could never have passed.

The rest, closed in the story files: STORY-217's ZR-8 citation was 100 lines stale after the wiki
split (`:671-678` → `:736`) and its AC1 used a token grep that cannot decide its own condition;
STORY-218 carried **three wrong line citations inside the sprint about citation accuracy**, and its
"converge on `config_dir`'s shape" note would have removed the class attribute `harness.py:763`
depends on, making its own AC4 unsatisfiable; STORY-220 AC7 required bumping `verified_sha`, a field
deleted repo-wide the day before (`d9319d8`), and its `≥ 9` floor would go red on STORY-155's
legitimate port removal; STORY-212 was **not Definition-of-Ready** — its `mutate` mutation format, the
entire interface of one of three subcommands, was unresolved in story, backlog and plan.

**Verified PASS, no change needed:** STORY-219's 129-failure measurement reproduced exactly;
STORY-220's discovery rule reproduces `pyproject.toml`'s nine entries entry-for-entry with the three
excluded modules matching neither rule; and **STORY-217's expiry condition has NOT fired** — no core
service imports `ComponentRepository` or `SignalRepository`, so the sprint is not oversized. The
execution order 217 → 220 → 218 → 219 → 212 was independently confirmed correct, including that
STORY-212 has no wiki exposure at position 5.
