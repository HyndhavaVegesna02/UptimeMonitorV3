# Sprint 67 — Plan

**Date:** 2026-08-02 · **Branch:** `sprint-67` (off `sprint-66`, which stays unmerged)
**Mode:** `in-process` · **Committed:** 11 points / 4 stories (5 at approval; see the post-lock note)

## Goal

**Turn sprint 66's audit report into landed fixes.** Sprint 66 produced a yardstick, two standing
guards and seven filed defects; a report is a document, and a document does not fix a production
defect. This sprint fixes the highest-severity findings and drives both guards' exemption lists
toward empty — and hardens the DoD gate against the policy that took it red mid-sprint.

The measure of success is mechanical, because sprint 66 built it: **ZR-7's `_EXEMPTIONS` goes from
six entries to one, and ZR-3 loses its two `STORY-202` entries.** Every *retired* entry names the
story that is supposed to remove it, and each guard's stale-exemption test goes RED if a fix lands
without its entry being removed. The guards were written to detect this sprint happening.

> **Corrected after the lock, and the PO was told rather than it being quietly fixed.** This section
> originally read "five entries to zero". `_EXEMPTIONS` holds **six**. The sixth —
> `dynamo_publication_repository.py:53` — is a `PERMANENT` entry for `list_recent`, whose port
> promises "up to `limit`" rather than completeness, and STORY-199's own "Not in scope" paragraph
> says so correctly. **It stays.** An implementer following the approved text literally would have
> emptied the dict and taken the DoD gate RED. Caught by plan verification, then verified
> independently by enumerating the six keys via AST.

## Baseline (established at planning, 2026-08-02)

| | |
| --- | --- |
| Start commit | `86459ea` |
| Full DoD gate | **8/8 GREEN, exit 0** — `python -m pytest` **689 passed / 0 skipped**, 8 import contracts kept, ruff check + format clean (247 files), cfn-lint clean, frontend **363 passed in 51 files**, build + lint clean |
| `yt_selftest` | 35/35 OK |
| `yt_wiki` | CLEAN on all four blocking checks (sweep, facts, links, integrity); 2 advisory `refs` amplifier notes, unchanged |
| Dynamo | `uptime_dynamo_8021` on `127.0.0.1:8021`, `REQUIRE_DYNAMO=1` on every gate run |

**The baseline was RED when planning started, and the fix is already committed.**
`ruff format --check .` exited 1 on
`.claude/skills/yourteam/scripts/tests/test_backlog_story_parity.py` — the **A11 amendment's own
file**, landed at the sprint-66 retro *after* that sprint's final gate run (which recorded "246
files already formatted"), so the gate never saw it. A single line-wrap. Fixed at `86459ea`.

Worth carrying to the retro: A11 was routed to the **script** rung precisely because a machine
should check state parity — and the file itself never went through the machine that checks code.
**A13** ("re-run every recorded command as the last step before reporting") is the rule that would
have caught it, and it was written in the very same retro.

## Scope

| # | Story | Pts | Ceremony |
| --- | --- | --- | --- |
| 1 | **STORY-210** — harden the DoD gate: remaining exe shims + a policy-block diagnostic | 2 | both reviewers |
| 2 | **STORY-199** — paginate the five truncating persistence methods | 3 | both reviewers |
| 3 | **STORY-202** — `env_matrix.py` imports all seven env-var names | **3** | both reviewers |
| 4 | **STORY-200** — domain-typed `action` on the proposal port (**subsumes STORY-198**) | 3 | both reviewers |
| ~~5~~ | ~~**STORY-201** — clickpath normalizer uses `require_field`~~ | ~~1~~ | **dropped post-lock** |

**11 points**, at the top of the stated ~9–11 baseline — the same size as sprint 66. The sprint-66
retro's finding was that fix-round cost is driven by story *kind*, not size: an audit sprint's
deliverable is prose, which fails review in ways code does not. This sprint's deliverable is code
with mechanical proofs, so 11 is the right call rather than a stretch.

### Execution order, and why

**STORY-210 first** because it protects every other story's gate run, and because a mid-sprint gate
block cost sprint 66 a blocked story and a diagnosis cycle. The acute emergency is over — see below
— but the exposure is not.

