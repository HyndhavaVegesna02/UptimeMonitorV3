---
id: STORY-221
title: The frontend gate can false-red under parallel file execution — MaintenancePage inline-422 assertions
type: defect
points: 3
status: ready
refined: 2026-08-14   # sprint-72 planning; AC written from the measurements below. LOCKED into sprint 72 by the PO on 2026-08-14.
filed: 2026-08-06
sprint: 72   # story 1 of 4
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

The full-gate run executes `npm test` **after** `python -m pytest` (now 816 tests) and alongside
whatever else the machine is doing; run alone it passes. So the failure is a function of load, not
of code — which means **the standing gate can go red on correct work at any time**, and every
occurrence costs a diagnose-and-re-run cycle plus the risk that someone discounts a *real* red by
pattern-matching to this one. That second risk is the expensive one.

## MEASURED HIT RATE — 2026-08-06 (the filing measurement)

**Four runs of the UNMODIFIED gate command at a single commit (`56491a8`), with zero frontend diff
for the whole sprint, went:**

| run | mode | result |
| --- | --- | --- |
| 1 | parallel, inside the full 8-command gate | **FAIL** (2 tests, inline-422 assertions) |
| 2 | parallel, run alone | PASS |
| 3 | parallel, run alone | **FAIL** (`MaintenancePage.test.tsx:248`, timeout at 5000ms) |
| 4 | parallel, run alone | PASS |
| — | `--no-file-parallelism` ×2 | PASS, PASS (301s and 205s vs ~115s parallel) |

**That is 2 red in 4** — and run 3 failed *alone*, which breaks the "passes in isolation" limb that
discounted the first occurrence. The serialized limb is what held. Different assertions failed on
different runs, so this is a load/timing sensitivity across the file, not one brittle test.

**Not observed across sprint 71's gate runs** (three full runs, plus per-story `--only` runs, all
green on `npm test`). That does not clear it — a 2-in-4 that then goes 0-in-3 is consistent with
load, which is the hypothesis — but it does mean **the baseline must be re-measured before the fix,
not assumed** (AC1). This project has twice found a flake had already evaporated (STORY-178,
STORY-213 at 0-in-12).

## The seam — measured at sprint-72 planning (2026-08-14)

Contained and small, which is why this is a 3 and not an 8:

- `userEvent.setup()` is called with **default options** at **66 sites across 20 files** in the
  frontend suite — none passing options. The default (`setup/setup.js:24`, `delay: 0`) inserts an
  awaited macrotask between **every keystroke**: `keyboard/index.js` runs
  `for (actions) { await wait.wait(this.config); … }`.
- `user.type()` on a `datetime-local` field types the full `'2026-07-09T09:00'` literal — **16
  keystrokes, so 16 awaited macrotasks per field** — at
  `frontend/src/pages/MaintenancePage.test.tsx:286, 287, 332, 333, 366, 367, 399, 400, 437, 438`:
  **10 call sites across 5 tests, all in this one file.** No other test file in the suite types a
  `datetime-local` value (`grep` over `frontend/src`).
- The two `datetime-local` inputs exist only in `frontend/src/pages/MaintenancePage.tsx:167, 191`.
- The assertions that fail are `findBy*` calls with the **default 5000 ms** timeout.
- `beforeEach` calls `vi.setSystemTime(NOW)` **without** `vi.useFakeTimers()`
  (`MaintenancePage.test.tsx:44-51`) — deliberate and documented: MSW's fetch handling needs real
  timers. So the per-keystroke waits are **real** waits competing with 50 other jsdom environments.
- Suite-wide environment cost dominates either way: `environment 105.65s` serialized vs
  `environment 308.88s` parallel, against `tests 36.79s`.

Under contention, 32 real macrotask yields per test plus MSW round-trips is what has to fit inside
5000 ms — and sometimes does not.

## Acceptance Criteria

