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
