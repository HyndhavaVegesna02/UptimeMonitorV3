---
id: STORY-177
title: Provisional Dynatrace failure-code mapping — unblock failure-path demos and tests
type: chore
---

## Context

**There is currently no way to get a `DOWN` or `DEGRADED` observation into the system through the
real ingest path.** `map_synthetic_status` maps only `code == "0"` / `message == "HEALTHY"` → `UP`
and **raises** `UnknownVendorStatusError` on everything else
(`backend/src/adapters/inbound/dynatrace/health_mapping.py:65-70`). The omission is deliberate and
argued in that file (`:57-63`):

> Only the known-good value is mapped … Any other value raises `UnknownVendorStatusError` rather
> than guessing — the live verification (plan T6/AC6) forces the monitor to fail and reads the real
> DOWN/DEGRADED code from this error, and the mapping is extended with the observed value(s) THEN.
> Inventing failure codes here would silently mis-map (or mask) the real failure value during that
> verification, so it is deliberately NOT done.

That reasoning was sound when a live tenant existed. It no longer holds unchallenged: the PO's
Dynatrace trial expired 2026-07-28, so the "live verification" the comment defers to **cannot
happen**, and in the meantime the entire failure half of the business logic is unexercisable
end to end.

Two aggravating facts, both verified:

1. `dispatch.py:80` normalizes rows in a bare list comprehension, so a single failure-coded row
   raises and **the whole batch for that signal in that cycle is discarded** — healthy rows
   included. A real failure would cost us data, not just a mapping miss.
2. The codebase's own wiring test can only drive a `DOWN` by monkeypatching the mapping
   (`backend/tests/test_pull_loop.py:139-145`, with a comment saying exactly that). Anything that
   is not an in-process test — a demo engine, a staging run, an operator reproducing a report —
   has no route at all.

Found by the second `yt-plan-verifier` pass at sprint-62 planning, after two planning revisions
and one earlier verifier pass had all reasoned past it. Recorded as decision D-A in
`docs/scrum/sprints/2026-07-28-sprint-62/plan.md`; the PO chose to scope sprint 62's demo to `UP`
+ absence scenarios rather than take this on as a demo prerequisite, and to make it a first-class
story with its own review instead.

## Description

Add a **provisional, explicitly-labelled, single-sourced** failure-code mapping so the failure path
can be exercised before the real vendor codes are known — without the "silent mis-mapping" the
existing comment warns against.

The design problem is real and the story should be planned, not just implemented: the whole value
of today's fail-loud behaviour is that when a real failure finally arrives, we *see* the true code
instead of quietly bucketing it. Any solution must preserve that. Sketches to weigh at planning,
not decisions:

- **A gated mapping** — provisional codes apply only when explicitly enabled (env var or injected
  policy), so default/production behaviour stays byte-identical and fail-loud. Costs a config
  surface, and partly overlaps `sample_mode` (which STORY-155 removes).
- **An unconditional provisional mapping with loud provenance** — map a named set and log at
  WARNING with "provisional, unverified" whenever one is hit, so a real code arriving under a
  provisional label is still visible in the logs. Simpler; weaker guarantee.
- **Inject the mapping through the port** — the hexagonally-clean answer, and the most work.

Whichever is chosen, `dispatch.py:80`'s batch-loss behaviour should be fixed or consciously
accepted in the same story, since it is the reason a mapping miss is expensive.

## Acceptance Criteria

Drafted, not refined — this needs a refinement pass with the PO before it can enter a sprint.

- [ ] **AC1** — A `DOWN` and a `DEGRADED` observation can each be produced end to end through the
      real ingest path (DQL row → normalizer → `SignalObservation`) with no monkeypatching.
- [ ] **AC2** — Every provisional code lives in **one** named constant with a comment stating it is
      unverified and naming STORY-154 as the story that replaces it. No provisional code appears
      anywhere else in the codebase.
- [ ] **AC3** — When a real (non-provisional, unrecognized) code arrives, it is still surfaced
      loudly enough to be read and mapped — the property the current fail-loud design exists to
      protect. The story states explicitly how this is preserved under the chosen approach.
- [ ] **AC4** — `dispatch.py:80`'s whole-batch loss on a single bad row is fixed, or explicitly
      accepted with a recorded reason.
- [ ] **AC5** — Production behaviour with no provisional mapping enabled is unchanged, asserted by
      a test that the existing fail-loud path still raises.
- [ ] **AC6** — All five backend DoD gate commands exit 0.

## Open Questions

1. **Gated or unconditional?** (see Description) — affects blast radius and whether this can ship
   without a config surface.
2. **Does this supersede STORY-154 or precede it?** STORY-154 (map the *real* codes) stays blocked
   on trial renewal; this story is explicitly the stopgap. Confirm both remain, with 154 replacing
   this story's constant rather than duplicating it.
3. **Does it unblock anything beyond demos?** Likely yes — STORY-150's breadth model and STORY-151's
   per-component rollup both reason about `DOWN`/`DEGRADED` breadth and currently have no
   end-to-end verification route either.

## History

- 2026-07-28: created by PO decision D-A at sprint-62 planning, after the second `yt-plan-verifier`
  pass found that no demo scenario can produce a failure observation. Deliberately NOT folded into
  sprint 62 as a demo prerequisite: it changes `backend/src/` (which is what keeps STORY-148 and
  STORY-176 low-risk), it takes a slice of STORY-154, and it runs against the producing file's
  explicit written intent — so it earns its own review rather than arriving as a side effect.
  Draft status: needs refinement + estimate before entering a sprint.
