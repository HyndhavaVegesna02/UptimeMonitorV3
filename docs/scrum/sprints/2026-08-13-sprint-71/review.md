# Sprint 71 — review

**2026-08-14 · branch `sprint-71` (from `sprint-70` HEAD `7a82104`, tagged `sprint-71-start`)**
**10 of 10 points delivered. Gate 8/8 green at the final HEAD: 816 passed / 0 skipped, contracts 9 kept / 0 broken.**

Suite grew 800 → 816. 51 commits. Wiki compile pass CLEAN (sweep/facts/links/integrity).

## Goal, and whether it was met

> Every check the DoD gate runs, and every document a session loads, is either true or visibly
> stale. Nothing in the floor reports a result it did not measure.

**Met.** The fixture that green-lit dead containers now proves the service answers; the document
every session loads no longer describes infrastructure that doesn't exist; the flake that read as a
closed defect now diagnoses itself. But read §3 before accepting: the sprint's own proofs failed
this standard four times, and every one was caught by review rather than by the floor.

## Story by story

| Story | Pts | Outcome |
| --- | --: | --- |
| STORY-222 | 3 | Done after a fix round — 4 MAJORs |
| STORY-179 | 3 | Done after a fix round — **2 CRITICALs** |
| STORY-213 | 2 | Done after a fix round — 2 MAJORs |
| STORY-201 | 1 | **Done first-pass clean** |
| STORY-189 | 1 | Done, one self-caught fix commit |

**Four of five needed a fix round.** That is not a quality collapse — it is what a two-reviewer
pipeline is for, and every finding below was measured, not asserted.

### STORY-222 — the decommission, and a tombstone that laundered its citations

`CLAUDE.md`, two wiki articles, and an **executable** tool (`tools/ui-sweep/sweep.mjs` hard-coded
the dead CloudFront URL) all claimed a live stack.

The finding: converting `deployment-and-infra.md` to a `tier: reference` tombstone **renamed** the
`## Facts` heading rather than de-citing it, leaving nine `infra/stack.yaml:LINE` citations in an
article now permanently exempt from the sweep. Quality proved it by mutation — a citation pointing
5,000 lines past EOF stays **green** at reference tier and goes **RED** at map. Ten enforced
citations had silently lost their pin, and the guard's own exemption note asserted the article
"makes no live-code claims" while nine sat in it.

**The two reviewers recommended different fixes and I overrode quality's.** Reverting to
`tier: map` was protocol-correct and needed no guard edit — but it puts the stale count back to 3
and breaks AC10, which that reviewer hadn't accounted for. Took spec's de-lining instead.

### STORY-179 — the fix reintroduced the defect, twice, from two directions

**Botocore is more forgiving than the code assumed, and the probe inherited the forgiveness.**

1. **Lenient JSON parsing lets a bare `200 OK` satisfy `client.list_tables()` without raising.** So
   AC4 *as written* — "issue a real ListTables call instead of `GET /`" — would still have
   green-lit a non-DynamoDB responder. **The implementer found this mid-implementation and
   disclosed it unprompted.** Both reviewers confirmed the `TableNames` check is load-bearing:
   neutralise it → green in 0.88s; keep it → red in 3.15s.
2. **No botocore timeout config**, so one call was bounded by defaults, not by `timeout_seconds`.
   Measured at a 3s budget: **626 seconds against a silent peer — 209× over.** With the production
   default of 30s, a mapped-but-dead port hangs the fixture for *minutes* — the exact "healthy suite
   looks hung" symptom the story exists to remove, caused by the fix.

**And the shown-RED pinned the wrong function.** AC1's test asserted on `_free_tcp_port()`, which
after the diff is reached only from the test-injection branch. Reverting `start_container` to
ephemeral ports — **defect 1 verbatim** — left the suite **green, zero RED**. A9's discipline was
satisfied and the story still had no pin on its headline behaviour.

**Both surfaced only in AC8 config 2** (`DYNAMO_ENDPOINT_URL` unset) — the sole configuration that
executes this code. The implementer ran it once and got green; the reviewer ran it four times and
got one red. **Had the single run been trusted, this shipped.**

### STORY-213 — the flake had already gone, and the fix stated its own claim backwards

**Re-measured first: 0-in-12 after STORY-179's fixture rewrite; 47-in-47 across two fixture
generations.** Recorded as an honest negative. It correctly did not gate the story — the deliverable
was always the self-diagnosing message — but it means the helper's value now rests entirely on the
message quality, which is where both MAJORs landed.

**The mapping was stated backwards on the docstring of the test the flake actually fired on.**
Measured truth: flake = LEK **absent**; regression = LEK **present**. Not a fresh error — commit
`25f221c` is *titled* "correct the diagnostic docstring's flake/regression LEK mapping against the
observed evidence" and fixed two copies while missing a third written one commit earlier. A reader
applying it to a `=True` failure files a genuine STORY-199 regression as a flake.

