# Sprint 68 — Plan

**Status:** PROPOSED, awaiting PO approval. Not locked.
**Mode:** in-process · **Branch:** `sprint-68`, cut from `sprint-67` · **Points:** 10 · **Stories:** 4

---

## Goal

Close the sprint-66 audit's **live boundary violations** — the code that is wrong today, not the
guards for code that is clean. `ZR-8`'s two findings (a key schema declared three times on the boot
path of both composition roots; a vendor query builder living in the wrong zone without its
validation) and `ZR-3`'s remaining value and name duplications.

The success measure is mechanical, because sprint 66 built it: every unfixed entry in
`test_zr3_duplicate_declarations.py::_ADJUDICATED` names the story meant to remove it, and the
guard's stale-entry check goes RED if a fix lands while its entry stays. **Sprint 68 takes
`MUST-IMPORT-FROM-SRC` entries from four to zero** and gives `ZR-8` its first standing guard.

## The two-sprint closure map (the PO's framing: "full audit implementations in 2 sprints")

Nine stories, 20 points, ~10 per sprint — against a recent velocity of 9 / 7 / 8 / 13 / 11 / 11.

| | Sprint 68 — **fix what is broken** | Sprint 69 — **guard what is clean** |
| --- | --- | --- |
| | STORY-205 · `ZR-8` seed_dynamo key schema (3) | STORY-206 · `ZR-1` import contract (2) |
| | STORY-204 · `ZR-8` vendor_health DQL builder (2) | STORY-207 · `ZR-2` vendor-vocabulary AST walk (2) |
| | STORY-203 · `ZR-3` four value duplications (2) | STORY-208 · `ZR-4` five-file feature shape (1) |
| | STORY-215 · `ZR-3` env-var-name remainder (3) | STORY-209 · `ZR-5` CONFIG_DIR parity (2) |
| | | STORY-216 · mechanise `ENFORCED-BY` (3) |
| **Total** | **10** | **10** |

**Why this split and not an even mix.** The sprint-69 four are all *clean-tree* rules — there is no
violation to catch, so each must be proven by mutation rather than by demonstration. That is a
different working mode from sprint 68's, and mixing them halves both. More decisively, STORY-216
asserts that every `ENFORCED-BY` row names a guard that exists — and STORY-206/207/208/209 flip four
rows *into* `ENFORCED-BY`. It has to run after them, which pins it to the second sprint and pulls its
siblings with it.

**When sprint 69 closes, every `ZR-1..ZR-8` rule reaches a terminal verdict.** `ZR-6` has no standing
guard *by design* (its own Coverage verdict rules out a hard-failing contract) and `ZR-5`'s
operational half is `UNGUARDABLE` — both already stated in the catalogue, neither a gap left open.

**Deliberately outside the closure set, with reasons:**

- **STORY-214** (extract the shared pagination loop, rework the `ZR-7` guard) — spawned by sprint
  67's fix, not an audit finding. `ZR-7` is already `ENFORCED-BY` with a one-entry permanent
  exemption list; the helper is ergonomics. It is also *trapped*: the guard detects pagination
  lexically, so extracting the loop turns all five compliant sites red and forces a guard rework in
  the same change. Including it pushes a sprint to 13.
- **STORY-213** (the 1-in-11 pagination-test flake) — refined this session, sized 2, and **cut from
  this sprint during planning**. See the plan-verification findings below; the short version is that
  its filed evidence refutes the hypothesis that made it an "enabler" here.
- **STORY-211 / STORY-212** — process stories, not architecture debt.

---

## Stories, in execution order

Order is dependency-first, then blast radius, then size.

### 1 · STORY-205 — `ZR-8` finding 1, the key schema (3 pts) — *highest blast radius, runs first*

Three hand-built topology keys in `composition/seed_dynamo.py`, on the boot path of **both**
composition roots, duplicating what two repositories own. The audit called it its best boundary
finding; the drift has already cost two debugging runs once.

**Shape decided at refinement — option (b), a schema module the persistence adapters own**, not a new
port. `ZR-8`'s own Coverage verdict sanctions it in writing, and a new core-owned port for a value no
core service touches would launder a boot script through the core. Residue stated honestly in AC6:
composition still issues its own `boto3` writes — only the *schema* stops being triplicated.

**AC2 is the load-bearing one and came from the audit's own filing note:** change the schema *inside
a repository* and assert `seed_topology_dynamo` follows automatically with `seed_dynamo.py`
unchanged. A behavioural drift test, not a source assertion — it is the only AC that proves the
duplication is actually gone rather than merely relocated.

### 2 · STORY-204 — `ZR-8` finding 2, the DQL builder (2 pts) — *must precede #3*

