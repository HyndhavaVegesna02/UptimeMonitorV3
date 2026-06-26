# Sprint 9 — Review

**Goal:** Zone 5's two foundations — the proposal substrate (STORY-012) and the Statuspage publish
adapter (STORY-013) — setting up `decide` (STORY-024) next.

**Branch:** `sprint-9` (commits `a2985e1..77e694d`) · **Committed:** 6 pts · **Done:** 6 pts
**Capacity:** 6. **First sprint implemented externally (PO / Gemini); orchestrator reviewed.**

---

## STORY-012 — Proposal substrate: types + state machine + repository (3 pts) — ✅ DONE

**Pipeline:** external impl (Gemini) → spec **PASS** (Opus) → quality (Opus): 1 MAJOR → **fix loop 1**
(Gemini) → orchestrator-verified → DoD gate green.

Built: `ProposalState` + frozen `StatusProposal` (with the `model_validator` enforcing `resolved_at`
set IFF terminal — per the sprint-8 agreement); a `terminal` property + `is_valid_transition`;
`ProposalRepository` port (`create_open`/`get_open`/`resolve`/`record_approval_event`) + a fake;
`PostgresProposalRepository` (one-open-per-component via `ON CONFLICT DO NOTHING` on the partial-unique).
No migration — uses the existing `status_proposals`/`approval_events` tables. Reconciliation rule
correctly deferred to STORY-024.

### AC checklist (spec reviewer verified each MET)
- AC1 types + state machine + coherence validator (both rejected + valid shapes tested) ✅
- AC2 port + fake, SQL behind the port ✅ · AC3 create_open ON CONFLICT → None on the partial-unique
  (DB-gated) ✅ · AC4 get_open / resolve-frees-the-slot / approval_event written (DB-gated) ✅

**Fix loop:** quality caught that `resolve` did `UPDATE ... WHERE id=:id` with no `state='open'` guard
and ignored rowcount — silently re-resolving a terminal proposal / no-oping on an unknown id, and
diverging from the fake. Fix loop 1 added `WHERE id=:id AND state='open'` + a `rowcount != 1` raise,
made the fake raise to match, and folded three minors. Orchestrator verified by direct diff inspection.

---

## STORY-013 — Statuspage publish adapter + commit-first boundary (3 pts) — ✅ DONE

**Pipeline:** external impl (Gemini) → spec **PASS** (Opus) → quality **APPROVE** (Opus) → DoD gate green.

Built: `adapters/outbound/statuspage/` (first outbound adapter) — `StatuspagePublisher` implementing
`StatusPublisherPort`, resolving `component_id` → vendor id via an injected mapping (raises
`UnmappedComponentIdError` on unknown), mapping `ComponentStatus` → the Statuspage string
(`DEGRADED→degraded_performance`, exhaustive, raises on unknown), via an injected executor seam (no
live HTTP). Plus `composition/publish_helper.publish_best_effort` — catches `Exception`, logs, never
re-raises (proves a publish failure can't roll back the committed decision). The commit-first DB
ordering is correctly left to STORY-024.

### AC checklist (spec reviewer verified each MET)
- AC1 injected mapping + executor seam, request asserted ✅ · AC2 best-effort swallow+log (caplog) ✅
- AC3 fake executor, no live HTTP ✅ · AC4 adapter under outbound/, helper in composition/, boundary clean ✅

Quality APPROVE — zero Critical/Major. (Minor notes: a leftover import-smoke test; the degraded
fixture is unused since the executor return is discarded — recorded, non-blocking.)

---

## DoD evidence (orchestrator-verified, with DB)
| Command | Result |
|---|---|
| `pytest` | 264 passed (with DB) |
| `lint-imports` | 3 kept, 0 broken |
| `check_fk_direction.py` | 10 FKs, 0 violations |
| `alembic upgrade head` | no-op (no migration this sprint) |

## Demo
- Proposal substrate: `pytest backend/tests/test_proposal.py backend/tests/test_persistence_adapters.py -k proposal`.
- Publish adapter: `pytest backend/tests/test_statuspage_adapter.py`.
- Pure unit tests use in-memory fakes; the Postgres proposal repo uses a throwaway DB.

## Process note (first external-implementation sprint)
Gemini implemented to `plan.md`; the orchestrator ran the full DoD gate + spec/quality reviews. The
one MAJOR routed back to Gemini per the new workflow agreement and was fixed in a tight loop. Gemini
respected the boundaries — it never touched `sprint-current.yaml` or the working agreements.

## Wiki
Compile pass done: no stale articles. `canonical-types-and-ports.md` (proposal types + port) and
`persistence-adapters.md` (the adapter) updated by Gemini; new `statuspage-publish.md` for the publish
path. Orchestrator rehabilitated `architecture-boundary.md` (first `outbound` + 2nd composition
importer) and `persistence-adapters.md` (corrected drifted line citations + the resolve-guard Fact);
added the cited fixtures dir to `statuspage-publish.md`'s code_refs. Links clean.

## Carried into Sprint 10
- STORY-024 (decide, stage 4, 3, draft) — both halves it needs (proposals + publish) now exist;
  resolve its "current published status" read seam, then it ties Zone 4→5 together.
- Chores: STORY-027 / 029 / 030 (1 pt each, ready).

## PO verdict
- [x] STORY-012 — **ACCEPTED** (2026-06-26). 3 pts. Merged to main.
- [x] STORY-013 — **ACCEPTED** (2026-06-26). 3 pts. Merged to main.
- PO directed a follow-up: **STORY-031** (Sprint 9 review cleanups — leftover import-smoke test,
  unused degraded fixture, style nits) added to the backlog as `ready`.