Quality's second MAJOR is sharper: the `is_under_maintenance` message branched on LEK alone while
`spy.summary()` printed the discriminating **page count** one line above. Two causes render the same
LEK — and the one it misdiagnosed is the *leading* explanation, since the GSI-backed sites cannot
use `ConsistentRead=True`, a fact this story's own AC3 had recorded.

Verified clean and worth keeping: `PaginationSpy` changes only what tests **report**, never what
they **assert** — proven by mutation. The citation gate was untouched.

### STORY-201 — the only first-pass clean story, and the reason matters

It had a claim it *could not* prove: `normalize_clickpath_row` is unreachable in production, so the
quarantine-net behaviour cannot be shown end-to-end. **The implementer reported it as an inference
rather than manufacturing a route to make it look verified.** That is the exact discipline the other
four stories each failed once.

### STORY-189 — grep-for-other-copies, applied forward, and it found one

AC1 was already satisfied and correctly **not redone** — touching `demo-engine.md` would have reset
its staleness baseline for nothing. AC7's line-count-neutral constraint held (3 insertions, 3
deletions), so no citation moved.

Carrying STORY-213's lesson forward, the implementer grepped for other copies of each false
statement before committing — **and found one**: `core/queries/availability.py:71` carries the same
"expected-but-missing" phrase, and tracing the computation confirmed the limitation genuinely
applies there too. It did not fix it (outside AC4's scope, would blow the 1-point sizing) and
reported it. Filed below.

Its own fix commit is a small vindication: a wiki History note used a bare-filename citation, which
**STORY-219's citation ratchet caught** as new debt (188→189). Corrected to a full path.

## The AWS question, settled

`CLAUDE.md` had asserted the stack was torn down. The repo's own template contradicted the DynamoDB
half — `DeletionPolicy: Retain` on both tables and the frontend S3 bucket means `delete-stack`
leaves all three orphaned, and `deployment-topology.md` records that those leftovers block a fresh
create by name.

**Verified against the live account: nothing survived.** Stack gone, both tables gone, bucket gone,
cluster gone, CloudFront DNS doesn't resolve. `CLAUDE.md` now carries the evidence table instead of
the hedge — leaving the hedge would have been the mirror image of the defect, a document *less*
certain than the evidence supports.

⚠ **The `Retain` policy is still in the template.** The next deploy-then-teardown cycle recreates
the hazard. Recorded on STORY-090's archived entry, where a redeploy decision would start.

## Process incident

**The STORY-213 spec reviewer ran `git stash pop`** — forbidden by its own definition — and popped
an unrelated **2026-07-14** stash, leaving live merge-conflict markers in two `backend/src/` files.
Repaired by the orchestrator (all three files were untouched by the story diff, so HEAD was
correct). **The stash entry is intact and undropped** for deliberate disposal.

The reviewer stopped rather than compounding it with another forbidden command, and disclosed fully.
**This is the second `git stash` workaround this sprint** — see the retro.

## Plan verification earned its keep, against my own plan

The pre-lock verifier returned **RE-PLAN**: 3 CRITICAL, 8 MAJOR against sprint 71 v1. Nine of eleven
committed points had **no acceptance criteria** — I had written three story files in *filing* shape
during the equilibrium pass and put them into a sprint unrefined. Two of my price justifications
were refuted by measurement, and two ordering rationales were refuted outright and removed.

## Filed during the sprint

1. **STORY-224** — 7 skill-level test modules that no DoD command runs (`testpaths = backend/tests`;
   800 collected, 0 from `.claude/`). `test_template_parity` caught A19 silently reverting last
   sprint; `test_scrum_encoding` is STORY-188's guard. Both run only when someone remembers
   `yt_selftest`.
2. **STORY-225** — `infra/stack.yaml`, `Dockerfile`, `.dockerignore`, `scripts/create_tables.py` are
   in **no** article's `code_refs`, created by STORY-222's tombstone conversion. cfn-lint gates
   `stack.yaml` every run.
3. **`core/queries/availability.py:71`** — the same "expected-but-missing" phrase STORY-189 fixed in
   the DTO, in the domain type it mirrors. Needs its own line-neutrality pass.
4. **`zone-rules.md`'s `vendor_health.py:70-133` citation has drifted** from `:751` to `:812` — a
   live instance of the STORY-223 defect class.

## Wiki

Sweep, facts, links, integrity **CLEAN** at final HEAD. **13 map-tier articles, 4 reference** (was
14/3 — STORY-222 converted one). **Stale articles 3 → 2.** Citation advisory unchanged at **146** —
no new citation debt across 51 commits, and the ratchet caught the one attempt.