Then **199** (the only live production defect in the set, and the largest), **202** (safety-adjacent
and touches `settings.py`, which 200 does not), and **200** last.

**One ordering hazard, created by this plan and caught in verification:** 199 and 200 both edit
`dynamo_proposal_repository.py`, and 199's pagination loop at `:174` shifts every citation below it.
STORY-200's `:265`/`:268`/`:286`/`:292` **will be stale** by the time it runs; its story file now
carries an instruction to re-derive them first. The plan boasted "every citation re-derived, none
had drifted" while scheduling the drift it was about to cause.

**Drop order if the session runs short:** 202 first, now that 201 is already out. **Never** 199 — it
is the live defect and the sprint's reason to exist. 210 is never dropped either, because it is the
thing that keeps the gate trustworthy for the rest.

### Ceremony note

**All four remaining stories get both reviewers.** Three are 3-pointers, and STORY-210 is 2 points
but edits the DoD and the gate runner itself. That follows the sprint-66 evidence, not habit: **both
reviewers found real defects in every story of that sprint**, several already accepted by the
orchestrator, for the third sprint running. STORY-201 — the only story that would have taken the
small-story ceremony — is no longer in the sprint.

## Verified facts at planning

Each was produced by a command, re-run today against HEAD. The sprint-66 retro found that this
sprint's filings repeatedly carried drifted line numbers, so every citation in every story entering
this sprint was re-derived. **No `file:line` citation had drifted.**

**But two of these V-facts were still WRONG, and both are marked CORRECTED below.** Neither was a
drifted line number — they were a miscount (V1) and an inference written as a measurement (V8), and
re-checking citations does not catch either. That is worth carrying to the retro: the sprint-66
lesson was "re-derive your citations", and this plan did that faithfully and still shipped two false
facts, one of which was the sprint's headline success measure.

- **V1 — CORRECTED. The ZR-7 exemption list holds SIX entries, of which five belong to STORY-199.**
  The five to retire are keyed at `dynamo_component_repository.py:29`,
  `dynamo_maintenance_repository.py:68` and `:90`, `dynamo_proposal_repository.py:174`,
  `dynamo_signal_repository.py:30` — all naming `"Fix: STORY-199."`, each pointing at the exact
  `.query(` call site. **The sixth, `dynamo_publication_repository.py:53`, is `PERMANENT` and
  stays.** This V-fact originally said "exactly five", which is what produced the wrong success
  measure above; it was written from a `grep` that matched only the `STORY-199` reason strings.
  Re-derived by AST enumeration of the dict keys.
- **V2 — the live defect is unchanged.** `is_under_maintenance` (def `:86`, query `:90`) still
  pairs `Key("gsi1pk").eq("MAINT") & Key("gsi1sk").lte(...)` with a post-read `FilterExpression` on
  `component_id`/`ends_at` and no `LastEvaluatedKey` loop.
- **V3 — the correct pattern is in the same directory**: `dynamo_observation_repository.py`
  `in_window` (`:93`–`:118`) with the `_limit` test hook at `:23`.
- **V4 — STORY-198 has NOT landed.** `dynamo_proposal_repository.py:286` still reads
  `if action == "approved":`. The STORY-200 story file asserted it was "already landed" and reasoned
  about reconciling with it; that was wrong, and is corrected. This is why 200 now subsumes 198.
- **V5 — STORY-198's test trap is real.** `backend/tests/fakes.py:175-183`'s
  `record_approval_event` only appends a dict; it does not denormalize `approved_actor`. And
  `dynamo_publication_repository.py:94-96` reads `approved_actor` as the sole source of
  `Publication.author`. So the branch is observable **only** against real DynamoDB — a fake-based
  test would assert nothing while looking green.
- **V6 — five of STORY-202's seven names have nothing to import.** `settings.py:32-38` reads
  `CONFIG_DIR`, `AWS_REGION`, `DYNAMO_ENDPOINT_URL`, `DYNAMO_OBSERVATIONS_TABLE`,
  `DYNAMO_CONTROL_TABLE` as **function-body literals**; only the two Statuspage names are module
  constants (`:49-50`). This is what re-pointed the story 1 → 2 and pulls it into `backend/src/`.