`composition/vendor_health.py` builds DQL without the adapter's breaking-character validation, and
the probe it feeds runs **first**, at loop startup. **Shape decided at refinement — move the builder
into the adapter**, not merely share a validator: `ZR-8` says query construction lives in exactly one
adapter, and the validator-only fix leaves composition building DQL, which is the violation itself.

**Ordering constraint:** this relocates `_HEALTH_CHECK_WINDOW`, whose `file:line` is cited by
`tools/demo_engine/store.py` — the exact citation STORY-203 AC4 adjudicates. 204 before 203.

### 3 · STORY-203 — `ZR-3`'s four value duplications (2 pts)

Four `MUST-IMPORT-FROM-SRC` entries, all MINOR, none a live defect — measured today at **13 colliding
pairs**, expected 9 after. **AC2 guards the real risk:** two of the four sit inside a *defensive
blocklist* asserting the resolved table name is not the production default, and a careless "import
the constant" fix turns that blocklist into a tautology. AC4 requires a genuine decision on the
fifth, cross-representation case — `store.py` already carries a written wire-contract justification
that may well be correct, and upholding it is a legitimate outcome.

### 4 · STORY-215 — the env-var-name remainder (3 pts) — *runs last; enabler for sprint 69*

**Four sites, not the two its old title named.** Two are the `DYNATRACE_*` pair STORY-202 left, whose
*declaring* side is itself a function-body literal — there is no constant to import yet, which is
precisely why 202 left them. One is new, found at this refinement and absent from the audit's list:
`scripts/seed_topology.py:25` reads `CONFIG_DIR` with its own `"config/apps"` default, bypassing
`load_settings()` — a third process resolving publish-guard-relevant config on its own terms, which
is the sprint-64 incident's own shape. Fixing it lets sprint 69's STORY-209 assert a clean `ZR-5`
invariant instead of carrying an exemption it cannot explain.

**The fourth is the consequential one, and both sprint-67 reviewers flagged it independently.**
`backend/tests/test_demo_fleet_config.py:164,200` re-type `"CONFIG_DIR"` — and that is STORY-176's
file, the `create_app` test asserting `CONFIG_DIR` governs *publisher safety*. So the literal that
re-creates the drift risk sits **in the test that guards the publish guard**: `CONFIG_DIR` selects
`config/demo`, which empties `statuspage_mapping()`, which is what yields a `LoggingPublisher` — and
`decide` publishes recoveries with **no human gate**. A rename that silently missed this test would
leave it green while asserting nothing. The `ZR-3` sweep is structurally blind to it (it compares
`backend/src/` declarations against `tools/` literals; this file is under `backend/tests/`), which is
why nobody adjudicated it, and why AC5 requires its own mutation.

**Resized 2 → 3 at refinement.** Promoting two new constants re-runs STORY-202's own trap:
newly-declared shape-i values turn existing `tools/` literals into *fresh* `ZR-3` collisions — the
sequence that took 202 from 1 point to 3. AC6 expects the sweep count to move in both directions and
requires adjudicating every new collision.

Runs last because it re-keys `_ADJUDICATED` line numbers after STORY-203 has already done so —
**not**, as this plan first claimed, because that makes it one re-keying pass instead of two.
Verification refuted that: both stories edit `harness.py`, so its surviving entries shift twice in
either order. The ordering still helps (215 re-derives against a settled file rather than racing
203), but the saving is smaller than claimed and both stories now require re-derivation.

**Explicitly out of scope:** `test_settings.py:30` (`assert CONFIG_DIR_VAR == "CONFIG_DIR"`) is the
**pin**, not a duplication, and survives untouched. A test *asserting* a constant's value is
protection; a test *re-typing* the name to consume it is drift. That distinction is the entire
difference between this exclusion and the fourth site above.

---

## Constraints

- **C1 — Nothing lands without something going RED first.** Every story carries an explicit mutation
  or pre-fix-failing test. Carried from sprint 67, where it worked.
- **C2 — Re-derive every number; never copy one.** Counts, line numbers and sweep totals are
  measured at HEAD by the story that quotes them. If a figure does not reproduce, **say so** rather
  than editing it. Sprint 67 hit this twice.
- **C3 — Prose that misinforms is a blocking defect, not a nit.** Ten of sprint 67's eleven blocking
  findings were documents made false by the commit that wrote them. Every story here touches
  `zone-rules.md`; each carries an AC requiring the catalogue to move in the *same* commit as the
  code, including the paragraphs below the table.