- [ ] **AC1 (a measured BEFORE, at this sprint's HEAD)** — before any fix, `npm test` is run
      **≥ 8 times in the shape the gate runs it** (i.e. following `python -m pytest`, not alone —
      the filing's run 1 failed inside the full gate), with a verified-empty
      `git diff --stat <sprint-72-start>..HEAD -- frontend/`. Record per-run pass/fail, the failing
      test names and assertions, and wall-clock. **An honest negative is an acceptable result and
      does not block the story** — if the rate is 0/8, say so plainly and proceed; do not
      manufacture a failure. What is NOT acceptable is an unmeasured "it flakes".
- [ ] **AC2 (the fix is at the test's own seam — prohibited by EFFECT, not by location)** — the
      change alters **how input is delivered**, not how long the runner waits and not how much of
      the suite runs at once. The diff must NOT, **by any route**:
      - raise any `findBy*`/`waitFor` timeout (per-call, or via `configure({asyncUtilTimeout})`);
      - **reduce or disable file/worker parallelism anywhere** — not in `package.json`'s `test`
        script, not as a CLI flag, and **not in `frontend/vite.config.ts`** via
        `test.fileParallelism`, `test.pool`, or
        `test.poolOptions.*.{singleFork,singleThread,maxForks,maxThreads}`. `vite.config.ts`
        currently declares **no pool settings at all** (`test: {environment, globals, setupFiles,
        css}`), so adding one there would serialize the suite identically to the flag while
        satisfying a location-scoped prohibition. Named explicitly because pre-lock verification
        found exactly that loophole;
      - add a retry.
      Each hides the defect rather than removing it, and the serialized option costs a measured
      ~2× wall-clock (205s vs 93s). **If the implementer concludes one of these is the only viable
      fix, the story BLOCKS for a PO decision** rather than silently taking the broad option.
      **Two fixes are known viable and violate none of the above** (verified at pre-lock against
      the installed `@testing-library/user-event`: `utils/misc/wait.js` returns immediately when
      `typeof delay !== 'number'`): `userEvent.setup({ delay: null })`, which removes all 16 waits
      per field, and `fireEvent.change`. So this AC does not block the story by construction.
- [ ] **AC3 (the tests still assert what they claimed — mutation-proven)** — this is the
      tests-that-lie guard, and it is the AC that matters most. With the fix in place, break the
      product path each affected test claims to pin — e.g. neutralise `MaintenancePage`'s inline
      field-error rendering — and confirm **every one of the 5 affected tests still fails**. A
      faster input path that also stops detecting a broken 422 render is a worse outcome than the
      flake. Revert the mutation; state the before/after in the report.
- [ ] **AC4 (a measured AFTER, same shape and at least the same N as AC1)** — re-run under the
      same load shape, ≥ the AC1 run count, and record the two rates side by side. If AC1 returned
      an honest negative, say explicitly that the after-measurement cannot be compared to it and
      that the fix rests on the seam analysis alone — **do not present an uncomparable pair as a
      before/after**.
- [ ] **AC5 (determinism is not bought with wall-clock)** — record `npm test` total wall-clock
      before and after. A material regression (say >20%) means the fix serialized something and
      must be reported as such, not absorbed silently.
- [ ] **AC6 (no product behaviour change, and the diff check reaches the config files too)** —
      `git diff` touches no file under `frontend/src/` other than test files and test setup, **and
      no `frontend/` root config file** (`vite.config.ts`, `package.json`, `tsconfig*.json`). The
      second half is not decoration: scoping this check to `frontend/src/` alone would let AC2's
      prohibited serialization land in `vite.config.ts` unseen by both ACs. If a product or config
      file genuinely must change, it is named with its reason in the report; "Not in scope" below
      still governs.
- [ ] **AC7 (gate)** — the DoD commands the diff can affect exit 0, `npm test` among them, at the
      story's final HEAD. Run the wiki sweep after the last commit and take what it returns; do
      **not** pre-declare a blast radius (`plan-verification.md:19`). For information only, not as
      a prediction: `MaintenancePage.test.tsx` is in no article's `code_refs`, and
      `MaintenancePage.tsx` / `vite.config.ts` / `package.json` are `code_refs` of
      `frontend-zone.md`, which is currently `status: stale` and therefore not swept.

## Open Questions

None. The three refinement questions in the filing are settled above: the `datetime-local` typing
path is the measured seam; the jsdom environment cost is real but is the suite's shape, not this
story's scope; and the enforcement shape is fixed by AC2 (narrow, at the test seam).

## Not in scope

Any change to `MaintenancePage` product behaviour. The suite-wide jsdom environment cost
(`environmentMatchGlobs`, shared setup, pool tuning) — that is a separate optimisation story and
would change every test file. STORY-213 (the backend pagination flake, now measured 0-in-12).
Changing the DoD command list — STORY-224 owns that this sprint.

## History

- 2026-08-06: filed from STORY-206's gate red. Measured 2-in-4 the same day.
- 2026-08-14: **refined at sprint-72 planning, estimated 3.** The seam was measured (10 `user.type`
  calls on `datetime-local` across 5 tests, all in one file; 16 awaited macrotasks per field;
  default 5000 ms `findBy` timeout), which is what makes a narrow fix credible and bounds the
  estimate. AC1/AC4 require a measured before and after in the gate's own load shape, with an
  honest negative explicitly permitted — sprint 71 saw two flakes evaporate before their fix.
  AC3 was added because a faster input path is exactly the kind of change that can silently stop
  asserting; the risk here is not "does it still pass" but "does it still fail when it should".
