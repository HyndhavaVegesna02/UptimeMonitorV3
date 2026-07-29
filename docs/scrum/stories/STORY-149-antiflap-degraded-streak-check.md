---
id: STORY-149
title: Anti-flap — require a streak for DEGRADED, symmetric with the DOWN ladder
type: defect
---

## Context

`anti_flap` proposes `degraded` for a `DEGRADED` streak of **any length, with no length check
at all** (`backend/src/core/services/pipeline.py:226-227`):

```python
if streak_.health is Health.DEGRADED:
    return _propose(ComponentStatus.DEGRADED)
```

The `DOWN` branch immediately above it requires `length >= thresholds.degraded` before
proposing anything, and returns an unpublishable internal warning for a streak of exactly 1
(`pipeline.py:215-224`). `DEGRADED` has no such damping.

**Repro (why this matters as locations grow).** `_collapse_health` returns `DEGRADED` for
**any** disagreement between a cycle's per-location observations (`pipeline.py:84-97`) — it
returns `DOWN` only when *every* location is down. So:

- With **one** location (today's live topology) a mix is impossible: one observation is either
  `up` or `down`, so `DEGRADED` only arises if the vendor itself reports it. The unguarded path
  is effectively dead code in production.
- With **3–7** locations, a mix is the normal consequence of any single location hiccuping
  **once** — and each such cycle proposes a public status change with **zero anti-flap
  damping**. One blip moving a public status page is precisely what anti-flap exists to prevent.

Given the PO's confirmation that many more components (and their locations) are coming, this
becomes live the moment a second location exists.

This is **Phase 1** of the agreed fix. Phase 2 — the breadth-ceiling model (D1/D2), which also
addresses the `major_outage` severity ceiling and the `degraded` semantic conflation — is a
separate, larger story and is NOT in this sprint. Phase 1 is deliberately scoped to the four
lines that close the damping hole with no modelling debate.

## Description

Make the `DEGRADED` branch of `anti_flap` symmetric with the `DOWN` ladder: require the streak
to reach `thresholds.degraded` before proposing, and return the existing internal-warning
outcome for a streak of exactly 1.

`thresholds.degraded` already means "how many consecutive bad cycles before we call it
degraded" (`AntiFlapThresholds`, `pipeline.py:146-147`), so no new config is needed.

## Acceptance Criteria

- [ ] **AC1** — A `DEGRADED` streak with `length >= thresholds.degraded` proposes
      `ComponentStatus.DEGRADED` (unchanged outcome for the sustained case).
- [ ] **AC2** — A `DEGRADED` streak with `length == 1` returns the **internal-warning** outcome
      (`proposed_status is None`, `internal_warning is True`) — logged, never published —
      exactly as the `DOWN` branch does for a single failure (`pipeline.py:222-223`).
- [ ] **AC3** — A `DEGRADED` streak with a length above 1 but below `thresholds.degraded`
      proposes **nothing** (`proposed_status is None`, `internal_warning is False`). Covers the
      case reachable when `thresholds.degraded > 2`.
- [ ] **AC4 (regression — proves the defect is gone)** — A test asserts the OLD behaviour no
      longer holds: a `DEGRADED` streak of 1 previously proposed `degraded`, and now does not.
      This test must fail if the fix is reverted.
- [ ] **AC5 (degenerate length 0 — symmetry only, NOT a field-impact change)** — A `DEGRADED`
      streak of length 0 returns **nothing** (`proposed_status is None`,
      `internal_warning is False`), exactly as a `DOWN` streak of length 0 does
      (`pipeline.py:224`).
      **`Streak(DEGRADED, 0)` is unreachable from `streak()`** — verified: `pipeline.py:117-121`
      starts `length` at 0 and the first `reversed()` iteration always compares
      `non_maintenance[-1].health` to itself, so any non-`None` return has `length >= 1`; and
      `collapse` emits `health=None` only with `under_maintenance=True`, which `:112` filters out.
      So this AC keeps the ladder symmetric at the unit boundary and nothing more. Nobody should
      hunt for a scenario that produces it. It is a deliberate change to an unreachable unit
      boundary, with no field impact. Note that
      `backend/tests/test_anti_flap.py:240-248`
      (`test_degenerate_degraded_streak_of_length_zero_still_proposes_degraded`) asserts today's
      outcome and is **intentionally rewritten**, not deleted — its replacement asserts the new
      symmetric outcome and keeps the "does not crash / does not mis-bucket" intent.
- [ ] **AC6 (the two tests that assert the defect, named)** — Exactly two existing tests encode
      the old rule and are rewritten with it:
      `test_anti_flap.py:185-190` (`test_sustained_degraded_streak_of_length_one_proposes_degraded`)
      and `test_anti_flap.py:240-248` (above). No other `anti_flap` test changes. Each rewrite
      keeps the original test's intent and renames it to state the new rule.
- [ ] **AC7 (the docstring documents the defect and must change with it)** —
      `pipeline.py:210-211` currently reads "`Health.DEGRADED` … always `degraded` — there is
      only one failing-adjacent bucket for this health, so **no length comparison is needed**".
      That sentence is the defect written down. The docstring is updated in the same diff to
      describe the streak requirement.
- [ ] **AC8 (no collateral change)** — Every existing `anti_flap` test for the `DOWN` and `UP`
      branches passes **untouched** — no assertion is edited, weakened, or deleted. The
      `DOWN` ladder (`major`/`partial`/`degraded`/warning) and the `UP` recovery threshold are
      byte-identical in the diff.
- [ ] **AC9** — All five backend DoD gate commands exit 0.

## Open Questions

None.

**Verified to have no downstream effect** (checked pre-lock, so it is not re-litigated during
implementation): `orchestrate.py:124-139` already returns NOOP when `proposed_status is None`,
so the new "nothing proposed" outcomes need no caller change; and no orchestration or e2e test
drives a `DEGRADED` collapse — `Health.DEGRADED` appears only in `test_anti_flap`, `test_pipeline`,
`test_streak`, `test_availability`, and `test_dynatrace_adapter`. The fix therefore cannot alter
`decide` behaviour.

## History

- 2026-07-28: drafted as Phase 1 (P1) of the anti-flap/breadth work agreed with the PO. Phase 2
  (breadth sets a severity ceiling, duration climbs to it; minority-unreachable caps at
  `partial_outage`) is recorded as D1/D2 in
  `docs/scrum/sprints/2026-07-28-sprint-62/decisions-and-future-work.md` and is explicitly out
  of this sprint. Note that on the live HTTP path today no vendor mapping produces `DOWN` or
  `DEGRADED` at all (`health_mapping.py:65-70`), so this fix is verified against fixtures and
  demo-engine scenarios rather than live vendor failures.
- 2026-07-28: **second verifier pass + PO decision D-A — the reality gate no longer uses the demo
  engine.** It was to be a demo-engine scenario making one location fail for one cycle. That would
  have been a **false pass**: no demo scenario can produce a `DOWN` observation at all
  (`map_synthetic_status` raises on any non-healthy code, `health_mapping.py:65-70`;
  `dispatch.py:80` loses the whole batch when it does), so step 1's "no proposal appears" would
  have held because nothing was ingested, not because anti-flap damped it — and step 2 would then
  have failed, on the last story of the sprint. The gate is now an `orchestrate_signal`-level test
  over **seeded** multi-location observations, which enters the pipeline below the vendor mapping
  and exercises the real `collapse → streak → anti_flap → decide` chain plus real persistence and
  the live HTTP surface, with no invented vendor codes. See `plan.md` "Reality gate (149)".
- 2026-07-28: **amended after `yt-plan-verifier` (pre-lock, verdict GAPS).** Three additions,
  all from reading the existing tests rather than assuming a 4-line change is self-contained:
  the length-0 outcome was unspecified while `test_anti_flap.py:240-248` explicitly asserts
  today's behaviour (now AC5); the two tests that encode the defect are now named (AC6) — the
  original draft said the fix touched no existing test, which was wrong; and the docstring at
  `pipeline.py:210-211` states the old rule verbatim, so it is in scope (AC7). Also recorded:
  the verifier confirmed the fix has no effect in `decide` or in any e2e test, and the reality
  gate is pinned to a **single-monitor** component so the known STORY-151 sibling-OBSOLETE path
  cannot spoof the evidence in either direction.
- 2026-07-29: **implemented and Done.** Commits: `c332f91` (steps 1–4, the four DEGRADED-branch
  tests, confirmed red first — two of them REWRITE the tests that encoded the old rule, per AC6),
  `40e2a2c` (step 5, the fix + the AC7 docstring in the same diff), `8794d7d` (plan ticks after
  steps 6–7), `1e025a8` (the wiki blast-radius pass). Scoped DoD gate 5/5 at `1e025a8`, 572 tests.
  AC8 verified at the diff level, not merely asserted: `git diff 7d3b682..HEAD -- pipeline.py`
  touches only the `DEGRADED` branch and its docstring — `collapse`, `streak`, the whole `DOWN`
  ladder and the `UP` recovery check are byte-identical. The check ORDER is `>= degraded` before
  `== 1`, mirroring `DOWN`, so a config with `degraded == 1` proposes rather than warns exactly as
  `DOWN` does at the same threshold. Reality gate PASS 12/12 (`orchestrate_signal` over seeded
  multi-location observations, real DynamoDB-Local tables, real `/api/v1/approvals` over live HTTP):
  one disagreeing cycle → NOOP, no proposal, empty endpoint; sustained disagreement → exactly one
  open proposal, which the endpoint serves. The same gate, run unchanged at the pre-fix commit
  `7d3b682` in a worktree, scored 7/12 — failing on exactly the five checks this fix owns, and
  nothing else. Pre-fix, a single blip wrote a proposal and served it over HTTP: the defect made
  visible end-to-end rather than argued from a unit test. Honest limit, unchanged from the pre-lock
  note above: both phases are SEEDED, because no vendor mapping produces `DOWN`/`DEGRADED` on the
  live path today (STORY-177). The first implementer died mid-story on an API session limit after
  step 7; the commit-per-green-step cadence meant nothing was lost but the wiki pass, which the SM
  then completed — no code re-derived, no work discarded.
