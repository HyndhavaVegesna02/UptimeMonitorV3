---
id: STORY-213
title: test_dynamo_component_repository_list_components_paginates fails intermittently — the message reads as a pagination defect
type: defect
points: 2
status: draft
filed: 2026-08-03
refined: 2026-08-03
sprint: null
---

## Context

Filed from STORY-199's quality review, **with reproduction evidence attached**. It is *not* a defect
in STORY-199's code, and the reviewer proved that before filing: the production loop was
mutation-verified correct and the `ZR-7` guard independently confirms all six compliant call sites.

Observed once, on the first of eleven full-suite runs against committed HEAD, with `REQUIRE_DYNAMO=1`:

```
FAILED backend/tests/test_dynamo_component_repository_list_components_paginates
assert {'comp-page-0', 'comp-page-1'} == {10 ids}
```

— i.e. with `repo._limit = 2`, `list_components` returned **page 1 and stopped**. Did not recur in
10 further full runs (694 passed / 0 skipped each) nor in 25 consecutive targeted runs.

**The reviewer's hypothesis, unconfirmed:** a lost write or an absent `LastEvaluatedKey` from
DynamoDB Local under the `conftest` `clean_dynamo_tables` fixture's ~1,400 delete/recreate table
cycles per run. Related to STORY-179 (the same fixture's known ephemeral-port defect — same fixture,
different symptom).

**Why it is worth a story despite being rare:** the failure message is indistinguishable from
"pagination is broken" — the exact defect sprint 67 had just fixed. At ~1-in-11 it will eventually
fire for someone who then spends a day re-investigating a closed defect. **That cost is the story,
not the flake.**

## Refinement decisions

**1. The deliverable is a self-diagnosing assertion, not a reproduction.** The filed note offered a
choice between hardening the fixture and making the assertion self-diagnosing. Hardening is
speculative — the mechanism is unconfirmed and survived 35 attempts to reproduce. The *stated* cost
is a message that misleads, so fixing the message is the fix. Fixture hardening stays a probe (AC3),
not a promise.

**2. Non-reproduction must not block the story.** An earlier draft of these AC required reproducing
the failure first (agreement A8). That would block this story **by construction** — 35 runs already
failed to reproduce it. A8 governs spikes with a reproducible target; it does not apply here, and
saying so is part of the story.

**3. It is NOT scheduled into sprint 68.** It was briefly placed there as an "enabler" on the theory
that sibling tests polluted a shared table — which the evidence above refutes (pollution yields
*extra* ids; this returned *fewer*). With the mechanism being DynamoDB Local flakiness, it protects
none of sprint 68's work. It is real, it is small, and it waits.

## Acceptance Criteria

- [ ] **AC1 — the message distinguishes a flake from a regression at a glance.** On failure the
      assertion reports the observed page count, the ids actually returned, and whether a
      `LastEvaluatedKey` was present when the loop exited. Proven by *forcing* a failure (inject a
      truncated result) and recording the emitted message — not by describing it.
- [ ] **AC2 — the test is not weakened. This is the constraint the filed note puts in capitals.**
      It remains one of STORY-199's five AC2 proofs: still full set equality against all ten
      `comp-page-*` ids, and removing `list_components`'s `LastEvaluatedKey` loop must still take it
      RED. Record the mutation, the failure, the restore, and an empty `git diff`.
- [ ] **AC3 — the fixture hypothesis is probed and the result recorded either way.** Examine whether
      `clean_dynamo_tables`'s delete/recreate cycle can race a subsequent write, and whether the
      repository's loop mishandles an absent `LastEvaluatedKey`. **If a concrete defect is found, fix
      it. If not, record the negative result with what was checked.** Non-reproduction is an outcome,
      not a failure of the story.
- [ ] **AC4 — the four sibling `_limit`-forcing tests** (`list_windows`, `list_signals`, `list_open`,
      `is_under_maintenance`) get the same diagnostic treatment, or it is stated per test why they do
      not need it. A bare "checked, fine" is not evidence.
- [ ] **AC5 — no skips.** The gate runs with `REQUIRE_DYNAMO` set (agreement A6); a skipped
      DynamoDB test is a failure, not a pass.
- [ ] **AC6 — cross-referenced with STORY-179**, which owns the same fixture's other known defect, so
      whoever takes 179 sees this evidence.

## Not in scope

Extracting the shared pagination loop (STORY-214). Changing any adapter's pagination behaviour.
Fixing STORY-179's ephemeral-port defect.
