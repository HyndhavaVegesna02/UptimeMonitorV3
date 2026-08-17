# Sprint 74 — Review

**Goal:** *Pay the review debt, then leave the enforcement machinery more honest than we found it.*

**Committed 15 points. Delivered 15 points, 4 of 4 stories.** Branch `sprint-74`, final HEAD
`c439f9e`, gate **9/9 green**, wiki compile pass CLEAN across sweep / facts / links / refs /
integrity, tree clean.

**A new high: 15 points, against a previous best of 13.** Velocity 11, 10, 11, 11, 10, 8, 13, **15**.
The plan said at lock that 15 was two above the record, and named STORY-227 as the declared first
drop. **The drop was never invoked** — the session window reset before the tail, and descoping a
story we had room to deliver would have been habit rather than judgment.

**Nothing is merged.** Sprints 66–74 all stay unmerged.

---

## The goal, measured

Every story here was a sprint-73 carried minor, per the PO's directive at that close. The equilibrium
backlog was deliberately untouched — that is sprint 75's.

| | |
| --- | --- |
| Carried minors closed | **14 of 14** (the four stories cover all of them) |
| Wiki articles made honest | `frontend-zone.md` demoted, plus 6 `tier: map` articles re-verified |
| Enforcement machinery | route table, citation gate, Facts lint and a DynamoDB claim all strengthened |

---

## Story 1 — STORY-228 (2 pts): four documentation leftovers

- **Spec: FAIL → MET** after the fix round. **Quality: REQUEST CHANGES → 2 MAJORs, fixed.**
- **Gate 9/9 at `1e1d870`.** Reality gate: zero sample-mode references in the **built bundle**.

**The MAJOR both reviewers found independently is the sprint's best lesson.** AC3's fix de-lined a
citation — and that turned `yt_wiki.py facts` **red**, proven two-sided (pre-image exit 0, the fix
exit 1). The mechanism: `citation_gate.py`'s regex **requires** a line number, `yt_wiki.py`'s does
**not**. Removing `:54` moved the citation from *invisible to every checker* to *flagged by a second
one*, while leaving the actual harm — no drift signal — untouched. Resolved by adding the path to
`code_refs` and restoring the citation.

Second MAJOR: the correction to a "record everything" claim **dropped AC1(e)**, which was never
retired and is still asserted in the harness. An incomplete record produced by the fix for an
incomplete record — and nothing lints `tools/`, so no check would have caught it.

## Story 2 — STORY-229 (5 pts): the `frontend-zone.md` routing decision

- **Spec: PASS** (six AC, met or N/A-justified). **Quality: REQUEST CHANGES → 3 MAJORs, fixed.**
- **Gate 9/9 at `519e65c`.** Reality gate at the mechanism level: the sweep now reports
  *"frontend-zone.md not swept (tier=reference — no live claims)"*.

**AC1 made the decision the deliverable, and the decision was not the default.** It chose **(b)
demote to `tier: reference`** — 634 lines → 167 — over rehabilitating as `tier: map`. Grounds:
quarantined since 2026-08-12 with zero consumers across four-plus months, and `tier: map` is the
only shape with recurring cost. **(c) archive was rejected on a good distinction:** `frontend/` is
live, gated code, whereas the tombstone shape is reserved for subjects that no longer exist.

**Quality audited the deletion rather than approving it**, which is what this story needed. It traced
every non-obvious *reason* the pre-image carried and confirmed each survives **in code, where it
cannot rot**. **No Fact's content now exists nowhere.** It also found a pre-image Fact that was
*already false* — evidence the article was decaying, not being maintained.

All three MAJORs were truth defects in an article that **will never be swept again**. The sharpest:
the story asserted the correct precedent in the article's History and its **inverse** in the test
docstring — contradicting itself across two files, and within six lines of itself.

## Story 3 — STORY-226 (3 pts): validation ergonomics

The sprint's **only** runtime behaviour change.

- **Spec: PASS** (seven AC). **Quality: REQUEST CHANGES → 3 MAJORs, fixed.**
- **Gate 9/9 at `f212901`**, pytest 831 → 838 (+7, exactly the new tests).

