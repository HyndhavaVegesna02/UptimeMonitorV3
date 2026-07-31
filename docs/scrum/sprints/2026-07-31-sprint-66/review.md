# Sprint 66 — Review

**Date:** 2026-07-31 · **Branch:** `sprint-66` (off `sprint-65`, unmerged) · **Mode:** in-process
**Committed:** 11 points / 4 stories · **Delivered: 11/11 points, all four stories Done**

## The verdict you need to give

All four stories are Done with recorded gate evidence and a full 8/8 green gate at the final HEAD
(689 passed, 0 skipped). Two PO decisions were taken during the sprint and are folded in below: the
DoD invocation change you approved, and the reviewer pass you asked for on STORY-197.

**STORY-197 was Blocked at AC7 for part of the sprint** by the Device Guard regression, and I did not
mark it Done until the gate was genuinely green — the mechanical floor says a nonzero exit is a
nonzero exit. Both gate records, RED and green, are kept in `dod_evidence` rather than the RED being
overwritten.

| Story | Pts | Status | One line |
| --- | --- | --- | --- |
| STORY-194 | 3 | **Done** | The rule catalogue — `zone-rules.md`, rules `ZR-1..ZR-5` (now 8) |
| STORY-195 | 3 | **Done** | Audited `core` + `adapters`, 58 modules |
| STORY-196 | 2 | **Done** | Audited `api` + `composition` + the `tools/`→`src/` boundary, 85 modules |
| STORY-197 | 3 | **Done** | Two guards landed and RED-proven; spec PASS, quality FIX_REQUIRED -> fixed |

## What the sprint actually produced

**A yardstick that didn't exist.** `docs/scrum/wiki/zone-rules.md` — eight rules covering the
boundary violations the eight `lint-imports` contracts structurally cannot see, each with a
normative statement, a source, a compliant citation, and a coverage verdict.

**Two standing guards, both shown RED before being trusted:**
- `backend/tests/test_zr7_pagination_guard.py` — every `.query(`/`.scan(` under
  `adapters/persistence/` must paginate or carry a reasoned exemption.
- `backend/tests/test_zr3_duplicate_declarations.py` — promotes `tools/zr3_duplicate_sweep.py` to a
  standing test so no new `tools/`↔`src/` duplication lands unadjudicated.

**Seven defects found and filed** (`STORY-198`…`STORY-205`), three of which matter beyond hygiene:

1. **A live production defect that does not raise.** `dynamo_maintenance_repository.py:90`'s
   `is_under_maintenance` pairs an unbounded query with a post-read filter and discards
   `LastEvaluatedKey` — past a 1 MB page it returns `False` for a component that **is** under
   maintenance, silently disabling maintenance suppression in `decide`. Four sibling methods share
   the shape. (`STORY-199`)
2. **A credential-safety drift risk.** `env_matrix.py` hardcodes the env-var **key names** the
   harness uses to inject fake credentials. A rename in `settings.py` would silently stop them
   matching and let `asgi.py`'s own `load_dotenv()` supply the **real** Statuspage credentials.
   `CONFIG_DIR` is in the same set and is graded most severe of the seven — it is what selects
   `config/demo` and therefore what empties `statuspage_mapping()`. It *is* the publish guard.
   (`STORY-202`)
3. **`composition/seed_dynamo.py` is an adapter.** Raw `boto3` writes hand-building the key schema
   two repositories already own — a third declaration, on the boot path of both composition roots.
   The drift has already bitten once; `failure_path_reality_gate.py:163-172` carries the scar.
   (`STORY-205`)

Plus **four deferred-guard stories** (`STORY-206`…`209`) carrying the guard sketches for the rules
that are clean today and provable only by mutation.

## The uncomfortable finding, which belongs in the retro

**The audit's value came mostly from adversarially reviewing the audit, not from the audit.**

- STORY-195 first reported zero violations across 58 files with 57 `CLEAN` verdicts. Its quality
  reviewer independently re-read ~46 of those files and found **three MAJORs inside files already
  verdicted `CLEAN`**, including finding 1 above.
- STORY-196 then applied that lesson (per-file read-vs-grep annotations) and **passed spec review on
  the first pass** — but its quality reviewer still found four MAJORs, including finding 3.

Both reviewers found real defects in **every** story this sprint, including ones I had personally
accepted. That is now the third sprint running. It is the strongest argument yet for never trimming
the two-reviewer ceremony to save budget.

## Honest notes on how this sprint was run

- **STORY-197 was written and accepted by the same person for a while.** Its implementer was stopped
  mid-story and could not be resumed, so I completed AC4–AC7 myself and re-derived all four RED
  proofs rather than trusting the agent's self-report. I flagged that gap as material; you asked for
  the reviewer pass, and it promptly found a dangerous defect I had accepted (see the section below).
  That is the single clearest vindication of the two-reviewer ceremony this sprint produced.
