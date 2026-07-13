---
id: STORY-066
title: Publication author metadata (Publications timeline)
type: feature
---

## Context
Filed 2026-07-07 from the Sprint 38 redesign data-gap analysis. The mock's Publications timeline
shows an **author**, an **outcome** chip, and an **incident** reference. `PublicationDTO` carried
none of these; STORY-062 omits them (`pages/PublicationsPage.tsx:48-50` explicitly flags the gap).

This story's scope narrowed at Sprint 45 refinement (2026-07-13):
- **Outcome** was already delivered by **STORY-072** (accepted Sprint 40): `PublicationDTO.outcome`
  = `succeeded`/`failed` (`api/v1/publications/models.py:32-33`). Done — not in this story.
- **Incident id** split out to **STORY-081** — it is genuinely new *and speculative*: the
  Statuspage response is discarded at the executor boundary, and the current publish flow only
  PATCHes component status, it never creates incidents. Not worth building until real Statuspage
  incidents are in scope (PO decision 2026-07-13).
- **Author** is the remaining, derivable piece — this story.

Scout probe (2026-07-13) findings for author:
- Author is **already captured** in `approval_events.actor` (TEXT NOT NULL) when an approval
  happens (`core/services/approval.py` records `actor`; `approval_events` table, migration
  `3a8254bcfe59`). There is **no separate user/identity concept** — actor is an opaque string; the
  frontend seam `api/actor.ts` currently supplies the placeholder `"dashboard-operator"` (real
  identity deferred to STORY-017).
- It is **derivable, not new capture**: join `publications.proposal_id → status_proposals.id ←
  approval_events.proposal_id` and read the `actor` of the `approved` event. Caveat:
  `publications.proposal_id` is **nullable** (`3a8254bcfe59` — some publishes aren't
  proposal-triggered), so author is `null` for those rows. **No schema migration required.**
- Read path today: `PublicationsService.list_recent` maps `Publication` domain → `PublicationDTO`
  directly (`api/v1/publications/service.py:21-34`); `Publication` is a frozen read model
  (`core/domain/publication.py`); `PostgresPublicationRepository.list_recent` selects the six
  publication columns (`adapters/persistence/publication_repository.py:78-109`).

## Description
Surface the publish **author** on the Publications read path + `PublicationDTO`, derived on read
from `approval_events.actor` via `publications.proposal_id`. Then the frontend renders the author
in the timeline rows, degrading gracefully when absent.

## PO-approved design decisions (2026-07-13)
- **Author-only** this story; incident split to STORY-081; outcome already done (072).
- Author is **derived on read** (no new column, no new capture). `null` when the publication has no
  `proposal_id` or no matching `approved` approval event.

## Acceptance Criteria
- [ ] **AC1 (read model — author derivation).** `PublicationDTO` gains `author: str | None`. The
  publication read path resolves author by joining `publications.proposal_id` to the `approved`
  `approval_events.actor` for that proposal. A publication with `proposal_id = NULL`, or whose
  proposal has no `approved` event, yields `author: null`. The `Publication` read model carries an
  optional derive-on-read `author: str | None = None` (documented as not persisted by `record`).
- [ ] **AC2 (persistence parity).** The SAME contract test against the Postgres repository AND the
  in-memory fake covers: proposal-triggered publish whose proposal was approved by actor X →
  `author == "X"`; publish with `proposal_id = None` → `author is None`; publish whose proposal has
  no approval event → `author is None`. `GET /v1/publications` serializes `author` (string or
  `null`).
- [ ] **AC3 (no schema change).** The story diff adds **no Alembic migration**; the existing
  publications columns are unchanged; `check_fk_direction.py` still exits 0.
- [ ] **AC4 (frontend).** The Publications timeline renders the author when present and degrades
  gracefully (omits / placeholder) when `null`. `PublicationDTO` in `api/types.ts` gains `author`.
  MSW fixtures — derived from a real `/api/v1/publications` wire response captured during
  implementation — include both an author-present and an author-null row.
- [ ] **Gates + wiki blast radius.** Full nine-command `yt_gate.py` green; `yt_wiki.py` sweep clean.

## History
- 2026-07-07: filed from the redesign data-gap analysis. Status: draft (needs refinement + estimate).
- 2026-07-13: refined at Sprint 45 planning (scout probe recorded above). Scope narrowed to
  author-only (outcome done by 072; incident → STORY-081). Estimate **3**; PO design decisions
  recorded; scheduled into Sprint 45. Status: ready.
