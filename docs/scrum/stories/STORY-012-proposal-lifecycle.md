---
id: STORY-012
title: Proposal substrate — types + state machine + repository
type: feature
---

## Context
Spec: dossier §12 (proposal lifecycle) + §9 (schema) + T1.2. Zone 5. The persistence + domain
SUBSTRATE for status proposals — the foundation `decide` (STORY-024) consumes. Split at sprint-9
refinement: the **reconciliation RULE** (worse→supersede, recovered→obsolete, same→leave) is a core
business decision that §10 assigns to `decide`, so it moves to **STORY-024**. This story builds only
the types, the state machine, the port, and the Postgres adapter it needs.

The schema already exists (STORY-006, `migrations/.../3a8254bcfe59_spine_schema.py`):
- `status_proposals(id, component_id FK→components RESTRICT, from_status, to_status, state, reason,
  proposed_at, resolved_at, created_at)`; `state` CHECK ∈ {open, approved, rejected, superseded,
  obsoleted}; partial-unique index `uq_status_proposals_active_component` WHERE `state='open'`.
- `approval_events(id, proposal_id FK→status_proposals CASCADE, actor, action, notes, occurred_at)`;
  `action` CHECK ∈ {approved, rejected}.
No migration is needed — these tables exist.

## Description
- **Domain** (`core/domain/`): a `ProposalState` enum (open/approved/rejected/superseded/obsoleted,
  mirroring the schema CHECK) and a frozen `StatusProposal` type
  (`component_id`, `from_status: ComponentStatus | None`, `to_status: ComponentStatus`,
  `state: ProposalState`, `reason: str | None`, `proposed_at`, `resolved_at: datetime | None`,
  optional `id`). A `model_validator(mode="after")` ENFORCES the coherence invariant (per the
  sprint-8 working agreement): `resolved_at` is set IFF `state` is terminal (not `open`); an `open`
  proposal has `resolved_at is None`. A `terminal` helper / valid-transition rule: `open` may
  transition only to a terminal state; terminal states are final.
- **Port** (`core/ports/`): `ProposalRepository` (ABC, domain vocabulary):
  - `create_open(self, proposal: StatusProposal) -> StatusProposal | None` — persist a new OPEN
    proposal; returns it, or `None` if an open proposal already exists for that component (the
    partial-unique conflict — a safe no-op, AC3).
  - `get_open(self, component_id: str) -> StatusProposal | None`.
  - `resolve(self, proposal_id, *, to_state: ProposalState, reason, resolved_at) -> None` — move an
    open proposal to a terminal state.
  - `record_approval_event(self, proposal_id, *, actor, action, notes, occurred_at) -> None`.
  Export from `core/ports/__init__.py`. Add a fake for unit use (`backend/tests/fakes.py`).
- **Adapter** (`adapters/persistence/proposal_repository.py`): `PostgresProposalRepository(engine)`
  mirroring the existing repos. `create_open` uses `INSERT … ON CONFLICT DO NOTHING` against the
  partial-unique index (a losing concurrent writer no-ops + a `logging` debug line, not an
  exception — AC3); `get_open`/`resolve`/`record_approval_event` are parameterized SQL. DB-gated test.

The **reconciliation rule** + reading "current published status" are OUT OF SCOPE (STORY-024).

## Acceptance Criteria (refined — PO-approved 2026-06-26)
- [ ] AC1: `StatusProposal` + `ProposalState` model a proposal with a valid-transition rule
      (`open` → a terminal state only; terminals are final) and a `model_validator` enforcing
      `resolved_at` set IFF terminal — tested for both the rejected (incoherent) and the valid shapes
      (sprint-8 value-object agreement). Lives in `core/domain/`.
- [ ] AC2: `ProposalRepository` port (`create_open` / `get_open` / `resolve` /
      `record_approval_event`) in `core/ports/`, domain-typed; a fake exists for unit use;
      `lint-imports` green (all SQL behind the port).
- [ ] AC3: `PostgresProposalRepository.create_open` enforces ONE open proposal per component via
      `INSERT … ON CONFLICT DO NOTHING` on the partial-unique index — a second concurrent open is a
      safe no-op (returns `None` + a debug log, never raises). DB-gated test proves it (insert two
      opens for one component → only one persists, second returns `None`).
- [ ] AC4: `get_open` returns the open proposal (or `None`); `resolve` transitions an open proposal
      to a terminal state (and a NEW open can then be created for that component);
      `record_approval_event` writes an `approval_events` row. DB-gated tests cover these. No new
      migration (uses the existing tables).

## Resolved Questions
- Actionable states for the partial-unique index: `state = 'open'` (the schema's existing predicate);
  exactly one OPEN proposal per component. PO-approved 2026-06-26.
- Reconciliation rule (worse→supersede / recovered→obsolete / same→leave): OUT OF SCOPE — moved to
  STORY-024 (decide), which §10 assigns it. PO-approved split, 2026-06-26.

## History
- 2026-06-23: drafted from dossier §12. Status: draft.
- 2026-06-26 (sprint-9 refinement): split to SUBSTRATE-ONLY (types + state machine + repo + Postgres
  adapter); reconciliation rule moved to STORY-024; open question (actionable states) resolved;
  coherence invariant added per the sprint-8 agreement; estimate 5 → 3. Status: ready.