- **My own error, caught by a reviewer:** my recovery commit for STORY-195 shipped two unfilled
  `[[…PLACEHOLDER]]` tokens under headings claiming "real output". I had grepped the rescued work
  for `TBD` and missed them. Fixed.
- **I corrected a defect neither reviewer could have caught**, because it emerged from a fix round:
  `ZR-3`'s pinned scope excluded the very violation it adjudicates, which is also why its "narrow"
  measurement returned 0 while a real duplicate stood.
- The plan-verifier was skipped (recorded); my own pre-lock probe caught two gaps that would have
  made STORY-194's AC1 unsatisfiable.

## The Device Guard regression (resolved during the sprint)

Mid-sprint, `pytest` and `cfn-lint` began failing with **"blocked by your organization's Device Guard
policy"**, taking the full gate RED and blocking STORY-197 at AC7. Proven environmental to the
standard the 2026-07-06 agreement demands — not asserted:

- `pytest` passed in isolation via the module form (**689 passed, 0 skipped**); only the `.exe` shim
  was blocked.
- `cfn-lint` was blocked one level deeper, even via `python -m cfnlint` (a blocked DLL).
- `infra/` was untouched all sprint, so `cfn-lint`'s input was byte-identical to green runs earlier
  the same day.
- Reproduced twice, back to back; the other six commands passed, frontend included.
- **It regressed mid-sprint** — the baseline at `d4ad03e` was a full 8/8 green with the same runner.

**Timestamps pin it:** clean at 02:40, 05:07 and 11:16 UTC; blocked at 16:33 UTC the same day.

You approved the fix, and it is in. Both gate records — the RED and the green — are kept in
`dod_evidence`, so the regression stays part of the sprint's history rather than being quietly
overwritten. The underlying policy problem remains filed as **`STORY-210`**; worth raising with
whoever administers Device Guard, because if its coverage keeps widening the next casualty is
`ruff.exe` or the npm toolchain, and the module-form workaround only stretches so far.

## What the STORY-197 reviewer pass found (added after the PO requested it)

You asked for the reviewer pass I flagged as missing. It was the right call — it found a **dangerous
defect in work I had personally accepted**.

**Spec review: PASS on all seven AC**, having independently re-derived all four RED proofs by
mutation and re-run the full gate itself. **Quality review: FIX_REQUIRED, 3 MAJOR.**

**The dangerous one.** ZR-7's guard decided "this method paginates" by finding the string
`LastEvaluatedKey` anywhere in it. The reviewer added a realistic warn-on-truncation stopgap to
`is_under_maintenance` — still reading a single page — and the guard replied *"now loops on
LastEvaluatedKey; remove this exemption, the fix has landed"*, about the exemption covering **the
live production defect**. Following that instruction would have left the defect permanently
unguarded. The guard asserted a conclusion its own proxy could not support.

**Three more blind spots**, each demonstrated green against a deliberately unpaginated call site: a
repository in a subdirectory, a module-level function, and a second unpaginated call inside an
otherwise-paginating method. All four are now closed and re-proven by probe.

**Two findings against me, both fair:** `CLAUDE.md` still instructed the blocked shims after I
changed the DoD — violating the very AC4 discipline this story enforces — and my "8 citation-sweep
failures" count was stale (it is 11, because the prose I wrote introduced three new matches and I
never re-ran it). Both fixed; the second is exactly the C2 rule I had been applying to everyone else.

I also corrected ZR-8's deferral reason, which claimed a guard would be RED on real code — false,
since ZR-3 and ZR-7 were in that same position and this story solved it with exemption lists. The
honest reasons are the two-guard cap and the fact that ZR-8's violations are whole-function shape.

## The DoD change you approved

`pytest` -> `python -m pytest`, and `cfn-lint` -> `python -c "from cfnlint.runner import main;
main()" infra/stack.yaml`. Only the entry points moved; the checks, tests and eight contracts are
unchanged, and both reviewers verified that independently. `cfn-lint` needed a different answer than
I first assumed — it has no `__main__`, so `python -m cfnlint` does not work. `CLAUDE.md`,
`.scrum/definition-of-done.md` and `docs/scrum/wiki/dev-setup-and-dod.md` all now record the reason
and the date, mirroring the 2026-07-12 `lint-imports` precedent. The underlying policy problem
remains filed as **STORY-210**.

## Velocity

Accepted points are recorded once you rule. On the current state: **11 of 11**, against a stated
~9–11 baseline. Sprint 65 ran 13 and bought three fix rounds; this sprint ran 11 and still needed
three fix rounds, which says the fix-round cost is driven by story *kind*, not size — an audit
sprint's output is prose, and prose fails review in ways code does not.
