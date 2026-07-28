# How the calculations work — and what the new config shape changes

**Date:** 2026-07-28. Every claim cites `file:line` at `main` (`517fc38`).
Companion to `config-shape-proposal.yaml` and `ui-backend-gap-analysis.md`.

---

## 1. The live pipeline, per monitor

One `run_periodic` coroutine per **signal** (= per monitor) — `composition/run.py:136`.
Each cycle of one monitor runs five stages:

### Stage 0 — Ingest: one monitor → many location rows

`build_dql_query(native_id=…)` filters `dt.synthetic.monitor.id == "<native_id>"`
(`adapters/inbound/dynatrace/query.py:86`). One query, one monitor. The response holds
**one row per location per execution** — `http_normalizer.py:4`: *"One row is one location
execution; this function never aggregates across rows."*

Every row is flattened to a `SignalObservation` carrying the **same `signal_key`** and its
**own `location`** (`_assembly.py:105,114`). The location value on the real wire is an
opaque entity id — `SYNTHETIC_LOCATION-000000000000005C`
(`tests/fixtures/dynatrace/grail_synthetic_events.json:12`, a real captured sample).

### Stage 1 — Bucket into cycles

`bucket_into_cycles` (`core/queries/availability.py:133`) floor-divides each
observation's offset from `since` by `interval`; bucket *k* covers
`[since + k·interval, since + (k+1)·interval)`. **Empty buckets are never returned** — a
missing bucket *is* a gap, detected by comparing `len(buckets)` against the expected cycle
count (`ceil((until − since) / interval)`).

### Stage 2 — Collapse: N locations → 1 verdict

`collapse` (`core/services/pipeline.py:40`) reduces one cycle's per-location observations
to a single `Verdict`. The verdict's instant is `max(observed_at)` across the cycle — *"when
the slowest-reporting location actually completed"* (`pipeline.py:63`).

`_collapse_health` (`pipeline.py:84`) is the rule that matters:

| Locations in the cycle report | Cycle verdict |
| ----------------------------- | ------------- |
| all `up` | `up` |
| all `down` | `down` |
| **anything else** (any mix, or all `degraded`) | **`degraded`** |

If `under_maintenance` is true, the verdict is maintenance with `health=None` and never
participates in health reasoning (`pipeline.py:66-72`).

### Stage 3 — Streak

`streak` (`pipeline.py:100`) reads verdicts backward from the newest, **skipping
maintenance verdicts entirely** (they neither break nor extend a run), counting while the
health matches. Returns `None` if there is no non-maintenance verdict.

### Stage 4 — Anti-flap

`anti_flap` (`pipeline.py:199`) maps streak → proposed `ComponentStatus` against the
per-app thresholds (`major: 5, partial: 3, degraded: 2, recovery: 2`):

```
DOWN     length >= major    -> major_outage
         length >= partial  -> partial_outage
         length >= degraded -> degraded
         length == 1        -> internal warning (logged, NEVER published)
DEGRADED (any length)       -> degraded          <-- NO length check (pipeline.py:226)
UP       length >= recovery -> operational
```

### Stage 5 — Decide

`DecideService.decide` (`core/services/decide.py:79`) compares the proposal to the
component's **currently published** status:

- **worse than current** (a degradation) → open a `StatusProposal` for human approval.
  Nothing is published. An existing open proposal at a different status is resolved
  `SUPERSEDED` and a new one opened; an identical one is left alone (`NOOP`).
- **better than current** (a recovery) → **published immediately**, no gate
  (`decide.py:122-126`).
- **recovered while a degradation is pending** → the open proposal is resolved
  `OBSOLETED` and nothing is published (`decide.py:163-168`) — the outage was never shown.

Repository writes happen **before** the publish (commit-first, no rollback).

---

## 2. Availability and completeness — a separate, on-demand path

Never cached, never stored; computed per request by `AvailabilityCalculator.compute`
(`availability.py:182`). It reuses `collapse` but **never consults the streak**.

