# Sprint 66 — Review

**Date:** 2026-07-31 · **Branch:** `sprint-66` (off `sprint-65`, unmerged) · **Mode:** in-process
**Committed:** 11 points / 4 stories · **Delivered: 8 points done, 3 points blocked**

## The verdict you need to give

Three stories are Done with recorded gate evidence. **STORY-197 is Blocked at its final AC by an
environment regression, not by its own work** — I did not mark it Done, because the mechanical floor
says a nonzero exit is a nonzero exit. Your call at the bottom.

| Story | Pts | Status | One line |
| --- | --- | --- | --- |
| STORY-194 | 3 | **Done** | The rule catalogue — `zone-rules.md`, rules `ZR-1..ZR-5` (now 8) |
| STORY-195 | 3 | **Done** | Audited `core` + `adapters`, 58 modules |
| STORY-196 | 2 | **Done** | Audited `api` + `composition` + the `tools/`→`src/` boundary, 85 modules |
| STORY-197 | 3 | **Blocked** | Two guards landed and RED-proven; blocked at AC7's full 8/8 gate |

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

- **STORY-197 has had no reviewer pass at all.** Its implementer was stopped mid-story and could not
  be resumed, so I completed AC4–AC7 myself and re-derived all four RED proofs rather than trusting
  the agent's self-report. But no independent eyes have checked it. Given the record above, that gap
  is material.
- **My own error, caught by a reviewer:** my recovery commit for STORY-195 shipped two unfilled
  `[[…PLACEHOLDER]]` tokens under headings claiming "real output". I had grepped the rescued work
  for `TBD` and missed them. Fixed.
- **I corrected a defect neither reviewer could have caught**, because it emerged from a fix round:
  `ZR-3`'s pinned scope excluded the very violation it adjudicates, which is also why its "narrow"
  measurement returned 0 while a real duplicate stood.
- The plan-verifier was skipped (recorded); my own pre-lock probe caught two gaps that would have
  made STORY-194's AC1 unsatisfiable.

## Why STORY-197 is Blocked — and the decision I need

The full 8/8 gate exits 1. `pytest` and `cfn-lint` both fail with **"blocked by your organization's
Device Guard policy"**. Proven environmental to the standard the 2026-07-06 agreement demands:

- `pytest` passes in isolation via the module form — **689 passed, 0 skipped** (685 + the 4 new
  guard tests). Only the `.exe` shim is blocked.
- `cfn-lint` is blocked one level deeper, even via `python -m cfnlint` (a blocked DLL), so the module
  form is **not** a workaround for it.
- `infra/` is untouched all sprint, so `cfn-lint`'s input is byte-identical to green runs earlier the
  same day.
- Reproduced twice, back to back. The other six commands pass, frontend included.
- **It regressed mid-sprint** — the baseline at `d4ad03e` was a full 8/8 green with this same runner.

Filed as **`STORY-210`**, and it blocks the DoD gate itself, so it blocks every future story.

**Three decisions for you:**

1. **STORY-197** — accept it despite the RED gate (the work is complete and verified, the failure is
   demonstrably not its own), or leave it Blocked and carry it into sprint 67?
2. **`STORY-210`** — there is direct precedent for the fix: the same policy blocked
   `lint-imports.exe` and the DoD command was changed to the module form. I recommend the same for
   `pytest` (`python -m pytest`). **Editing `.scrum/definition-of-done.md` is your call and I have
   not touched it.** `cfn-lint` needs a separate answer — reinstall `regex`, a policy exemption, or
   move it to CI.
3. **Should STORY-197 get its reviewer pass** before the guards are trusted further?

## Velocity

Accepted points are recorded once you rule. On the current state: **8 of 11**, against a stated
~9–11 baseline. Sprint 65 ran 13 and bought three fix rounds; this sprint ran 11 and still needed
three fix rounds, which says the fix-round cost is driven by story *kind*, not size — an audit
sprint's output is prose, and prose fails review in ways code does not.
