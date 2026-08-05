# Sprint 69 — Plan

**Status:** **APPROVED AND LOCKED 2026-08-05.** Plan-verified pre-lock (GAPS found and closed — see
below). Branch cut from `29eb824`, tagged `sprint-69-start`. Scope is frozen: PO requests from here
go to the backlog, not into this sprint.

**PO decision at approval:** *"take the 11 with AC6"* — clarified, because AC6 had come to mean two
things. **11 points, STORY-220 deferred to sprint 70**; STORY-206's current AC6 (the catalogue row
flip) is in. The declined alternative was 13 with the completeness test pulled back in. **Accepted
consequence:** for one sprint ZR-1's forbidden-module list is complete only as far as a human
maintains it, and STORY-206 AC6 requires the row to say so.
**Mode:** in-process · **Branch:** `sprint-69`, to be cut from `sprint-68` (`240549b`) · **Points:** 11 · **Stories:** 5

**Verified precondition at the cut point.** Tree clean at `240549b`; the sprint-68 close baseline is
8/8 gate commands green, **714 passed / 0 skipped** under `REQUIRE_DYNAMO=1`, `Contracts: 8 kept,
0 broken` (`.scrum/sprint-current.yaml:850-878`), and 714 collected was re-confirmed at HEAD during
plan verification. Every story in this sprint proves itself by *mutate → red → revert → green*, and
that is the green it reverts to.

---

## Goal

**Guard what is already clean, and stop the catalogue from claiming guards it does not have.**

Sprint 68 fixed the code that was wrong. The four rules left over — `ZR-1`, `ZR-2`, `ZR-4`, `ZR-5` —
have **zero live violations**, which is exactly why they are dangerous: nothing fails today, so
nothing stops tomorrow's first violation either. Each gets a standing guard, and each guard must be
**shown RED by a mutation** before it counts (A9) — a guard that has only ever been green is not a
guard.

Then STORY-216 closes the loop the whole sprint depends on: a test that every `ENFORCED-BY` row in
`zone-rules.md` names a guard that actually exists. It runs last, because the four stories before it
create four new `ENFORCED-BY` rows for it to check.

**When this sprint closes, every `ZR-1..ZR-8` rule has a terminal verdict** — enforced, or
explicitly and honestly unguardable, with nothing left in `GUARDABLE-DEFERRED`.

## The closure map's second half

The PO's framing was "full audit implementations in 2 sprints". Sprint 68 delivered the first half
10/10. This is the second.

| | Sprint 68 — *fix what is broken* (**closed, 10/10 accepted**) | Sprint 69 — *guard what is clean* |
| --- | --- | --- |
| | STORY-205 · `ZR-8` seed_dynamo key schema (3) ✅ | STORY-206 · `ZR-1` import contract (**3**, was 2) |
| | | *(STORY-220 · ZR-1 list completeness (2) → sprint 70)* |
| | STORY-204 · `ZR-8` vendor_health DQL builder (2) ✅ | STORY-207 · `ZR-2` vendor-vocabulary AST walk (2) |
| | STORY-203 · `ZR-3` four value duplications (2) ✅ | STORY-209 · `ZR-5` CONFIG_DIR parity (2) |
| | STORY-215 · `ZR-3` env-var-name remainder (3) ✅ | STORY-208 · `ZR-4` five-file feature shape (1) |
| | | STORY-216 · mechanise `ENFORCED-BY` (3) |
| **Total** | **10** | **11** |

**Why 11 and not the mapped 10 — and why not 13.** STORY-206 is re-estimated 2 → 3, but not for the
reason refinement first gave. Refinement added a completeness test (the contract's forbidden list
ships with a prose *"a newly added port MUST be appended in the same commit"* note — a mechanical
guard whose completeness rests on a sentence nobody must read). Plan verification then found the
story's real cost elsewhere: **the 8 → 9 contract-count ripple is nine living files with ~20
occurrences, not the three the first pass claimed** — and the same files carry `eight` for the *DoD
command count*, which must not change. That sweep is the 3.

Carrying the completeness test too would make STORY-206 a 5 and this sprint a 13. Against recent
velocity (**10 / 11 / 11 / 13 / 8 / 7**) a 13 is reachable, but the PO pacing directive says sit
near 9–11 and split rather than cram. **So the completeness test is split out as STORY-220** (2 pts,
proposed sprint 70, depends on STORY-206). It is not dropped, and until it lands ZR-1's catalogue
row must say the list is hand-maintained. **PO decision at approval:** take 11 with the split, or
pull STORY-220 back in for 13 — see "Decisions the PO owns".

