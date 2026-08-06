---
id: STORY-221
title: The frontend gate can false-red under parallel file execution — MaintenancePage inline-422 assertions
type: defect
points: null
status: draft
filed: 2026-08-06
sprint: null
---

## Context

**Filed under the 2026-07-06 working agreement, which requires it:** *"A gate that can flake is
filed as a defect so the mechanical floor stays trustworthy — a flaky gate is never left as the
standing gate."* This story is that filing. It is not a request to change any product behaviour.

## What happened, exactly

During STORY-206's DoD gate (sprint 69, HEAD `51fa6a9`), command 6 of 8 — `npm test` — exited 1
with **2 failures**, both in `frontend/src/pages/MaintenancePage.test.tsx`. The reported failure is
an inline-422 assertion timing out:

```
❯ src/pages/MaintenancePage.test.tsx:339:47
    await within(startField as HTMLElement).findByText('starts_at mu…
```

and the dumped DOM shows the `datetime-local` Start input rendered with `value=""` — i.e. the
`user.type(...)` that should have populated it had not taken effect when the assertion ran, so no
POST fired, so no 422 came back, so the inline error never appeared.

## Why it was discounted as contention, and the proof

Both limbs the 2026-07-06 agreement demands were satisfied **before** the red was discounted:

1. **Empty diff since the sprint cut.** `git diff --stat sprint-69-start..HEAD -- frontend/`
   produced no output. STORY-206 touched `pyproject.toml`, `CLAUDE.md`, `.scrum/definition-of-done.md`
   and five wiki articles — not one file under `frontend/`.
2. **Passes with adequate resources.** `npm test -- --no-file-parallelism` → **51 files / 363
   tests passed**. Then the **unmodified** gate command, run alone via
   `yt_gate.py --only "npm test"` at the same commit `51fa6a9` → **exit 0**, 51 files / 363 tests.

The valid signal is the isolated re-run; it is recorded as STORY-206's `npm test` evidence with a
prominent note, machine-emitted rather than hand-transcribed.

## Why this is worth fixing rather than remembering

The full-gate run executes `npm test` **after** `python -m pytest` (714 tests, ~91s) and alongside
whatever else the machine is doing; run alone it passes. So the failure is a function of load, not
of code — which means **the standing gate can go red on correct work at any time**, and every
occurrence costs a diagnose-and-re-run cycle plus the risk that someone discounts a *real* red by
pattern-matching to this one. That second risk is the expensive one.

This is a distinct defect from the known backend flake (STORY-213, 1-in-11 `list_components`
pagination). Two independent flakes in one gate is the thing to notice.

## Refinement should settle

1. **Is it the `datetime-local` typing specifically?** `user.type()` on a `datetime-local` input is
   a known source of timing sensitivity. Check whether the affected assertions can use
   `fireEvent.change` / direct value set, or `await user.type(...)` with an explicit `waitFor` on
   the field value before submitting — a fix at the test's own seam rather than at the runner's.
2. **Or is it the suite-wide `environment` cost?** The serialized run reported
   `environment 105.65s` against `tests 36.79s`; the parallel run reported `environment 308.88s`.
   jsdom environment setup dominates either way, which points at per-file environment churn as the
   real contention source — possibly fixable with `environmentMatchGlobs` or a shared setup.
3. **Decide the enforcement shape.** Options: fix the assertions (narrow, preferred); pin
   `--no-file-parallelism` in the `test` script (broad, costs ~2× wall-clock — 205s vs 93s
   measured, so it is NOT free); or raise the specific `findBy*` timeout (weakest — it hides
   rather than fixes).
4. **Reproduce it deliberately first.** Do not fix what has not been made to fail on demand: run
   the full gate sequence (not `npm test` alone) several times and record the hit rate, the way
   STORY-213's 1-in-11 was measured. A fix with no measured before/after is not a fix.

## Not in scope

Any change to `MaintenancePage` product behaviour. STORY-213 (the backend pagination flake).
Changing the DoD command list.
