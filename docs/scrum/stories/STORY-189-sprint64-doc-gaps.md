---
id: STORY-189
title: Close the two doc/wiki gaps sprint 64 found but deliberately left
type: chore
points: 1
status: ready
refined: 2026-07-30
---

> **CUT FROM SPRINT 65 at plan verification (2026-07-30), PO-approved — sprint-66 candidate.**
> Not only for sizing: finding 1 rewrites `demo-engine.md` frontmatter, which **STORY-191 AC10** also
> rewrites. Deferring removes the collision entirely.
>
> **Two corrections found at verification, folded in below:** the field is **`gap_verdicts`**, not
> `missing_cycles` (no such field exists anywhere in the repo), and finding 1 is **worse** than first
> written — `demo-engine.md` does not mention `tools/demo_loop_gate/` **anywhere**, not merely in its
> `code_refs`.

## Context

Three findings from sprint 64 that were real but out of that sprint's scope, filed together because
each is a docs-only edit. All three are the same failure mode: **prose that claims more than the code
delivers** — the "trusted-and-wrong" state the wiki protocol exists to make impossible.

## The three gaps (all re-verified 2026-07-30)

### 1. `demo-engine.md`'s `code_refs` omit the whole `tools/demo_loop_gate/` package

`docs/scrum/wiki/demo-engine.md`'s frontmatter lists 27 `code_refs` covering `tools/demo_engine/*`,
its tests and `config/demo/*` — but **nothing** under `tools/demo_loop_gate/`, which STORY-182 added.
The package is **8** `.py` modules (`harness.py`, `env_matrix.py`, `fleet_coverage.py`,
`guard_reality_gate.py`, `backfill_reality_gate.py`, `publisher_chain.py`, `evidence.py`,
`__init__.py`) plus `backend/tests/demo_loop_gate/`.

**It is worse than a `code_refs` omission.** `grep -c demo_loop_gate docs/scrum/wiki/demo-engine.md`
returns **0** — the package is absent from the article's **Facts**, not just its frontmatter, and
those Facts still read that no demo loop has been started by any story to date and describe STORY-182
as future work. Sprint 64 falsified that. So the fix is a **Fact rewrite**, not a `code_refs`
addition plus a `verified_sha` re-stamp — which is exactly what AC1 forbids.

Because staleness is computed as `git diff <verified_sha>..HEAD -- <code_refs>`, a change to any of
those 8 modules **cannot** mark this article stale. The article describes them and the mechanical sweep
is blind to them — precisely the gap the wiki protocol's git-arithmetic rule exists to close.

### 2. `vendor_health.py`'s docstring says a healthy id logs nothing; it logs at INFO

`backend/src/composition/vendor_health.py:85-86` states:

> A healthy id logs nothing (kept quiet; the loud signal is reserved for the failure case, AC1).

The `else` branch at `:125-132` calls `logger.info("Vendor-id health OK for signal_key=%r ...")`.
A healthy id **does** log — at INFO. The intent ("the loud signal is reserved for the failure case")
is still true and worth keeping; the absolute claim "logs nothing" is false and should say what the
code does.

### 3. `availability/models.py` claims expected-but-missing on an observed-locations denominator

`backend/src/api/v1/availability/models.py:36-37` documents **`gap_verdicts`** as:

> Count of expected-but-missing cycles — excluded from the denominator.

But `completeness_pct` at `:24-25` is documented as *"Actual ÷ (intervals × distinct_locations) over
raw observations"* — and `distinct_locations` (`:39`) is **observed**, not expected. With an
observed-locations denominator, a location that never reported at all in the window is invisible, so
"expected-but-missing" overclaims: only gaps at locations that reported at least once can be counted.

This is documentation only. The underlying behaviour is **STORY-152** ("Completeness uses expected
locations, not observed ones") and is explicitly **not** in scope here — the fix is to make the
docstring describe the current, narrower truth and cite STORY-152 as the story that widens it.

## Acceptance Criteria

- [ ] **AC1** — `demo-engine.md`'s `code_refs` include every file under `tools/demo_loop_gate/` and
      its tests. `verified_sha` is bumped only after the article's Facts are actually checked against
      those files — a re-stamp without a read is exactly what the protocol forbids.
- [ ] **AC2** — `python .claude/skills/yourteam/scripts/yt_wiki.py` passes all four checks (sweep,
      Facts coverage, link lint) after the change.
- [ ] **AC3** — `vendor_health.py`'s docstring states what the code does: a healthy id logs at INFO,
      and the loud WARNING is reserved for drift and probe failure. The preserved intent stays; the
      false absolute goes.
- [ ] **AC4** — `availability/models.py`'s **`gap_verdicts`** (`:36-37`) docstring describes the current
      observed-locations behaviour and its limitation, and names **STORY-152** as the story that
      changes it. No behavioural change, no test change beyond docstring assertions if any exist.
- [ ] **AC5** — No production behaviour changes anywhere in this story. The diff is docstrings and
      wiki frontmatter only; `git diff` shows no change to any executable statement.
- [ ] **AC6** — The five backend DoD gate commands exit 0 with pass/skip counts recorded
      (`REQUIRE_DYNAMO=1`, working agreement A6).

## Conflict note

**Overlaps STORY-191 AC10**, which also updates `demo-engine.md`'s Facts and `code_refs`. Whichever
lands second reconciles rather than overwrites — the two must not fight over the same frontmatter.
Sequencing this story after STORY-191 avoids the collision entirely.

## History

- 2026-07-30: filed as a sprint-64 follow-up ("three doc/wiki gaps left deliberately"), estimated
  1 point.
- 2026-07-30: refined at sprint-65 planning; all three findings re-verified against the current tree
  with citations. Sequenced after STORY-191 to avoid the `demo-engine.md` frontmatter collision.
