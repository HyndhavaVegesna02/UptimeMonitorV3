---
id: STORY-205
title: composition/seed_dynamo.py must call the persistence adapters' key schema, not re-implement it
type: defect
points: 3
status: ready
filed: 2026-07-31
refined: 2026-08-03
sprint: 68
---

## Context

`ZR-8` Finding 1 (`docs/scrum/wiki/zone-rules.md`) — the sprint-66 audit's biggest single miss, found
only in STORY-196's quality-review fix round because it fell through the crack between the two audit
passes: STORY-195 covered `adapters/`, STORY-196 covered `composition/`, and this is `composition/`
doing `adapters/`'s job. Authoritative detail:
`docs/scrum/sprints/2026-07-31-sprint-66/audit-api-composition-tools.md` §6.

`backend/src/composition/seed_dynamo.py` hand-builds the DynamoDB topology key schema three times —
`:29-30` (`APP#`), `:43` (`COMPONENT#`), `:58-59` (`SIGNAL#`) — with raw `table.put_item` /
`table.update_item` and a hand-written `UpdateExpression`. That schema is owned by
`dynamo_component_repository.py` and `dynamo_signal_repository.py`, so it is declared in **three**
places, on the boot path of **both** composition roots (`run.py::main`'s topology seed,
`app.py::create_app`'s lifespan seed). `docs/scrum/wiki/persistence-adapters.md:36` already describes
`seed_topology_dynamo` alongside the repositories — the wiki had filed it with the adapters long
before the audit looked.

**The drift has already bitten once and the scar is in the tree:**
`tools/demo_loop_gate/failure_path_reality_gate.py:161-176`'s docstring records a first version using
`pk=COMPONENT#<id>, sk=META` where the repository uses `pk=TOPOLOGY, sk=COMPONENT#<id>` — the write
created a phantom item nothing read, the read-back "verified" it against the same wrong key, and an
AC precondition passed vacuously. Two full debugging runs were spent on a defect that did not exist.

**Re-derived at refinement (2026-08-03), not copied from the audit.** `grep -rn '"TOPOLOGY"'` over
`backend/` returns ten sites: five in the two repositories
(`dynamo_component_repository.py:35,55,69`, `dynamo_signal_repository.py:36,57`), three in
`seed_dynamo.py` (`:29`, `:43`, `:58`), two in `backend/tests/test_dynamo_adapters.py:17,82`.
`failure_path_reality_gate.py` is **already clean** at HEAD — it routes through the real repository
and its docstring explains why — so the drift citation above is history, not a live second site.

## The design decision, made at refinement (not left to the implementer)

The filed note flagged this as the sizing risk: the repositories expose no seed-shaped bulk upsert
(`set_status`/`get` are single-item, request-scoped), and **no repository owns `APP#`-shaped writes
at all**. Two shapes were available:

- **(a) Give the repositories write methods** (`upsert_component`, `upsert_signal`) plus a new
  `TopologyRepository` port for the `APP#` item.
- **(b) Extract the key schema into one module the persistence adapters own**, imported by both
  repositories *and* by `seed_topology_dynamo`. — **CHOSEN.**

Reasoning: `ZR-8`'s own Coverage verdict already sanctions (b) in writing — "calls
`DynamoComponentRepository`/`DynamoSignalRepository` **(or an equivalent shared helper those adapters
expose)**". Option (a) forces a new core-owned port for a value no core service reads or writes;
topology seeding is a composition-time concern, and a port exists to serve the core, not to launder a
boot script through it. (b) makes the schema single-declaration, which is the finding.

**Verified feasible at plan verification (2026-08-03) — both sizing worries are non-issues:**
- The hand-written `UpdateExpression` (`seed_dynamo.py:44-51`) **names no key attribute**, so only
  the `Key=` argument needs the helper; the expression itself is untouched.
- `APP#` has exactly **one** construction site in the entire tree (`seed_dynamo.py:30`, verified
  across `backend/`, `tools/` and `scripts/`), so an `app_key()` helper suffices and **no port is
  needed** — which was the concern that put a `TopologyRepository` on the table.
- No import-linter contract is threatened: nothing constrains `composition → adapters`;
  `adapters-edge-only` forbids only the reverse.

**Stated residue, recorded in the rule rather than quietly closed (AC6):** (b) leaves
`seed_dynamo.py` issuing its own `boto3` writes. The *schema* stops having three declarations;
"composition writes to DynamoDB directly" remains true and is a separate, larger question needing a
real write port. **Expiry condition:** if a core service ever needs to read or write topology, (b)
expires and (a) becomes correct.

## Acceptance Criteria

- [ ] **AC1 — one declaration, in BOTH key shapes.** Every topology key is constructed in exactly ONE
      module under `backend/src/adapters/persistence/`. **Two shapes count, and naming only the first
      lets four literals survive legally:** (i) the item-key **dict**
      (`{"pk": "TOPOLOGY", "sk": f"COMPONENT#{id}"}`), and (ii) the boto3 **query condition**
      `Key("pk").eq("TOPOLOGY") & Key("sk").begins_with("COMPONENT#")`
      (`dynamo_component_repository.py:35-36`, `dynamo_signal_repository.py:36-37`). Re-derive the
      site count before and after with `grep -rn '"TOPOLOGY"' backend/` and record both numbers — do
      not copy the ten quoted in Context.
- [ ] **AC2 — the behavioural drift test, and it is the important one.** *Restated at plan
      verification: the original wording was written against the option-(a) world and is
      unperformable under (b) — once the repositories import the schema, there is no "schema inside
      a repository" left to change.*
      Change the sort-key prefix **wherever the repository OBTAINS it** — pre-fix, the repository's
      own inline literal (`dynamo_component_repository.py:56`/`:70`); post-fix, the shared module the
      repository imports — and assert `seed_topology_dynamo` follows **with `seed_dynamo.py`
      unchanged**: seed, then read back through the repository, and get the item. Pre-fix the two
      diverge and the read-back fails; post-fix it succeeds.
      **Two honesty conditions.** (1) The standing test is evidence only *in conjunction with the
      recorded mutation* — unmutated it is green both before and after the fix, so it does not by
      itself prove the duplication is gone. Do not claim otherwise. (2) The mutation also reddens
      `backend/tests/test_dynamo_adapters.py:17,82`, which hand-build `"pk": "TOPOLOGY"` in their
      seed helpers — that is **expected and not a failure of the fix**; record it rather than
      "fixing" it into silence. Restore; `git diff` empty.
- [ ] **AC3 — the repositories use it too.** `DynamoComponentRepository`, `DynamoSignalRepository`
      and `seed_topology_dynamo` all obtain keys from that one module. This removes a THIRD
      declaration, not a second: leaving the repositories with inline literals would just move the
      duplication. Existing repository behaviour unchanged, proven by `test_dynamo_adapters.py`
      passing **without modification**.
- [ ] **AC4 — a standing guard, shown RED.** A test in `backend/tests/test_zone_layout.py` (the file
      `ZR-8`'s Coverage verdict names) asserts `composition/seed_dynamo.py` constructs no `pk`/`sk`
      dict literal of its own. Demonstrated RED by re-introducing one hand-built key and showing the
      guard fail *naming that site*; restore, `git diff` empty. Record the command and its output.
- [ ] **AC5 — the catalogue moves in the same commit.** `zone-rules.md`'s `ZR-8` adjudication row
      leaves `GUARDABLE-DEFERRED (STORY-204, STORY-205)` for its true post-fix verdict, **and** the
      "why only two rules were mechanised" paragraph nine lines below the table — which names ZR-8's
      violations as live — is updated in the SAME commit. Sprint 67 found exactly this
      row-contradicts-paragraph defect left behind by a fix; it does not recur here.
      **Plus two citations that are ALREADY STALE at HEAD and get repointed here, since this story is
      rewriting the code they point into:** `zone-rules.md:651-652` cites
      `dynamo_component_repository.py:39-40` and `dynamo_signal_repository.py:41-42` for the key
      schema — STORY-199's pagination loops displaced both (`:39-40` is now
      `ExclusiveStartKey`/`if self._limit`), and the article was stamped `verified` at `013f344`
      anyway. Also repoint `tools/demo_loop_gate/failure_path_reality_gate.py:166-167`, whose
      docstring cites `dynamo_component_repository.py:36-41` for the same schema.
- [ ] **AC6 — the residue is written down.** `ZR-8`'s rule text states plainly that composition still
      issues its own `boto3` writes, that only the key schema was unified, and the expiry condition
      above. A follow-up story is filed for the write-port question. An `ENFORCED-BY` claim wider
      than what AC4's guard actually checks is a fail (sprint 67, MAJOR-1).
- [ ] **AC7 — `persistence-adapters.md` follows.** That article carries `seed_dynamo.py` in its
      `code_refs`, so this story's diff makes it stale by git arithmetic. Update or re-verify it
      before the story passes the DoD gate (forward blast radius), and do not stamp `verified_sha`
      on prose that was not re-read. **Fix its one unresolvable citation while there:** measured at
      sprint-68 planning, `yt_wiki` reports that article citing `src/composition/seed_dynamo.py` — a
      path that does not resolve from the repo root (the tree is `backend/src/...`), so the Facts
      lint has been **skipping** that claim entirely. It is a Fact about the very file this story
      rewrites.

## Not in scope

Introducing a topology write port (filed by AC6); changing *what* `seed_topology_dynamo` writes;
`scripts/seed_topology.py`'s config resolution (STORY-215 AC2, same sprint).
