# Sprint 36 — review (2026-07-06)

**Goal:** Production-hardening: the live loop survives transient vendor/network errors, the
documented `.env`-based startup actually works, and the accumulated quality minors are
cleared.
**Committed:** 050 (3) + 043 (2) + 047 (1) = 6 (PO-directed over-commit). **Delivered for
verdict: all three, 6/6** — the over-commit never bit.
Branch `sprint-36` (cut from main @ `2f4547c`); sprint 35 (deployment) remains parked and
untouched on its own branch.

---

## STORY-050 — live-loop transient-error resilience (defect, 3 pts)

**What:** the 2026-07-03 incident (one SSL handshake timeout killed the whole loop after
2.5h) can no longer happen: `run_periodic` wraps ONLY the `run_cycle` call in
`except Exception`, logs `signal_key` + cause + per-signal consecutive-failure count via
`logger.exception`, and keeps scheduling. Success resets the counter. LOG-ONLY per the PO
decision — the loop never exits on cycle failures. Startup stays fail-fast (secrets are
checked before any loop coroutine exists); cancellation and `stop_event` still stop the
loop, including immediately after a FAILED cycle.

**Evidence:** spec PASS (AC1–AC3 all MET; every design pin traced to a driving test — the
AC1 test asserts the second cycle's ingest actually ran via its `source_event_id`; AC2
asserts `build_live_loop` is never called on missing secrets; counter messages asserted
by content: 1, 2, reset-to-1, and the follow-up 1, 2, 3). Quality APPROVE 0C/0M
("exemplary") — no busy-loop on hard failure, `on_cycle` bugs still propagate,
CancelledError untouched. One spec finding (test peaked at 2 consecutive vs the AC's ≥3)
fixed same-session @ `738d055`. Gates: 504 passed + five green at that SHA.

**Demo:** `pytest backend/tests/test_pull_loop.py -q` — 12 tests including the scripted
fail/fail/succeed/fail and fail×3 sequences.

## STORY-043 — `.env` never loaded (defect, 2 pts)

**What:** `load_dotenv()` now runs at the two process entrypoints (`run.py::main`,
`asgi.py` module init) — the documented "put secrets in `.env` and run" recipe is true for
the first time. Exported env vars ALWAYS win (Railway/production structurally unaffected —
matters for the parked deployment sprint). `python-dotenv` added as a runtime dep.
CLAUDE.md's two false claims and the `dev-setup-and-dod.md` wiki Fact corrected (AC5).

**Evidence:** gate-only pipeline; orchestrator gates @ `0a8b36b`: 508 passed + five green.
Ordering test proves dotenv loads BEFORE settings/secrets in `main()`; asgi mirror test;
precedence test (exported wins). Notable implementer catch: four pre-existing entrypoint
tests would have started loading the REAL repo `.env` after this change — patched to stay
hermetic (no test touches real secrets).

**Demo:** scrub the shell env, keep only `.env`, run `python -m src.composition.run` — it
boots (pre-story it crashed with `MissingLiveSecretError`).

## STORY-047 — quality-review minors (chore, 1 pt)

**What:** all five enumerated minors applied, none stale: (1) `create_app` keeps
status-write-back when `component_repo` is injected without `publication_repo` (was
silently dropping to a bare logger — a real behavior fix from the STORY-045 review);
(2) the `publish_best_effort` dual seam folded into `BestEffortPublisher.publish`;
(3) availability child DTOs derive from `_to_dto()` instead of nine-field duplication;
(4) the double-iteration item deliberately left (no-behavior-change rule, documented);
(5) `FakeSampleModeRepository` store hint parametrized.

**Evidence:** orchestrator gates @ `8237962`: **511 passed** + five green, frontend
untouched across the whole sprint. Wiki: 4 articles updated/re-verified; compile pass
re-pinned `dev-setup-and-dod.md` (sha had been placed at the code commit rather than the
wiki commit — content was already accurate).

## Compile pass
Staleness sweep at HEAD: ALL CURRENT (after the one re-pin). Link lint: 0 broken.

## Blocked stories
None in sprint 36. (Sprint 35 / STORY-017 remains parked by PO direction — resume recipe
in `sprint-current.yaml`; not part of this review.)

## Velocity on acceptance
All three accepted → record `{sprint: 36, committed: 6, accepted: 6}`.

## Retro preview (inputs)
- Implementer session-limit crash recovered cleanly under the 2026-06-25 rule (sprint-35's
  agent, orchestrator finished the sweep tail) — second occurrence of the pattern; the
  agreement is carrying its weight, no amendment obviously needed.
- The STORY-043 hermetic-tests catch (entrypoint side-effects leaking real secrets into
  the suite) is amendment material: "a story adding entrypoint side-effects audits every
  existing test that drives that entrypoint."