**Availability %** — over collapsed *verdicts*:

```
availability_pct = passing_verdicts / (total_verdicts − maintenance_verdicts)
```

`up` passes; `down`/`degraded` don't. Maintenance is excluded from **both** sides. Gaps are
excluded from the denominator entirely — a missing cycle never reaches `collapse`, so it
can be neither passing nor maintenance. Zero observations → `None`, never a misleading
`0.0` (`availability.py:47-48`).

**Completeness %** — over raw *observations*, at a deliberately different grain:

```
completeness_pct = actual_observations / (intervals × distinct_locations)
   where intervals          = window / interval
         distinct_locations = COUNT(DISTINCT location)  ← OBSERVED (availability.py:74)
```

The location-aware denominator is what stops a 3-location signal reporting 300%
completeness (`availability.py:16-18`).

**Component rollup** — `rollup_group` (`availability.py:285`):

- `availability_pct`, `completeness_pct` → **MIN** of the children that have a value.
  `None` children are excluded from the min (a no-data child can't drag a healthy group to
  "unknown"); if every child is `None`, the rollup is `None`.
- `total_verdicts`, `passing_verdicts`, `maintenance_verdicts`, `gap_verdicts` → **SUM**
  across *all* children including no-data ones, so an absent child stays visible.
- `distinct_locations` → **deliberately NOT summed** (`availability.py:306-310`): it exists
  per-leaf to make one signal's denominator auditable, and summing would double-count
  shared locations.

So a component's availability is *its worst monitor's* availability. That is already
multi-monitor-correct and needs no change.

---

## 3. What the new config changes

### 3.1 `expected_locations` fixes a real blind spot — with arithmetic

Today `distinct_locations` is what was **observed**. If a location goes *completely* dark
for the whole window, it silently leaves the denominator.

Worked example — 24h window, `interval_seconds: 120` → 720 cycles, 3 expected locations,
Mumbai fully dark all day, the other two reporting perfectly:

| | actual obs | denominator | completeness |
| --- | --- | --- | --- |
| **today** (observed locations = 2) | 1440 | 720 × **2** = 1440 | **100.0%** ← blind |
| **with `expected_locations`** (= 3) | 1440 | 720 × **3** = 2160 | **66.7%** ← correct |

And note what availability does in the same scenario: every cycle still has two locations
reporting `up`, so every verdict collapses to `up` and **`availability_pct` is 100%**.
That is *correct* — the service genuinely was up. Completeness is the only number that can
say "we are a third blind", which is precisely the availability-vs-completeness separation
the design exists to preserve. Today that safeguard doesn't fire.

**Cost:** the calculator must prefer configured locations over observed ones, so the
`distinct_locations` field stops being purely derived. And the list must be kept accurate —
a stale entry for a location Dynatrace no longer runs produces permanent false "missing
data". That is the opposite failure, and it argues for keeping the list short and reviewed.

### 3.2 Multiple monitors per component — the monitors will fight each other

**This is a correctness bug that does not exist today and appears the moment a component
has two monitors.**

`run.py:136` starts one loop **per signal**. Each loop calls `orchestrate_signal`, which
resolves `component_id = config.component_for_signal(signal_key)`
(`composition/orchestrate.py:88`) and then calls `decide_service.decide(component_id=…)`
(`orchestrate.py:154`). **Every monitor independently proposes a status for the shared
component, knowing nothing about its siblings.**

Concretely, with `api-gateway` carrying `api-gateway-health` (60s) and
`api-gateway-graphql` (300s):

1. `api-gateway-health` sees a `down` streak of 3 → proposes `partial_outage` → opens a
   proposal awaiting approval. Correct.
2. `api-gateway-graphql` runs, sees its own `up` streak of 2 → proposes `operational` →
   `decide` reads this as *"better than current"* → **resolves the open proposal
   `OBSOLETED` and publishes a recovery** (`decide.py:157-168`).

