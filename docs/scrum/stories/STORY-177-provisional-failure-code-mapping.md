---
id: STORY-177
title: Provisional Dynatrace failure-code mapping — unblock failure-path demos and tests
type: chore
points: 3
status: ready
refined: 2026-07-30
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
   raises and the whole batch for that signal in that cycle is discarded — healthy rows included.
   **Refinement 2026-07-30 found this understates the damage:** the raise happens inside
   `fetch_observations` (`adapter.py:44`), which runs *before* `ingest_observations`
   (`pull_loop.py:102` then `:109`), so `_watermark_repo.advance` (`ingest_service.py:139`) is
   never reached. `run_periodic` catches the exception, logs ERROR, sleeps, and re-queries **the
   same window** next cycle — containing the same unmappable row. One bad row therefore does not
   cost one batch; it **stalls that signal permanently**. This is now its own story,
   **STORY-190**, sequenced BEFORE this one.
2. The codebase's own wiring test can only drive a `DOWN` by monkeypatching the mapping
   (`backend/tests/test_pull_loop.py:139-145`, with a comment saying exactly that). Anything that
   is not an in-process test — a demo engine, a staging run, an operator reproducing a report —
   has no route at all.

Found by the second `yt-plan-verifier` pass at sprint-62 planning. Recorded as decision D-A in
`docs/scrum/sprints/2026-07-28-sprint-62/plan.md`.

## Description

Add a **provisional, explicitly-labelled, single-sourced** failure-code mapping so the failure path
can be exercised before the real vendor codes are known — without the "silent mis-mapping" the
existing comment warns against.

**Approach: unconditional mapping with loud provenance (PO-decided 2026-07-30).** A named set of
ASSUMED `(code, message)` pairs maps to `Health.DOWN` / `Health.DEGRADED` at all times — no env
var, no config surface, no injected policy. Every provisional hit logs at WARNING naming the code,
the message, and its unverified status.

Why this and not the two alternatives (recorded so it is not re-litigated):

