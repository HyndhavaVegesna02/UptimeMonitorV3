# Sprint 27 — Plan

**Dates:** starts 2026-07-02.
**Goal:** the Approvals tab (STORY-015c) — the human approval gate — plus the shared `useFetch<T>`.
**Branch:** `sprint-27` (tag `sprint-27-start` @ `7938f2a`). Committed: 5 pts (velocity mean 4.33).
**Mode:** in-process — Sonnet 5 implementer at high effort; Opus spec + quality reviewers (5 pts → full pipeline).
**Execution order:** single story; within it, AC5 (shared `useFetch<T>`) FIRST (015b's `useComponents`
refactors onto it, and the new approvals hook is built on it), then the tab.

All work is inside `frontend/`. **No backend source change.** Six backend DoD commands stay green
untouched; the three frontend commands (`npm test` / `npm run build` / `npm run lint`, from
`frontend/`) exit 0 on a clean committed tree. Reuse the shell's tokens + primitives; no new raw hex.
Design reference: `DESIGN-linear.app.md` (guide). This is the 2nd real tab — mirror the per-tab
pattern 015b set (page in `pages/`, fetch hook in `features/<tab>/`, per-feature MSW module in
`mocks/handlers/`).

TDD cadence: failing test → see it fail → minimal code → green → **commit after every green step**,
staging only touched files (never `git add -A`), branch verified `sprint-27` before each commit.

## Verified API contracts (do not assume beyond these)

- `GET /api/v1/approvals` → `list[ProposalDTO]`. `ProposalDTO` (`backend/src/api/v1/approvals/models.py`):
  `{ id: number, component_id: string, from_status: string | null, to_status: string, state: string,
  proposed_at: string (ISO datetime) }`. **No reason/evidence, no friendly name.**
- `POST /api/v1/decisions/{proposal_id}` (`backend/src/api/v1/decisions/`): body
  `{ action: "approve" | "reject", actor: string (non-empty), notes?: string | null }` →
  `DecisionResponse { proposal_id: number, state: string, resolved_at: string }`. Status:
  **200** ok · **422** action not approve/reject OR actor empty · **404** `ProposalNotFoundError` ·
  **409** `ProposalNotOpenError` (up-front guard OR lost-race concurrent double-submit).

## STORY-015c — Approvals tab (5 pts) — AC1–AC5