The healthy monitor erases the failing monitor's outage. Then the failing monitor opens it
again next cycle, and the two flap against each other indefinitely — anti-flap cannot damp
this, because each monitor's *own* streak is perfectly stable.

Today this is invisible: exactly one signal per component, so there is no sibling to
disagree with. `create_open` returning `None` guards against *duplicate* opens
(`decide.py:110-111`), but nothing guards the recovery-publish path.

**The fix is a per-component rollup between stage 3 and stage 5**: gather all of a
component's signals' verdicts, derive one component-level health, and let *that* drive
anti-flap and decide — instead of each signal deciding for the whole component. Which
means the decision loop stops being per-signal and becomes per-component, with signals as
inputs. That is a real change to `run.py` / `orchestrate.py`, and the rollup rule needs a
product decision: is a component down when **any** monitor is down (worst-of, matching
`rollup_group`'s MIN for availability), or only when all are?

**Worst-of is the consistent choice** — it matches how availability already rolls up, and
"the checkout API is fine but the checkout journey is broken" should not read as healthy.

### 3.3 More locations makes an unguarded anti-flap path go hot

`_collapse_health` returns `degraded` for **any** mix of location healths
(`pipeline.py:97`), and `anti_flap` proposes `degraded` for a `DEGRADED` streak
**with no length check at all** (`pipeline.py:226-227`) — unlike the `DOWN` ladder, which
requires `length >= degraded` (default 2) before proposing anything.

With **one** location (today) a mix is impossible: a single observation is either `up` or
`down`, so `degraded` only ever arises if the vendor itself reports it. The no-streak-check
path is effectively dead code in production.

With **3–7** locations, a mix is the normal consequence of any single location hiccuping
once — and each such cycle proposes a `degraded` status change with **zero anti-flap
damping**. The whole point of anti-flap is that one bad cycle doesn't move a public status
page; this path bypasses it.

Two candidate fixes, both needing a product call:
- **Require a streak for `DEGRADED` too** — `length >= thresholds.degraded`, symmetric with
  the `DOWN` ladder. Smallest change, closes the hole.
- **Make collapse quorum-aware** — distinguish "1 of 7 locations failing" from "6 of 7
  failing" instead of flattening both to `degraded`. Richer and enables the reference UI's
  *"3 of 5 signals failing in eu-west-1 + us-east-1"* reasoning text honestly, but it is a
  change to the §10 collapse rule.

### 3.4 Display-only additions — no maths touched

`group`, `description`, and `locations[].label` never enter a calculation. `group` is a
mono sub-label (slug-normalized so it can become structural later without cleanup);
`description` is a capped card subtitle; `label` is the operator-facing name for a probe
location, replacing `SYNTHETIC_LOCATION-000000000000005C` on screen. The `locations`
block's `native_id` **is** matched against wire data, but only to resolve the alias — it
changes no arithmetic.

---

## 4. Summary

| Change | Effect on calculations |
| ------ | ---------------------- |
| Nesting monitors under components | **None.** Authoring shape only; a flattened `app.signals` accessor keeps all 7 consumers working. |
| `group` / `description` / location `label` | **None.** Display only. |
| `expected_locations` | Completeness denominator becomes *expected* × intervals instead of *observed* × intervals. Closes the fully-dark-location blind spot (§3.1). |
| **Multiple monitors per component** | **Breaks the decision path** — monitors publish over each other's proposals (§3.2). Needs a per-component rollup before anti-flap/decide. |
| **Multiple locations per monitor** | Makes the unguarded `DEGRADED` proposal path hot (§3.3). Needs a streak requirement or quorum-aware collapse. |

§3.2 and §3.3 are **prerequisites for the fleet expansion**, not UI work — and neither is
in the current sprint-62 scope. They should be stories before real multi-monitor
components go live, or the first multi-monitor component will flap its Statuspage.