## Stories, in execution order

Dependency first, then blast radius, then size.

### 1 · STORY-206 — `ZR-1`'s import contract (3 pts) — *widest ripple, runs first*

A ninth import-linter contract, `inbound-adapters-dont-persist`, forbidding
`src.adapters.inbound` from importing the nine repository/watermark port modules — and deliberately
NOT `signal_ingest` (the core's documented front door, dossier §6/§8), `clock` or `status_publisher`.

It runs first because it is the only story whose change escapes `backend/tests/`: it edits
`pyproject.toml` and moves the contract count of record from **eight to nine** in three places
(`CLAUDE.md:198`, `.scrum/definition-of-done.md:57`,
`docs/scrum/wiki/architecture-boundary.md:22`), in the same commit, with grep evidence.

- Verified at planning: all nine port modules exist; `grep -rn "from src.core"
  backend/src/adapters/inbound/` returns five hits, **all `core.domain`, zero `core.ports`**.
- **The contract loads and trips — proven at plan verification, not assumed.** The real
  `importlinter` CLI ran against a scratch TOML holding it verbatim (`KEPT`, exit 0, 151 files /
  432 dependencies); the grimp graph was then rebuilt with the AC3 edge added in memory and
  `ForbiddenContract.check` returned `kept=False`.
- **Shown RED:** add `from src.core.ports.observation_repository import ObservationRepository` to
  `adapters/inbound/dynatrace/adapter.py` as an unused annotation → the import-boundary command
  exits nonzero naming the contract. Revert; `git diff` empty.
- **AC4 is now a discrimination rule, not a site list** — contract-count claims change, DoD
  command-count claims (`CLAUDE.md:188`, `dev-setup-and-dod.md:118`, and `zone-rules.md:802` inside
  the adjudication legend itself) do not. Living files only; `docs/scrum/sprints/` and
  `docs/scrum/stories/` are append-only.

### 2 · STORY-207 — `ZR-2`'s vendor-vocabulary AST walk (2 pts)

A test parsing all 31 `core/` modules for vendor tokens appearing as identifiers, args, attribute
names, call keywords, or stored values — while leaving the three compliant prose forms and the
`Provenance` carve-out alone.

- Verified at planning: a throwaway prototype of exactly this walk over `backend/src/core/` scanned
  **31 modules, 0 hits**. Clean on arrival, mutation required.
- **Shown RED:** add `dynatrace_code: str` to a `core/domain` model. Also proven in the *compliant*
  direction (AC2) — an over-triggering walk would flag the six docstring citations ZR-2 has already
  adjudicated COMPLIANT, and would have to be reverted rather than obeyed.
- **The residue ships in the guard's own docstring:** string annotations and dynamically constructed
  identifiers stay invisible. ZR-2 may not be called fully enforced, anywhere.

### 3 · STORY-209 — `ZR-5`'s CONFIG_DIR parity (2 pts) — *highest-care mutations*

`load_settings()` parity plus an AST assertion that neither `run.py::main` nor `app.py::create_app`
reads the `CONFIG_DIR` env var itself.

Third because its mutations temporarily edit the two composition roots — the publish-safety
surface. They are source-level only and no loop is ever run; the standing rule still holds
(**never** `python -m src.composition.run`; pin `CONFIG_DIR=config/demo` for anything constructing
`create_app()`).

- Verified at planning: `grep -rn "CONFIG_DIR" backend/src/` hits **`settings.py` only** — the roots
  are clean today, so the proof is a mutation, twice (once per root, AC4 + AC5). A guard watching
  only one root would be the very asymmetry ZR-5 names.
- **Its scope limit is half the story:** the two-process operational failure that actually caused
  the sprint-64 incident is UNGUARDABLE here and stays runbook discipline. That sentence goes in the
  docstring and stays in the row.

### 4 · STORY-208 — `ZR-4`'s five-file feature shape (1 pt)

Extend `test_zone_layout.py::test_zone_layout_agreements` (`:126`) to assert each `api/v1` feature's
module set equals exactly the five files, with `health` the one enumerated exception.

- Verified at planning: ten features, nine conform, `health` is the single documented deviation
  (its own controller docstring says why). Unchanged since the audit.
- **One HEAD fact the audit sketch missed, and it is load-bearing:** every feature directory holds a
  `__pycache__/` on any machine that has run the suite. A naive set-equality assertion is red on a
  dev box and green in clean CI. AC2 makes the `*.py`-only filter explicit, with the reason.
- **Shown RED twice, in both directions:** remove a required file, *and* add a sixth — the second
  is what proves set equality rather than a subset check.

### 5 · STORY-216 — mechanise the `ENFORCED-BY` claim (3 pts) — *must run last*

A test that every `ENFORCED-BY` row in `zone-rules.md` names a path that exists and a test function
that exists. Sprint 67's loudest finding: `ZR-6`'s row claimed a guard, and reverting the entire fix
left the suite at 696 passed — identical. The row was false, and the legend twelve lines above it
already forbade exactly that.

It runs last because stories 1–4 each flip a row into `ENFORCED-BY`; running it earlier would
validate a table about to change four times. **AC6 forbids an exemption list on this particular
guard** — a failing row is fixed, because exempting it would reproduce the original defect.

**Refinement settled its open question:** the check lives in `backend/tests/`, not in
`yt_wiki.py`. Decisive reason — `yt_wiki.py` must stay project-GENERIC (PO rule, 2026-07-13), and
`zone-rules.md`'s adjudication table is a project-specific format. Secondary: `yt_wiki.py` is not a
DoD command, so a check there gates nothing at story close. Consequence: AC2 AST-parses the named
file instead of shelling out to `pytest --collect-only`, and states its residue (a test that exists
but is skipped still counts as present).

---

## What is deliberately NOT in this sprint

- **STORY-220 · ZR-1's forbidden-list completeness test (2, split out at plan verification).**
  Depends on STORY-206, so it cannot precede it, and folding it in makes the sprint a 13. The cost
  of deferring is stated rather than hidden: for one sprint, ZR-1's list is complete only as far as
  a human maintains it, and STORY-206 AC6 requires the row to say exactly that.
- **STORY-219 · wire `citation_sweep.py` into the gate (3, refined this session).** The strongest
  sprint-70 candidate — sprint 68 produced five occurrences of the defect it prevents, and A18
  landed only the staleness half, which is blind to three of the five. Excluded because it is wiki
  tooling, not audit closure, and this sprint is already at 11.
- **STORY-218 · `Settings` declares every default twice (2, refined this session).** Re-verified at
  HEAD; unchanged. A duplication fix, not a guard.
- **STORY-217 · topology write port (1, refined this session).** Refinement answered its own
  question mechanically: `grep -rn "topology" backend/src/core/` returns reads and docstrings only —
  **no core service writes topology**, so the expiry condition has NOT fired and the correct outcome
  is a dated re-affirmation with no code. Real, but it buys a re-check, not a guard.
- **STORY-214 · extract the shared pagination loop.** Unchanged from sprint 68's reasoning: spawned
  by a fix rather than by the audit, and *trapped* — the `ZR-7` guard detects pagination lexically,
  so extracting the loop turns five compliant sites red and forces a guard rework in the same
  change.
- **STORY-213 · the 1-in-11 pagination flake.** Did not fire once in sprint 68. Still filed.

## Constraints and standing facts (carried into every dispatch)

- **Sprints 66, 67 and 68 stay unmerged; nothing touches main.** Standing PO directive, re-confirmed
  at the sprint-68 review. Sprint 69 cuts from `sprint-68` (`240549b`).
- **Gate runs need `DYNAMO_ENDPOINT_URL=http://127.0.0.1:8021` and `REQUIRE_DYNAMO=1`.** Container
  `uptime_dynamo_8021` verified up at planning (6 days). A wrong endpoint under `REQUIRE_DYNAMO=1`
  **errors** rather than skips (A6, by design) — that looks like a code red and is a setup error.
- **DynamoDB Local namespaces tables by access-key-id + region**, and `make_dynamo_resource` forces
  `test`/`test` when an endpoint is set. Tables created under other credentials are invisible and
  surface as `ResourceNotFoundException`.
- **Publish safety.** Never run `python -m src.composition.run` — `decide` publishes recoveries with
  no human gate. Anything constructing `create_app()` pins `CONFIG_DIR=config/demo`.
- **Console-script shims are blocked by Device Guard** — module form only (`python -m pytest`,
  `python -c "from importlinter.cli import ..."`, `python -c "from cfnlint.runner import main; ..."`).
- **A PreToolUse hook blocks bulk git staging** during an active sprint. Stage explicitly.
- **A18 / C3:** wiki prose lands in the SAME commit as the code it describes;
  `python .claude/skills/yourteam/scripts/yt_wiki.py c3 --range <base>..HEAD` is run per story
  (advisory).
- **Window check (PO directive 2026-07-29) at every agent boundary**, not per story.

## Plan verification

**Dispatched** (`yt-plan-verifier`, pre-lock) — findings and their resolution are recorded below
before the PO sees this plan.

Justification for dispatching rather than skipping: the token-economy rule exempts *purely internal*
sprints, and this one is not, on two counts. (1) **STORY-216 consumes a document its four siblings
produce in the same sprint** — the adjudication table's row format is an intra-sprint consumer
contract, and if 206–209 write rows in a shape 216 cannot parse, the failure surfaces at the last
story of the sprint. (2) Every story's entire value rests on a mutation *actually tripping its
guard*; a mutation that silently passes yields a guard that has only ever been green, which is the
defect this sprint exists to end.

### Verdict: **GAPS** — 14 found, all closed before this plan reached the PO

It also confirmed the load-bearing claims: the contract loads and trips; the nine/three port split
is right; the ZR-2 walk really is 31 modules / 0 hits and really does catch `dynatrace_code: str`
(via the `AnnAssign` target being an `ast.Name`) while leaving all prose forms compliant; the
`CONFIG_DIR` roots are clean; the ten features and the `__pycache__` hazard are exactly as planned;
and no story needs a ninth DoD command.

**Expensive gaps — would have surfaced at STORY-216 or at sprint close:**

| # | Finding | Closed by |
| --- | --- | --- |
| G1 | **STORY-216's row grammar was unspecified.** Five literal readings of AC1 were implemented and run against the real table: one gives **4 false REDs of 4** (it captures the trailing backtick), one silently skips ZR-8's two guards, one pulls a line-wrapped `ENFORCED-BY` out of History that resolves *by luck*. AC6 would then have sent an implementer to edit four **correct** rows. | AC1 rewritten to pin the grammar — scope, code-span references, multiple refs per cell, Detail/History out of scope. AC6 gains "if the grammar and a correct row disagree, the grammar is wrong." |
| G2 | **STORY-206 AC7 wrote a row STORY-216 could not parse.** It named an import-linter *contract*, not a path; 216 asserted "a path that exists"; AC6 forbade exempting it. The intra-sprint consumer break this dispatch was justified on. | STORY-216 AC1 gains a second reference kind (non-path token → contract name resolved against `pyproject.toml`), with AC4(c) mutating that half. STORY-206 AC6 writes the row in that shape. |
| G3 | **STORY-209's row mixed two verdicts and put a parenthetical inside the code span** → guaranteed false red. | AC7 pins the parenthetical outside the span; 216 AC1 explicitly permits `ENFORCED-BY` + `UNGUARDABLE` in one cell, naming ZR-5. |
| G4 | **STORY-216 had no non-vacuity floor** — a zero-row parse passed green. Sprint-67's MAJOR-1, reproduced inside the guard built to end it. | AC1: assert all eight `ZR-1..ZR-8` parsed and ≥ 1 reference resolved. Same floor added to STORY-207 (AC9) and STORY-208 (AC8), which both drive off filesystem discovery. |
| G5 | **STORY-216 AC4 proved only half the guard** — AC2's AST test-name resolution never went red, shipping unproven under the sprint's own A9 rule. | AC4 becomes three mutations, one per resolution path. |
| G6 | **STORY-206's "eight appears in three places" was wrong** — nine living files, ~20 occurrences, and the repo had already measured this two days earlier. AC4's own evidence command would have left ~19 survivors against its stated "zero" criterion, and a naive sweep would have corrupted three **command**-count claims. | AC4 rewritten as a discrimination rule with a living-files scope; AC7 added for the five wiki articles citing `pyproject.toml`; story re-scoped and STORY-220 split out. |

**Cheap gaps — would have surfaced at implementation:**

| # | Finding | Closed by |
| --- | --- | --- |
| G7 | **STORY-208's mutation could not produce the red it described.** Every `models.py` has two importers and `test_zone_layout.py:12` imports all ten routers, so renaming one is a `ModuleNotFoundError` **collection error** — the shape guard never executes, and the recorded "red" would not be the guard firing. | AC4(a) retargeted to `approvals/validation.py` — one of five feature files with **zero** importers (verified). |
| G8 | **STORY-207's residue statement was FALSE** for the walk its own AC1 specifies. Both examples ZR-2 names *are* caught, as string constants. The text predates the six-rule walk and AC4 ordered it shipped verbatim — an implementer believing it might have weakened rule (6) to "fix" the contradiction. | AC4 restates the true residue and drops "verbatim"; `zone-rules.md`'s ZR-2 paragraph is corrected in the same commit. |
| G9 | **STORY-207 AC1 and AC3 were mutually unsatisfiable.** `Provenance(system="dynatrace")` — ZR-2's explicitly *sanctioned* channel — is flagged by rule (6). Both ACs could have been "met" by a vacuous test, leaving the row claiming a carve-out the guard does not implement. | AC3 rewritten as a stated residue: the carve-out is unimplemented, a future literal will false-positive, and the correct response then is a narrow exemption — never deleting the domain's sanctioned channel. Carried into AC8's row. |
| G10 | **STORY-209 guarded only half of ZR-5's own statement** — the rule forbids a hardcoded default *and* a differently-named var; AC2 caught only the second, while AC7 flipped the row to `ENFORCED-BY` unqualified. The overclaim STORY-216 exists to punish, in the same sprint. | AC3(b) states the code-level residue; AC7 carries it into the row. |
| G12 | **"Stated in the check's own output" is unimplementable** — a passing `pytest` emits nothing. | STORY-216 AC2/AC3 align on docstring + assertion failure message, matching how 207 and 209 already word it. |
| G13 | The plan stated no verified precondition to diff the revert-to-green proofs against. | Baseline added at the top of this plan. |

**Two notes carried into the stories rather than the plan:** STORY-206 AC6's exclusion set is dead
code under its own discovery rule (harmless, but it specifies an unexercisable branch — noted in
STORY-220); and neither `app.py` nor `run.py` imports `os`, so STORY-209's mutations need an
`import os` added — a `NameError` there is not the guard failing.

## Definition of Done

Unchanged — the eight commands in `.scrum/definition-of-done.md`, all exit 0, evidence emitted by
`python .claude/skills/yourteam/scripts/yt_gate.py` and merged verbatim.

**This sprint adds no ninth command** — every guard lands inside `python -m pytest` or inside the
existing import-boundary command. Any story proposing a ninth command has misread its own AC.

Per-story gates may be `--only`-scoped mid-sprint; the **full eight-command gate on the final HEAD
is the evidence of record** at close, with a nonzero skip count treated as an incomplete gate (A6).

**Reality gate, this sprint:** the mutation IS the reality gate. Every story records its shown-RED
proof — command, output tail, and the `git diff`-empty confirmation after revert — in the board's
`reality_gate.discrimination_proof`. A story whose guard was never seen red is NOT Done, and spec
review returns NOT_MET rather than MET-with-a-note.

## Risks

| Risk | Handling |
| --- | --- |
| A mutation passes silently, yielding a never-red guard | The proof is an exit code plus output naming the guard, not a claim (A7/A9). Reviewers verify the recorded output, not the summary. Plan verification already caught one mutation (STORY-208's) that would have produced a collection error instead of a guard red. |
| A guard passes because it checked nothing | Non-vacuity floors added to STORY-207, 208 and 216 — the guard must assert its own discovery was non-empty. |
| A guard over-triggers and flags already-adjudicated compliant code | STORY-207 AC2 tests the compliant direction explicitly. An over-triggering guard is reverted, never obeyed by editing compliant code. |
| `__pycache__` makes STORY-208 machine-dependent | Caught at planning; AC2 requires the `*.py`-only filter and its reason. |
| STORY-206's doc ripple lands in a later commit than the contract | AC4 names the same-commit requirement and demands before/after grep evidence — the A18 defect class. |
| Four rows written in a shape STORY-216 cannot parse | The plan-verifier dispatch above exists largely for this; 216 running last is the containment. |
| STORY-209's mutations touch the composition roots | Source-level only, reverted immediately, no loop run. `git diff` empty is part of the AC. |

## Decisions the PO owns at approval

1. **11 points with STORY-220 split out, or 13 with it pulled in?** Recommendation: **take the 11.**
   The split is honest — ZR-1's forbidden list stays hand-maintained for one sprint and its row
   *says so* — and 13 would mean cramming against your own pacing directive. Pulling it in makes
   STORY-206 a 5 and the sprint a 13.
2. **Execution order.** Proposed 206 → 207 → 209 → 208 → 216. Only 216's position is forced (its
   four inputs are written by the four before it).
3. **The four drafts refined this session** — STORY-217 (1), STORY-218 (2), STORY-219 (3),
   STORY-220 (2) — are proposed as `ready` for sprint 70, not pulled in here. Confirm, or pull one
   in and drop a guard.
4. **Sprints 66–69 all remain unmerged** unless you say otherwise.
5. **Two catalogue corrections land inside stories, not as their own work** — ZR-2's residue
   paragraph (`zone-rules.md:238-243`, factually wrong for the walk being built) in STORY-207, and
   the legend's "exactly one verdict per rule" line (`:801`, already broken by ZR-5 at `:812`) in
   STORY-209. Flagging because they edit the audit catalogue itself, which is the sprint's yardstick.
