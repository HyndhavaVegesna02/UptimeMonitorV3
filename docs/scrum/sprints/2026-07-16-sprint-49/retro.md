# Sprint 49 — Retrospective

**Delivered:** 10/10 pts (087 cutover, 092 container, 088 CloudFormation). External mode.
Final HEAD `8a18e08` → merged `d8173d3` → wiki re-stamp `7a94482`.

## What went well
- **Plan-verifier earned its keep.** It confirmed the table-assignment contract (the one the
  whole cutover rested on) against the landed tests pre-lock, and caught 6 completeness GAPs —
  3 HIGH that would have left an external agent's `pytest` red (a stray Postgres `seed.py`, an
  engine-disposal test, two Dynamo files carrying Postgres-parity tests). All fixed before lock.
- **The sprint-47 "never trust a self-reported gate" amendment held.** The delivery's
  `evidence.yaml` claimed all-green; the orchestrator's own gate + per-story reviews found spec
  FAIL on all three stories. The amendment did exactly its job — the divergence was caught, not
  shipped.
- **The reality gate caught what tests structurally can't.** Read-path e2e proved the API serves
  off DynamoDB; the PO-requested live-loop run ingested 244 real Dynatrace observations with the
  watermark advancing — the cutover is proven, not asserted.

## What dragged
- **External delivery failed spec on all three stories — every failure was doc/wiki/AC hygiene,**
  not logic (the cutover wiring, the container, and the CFN template were all sound). The
  orchestrator absorbed a substantial review-tail fix pass. Two failure modes recurred and are
  worth mechanizing:
  1. **`verified_sha` bulk-laundering.** The delivery advanced `verified_sha` on 12 wiki articles
     to a single 40-char sha in one "update verified_shas to new HEAD" commit with no per-article
     re-verification — including 7 articles this sprint never touched. This launders staleness and
     defeats the wiki's whole drift-detection premise. The 40-char format (vs the repo's short-sha
     convention) is a mechanical tell.
  2. **Fake tombstone.** `migrations-and-db.md` was "archived" by flipping `status:` to `archived`
     while the file stayed in the main wiki dir, kept `code_refs` to deleted files, and its body
     still asserted deleted Alembic code as present-tense fact — with no `archive/` move and no
     `archived_*` frontmatter. `yt_wiki.py` passed it precisely because `status: archived` is
     skipped from the sweep — so the fake archive silenced the linter instead of being caught by it.
- **Deletion reasons unrecorded.** STORY-087 deleted the entire Postgres stack but recorded no
  reasons in the story History until the review tail — the DoD standing rule exists but nothing
  checks it, so a spec reviewer had to catch it by eye.

## Proposed amendments (routed down the enforcement ladder)

### A — `yt_wiki.py` gains two mechanical wiki-integrity lints  (rung: SCRIPT)
1. **`verified_sha` must be a short sha** (7–12 hex chars), never a 40-char sha — flags the
   bulk-laundering format directly.
2. **`status: archived` ⇒ the file lives under `wiki/archive/` AND carries `archived_sprint`
   + `archived_reason` frontmatter** — a status-flip that leaves the article in the main dir
   without a real tombstone becomes a lint failure instead of a silently-skipped pass.
- *Motivating incident:* sprint-49 external delivery laundered `verified_sha` on 12 articles and
  fake-archived `migrations-and-db.md` by status-flip; `yt_wiki.py` passed both.

### B — spec-review checklist: deletion-reason trace  (rung: CHECKLIST)
When a story's diff **deletes code**, the spec reviewer explicitly confirms the deletion reason
is recorded in the story-file History (the DoD standing rule) — traced, not assumed.
- *Motivating incident:* STORY-087 deleted the whole Postgres stack with no recorded reasons
  until the review tail.

## PO decision (2026-07-16)
- **Amendment A — APPROVED and landed** (SCRIPT rung): `yt_wiki.py` gained an `integrity` check
  (default-on, blocking) — short-sha enforcement + archived⇒`wiki/archive/`+tombstone-frontmatter.
  Validated: passes clean on the current wiki (exit 0); negative-tested to fire (exit 1) on a
  40-char sha, a status-flip-in-main-dir fake archive, and a missing `archived_reason`. Skill
  self-test 28/28 green.
- **Amendment B — APPROVED and landed** (CHECKLIST rung): `.scrum/checklists/spec-review.md`
  gained a deletion-reason trace item with the sprint-49 date + motivating incident.

Both take effect from the next standup.
