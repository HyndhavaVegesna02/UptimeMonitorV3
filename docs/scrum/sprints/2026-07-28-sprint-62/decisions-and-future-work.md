# Decisions taken + future work (pipeline correctness)

**Date:** 2026-07-28. Decisions from the PO discussion; every claim cites `file:line` at
`main` (`517fc38`). Companion to `calculations-under-new-config.md`.

---

## Decided

### D1 — Breadth sets a severity ceiling; duration climbs to it

`_collapse_health` (`core/services/pipeline.py:84`) currently flattens **any** disagreement
between locations to `Health.DEGRADED`, and `anti_flap` (`pipeline.py:226-227`) proposes
`degraded` for a `DEGRADED` streak **with no length check** — unlike the `DOWN` ladder,
which requires `length >= thresholds.degraded`.

Three defects follow, all invisible at one location and all worsening as locations grow:

1. **No damping.** One location hiccuping for one cycle proposes a public status change,
   which is precisely what anti-flap exists to prevent.
2. **Severity ceiling.** `collapse` returns `DOWN` only when *every* location is down
   (`pipeline.py:95`), so with 7 locations a single surviving probe pins the component at
   `degraded` forever. **`major_outage` becomes practically unreachable as locations grow.**
3. **Semantic conflation.** `Health.DEGRADED` means both "the vendor says it worked but
   performed badly" (`map_execution_outcome`'s `"partial"` → `DEGRADED`,
   `health_mapping.py:26`) and "some locations could not reach it" (produced by `collapse`).
   Those are different facts and want different words.

**Root cause:** severity has two independent dimensions and the design uses only one.
*Breadth* (how much is affected) is `partial_outage`/`major_outage` language; *duration*
(how long it persisted) is the `2/3/5` ladder. Today duration alone drives severity and
breadth is destroyed at collapse. At one location breadth is always 100%, so the flaw
cannot be seen.

**Decision:** the verdict carries `locations_failing` / `locations_total` alongside `health`;
**breadth caps how severe a proposal may become, and the existing duration ladder climbs up
to that cap.**

| Breadth of failure | Severity ceiling |
| ------------------ | ---------------- |
| all locations failing | `major_outage` |
| majority failing | `major_outage` |
| **minority failing** | **`partial_outage`** (PO decision, see D2) |
| vendor reports "worked but poorly" | `degraded` |

Availability and completeness maths are **untouched** — they only ask "is this verdict
`up`?" (`availability.py`), so keeping `health` on the verdict preserves both exactly.

**Backwards compatible at one location**, which is the current live topology:

| Scenario | Today | After D1 |
| -------- | ----- | -------- |
| 1 location, down, 2 cycles | degraded | degraded — unchanged |
| 1 location, down, 3 cycles | partial outage | partial outage — unchanged |
| 1 location, down, 5 cycles | major outage | major outage — unchanged |
| 7 locations, 1 down, 1 cycle | **degraded immediately** ✗ | nothing — unconfirmed ✓ |
| 7 locations, 1 down, 3 cycles | degraded | partial outage, capped ✓ |
| 7 locations, 6 down, 5 cycles | **degraded (stuck)** ✗ | **major outage** ✓ |

With one location breadth is always 100% → ceiling `major_outage` → the 2/3/5 ladder runs
exactly as it does today. No live behaviour change.

### D2 — Minority-unreachable caps at `partial_outage`, not `degraded`

**PO decision 2026-07-28.** Two indistinguishable worlds produce "2 of 7 locations
failing": the service really is broken in those regions (real users down), or those probes
are themselves broken (nothing wrong with the service). The data cannot separate them.

The tie is broken by the **human gate**: anything worse than the currently published status
opens a proposal and **publishes nothing** until a person approves it
(`core/services/decide.py`). So over-classifying costs an operator a glance and a rejection
— not a false public outage. Under-classifying actively misinforms in the reassuring
direction (telling customers "Degraded Performance" while a region times out) and throws
away the very breadth information D1 exists to preserve. `partial_outage` therefore strictly
dominates.

`degraded` is reserved for its literal meaning: the vendor reporting a check that succeeded
but performed badly.

**Condition attached:** an operator can only tell the two worlds apart by seeing *which*
locations and *how many*. This makes the proposal reasoning text **load-bearing, not
cosmetic** — see the `StatusProposal.reason` finding in `ui-backend-gap-analysis.md` §3a
(the field exists at `core/domain/proposal.py:51` and is never populated at open time).

### D3 — Phasing

| Phase | Work | Est | When |
| ----- | ---- | --- | ---- |
| **P1** | Add the streak-length check to the `DEGRADED` branch of `anti_flap`, symmetric with the `DOWN` ladder. Closes defect 1 alone. Four lines, no modelling debate. | ~1 | can land any time |
| **P2** | The full D1/D2 breadth model: verdict carries the location counts, `anti_flap` takes both dimensions, config gains the majority boundary. Closes defects 2 and 3. | ~5 | **prerequisite for real multi-location components** |

