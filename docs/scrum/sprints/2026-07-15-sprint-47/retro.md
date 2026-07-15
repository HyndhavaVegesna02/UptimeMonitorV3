# Sprint 47 Retrospective — dev-db gate false-red fix + two DynamoDB adapters

**Outcome:** 15/15 points accepted (STORY-080, STORY-084, STORY-085), merged to main (`2e29e72`);
accept-with-follow-up (3 minors → STORY-091). Second consecutive external delivery.

## What went well

- **The external-mode verification floor paid off a second time.** Six reviewers (spec + quality
  per story) caught two quality MAJORs the delivery's "all nine gates clean" summary never
  mentioned: STORY-080's bare `except (ImportError, Exception)` in the readiness loop (which
  manufactured the exact opaque false-red the story exists to kill) and STORY-085's dead-code
  `record_approval_event` handler (flagged independently by BOTH reviewers). The floor is now the
  reliable safety net for external work.
- **The dev-db false-red is actually gone.** STORY-080 landed and the full `test_dev_db_*` family
  passed together on a clean slate (17/17), including the two tests that false-red the sprint-46
  gate. This sprint's own `pytest` passed outright (611) with no contention flake — the first clean
  full-suite run in several sprints. The retro's escalation is resolved.
- **Real-container parity held for the adapters.** STORY-084/085 reuse the same contract-assertion
  approach as the earlier DynamoDB adapters against a live DynamoDB-Local container (no mocked
  boto3); the availability-parity test genuinely runs BOTH the Postgres and DynamoDB adapters and
  compares, and the proposal lifecycle test drives the REAL ApprovalService. Genuine reality-gate
  coverage, not internal-consistency theatre.

## What dragged

- **External delivery arrived as one uncommitted tree — no TDD commit cadence.** The crash-recovery
  mechanism (a commit after every green step) was entirely bypassed; the orchestrator had to read
  each diff and commit it as a per-story reviewable object before it could review or gate anything.
  It worked, but only because the orchestrator recognized the situation — the `external` mode spec
  said how to VERIFY but nothing about what to REQUIRE back from the external agent.
- **The full gate silently no-DB'd two commands.** Running `yt_gate.py` standalone left
  `DATABASE_URL` / `DATABASE_URL_DIRECT` unset, so `alembic upgrade head` and
  `check_fk_direction.py` errored on missing-env — a false-red structurally distinct from the code
  failing (the DB-gated *tests* self-provision and passed inside `pytest`; only the two standalone
  CLI commands read the env directly). It surfaced as a raw `KeyError` and cost a diagnose +
  provision + re-run cycle before the evidence was complete.

## Estimates

All three delivered at estimate (080: 5, 084: 5, 085: 5). 15 pts was ~2× recent velocity and a
deliberate PO stretch; it landed, but the two MAJOR fixes + the gate re-run were real orchestrator
overhead on top. No story re-scope.

## Amendments landed (PO-approved 2026-07-15)

1. **External-delivery contract at handoff** — *reference rung* (`references/execution-modes.md`,
   `external` section). The mode spec now states what the orchestrator requires when handing work
   out and checks on return: (a) commit per story with `STORY-NNN:` messages (ideally the per-green
   TDD cadence); if it arrives as one uncommitted blob, the orchestrator commits per-story as the
   reviewable object BEFORE reviewing; (b) never trust a self-reported gate result — the
   orchestrator's own `yt_gate.py` run on the final HEAD is the only record that counts; (c)
   reviewers get each story's own commit range. Makes this sprint's ad-hoc salvage the standing
   expectation. (Motivating incident: sprint-47 uncommitted external delivery + false "all gates
   clean" summary.)

2. **Generic env-precondition preflight in the gate** — *script rung* (`scripts/yt_gate.py`) + a
   project-supplied annotation in `.scrum/definition-of-done.md`. The gate now warns UP FRONT, by
   name, when a command's required env var is unset — instead of surfacing a raw `KeyError` mid-run.
   Kept project-GENERIC per the 2026-07-13 rule: the runner hardcodes no var names; the project's
   DoD line declares them via `(requires-env: VAR, ...)` (annotated here on the alembic +
   check_fk_direction commands with `DATABASE_URL_DIRECT` / `DATABASE_URL`). A literal `$VAR`/`%VAR%`
   scan of the command text is a fallback. Advisory only — it never blocks; the command still runs
   and reds honestly if the missing var truly breaks it. Self-test stays green (28/28); the preflight
   was verified to fire on the exact sprint-47 case.
   *Process note:* the first implementation (a `$VAR` regex over the command string) was a no-op for
   this incident — the env dependency lives INSIDE the invoked code, not in the command text — and
   an over-clever walrus-in-comprehension broke the self-test. Both were caught by verifying before
   claiming done; the shipped version uses the DoD annotation as the reliable signal.

## Forward

Board clean for the AWS epic's next slice: **STORY-086** (DynamoDB publications + maintenance +
rejected-observations adapters + seed rewrite, 5 pts, `ready`) — it depends on STORY-085's
`approved_actor` denormalization, now landed. **STORY-091** (this sprint's 3 deferred minors) is a
draft needing an estimate. After 086 → 087 is the composition cutover (retires the Postgres gate;
the DoD amendment finally takes effect).