- **An env gate buys nothing for the property it appears to protect.** The value of today's
  fail-loud behaviour is that a *real* failure code surfaces so it can be read and mapped. A code
  outside the provisional set raises identically whether or not a gate exists — so AC3 holds either
  way. Meanwhile a gate adds a second thing that must be set on **both** the loop process and the
  API process, which is exactly the footgun class that cost sprint 64 real effort with `CONFIG_DIR`
  (see CLAUDE.md's demo-engine section). It would also partly duplicate `sample_mode`, which
  STORY-155 removes.
- **Injecting a mapping policy through a core-owned port would be worse hexagonally, not better.**
  Ports the core owns must be expressible **in domain types** (CLAUDE.md §4). An interface for
  status mapping would have to name `code` / `message` — vendor vocabulary — dragging Dynatrace
  concepts toward the core. Injection buys configurability, not purity. The correct home for
  vendor-word→domain-type translation is the inbound adapter it already lives in.
- The residual risk of unconditional mapping is bounded: if the real DOWN code turns out to differ
  from the assumed one, the assumed pair simply never occurs in production, and any real code still
  raises. If the real code *matches* the assumed pair, we mapped it correctly and the WARNING names
  it. There is no state in which a real code is silently swallowed.

## Zone constraint (binding — CLAUDE.md §4)

The entire change is confined to `backend/src/adapters/inbound/dynatrace/`. In particular:

- **No change to `core/`.** `Health.DOWN` and `Health.DEGRADED` already exist and are already
  mapped from the legacy outcome path (`health_mapping.py:23-27`); no new enum member, no new
  domain type, no new port.
- Vendor vocabulary (`code`, `message`, the literal code strings) must not appear outside
  `adapters/inbound/dynatrace/`.
- The eight `lint-imports` contracts must pass unchanged; no contract may be edited to accommodate
  this story.

## Acceptance Criteria

- [ ] **AC1** — A `DOWN` and a `DEGRADED` observation can each be produced end to end through the
      real ingest path (DQL row → `normalize_rows` → `SignalObservation`) with **no monkeypatching**
      and no test double for the mapping. Asserted by tests that call the real
      `normalize_rows`.
- [ ] **AC2** — Every provisional code lives in **one** named constant in
      `adapters/inbound/dynatrace/health_mapping.py`, with a comment stating it is UNVERIFIED and
      naming STORY-154 as the story that replaces it. The literal code/message strings appear
      **nowhere else in the repository** — including
      `tools/demo_engine/assumed_failure_codes.py`, which must **import** them from
      `src.adapters.inbound.dynatrace.health_mapping` rather than redeclaring them. (Direction is
      fixed by CLAUDE.md: `tools/` may import `src.*`, never the reverse.) Asserted by a test that
      greps/scans the tree for the literals, or by the demo-engine constant being an import alias
      with a test asserting identity with the backend constant.
- [ ] **AC3** — A `(code, message)` pair **outside** the provisional set still raises
      `UnknownVendorStatusError`, and the message still names the real `code` and `message` so an
      operator can read and map it. This is the property the fail-loud design exists to protect;
      a test asserts it explicitly.
- [ ] **AC4** — Every provisional hit logs at **WARNING**, naming the code, the message, and that
      it is provisional/unverified pending STORY-154. Asserted with `caplog`, including that a
      genuine `HEALTHY` row logs **no** such warning (so the warning is a real signal, not noise).
- [ ] **AC5** — `tools/demo_engine/assumed_failure_codes.py`'s docstring is corrected. Its current
      instruction — *"Do NOT use these to add a failure mapping to `backend/src/`; that is a
      separate, first-class, reviewed decision (STORY-177)"* (`:16-18`) — becomes **false** the
      moment this story lands, and its claim that the pair "carries no special acceptance anywhere
      in `backend/src/`" (`:31-32`) becomes false too. Both are rewritten to describe the new
      reality and still state that the codes remain UNVERIFIED.
- [ ] **AC6** — `health_mapping.py`'s module docstring (`:8-12`) and `map_synthetic_status`'s
      docstring (`:55-63`) are rewritten. The superseded argument ("failure codes are added once
      observed live", "deliberately NOT done") is replaced by the current reasoning **and states
      why it was superseded** (trial expired 2026-07-28; the deferred live verification cannot
      happen) so a future reader does not read the change as a regression.
- [ ] **AC7** — The zone constraint above holds: `git diff --name-only` for this story touches no
      file under `backend/src/core/`, and the eight `lint-imports` contracts pass unedited.
- [ ] **AC8** — The five backend DoD gate commands exit 0. (Frontend is untouched; the full
      eight-command gate is the record at sprint close.)

## Resolved questions (refinement 2026-07-30)

1. **Gated or unconditional?** → **Unconditional with loud provenance**, PO-decided. Full reasoning
   in Description above, including why the gate does not protect AC3 and why port injection is
   hexagonally worse.
2. **Does this supersede STORY-154 or precede it?** → **Precedes it; both remain.** STORY-154 (map
   the *real* codes) stays blocked on trial renewal. When it lands it **replaces the contents of
   this story's single constant** and deletes the provisional label — it must never add a second,
   parallel mapping. AC2's single-constant rule is what makes that replacement a one-line change.
   STORY-154's story file should be updated to say so.
3. **Does it unblock anything beyond demos?** → **Yes, confirmed.** STORY-150 (breadth sets a
   severity ceiling) and STORY-151 (per-component worst-of rollup) both reason about `DOWN` /
   `DEGRADED` breadth and today have no end-to-end verification route whatsoever. Neither is in
   this sprint, but both become verifiable after it. STORY-191 (this sprint) is what actually
   exercises the path through the live loop.

## Dependencies

- **Sequenced after STORY-190** (partial-batch resilience). 190 makes an unmappable row survivable;
  this story then lands the mapping on a path that already degrades gracefully. Reversing the order
  would mean shipping a mapping while a single unrecognised code can still stall a signal.
- **STORY-191 depends on this** — it drives a real `DOWN` through the demo loop and is the reality
  gate for AC1's claim at loop scale.

## History

- 2026-07-28: created by PO decision D-A at sprint-62 planning, after the second `yt-plan-verifier`
  pass found that no demo scenario can produce a failure observation. Draft status: needed
  refinement + estimate before entering a sprint.
- 2026-07-30: **refined and estimated at 3 points; status `ready`.** PO chose the unconditional
  approach. AC4's batch-loss item was **split out into STORY-190** and sequenced first, after
  refinement found the defect stalls a signal permanently rather than costing one batch. AC grew
  from 6 to 8 items: the zone constraint, the `tools/`→`src/` single-source rule, the two
  now-false docstrings, and the WARNING assertion are all explicit because sprint 65 runs in
  **external** mode, where `plan.md` and the AC are the entire contract and nothing is inferred.
