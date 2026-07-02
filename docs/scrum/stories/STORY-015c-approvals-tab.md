---
id: STORY-015c
title: Approvals tab — pending proposals list + approve/reject
type: feature
---

## Context
Spec: dossier §17 (the approval gate is the product's reason to exist — a degradation reaches
the public Statuspage only after a human approves it here). Zone 7. Split-child of STORY-015;
depends on STORY-015a. API: `GET /api/v1/approvals` (STORY-014b) +
`POST /api/v1/decisions/{proposal_id}` (STORY-014). The only mutating tab besides Maintenance.

## Description
Lists open status proposals and lets the operator approve or reject each. A decision is
deliberate: the action asks for confirmation before POSTing. After a decision the list refreshes.
A lost race (proposal already resolved by a concurrent decision — the API's 409) is surfaced as an
inline explanation and the list refreshes, never a crash or a silent no-op.

**API contract (VERIFIED 2026-07-02 — per the tab-AC-vs-DTO agreement):**
- `GET /api/v1/approvals` → `list[ProposalDTO]`, `ProposalDTO` = `{id: int, component_id: str,
  from_status: str | None, to_status: str, state: str, proposed_at: datetime}`. **There is NO
  reason/evidence field and NO friendly component name** — the tab renders `component_id`, the
  `from_status → to_status` transition (StatusBadges; `from_status` may be null for a first
  proposal), and `proposed_at`. (`backend/src/api/v1/approvals/models.py`.)
- `POST /api/v1/decisions/{proposal_id}` body = `{action: "approve" | "reject", actor: <non-empty
  str>, notes?: str | null}` → `DecisionResponse {proposal_id, state, resolved_at}`. Status codes:
  **200** success · **422** bad action / empty actor · **404** proposal not found · **409** proposal
  not open (already resolved / lost race). (`backend/src/api/v1/decisions/{models,validation,service}.py`.)

**Actor handling (PO decision 2026-07-02):** auth is deferred to STORY-017, so `actor` is a FIXED
placeholder for now — but supplied through a SINGLE swappable seam (one module, e.g.
`frontend/src/api/actor.ts` exporting `getActor()`), so when auth + scopes land the placeholder is
replaced in exactly one place. The placeholder value is NOT scattered across call sites.

## Acceptance Criteria
- [x] AC1: Open proposals render from `GET /api/v1/approvals`: `component_id`, the
      `from_status → to_status` transition (StatusBadges; handle null `from_status`), and
      `proposed_at` (mono). Empty state: "nothing pending approval". Uses the shared fetch hook
      (see AC5). Semantic, keyboard/reader-accessible markup.
- [x] AC2: Approve and Reject each POST `/api/v1/decisions/{proposal_id}` with
      `{action, actor, notes?}` where `action` is exactly `"approve"`/`"reject"` and `actor` comes
      from the swappable `getActor()` seam; a confirmation step precedes the POST; success refreshes
      the list. MSW tests drive both approve and reject end to end (assert the POSTed body shape +
      the list refresh).
- [x] AC3: A **409** (proposal no longer open — lost race) shows an inline "already resolved"
      message and refreshes the list; a **404** is handled likewise (gone → refresh); any other
      error shows the shell `ErrorState` with retry. All three POST-failure paths tested via MSW.
- [x] AC4: Loading / empty / list-load-error+retry states via the shell primitives; the action
      buttons are keyboard-operable (≥40px targets, visible accent focus ring), and the confirmation
      step is dismissable. Tested.
- [x] AC5: **Shared `useFetch<T>` established** (parallel-shape agreement — 015c is the 2nd fetch
      hook). Extract a generic `useFetch<T>(fetcher)` (discriminated-union state + cancelled-guard +
      attempt-keyed retry) from 015b's `useComponents`; refactor `useComponents` onto it; build
      `useApprovals` (or the approvals fetch) on it. No copy-pasted effect body. `useComponents`'s
      existing tests stay green (behavior identical); the generic gets its own unit test.

## Open Questions
None (API contract verified; actor handling + useFetch decided by PO 2026-07-02).

## History
- 2026-06-29: first version refined (never implemented — revert `521764c` hit first).
- 2026-07-02: re-refined for the Linear-guided direction. Status: ready. Estimate 5 (mutating
  tab, confirmation flow, race handling).
- 2026-07-02 (planning, Sprint 27): AC reconciled to the verified ProposalDTO/decision contracts
  (dropped the non-existent reason/evidence field; added the required `actor` via a swappable seam;
  enumerated the 422/404/409 codes). Added AC5 (shared `useFetch<T>`) per the parallel-shape
  agreement + Sprint-26 carry-forward. PO decisions: fixed-placeholder actor behind one seam;
  include the useFetch refactor here.