- **V7 — STORY-210's premise has changed and the story was rescoped.** The full gate is green
  today; `ruff.exe` is **still allowed** (`ruff --version` → `ruff 0.15.20`, exit 0), so the ruff
  work is preventive rather than a repair. `python -m ruff --version` returns the same version, so
  the module form is equivalent. `yt_gate.py` contains **no** policy-block detection — grep for
  `4551` / `Device Guard` / `Application Control` returns zero hits across its 389 lines.
- **V8 — CORRECTED, and this one is the most instructive.** It read: "`npm` has no module form. That
  exposure cannot be closed by an invocation change." That was an **inference presented as a
  measurement** — the exact error constraint C2 exists to catch, committed inside the plan that
  states C2. Measured: `node <npm_root>/bin/npm-cli.js --version` returns `11.6.2`, exit 0,
  bypassing the `npm.cmd` shim entirely — the direct analogue of `python -m ruff`. What is genuinely
  unverified is whether the policy would block the `.cmd` while permitting `node.exe`. AC7 now
  records that measured position; **adopting** the form is a separate PO decision and is out of
  scope. Left uncorrected, AC7 would have written "no module form exists" into
  `.scrum/definition-of-done.md` as a dated permanent fact.

## Plan verification

**This sprint IS contract-sensitive**, so the token-economy skip does not apply on its merits:
STORY-200 changes a **port contract** consumed by both an adapter and a core service, and STORY-199
is **scale-sensitive** logic whose defect only appears past DynamoDB's 1 MB page boundary. By the
rule, `yt-plan-verifier` should be dispatched.

**It was NOT dispatched, and the reason is environmental, not a judgement that it was unnecessary.**
This session carries a standing constraint against spawning subagents unless the PO asks. That is
flagged for the PO at approval below, because it affects how the whole sprint executes, not just
planning.

**What was done instead**, by the orchestrator directly, and recorded as V1–V8 above with the
command that produced each: every `file:line` citation in all five stories re-derived against HEAD;
both guards' exemption/adjudication lists read and matched against the stories that claim to retire
them; the STORY-198 test trap confirmed by reading `fakes.py` and the publication repository; the
STORY-200 design question settled against the actual enum, port and service code; and STORY-210's
premise re-measured, which is what revealed the story was stale and needed rescoping.

**This is not equivalent to an independent pass, and should not be recorded as if it were.** The
single loudest finding of sprint 66 was that self-review missed defects that independent review
then found — in every story, including ones the orchestrator had personally accepted. The
self-verification above did catch three real problems before the lock (V4, V6, V7), which is the
same pattern as sprint 66's self-probe. It is better than nothing and weaker than a second pair of
eyes.

## Post-lock changes (plan verification, 2026-08-02)

The verifier ran after approval and returned **GAPS — a blocker in four of the five stories**. None
of it was taken on the agent's word: the four most consequential claims were re-verified directly
before any story text changed (six `_EXEMPTIONS` keys enumerated via AST; the f-string enum
behaviour on Python 3.13.9; the six `harness.py` literals; `node npm-cli.js --version` → 11.6.2).
All four checked out.

**Eleven AC sharpenings applied directly. One scope change went back to the PO.**

The four that would have cost the most:

1. **STORY-199 AC5** instructed emptying a dict whose sixth entry is `PERMANENT` — following it
   takes the gate RED. This was the sprint's locked headline success measure.
2. **STORY-200 AC4** claimed byte-identical persistence while switching to enum-identity comparison.
   `ProposalState` is `(str, Enum)`, **not** `StrEnum`, so `f"{action}"` yields
   `"ProposalState.APPROVED"` on Python 3.13 — it would have silently corrupted the sort key of
   every approval event written.
3. **STORY-200 AC8** ("existing tests pass unchanged") directly **contradicted AC4**: two
   real-DynamoDB tests pass `action="approved"`, and `"approved" is ProposalState.APPROVED` is
   `False`, so they must change. The story was not completable as written.
4. **STORY-202's promotion silently created six new ZR-3 collisions** in a third file — the exact
   gate-red the story exists to prevent, caused by the story itself.