- [ ] **T1 — Shared `useFetch<T>` (AC5).** Extract a generic
      `frontend/src/features/lib/useFetch.ts` (or `src/lib/useFetch.ts` — match where shared hooks
      sit) from 015b's `useComponents`: `useFetch<T>(fetcher: () => Promise<T>)` returning
      `{ state, retry }` over a discriminated-union `FetchState<T>` (loading | error | success), the
      cancelled-guarded effect, and the `attempt`-keyed retry (mirror `useComponents` exactly — it's
      race-safe and eslint-clean). Unit-test the generic (success, error, error→retry via a fake
      fetcher / MSW). Then refactor `features/dashboard/useComponents.ts` to
      `useFetch(getComponents)` — its existing tests must stay green (behavior identical; rewrite,
      don't delete). No `eslint-disable`.
- [ ] **T2 — Actor seam (AC2).** Add `frontend/src/api/actor.ts` exporting `getActor(): string`
      returning a FIXED placeholder (e.g. `"dashboard-operator"`) with a doc-comment stating this is
      the single swap-point for STORY-017 auth. This is the ONLY place the placeholder lives. Unit
      test asserts it returns a non-empty string.
- [ ] **T3 — Types + client + MSW handler (AC1, AC2).** Add `ProposalDTO` +
      `DecisionRequest`/`DecisionResponse` to `frontend/src/api/types.ts` (mirror the verified
      shapes). Add to `frontend/src/api/client.ts`: `getApprovals(): Promise<ProposalDTO[]>` (GET
      `/v1/approvals`) and `postDecision(proposalId, body): Promise<DecisionResponse>` (POST
      `/v1/decisions/{id}` — extend the client with a typed POST helper that wraps network/non-2xx
      /malformed-body into `ApiError` carrying the status, mirroring `getJson`; the status must be
      readable so the tab can branch on 409/404). Add `mocks/handlers/approvals.ts` (GET handler +
      `FIXTURE_PROPOSALS` incl. a null-`from_status` case; a POST handler) composed into
      `mocks/handlers/index.ts`.
- [ ] **T4 — `useApprovals` + list render (AC1, AC4).** `features/approvals/useApprovals.ts` =
      `useFetch(getApprovals)`. `pages/ApprovalsPage.tsx` renders the open proposals via the hook:
      per proposal, `component_id`, the `from_status → to_status` transition (two `StatusBadge`s via
      `toHealthStatus`; render null `from_status` as e.g. an em-dash / "new"), `proposed_at` (mono),
      and Approve/Reject action buttons. Loading (`LoadingState`), empty ("nothing pending approval",
      `EmptyState`), and list-load-error+retry (`ErrorState`). Panel `headingLevel="h1"`. MSW-driven
      tests for success (incl. the null-from case), empty, and load-error+retry.
- [ ] **T5 — Approve/Reject + confirmation + failure handling (AC2, AC3).** A confirmation step
      precedes each POST (a dismissable confirm — inline confirm row or dialog; keyboard-operable,
      ≥40px targets, visible accent focus). On confirm, POST `{action, actor: getActor(), notes?}`.
      Success → refresh the list (re-run the hook's fetch). **Failure branches** (read the `ApiError`
      status): **409** → inline "already resolved" message + refresh the list; **404** → inline
      "no longer exists" + refresh; **any other** → the shell `ErrorState` (or an inline error) with
      the ability to retry the decision. MSW tests drive: approve success (+ assert POSTed body =
      `{action:"approve", actor:<placeholder>, notes?}`), reject success, 409, 404, and a generic
      500 — each asserting the named outcome (message + refresh vs error state).
- [ ] **T6 — Gates + blast radius.** All three frontend gates exit 0 on a clean committed tree. No
      CLAUDE.md/DoD change (no new command). Blast radius: this touches `frontend-zone.md` code_refs
      (client.ts, types.ts, mocks/handlers/, and adds useFetch/useApprovals/actor) — the orchestrator
      folds the article update into the sprint-end compile pass; flag any other article if touched.

## Conventions checklist (held at quality review)
- **Tokens, not hex;** status is dot/icon + ink label, never color-alone; health color never as text
  color (badge dot/bg carries it; label text = ink ≥4.5:1 both themes).
- **Tests drive real behavior:** MSW at the network boundary is the ONLY mock — never mock
  `useFetch`/`useApprovals`/the page under assertion; assert via accessible roles/text and (for the
  POST) the actual request body MSW received. Tests that lie / assert nothing = blocking.
- **A contract change rewrites its tests, never deletes coverage** (2026-06-29): the `useComponents`
  refactor onto `useFetch` keeps its behavior tests green; the generic gets its own test.
- **Parallel-shape / shared assembly** (2026-06-25): `useFetch<T>` IS this agreement being honored —
  no copy-pasted effect body between `useComponents` and `useApprovals`.
- **Every list surface has a tested empty state** (2026-06-25): "nothing pending approval".
- **Mutate-endpoint failure paths** (2026-06-28 TOCTOU family): the 409 lost-race path is explicitly
  handled AND tested (not just the happy path); 404 and generic error too.
- Scoped staging; commit-after-green; TS strict on; no `eslint-disable`; doc-comment new public
  hooks/modules mirroring the shell's style.
- **Double-test convention (Sprint-26 carry-forward):** it is fine to test the fetch state machine
  once at the `useFetch` level; the tab tests then assert the tab's own behavior (render, confirm,
  POST body, failure branches) — do NOT re-assert the generic fetch machine at the page level.

## Guardrails (implementer)
- Build to THIS plan + `docs/scrum/stories/STORY-015c-approvals-tab.md` + dossier §17 — never chat
  history. Do NOT change backend source (six backend gates stay green). Do NOT write `.scrum/` board
  state; do NOT run reviewers or merge — the orchestrator owns the back half.
- Genuine ambiguity → STOP and report the exact question. Effort > 3× the 5-pt estimate → STOP.
- Report: steps done + commit SHA each; every gate command + exit + tail; design decisions; anything
  noticed-but-not-done; or the blocking question.

## Sequencing rationale
`useFetch<T>` (AC5/T1) first: it's the foundation both the refactored `useComponents` and the new
`useApprovals` sit on, and doing it first means the tab is built on the shared hook rather than a
soon-to-be-replaced copy. Actor seam + types/client/handlers next (the data plumbing), then the list
render, then the mutate + failure handling (the highest-uncertainty piece — confirmation flow + four
response-code branches — gets the most runway). Gates + blast-radius last.