**P1 IS in sprint 62** — it is STORY-149. P2 is not; it is STORY-150, deferred. (Corrected
2026-07-28 after `yt-plan-verifier` flagged the original line, "Neither is in sprint-62 (UI)
scope", as wrong on both counts: P1 is in the sprint, and sprint 62 is backend-only, not UI.)

**Dependency to resolve first.** `map_synthetic_status` — the live HTTP path — maps **only**
`code == "0"` / `"HEALTHY"` → `Health.UP` and *raises* on anything else
(`health_mapping.py:65-70`). The real failure codes were deliberately left unmapped pending
live observation (STORY-016b: *"the live verification forces the monitor to fail and reads
the real DOWN/DEGRADED code from this error"*). **So no live-path mapping currently produces
`DOWN` or `DEGRADED` at all**, and P2 could only be reality-gated against fixtures.
Mapping the real failure codes is arguably the first story of the set — everything else here
reasons about failures we cannot yet ingest.

### D4 — A local Grail-shaped demo engine (PO decision 2026-07-28, option **b**)

**Context.** The PO's Dynatrace trial expired 2026-07-28: no observations arrive at all.
Nothing data-dependent can be reality-gated, and the multi-monitor / multi-location
correctness work (D1, D2, F3, freshness) cannot be exercised against realistic scenarios at
any price.

**Decision.** Build a **local HTTP server that speaks the Dynatrace Grail `execute query`
API**, driven by scripted scenario files, and point `DYNATRACE_ENV_URL` at it.

Why this shape (option b) over a fake `Executor` callable (option a): it requires **zero
production-code changes** — one env var — *and* is more faithful, additionally exercising
`make_grail_executor`, the real HTTP client, auth headers and response parsing. It injects
at the seam already documented for exactly this purpose:

```python
# adapters/inbound/dynatrace/query.py:32
Executor = Callable[[str], list[dict]]
#: Production wiring (composition root) will inject a real HTTP-backed
#: implementation; every test in this package injects a fake instead.
```

It only has to parse queries **we generate ourselves** — `build_dql_query` emits three
predictable clauses (`query.py:85-97`).

**It is a scenario player, not a random generator.** Random noise will not reliably produce
the cases that matter. Scenarios are scripted per monitor, e.g. the F3 bug on demand:

```yaml
api-gateway-health:   [up ×5, "down from 2 of 3 locations" ×4, up ×3]
api-gateway-graphql:  [up ×20]
```

**Location:** `tools/` at the repo root, **outside `backend/src/`** — never in the
production image, so a misconfiguration cannot serve fake data to real users. Keeps
import-linter contracts untouched.

**It supersedes `sample_mode`.** `SampleModeIngest` decorates `SignalIngestPort` and flips
**already-normalized** observations to `DOWN` (`composition/sample_mode.py:66-72`), so it
needs real data to have anything to flip — useless with the trial over. The demo engine sits
upstream and additionally exercises the normalizer, health mapping, dispatch, dedup and
watermark logic that sample-mode skips. Sample-mode is already on the removal list
(`docs/scrum/wiki/sample-mode.md`); this is what removes it.

**Two hard constraints:**

1. **Stub the publisher, or point at a throwaway Statuspage page.** `decide` publishes
   recoveries with **no human gate**, so fake outages and recoveries fed into the loop
   **will publish fake statuses to the real public status page.** Non-negotiable.
2. **It cannot validate the vendor failure codes.** `map_synthetic_status` raises on
   anything but `"0"`/`"HEALTHY"` (`health_mapping.py:65-70`) because a real failure code
   has never been observed. Codes the demo engine emits are **assumptions**. The residual
   risk is one string constant — a one-line fix on trial renewal — but it must stay
   labeled, not quietly absorbed as "the failure path is tested".

**Consequence for planning.** This becomes the **first story of sprint 62** and reorders what
follows, because it unblocks both tracks:

- the pipeline correctness work (D1/D2, F3, freshness) becomes verifiable against
  multi-monitor, multi-location scenarios — impossible today;
- the UI can be built and judged **at fleet scale** before the real fleet exists, which
  directly attacks the rejection risk and partly dissolves the "design for n=1 vs the dense
  design" tension (§3a) — both can now be seen.

Est ~5 points.

---

## Future work

### F1 — A rejected proposal reopens on the very next cycle (CONFIRMED defect, pre-existing)

Rejecting a proposal resolves it to `ProposalState.REJECTED`
(`core/services/approval.py:85`), which is terminal (`core/domain/proposal.py:29`). **Nothing
records the rejection as a suppression.** On the next cycle `decide` calls
`get_open(component_id)`, gets `None` (the rejected proposal is no longer open), finds the
proposed status still worse than the published one, and **opens a brand-new identical
proposal** (`core/services/decide.py:129-136`).

So an operator who rejects a proposal for a condition that is still true gets an identical
proposal again one cycle later — every 60s on a fast monitor. This is **not** introduced by
D1/D2; it is live behaviour today, and D2 makes it more visible by proposing on minority
failures too.

Needs a **suppression window after a rejection** — e.g. persist the rejection with a
cooloff, and have `decide` treat a recently-rejected identical (component, to_status) pair
as `NOOP` rather than opening again. Design questions: how long, does it reset if the
severity *increases*, and is the cooloff configurable per app? A rejection should almost
certainly not suppress a *worse* status arriving later.

### F2 — Per-location persistence, to separate a real regional outage from a flaky probe

D1 measures breadth **per cycle** — "2 of 7 failing right now". It cannot distinguish:

- **one location failing continuously for two hours** — a real regional problem, or a dead
  probe that should be fixed; either way actionable and stable, and
- **locations flickering in and out** — noise, where the *set* of failing locations keeps
  changing even though the count stays at ~2.

Tracking a streak **per (signal, location)** rather than per cycle would separate these
automatically, and would let the two worlds of D2 be told apart by the system instead of by
an operator reading the reasoning text.

Deliberately **not** built now: it is meaningfully more machinery (per-location streak
state), and D1 + the duration gate may well prove quiet enough in practice. Build only if
minority-failure proposals turn out noisy once real multi-location monitors are live —
that is an observation to make, not to predict.

### F3 — Per-component decision rollup

Under discussion separately — with N monitors on one component, each signal independently
runs streak → anti_flap → decide for the shared component, so a healthy monitor
`OBSOLETE`s a failing sibling's proposal and publishes a recovery. See
`calculations-under-new-config.md` §3.2. Also a prerequisite for multi-monitor components.
