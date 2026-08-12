---
id: STORY-217
title: Composition still writes to DynamoDB directly — decide whether topology seeding needs a real write port
type: chore
points: null
status: draft
filed: 2026-08-04
sprint: null
---

## Context

**Filed by STORY-205's AC6, which required the residue of its own fix to be written down rather
than quietly closed.** This story is that residue's ledger entry; the residue itself is stated in
`docs/scrum/wiki/zone-rules.md` ZR-8 Finding 1 (`:736`; the expiry condition at `:767`) and carries an explicit expiry
condition there.

STORY-205 closed `ZR-8` Finding 1 by extracting the DynamoDB topology key schema into one module,
`backend/src/adapters/persistence/topology_keys.py`, imported by `DynamoComponentRepository`,
`DynamoSignalRepository` and `composition/seed_dynamo.py::seed_topology_dynamo`. That removed the
**schema** duplication — the thing that had already drifted once and cost two debugging runs.

**It did not remove the underlying shape.** `seed_dynamo.py` still calls `table.put_item` /
`table.update_item` itself, with its own hand-written `UpdateExpression` (`:46-56`). So
*"composition writes to DynamoDB directly"* remains true at HEAD. That is a separate and larger
question than the one STORY-205 was scoped to answer, and it was deliberately left open rather
than smuggled into a 3-point story.

## Why this was NOT done inside STORY-205

Two shapes were available at STORY-205's refinement, and the rejection reasoning is recorded in
that story file:

- **(a)** Give the repositories write methods (`upsert_component`, `upsert_signal`) plus a new
  `TopologyRepository` port for the `APP#` item.
- **(b)** Extract the key schema into one module the persistence adapters own. — **CHOSEN.**

(a) was rejected because it forces a **new core-owned port for a value no core service reads or
writes**. A port exists to serve the core; topology seeding is a composition-time boot concern,
and routing a boot script through the core to satisfy a diagram would be laundering, not
architecture. `ZR-8`'s own Coverage verdict sanctions (b) in writing.

## The expiry condition — the trigger that makes this story real

From `zone-rules.md` ZR-8:

> if a core service ever needs to read or write topology, this shared-module shape expires and a
> `TopologyRepository` port (option (a), rejected at STORY-205 refinement only because no core
> service touches this value today) becomes correct.

**Until that trigger fires, the honest answer to this story may be "no, and here is why" — and
closing it that way is a legitimate outcome, not a dodge.** What is NOT acceptable is the
condition staying untracked, so that the day a core service does touch topology, nobody
remembers a decision was made and on what grounds.

## Refinement should settle, before this is estimated

1. **Has the expiry condition fired?** Re-derive it — does any `core/services/*` read or write
   topology at that point in time? If no, the cheapest correct outcome is to re-affirm (b), record
   the re-check date in `zone-rules.md`, and close this story without code.
2. **If it has fired**, scope option (a): the two repository write methods, the new port and its
   fake, `seed_topology_dynamo` rewritten to call them, and the `UpdateExpression`'s
   `if_not_exists(#s, :default)` semantics preserved — that expression is load-bearing (it
   preserves runtime component status across a re-seed) and any port method must keep it, not
   flatten it into a `put_item`.
3. **Note the blast radius either way:** `seed_topology_dynamo` runs on the boot path of BOTH
   composition roots (`run.py::main`, `app.py::create_app`'s lifespan seed), so a regression here
   is a startup regression in two processes, not one.

## Not in scope

The key schema itself (STORY-205, done). `ZR-8` Finding 2 (STORY-204). Changing *what*
`seed_topology_dynamo` writes.

---

## Planning re-check, 2026-08-05 (sprint-69 planning) — **estimate 1, NOT in sprint 69**

**Question 1 is answered mechanically, and the answer is NO — the expiry condition has not fired.**
`grep -rn "topology\|APP#" backend/src/core/` at HEAD returns twelve hits and every one is a READ
or a docstring: `core/domain/topology.py` (the `Signal` read model), `core/ports/signal_repository.py`
(*"Port interface for **reading** seeded-topology signals"*), and prose in three other ports. **No
`core/services/*` writes topology; none reads it through a write-capable port.** Seeding remains a
composition-time boot concern.

So the cheapest correct outcome stands: re-affirm option (b), record the re-check date in
`zone-rules.md` ZR-8's Finding 1 alongside the expiry condition, and close without code — which
that section's own text sanctions in advance. **Sized 1 point** on that basis. If a future sprint
finds the trigger fired, this becomes option (a) and re-estimates at 3+.

Deliberately NOT pulled into sprint 69: sprint 69 is the audit-closure guard set, and this story's
correct outcome is a documentation re-affirmation with no guard in it. It belongs with the next
batch, where its 1 point buys a dated re-check rather than diluting a themed sprint.

---

## Refinement, 2026-08-13 (sprint-70 planning) — **estimate 1, AC authored**

The 2026-08-05 re-check answered the only open question: the expiry condition has **not** fired. AC
below therefore describes a dated re-affirmation with no production code. If AC1 comes back
positive, this story is **Blocked and re-estimated at 3+**, never silently converted mid-sprint.

## Proposed Acceptance Criteria

- [ ] **AC1 — the expiry condition is re-derived by PORT IMPORT, not by token grep.** The
      2026-08-05 method (`grep -rn "topology\|APP#" backend/src/core/`) cannot decide the actual
      condition: a write method that mentions neither token is invisible to it, and at HEAD it
      returns 13 hits where this story records twelve. The derivation is instead:
      (a) list what `backend/src/core/services/*` imports from `src.core.ports`;
      (b) for each imported port, classify it read-only or write-capable from its own method
      signatures; (c) the condition has FIRED only if some core service imports a write-capable
      topology port — `ComponentRepository` (its `set_status` is write-capable) or
      `SignalRepository`. Record every command and its full output in the story's History, with a
      **per-hit read/write verdict**, so two implementers cannot count differently.
- [ ] **AC2 — if AC1 is negative, `zone-rules.md` ZR-8 Finding 1 gains a dated re-affirmation**
      alongside the existing expiry condition: the date, the command AC1 ran, and the sentence that
      option (b) stands until the trigger fires. The expiry condition text itself is not weakened or
      removed — it is what makes this re-checkable next time.
- [ ] **AC3 — if AC1 is POSITIVE, no code is written.** The story is marked Blocked with the naming
      evidence, and option (a) is re-estimated at the next planning. A 1-point story may not grow a
      new core-owned port inside a locked sprint.
- [ ] **AC4 — no production behaviour changes.** `git diff <start>..HEAD -- backend/src/` is EMPTY
      for this story. Asserted, not asserted-about.
- [ ] **AC5 — no-regression check on the Adjudication table, which this story does NOT edit.**
      AC2 appends to ZR-8's BODY prose (`zone-rules.md:736-767`); the Adjudication row is at `:878`,
      about 110 lines below. `test_zone_rules_enforced_by_claims.py` therefore passes with zero work
      here — that is the point, and it is recorded as a no-regression check, **not** as evidence of
      anything this story did. It is explicitly NOT the reason this sprint is contract-sensitive.
- [ ] **AC6** — full 8/8 DoD gate green at the final HEAD.
