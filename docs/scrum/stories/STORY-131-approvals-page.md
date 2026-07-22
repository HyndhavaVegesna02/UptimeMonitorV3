# STORY-131 — Approvals page on real backend data (first mutating page)

**Status:** ready · **Points:** 5 · **Sprint:** 60
**As** an operator, **I want** to review pending status-change proposals and approve or reject each
with a confirm step — **so that** no degradation is published to Statuspage without a human decision.

## Context
New-frontend initiative (sprint 60, external mode), on the sprint-59 design system + shell.
Replaces the `ApprovalsPage` placeholder. **The first page that mutates** — it introduces the
client write path. **Design fresh** with craft via the mandatory skills + refimg language; do NOT
reconstruct the old tab. Contracts in `plan.md` §Approvals. Add to `frontend/src/api/{client,types}.ts`:
the write helper(s) (`postJson`) and `postDecision(proposalId, body)`, plus `DecisionRequest` /
`DecisionResponse` types. The list source `getApprovals()` already exists (returns `ProposalDTO[]`).

## Acceptance criteria
1. **Pending list:** render every open proposal from `GET /api/v1/approvals` (`ProposalDTO`):
   component, the **from → to** status transition (health badges — `from_status: null` shows as
   "New"), and the proposed-at time. No invented fields (the wire has no severity/reason — do not
   fabricate them; a tone derived purely from `to_status` is allowed but must be clearly derived).
2. **Approve / reject** via `POST /api/v1/decisions/{proposal_id}` with body
   `{ action: "approve" | "reject", actor, notes? }`. `actor` is a single fixed operator constant
   (one swap-point for future auth).
3. **Confirm flow:** an action requires a second confirm step (idle → confirming → submitting);
   only one proposal is mid-decision at a time; the buttons disable while submitting.
4. **Error handling by status:** **409** (proposal not open / lost race / double-submit) → a
   non-destructive "already resolved" notice + list refresh; **404** (no longer exists) → "no longer
   exists" notice + refresh; any other failure → an inline error on that card with retry. A mutation
   never throws to the console.
5. **Success** resolves the card and refreshes the list from the server (no optimistic-only state).
6. States: loading / error (retry) / **empty** (a tidy "queue clear" state) / success.
7. Exactly one `<h1>`; buttons have accessible names; the confirm prompt is reachable + dismissable
   by keyboard; focus is managed sensibly across the state transitions; motion emil-guarded +
   `prefers-reduced-motion`; `tabular-nums` for any counts/times.
8. Gates: `npm test`, `npm run build`, `npm run lint` exit 0; every AC has ≥1 test — including a
   **forced 409** (double-submit / not-open) and a 404 test.

## Reality gate
Local stack up. Scripted Chromium: with the live queue **empty**, the "queue clear" empty state
renders (matches `GET /api/v1/approvals` → `[]`); the write path is exercised against the real
endpoint where a proposal is available, and the 409 path is demonstrated (a second submit of the
same proposal yields the friendly notice, not a crash). 390px + 1440px, zero console errors.

## History
- 2026-07-22: implemented on `sprint-60`. **Deleted** the `ApprovalsPage` placeholder
  (`PlaceholderPage` mount from STORY-121) and replaced it with the real page — no other page still
  uses it, and `PlaceholderPage` itself stays (Maintenance/Publications still mount it). Introduced
  the sprint's first write path: a private `postJson<T>` in `frontend/src/api/client.ts` mirroring
  the existing `getJson`'s `readOkJson`/`ApiError` handling (so `.status`/`.detail` populate
  identically for a non-2xx POST), plus `postDecision(proposalId, DecisionRequest)` ->
  `POST /api/v1/decisions/{proposal_id}` and the `DecisionRequest`/`DecisionResponse` types
  (`frontend/src/api/types.ts`). New `frontend/src/features/approvals/` module: `operatorActor.ts`
  (the single fixed `OPERATOR_ACTOR` constant — one swap-point for future auth),
  `useApprovalsDecisions.ts` (the confirm/submit state machine LIFTED to one shared slice so "only
  one proposal mid-decision at a time" is structural, not a per-card convention; 409/404 both
  refresh the list with a non-destructive notice, any other failure stays confirming with an inline
  retry, and a mutation never throws to the console — proven with forced 409/404/500 tests plus a
  `console.error` spy), and the fresh `ProposalCard` (from→to health badges via
  `api/statusMapping.ts::toHealthStatus`, `from_status: null` → "New", a two-step Approve/Reject ->
  Confirm/Cancel prompt that is keyboard-dismissable via Escape and focus-managed — Confirm gets
  focus on open, the original trigger gets it back on cancel, found by a `data-role` query against a
  stable container ref rather than a captured — and un-mount-stale — DOM node, since the trigger
  buttons live in a different subtree than the confirm block). `ApprovalsPage` assembles the list
  against `getApprovals()` with the existing `useFetch`/`LoadingState`/`ErrorState`/`EmptyState`
  ("Queue clear" for zero proposals). Extended `frontend/src/mocks/handlers/approvals.ts` with a
  null-`from_status` proposal fixture and a `POST /api/v1/decisions/:proposalId` handler. Every AC
  has ≥1 test, including page-level forced-409 and forced-404 integration tests (asserting both the
  friendly notice AND a genuine second `getApprovals` fetch, not just local removal). All three
  frontend DoD gates (`npm test`/`npm run build`/`npm run lint`) green on a clean tree.