- **C4 — No `ENFORCED-BY` claim wider than what the guard checks.** Sprint 67's MAJOR-1. STORY-205
  AC6 and STORY-203 AC7 state it per-story; STORY-216 mechanises it next sprint.
- **C5 — `REQUIRE_DYNAMO` set on every gate run** (agreement A6). A nonzero skip count is an
  incomplete gate, not a pass.
- **C6 — Branch stays unmerged.** Sprints 66 and 67 are unmerged; 68 cuts from 67. Nothing touches
  `main`. Standing PO directive, re-confirmed at the sprint-64 review.

## Plan verification

**Contract-sensitive: YES**, on two counts — STORY-204 touches the vendor DQL path, STORY-205 touches
the persistence key schema, which is a contract between the seed path and two repositories.

**A real `yt-plan-verifier` was dispatched POST-LOCK, pre-implementation (2026-08-03), after the PO
made subagent dispatch a standing authorisation and asked directly whether the plan had been
verified. Verdict: `GAPS` — 11 findings, 5 blocking. All were fixed in the stories and this plan
before any implementer was dispatched.** Sprint 67's verifier was also dispatched late and caught
that sprint's headline defect; the pattern repeated.

**The finding that matters most, because it refuted the orchestrator's own severity argument by
running the code rather than reading it.** STORY-215 claimed a rename would leave *the publish-guard
test* "green while asserting nothing." The verifier ran the mutation's observable state read-only:

```
statuspage_mapping() = {'http-check': 'xdnywbx77npw'}
line 174  assert mapping == {}   -> FAIL   <-- the test goes RED
delegate type = BestEffortPublisher
```

`test_demo_fleet_config.py:174` is a **working detector**. The test that actually passes for the
wrong reason is the *live*-side one at `:206-212`, whose literal sets `CONFIG_DIR=config/apps` while
the fallback default is also `"config/apps"` — so it succeeds whatever the variable is called. The
residual defect is real; the mechanism was **inverted** in the story, in this plan, and on the board.
An implementer executing that AC literally would have observed the opposite of what it demanded and,
under C2, been forced to stop. All three sites corrected.

**Four more blocking gaps, each of which would have produced wrong work:**
- **STORY-203 AC3 said `_ADJUDICATED` "loses exactly those four entries"** — but fixing the two
  `us-east-1` sites adds import lines that shift three *surviving* entries, taking **both** ZR-3
  guard tests red. Re-keying is mandatory, not optional. The same defect recurred in STORY-215.
- **STORY-204 carried no `zone-rules.md` AC at all**, while this plan claimed every story here did
  (constraint C3). Its commit falsifies four passages and marks the article stale with nothing to
  clear it.
- **STORY-215 AC1 cited a mock payload as a verbatim assertion.** `test_run_live_loop.py:332` is a
  fabricated `side_effect` on a *patched* function — it asserts nothing, and its text never matched
  the real message (`Missing required LIVE secrets:`). The only real pin is `test_live_secrets.py:65-68`.
- **STORY-215 AC6's "baseline to beat: 13"** is invalidated by STORY-203, which runs earlier and
  leaves 9 — a number the sprint's own story falsifies, which is the exact sprint-67 defect class.

**STORY-205's design decision survived, and got cheaper.** Option (b) is confirmed implementable:
the `UpdateExpression` names no key attribute, `APP#` has exactly one construction site in the tree,
and no contract is threatened. But **AC2 was written against option (a)'s world** — it told the
implementer to "change the schema inside a repository", which under (b) no longer exists. Restated,
with the honest note that the unmutated test is green both before and after.

---

An earlier verification pass was performed **by the orchestrator** before the PO saw this plan. It
changed the plan in six places, recorded here rather than silently folded in — the first four below
were confirmed by the verifier, the last two were its own corrections to its first draft:

1. **STORY-204 must precede STORY-203** — 204 relocates the `file:line` that 203 AC4 adjudicates.
   The original priority order had them the other way round.
2. **STORY-205's shape was undecided and is now decided** — the filed note flagged the sizing risk
   ("may need a new `TopologyRepository` port"). Refinement chose the schema-module option that
   `ZR-8`'s own Coverage verdict already sanctions, keeping it at 3 points.
3. **STORY-215's scope was understated by its own title** — a third `CONFIG_DIR` reader
   (`scripts/seed_topology.py:25`) was found at refinement, absent from the audit's list, and it is
   the reason 215 is an enabler for sprint 69's STORY-209.
4. **STORY-205 AC4's drift citation is already clean** —
   `tools/demo_loop_gate/failure_path_reality_gate.py` routes through the real repository at HEAD.
   The audit's citation is history, not a live second site; the AC now says *verify*, not *fix*.