**Reality gate proved both PO rulings through the real `load_config`:** the error reads *"authored as
'Not Valid!', normalized to 'not valid!'"*; and blank/empty descriptions become `None` while
`"  Checkout surface  "` survives **byte-identical with its padding** — which distinguishes the
implemented rule from the alternative that would have moved a pinned 80-character boundary.

**The MAJOR worth your attention:** the story claimed `description` "can never" be `""` at the API
seam. It can. The repository applies no normalization and the seeder is **upsert-only with no delete
path**, so a row seeded while `""` was legal and later dropped from config still reaches the DTO.
That claim was also a `tier: map` Fact — the sentence a cockpit implementer would cite when deciding
to drop their `""` branch. Rescoped in both places.

**One MAJOR was the orchestrator's fault:** a stale `:669-671` line citation came from my brief —
correct when verification measured it, invalidated by the story's own +16-line hunk. Fixed by
*deleting* the number rather than re-deriving it.

## Story 4 — STORY-227 (5 pts): six test-pinning gaps

- **Spec: PASS** (seven AC). **Quality: REQUEST CHANGES → 1 MAJOR, comment-only, fixed.**
- **Gate 9/9 at `c439f9e`.** Reality gate: the pinned `(method, path)` table matches the **live app**
  exactly — 12 pairs, `/api/v1/maintenance` carrying both GET and POST, sample-mode absent.

**Both reviewers independently reproduced the mutations rather than trusting them.** AC3's claim is
the standout: with NULL written, both the old and new assertions pass; with the attribute **omitted**,
`'group' in item` fails while `.get() is None` still passes. The old assertion was **vacuous on both
sides**. `persistence-adapters.md`'s Fact is now proven rather than asserted.

**The MAJOR is instructive given the story's subject.** The new settle barrier's comment claimed
waiting on the theme toggle *"proves no hook … is still pending"* — but that button renders
**synchronously**, so the wait drains nothing. The decoupling was right; the claim that the property
survived was not. A proof-label one step beyond its evidence, inside a story about greens that do not
mean what a reader assumes.

---

## What review caught that the authors did not

**Every story needed exactly one fix round. Nine MAJORs across four stories, and not one was in the
delivered mechanism — all were false or over-strong claims about it.** That is a consistent signature
this sprint: the code was right and the story *about* the code was wrong.

Four of the nine were **stale or wrong numbers/citations in a record**, which is now a pattern rather
than a coincidence:
- a de-lined citation that broke a second lint
- a dropped sub-AC in a "everything recorded" sentence
- a line number invalidated by its own commit (supplied by the orchestrator)
- a gate result attributed to the wrong commit (found by both reviewers independently)

**Three implementers each moved the citation population by writing a `path:NNN` inside backticks in
wiki prose.** All three were caught by the gate. The fourth story was warned in its brief and
produced **no** regression — the only story this sprint with an unchanged citation population.

## Blockers

**None.** No story was blocked at any point.

## Decisions for the PO

1. **Accept / reject each story.**
2. **Fifteen minors are carried, unfixed and unfiled**, recorded per-story under
   `carried_to_po_at_review` in `.scrum/sprint-current.yaml`. The three most substantive:
   - pin `set(SignalObservation.model_fields)` so a newly added field re-opens AC2's hole
     permanently — a genuinely good idea, but new scope;
   - `config.py`'s authored-value dict is built on **every** successful load but read only on the
     error path;
   - `CLAUDE.md` and `frontend-zone.md` both point at `frontend/README.md` "for current shape", but
     that README carries no layout, per-tab pattern, `useFetch` or MSW convention — the honest
     fallback is the code.
3. **Merging.** Sprints 66–74 remain unmerged — nine sprints of work off `main`.

## For the next planning

- **The backlog is 11 open, and none is `ready`.** Sprint 75 needs a refinement pass first.
- **STORY-192 must be re-measured** before sizing — sprint 73's archival removed roughly half its
  mojibake, and nothing has re-counted since.
- The PO's directive is discharged: the minors are finished, so **sprint 75 returns to the
  equilibrium list.**
