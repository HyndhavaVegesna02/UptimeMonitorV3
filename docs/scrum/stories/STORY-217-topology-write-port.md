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
`docs/scrum/wiki/zone-rules.md` ZR-8 Finding 1 (`:671-678`) and carries an explicit expiry
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
