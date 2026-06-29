# Sprint 20 — Retrospective

**Outcome:** 5/5 accepted (STORY-016) after one fix loop. **The backend is now wired for LIVE
operation** — real Dynatrace Grail DQL executor + real Statuspage HTTP executor + the live composition
driver (`python -m src.composition.run`) assembling `BestEffortPublisher(RecordingPublisher(
StatuspagePublisher))` over a config-seeded spine. Velocity history `…, 5, 5, 5`; last-3 mean **5.0**.

## The headline: a spec-rigor agreement earned its keep
STORY-016 shipped with all six DoD gates green — and a production-fatal bug. `composition/run.py` built
the publisher chain with the wrong constructor kwarg (`publisher=` instead of `delegate=`), so
`build_live_loop` raised `TypeError` the instant it ran: `python -m src.composition.run` could never
start. The gate stayed green because the assembly test **patched every constructor `__init__` to a
no-op** and asserted only call-counts — a textbook "test that lies."

This is exactly the failure mode the **2026-06-29 spec-review-verifies-AC-test-drives-behavior**
agreement was written for (born from Sprint 17's rigged AC3 test). Both Opus reviewers — spec AND
quality — independently traced the test bodies, saw the constructors were stubbed, and flagged the
matched pair. The mechanical floor could not catch this; the human-rigor layer did. The agreement is
working as designed.

## What went well
- **Both reviewers converged on the same root cause** without prompting — the over-mock hid the bug
  from the gate but not from a reviewer reading the test body.
- The fix was tightly scoped and the **rewritten test now genuinely guards the regression** (it
  constructs the real objects, so the old `publisher=` wiring makes it error, not pass).
- Everything OUTSIDE the assembly was solid first pass: named errors on both executors, empty-input
  tests, no vendor-type leak, and the engine dispose-on-failure (the highest-risk agreement) was real
  and properly tested.
- Resuming the two reviewer subagents via SendMessage after a mid-dispatch session-limit reset worked
  cleanly — no re-derivation, both returned full verdicts.

## What surfaced — the recurring "over-mocked composition test" hazard
The bug was only possible because the test mocked the very constructors whose wiring it claimed to
verify. A composition/assembly test that stubs the things being assembled proves nothing about the
assembly. This is the third "green test, wrong path" incident (Sprint 14 committed-tree, Sprint 17
rigged AC3, now Sprint 20 over-mock) — each a different disguise of the same lie.

## Process change (PO-approved)
1. **New working agreement (2026-06-29):** **a composition/assembly test constructs the REAL wired
   objects — it must not patch the `__init__` of the components it is asserting the wiring of.** Mock
   only the genuine I/O edges (the HTTP seam, the DB engine, `run_periodic`/`asyncio.sleep`); let the
   publishers/services/repos be built for real and assert the actual nesting (`isinstance` chain /
   `_delegate` references) and the kwargs threaded onward. Stubbing a constructor under test makes a
   wrong kwarg name pass silently — the exact gap that let a `TypeError`-on-startup ship green. Checked
   at quality review for any wiring/assembly test.

## Roadmap — what's left
The backend is complete AND live-wired. Remaining work is credential-observation + deployment + frontend:
- **STORY-016 live smoke (manual, AC5):** with `.env` set, run the loop against a throwaway/Neon
  Postgres, force the Dynatrace monitor to fail → proposal via `GET /api/v1/approvals` → approve →
  `xdnywbx77npw` flips on Statuspage + a `publications` row. The one open integration risk is whether
  the live Grail response field names match the recorded-fixture shape (flagged in
  [[dynatrace-adapter]] and plan.md); if not, it's a one-line fix in the executor's response mapping.
- **STORY-017** — deployment topology (Railway/Vercel/Neon); migrate → seed → serve + run the loop.
- **STORY-015** — frontend dashboard (six tabs); MUST be split before it enters a sprint; needs the
  Vitest/Playwright tooling decision. The read/write API it consumes is fully built.