5. **STORY-213 was in this sprint and was cut** — and this one is a correction, not a trim. It was
   placed here as an "enabler" for STORY-205 on the theory that sibling tests polluted a shared
   control table. Its filed evidence refutes that: the observed failure was
   `{'comp-page-0','comp-page-1'} == {10 ids}` — **fewer** rows, i.e. page 1 and stop, a lost
   `LastEvaluatedKey`. Pollution yields *extra* ids. The real (unconfirmed) mechanism is DynamoDB
   Local flakiness under the fixture's ~1,400 delete/recreate cycles, related to STORY-179 — which
   protects none of this sprint's work. Its AC were wrong too: they demanded reproduction first,
   which would have blocked it by construction, since 35 runs already failed to reproduce it. Both
   corrected in its story file; it is refined, sized 2, and waits.
6. **STORY-215 was understated by more than one site, and the biggest was one this pass first
   excluded in error.** An earlier draft of its AC dismissed `test_demo_fleet_config.py:164,200` as
   "test-side literals are the pin, not a duplication" — conflating it with `test_settings.py:30`.
   Both sprint-67 reviewers had independently flagged it as a real residual defect, and they are
   right: one *asserts* a constant's value (protection), the other *re-types the name to consume it*
   (drift), inside the test that guards the publish guard. Corrected, and the story resized 2 → 3.

Also measured at planning, for sprint 69's STORY-206: raising the import-linter contract count from
8 to 9 requires updating **15 occurrences of "eight contracts" across 6 living files** (`CLAUDE.md`,
`.scrum/definition-of-done.md`, `.scrum/backlog.yaml`, `zone-rules.md` ×9,
`ingest-service-and-pull-loop.md` ×2, `architecture-boundary.md`). The 30 further occurrences under
`docs/scrum/sprints/` and `docs/scrum/stories/` are **append-only history and must not be edited** —
they correctly describe what was true then. This is the STORY-210 AC2 pattern.

## Definition of Done

Unchanged — the eight commands in `.scrum/definition-of-done.md`, run via
`python .claude/skills/yourteam/scripts/yt_gate.py`, all exiting 0. Per-story gates may be scoped
with `--only`; the **full 8/8 on the final HEAD is the evidence of record**. No story is Done on a
self-report.

## Risks

| Risk | Mitigation |
| --- | --- |
| STORY-205 is the sprint's whole design content; if the schema module turns out to need a port after all, 3 points is optimistic | **Retired by verification** — option (b) confirmed implementable: the `UpdateExpression` names no key attribute, and `APP#` has exactly one construction site in the tree, so no port is needed. It runs **first**, while the session is fresh; a block still leaves three stories deliverable. |
| STORY-203 + STORY-215 both edit `_ADJUDICATED` and `zone-rules.md`'s ZR-3 section | Each has an AC naming the other. **Corrected by verification:** they also both edit `harness.py`, so its surviving entries get re-keyed **twice in either order** — the earlier "one re-keying pass instead of two" claim was false. Both stories now require re-deriving coordinates rather than carrying the other's forward. |
| A "fix" that makes a guard blind — 203's blocklist tautology, 215's untouchable pin | Explicit AC on both (203 AC2, 215 AC3) requiring the guard still fire against the defect it exists to catch. |
| STORY-215 creates fresh `ZR-3` collisions while removing others — STORY-202's own trap, which took that story from 1 point to 3 | Sized 3 up front rather than discovered mid-sprint. AC6 requires re-deriving the count in both directions and adjudicating every new collision; an unrecognised one is a guard failure, never a silent pass. |
| Session limit mid-story | Park with a committed handoff (standing PO directive). Drop order if the session runs short: **STORY-203** (all four findings MINOR, none a live defect). Never STORY-215 — sprint 69 depends on it. Never STORY-205 — it is the audit's biggest finding and the only one describing a defect that has already cost real debugging time. |

## Decisions the PO owns at approval

1. **Approve the sprint as scoped** — 10 points, four stories, in-process. Or take the drop order
   above as a standing trim.
2. **Subagents.** Sprint 67's ruling ("yt-implementer per story, then yt-spec-reviewer ∥
   yt-quality-reviewer; no story reaches review unreviewed") was recorded per-sprint and does not
   carry over on its own. It earned its keep: all four sprint-67 stories passed spec review and
   **failed** quality review, and this sprint's work is the same shape — small diffs whose defects
   live in the accompanying prose. Recommend re-confirming it, which also covers dispatching
   `yt-plan-verifier` rather than relying on the orchestrator pass above.
3. **The two-sprint closure map** — confirm sprint 69's five stories as the remainder, and confirm
   that STORY-214 stays out of it.