**PO decision on the scope change:** expand STORY-202 to `harness.py` (2 → 3 points) rather than
adjudicate the six, because they are true positives by the rule's own logic and because growing an
exemption list in the sprint dedicated to shrinking it would be perverse. **STORY-201 (1) was
dropped** to hold the committed 11 points — it was the declared first-to-drop item and no work had
started, so it returns to the backlog as `ready`.

**The honest read on the dispatch:** the orchestrator's own pre-approval probe caught three real
problems (V4, V6, V7) and felt thorough. It missed all four above. That is the sprint-66 finding
reproducing itself one sprint later, at the planning stage rather than the review stage.

## Constraints

- **C1 — every guard entry this sprint retires must be REMOVED, not re-keyed.** ZR-7's and ZR-3's
  entries are keyed by `(file, line)`, and the fixes shift those lines. The temptation is to update
  the key; the correct action is deletion, because the violation is gone. Each guard's
  stale-exemption test enforces this, which is why it is a constraint and not a hope.
- **C2 — no fix lands without something going RED first.** Every story here fixes a defect that
  green tests currently tolerate, so each carries a mutation or pre-fix proof (199 AC6, 200 AC7,
  202 AC4, 210 AC5). A fix whose removal turns nothing red is unpinned, whatever the coverage says.
- **C3 — the DoD change in STORY-210 AC1 is a PO decision**, called out for approval below. It is
  not taken unilaterally, mirroring how the sprint-66 change was handled.
- **C4 — a classification may never downgrade a red.** STORY-210's policy-block detector labels;
  it does not excuse. A blocked command still exits nonzero and still fails the gate (AC4). This is
  written down because "environmental" is exactly the word that could become a wave-through, and
  A12's motivating incident was a guard whose message invited an action its check could not justify.
- **C5 — `REQUIRE_DYNAMO=1` on every backend gate run**, with pass/skip counts recorded. A nonzero
  skip count is an incomplete gate, not a pass. STORY-200 AC5 in particular is meaningless without
  real DynamoDB.
- **C6 — env safety.** STORY-202 edits the mechanism that selects `config/demo` and therefore the
  publish guard itself. AC6 requires re-verifying that `statuspage_mapping()` is still `{}` and
  `build_publisher` still yields a `LoggingPublisher`, rather than reasoning that it should be
  equivalent. `decide` publishes recoveries with no human gate.

## The one decision needed from the PO

**STORY-210 AC1 changes the Definition of Done**: `ruff check .` → `python -m ruff check .`, and
`ruff format --check .` → `python -m ruff format --check .`.

Same checks, same rules, same files — only the entry point moves, exactly as the PO-approved
`lint-imports` (2026-07-12) and `pytest`/`cfn-lint` (2026-07-31) changes did. The difference from
those two is that **`ruff.exe` is not blocked today**, so this is preventive. The argument for doing
it now is that the policy has already widened twice without warning, both times mid-sprint, and the
retro named `ruff.exe` as the likeliest next casualty.

Declining is a reasonable call too — it keeps the DoD stable and accepts the risk of another
mid-sprint red. If declined, STORY-210 drops to AC3–AC8 (the diagnostic) and becomes 1 point, and
the sprint is 10.

## Definition of Done

Unchanged: the eight commands in `.scrum/definition-of-done.md`, all exit 0, evidence emitted by
`yt_gate.py` and merged verbatim. Scoped `--only` runs are permitted per story; the **full 8/8 gate
on the final HEAD is the evidence of record**. Plus the wiki compile pass before review.

## Steps

- [ ] Cut branch `sprint-67` from `sprint-66` at `86459ea`, tag `sprint-67-start`
- [ ] STORY-210 — implementer → both reviewers → gate → reality gate
- [ ] STORY-199 — implementer → both reviewers → gate → reality gate
- [ ] STORY-202 — implementer → both reviewers → gate → reality gate
- [ ] STORY-200 — implementer → both reviewers → gate → reality gate
- [ ] STORY-201 — implementer → gate
- [ ] Wiki compile pass (blocking)
- [ ] Full 8/8 gate on final HEAD → review
