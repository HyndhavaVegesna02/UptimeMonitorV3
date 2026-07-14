# Sprint 46 Retrospective — DynamoDB persistence seam

**Outcome:** 8/8 points accepted (STORY-082, STORY-083), merged to main (`abd13d2`).
Planned in-process; delivered externally (Antigravity) after a mid-sprint CC session limit,
then verified on resume under external-mode rules.

## What went well

- **Hexagonal boundaries did their job.** A database-engine swap touched only the adapter
  zone + composition seam; core, API, and frontend untouched; all 8 import-linter contracts
  held. Boundary-as-build-failure paid off exactly as designed.
- **Real-container tests gave genuine parity.** DynamoDB adapters reuse the *same*
  contract-assertion bodies as the Postgres adapters against a live DynamoDB Local
  container — no mocks, no drift, real reality-gate coverage. 15 DynamoDB tests green.
- **The external-mode review floor earned its keep.** Antigravity shipped one MAJOR (a
  teardown test with no Docker-skip guard, which would ERROR rather than skip on a
  no-Docker machine); spec+quality review caught it, and it was fixed in `6c4a257`. This is
  the concrete justification for "reviews regardless of size when delivery is external."

## What dragged

- **The dev-db harness flake false-red'd BOTH full-gate runs** (`test_dev_db_cli.py` at
  8153b53; `test_dev_db_fixture.py` at 6c4a257 — connection-disconnects under Docker load).
  Each cost a contention-proof cycle. The 2026-07-14(b) clean-container amendment stops
  *idle* containers, but the gate's *own* DB container still contends with the harness
  tests — a gap that amendment didn't close.
- **The session-limit pivot to external delivery was invisible on the board** (`mode` stayed
  `in-process`); external-mode verification happened only because the orchestrator recognized
  the situation on resume, not because a rule forced it.

## Estimates

Both stories delivered at estimate (082: 5, 083: 3). The one MAJOR was a cheap test-guard
fix, not a re-scope. No estimate miss.

## Amendments landed (PO-approved 2026-07-15)

1. **External-delivery pivots must set `mode: external` immediately** — *prose rung*
   (`working-agreements.md`). Makes the external-mode verification floor mechanical, not a
   judgment call, whenever a session limit or PO pivot moves implementation outside the
   in-process pipeline.

2. **Expedite STORY-080; the dev-db flake is a standing full-gate false-red until it lands**
   — *backlog-priority rung* (STORY-080 escalated to top priority for the next sprint).
   **Honest correction to the proposed interim:** the "serialize the harness tests in
   yt_gate.py" interim is a no-op — pytest here already runs serially (no xdist, no addopts).
   The flake is Docker/connection *resource* contention across the full suite, which is
   STORY-080's own durable-fix domain, not a parallelism knob. Landing that fix as an ad-hoc
   skill-script edit outside a story would violate "no code outside a sprint story," so it
   rides in STORY-080. Until then: the 2026-07-06 contention false-red protocol governs
   (empty diff since cut + passes isolated) and 2026-07-14(b) clean-container hygiene stands.

## Forward

Board is clean for the AWS epic's next slice. Natural next planning: **STORY-080** (dev-db
flake, now top priority — must be refined to an estimate first, it is still `draft`) and
**STORY-084** (DynamoDB observation adapter — the idempotent ingest transaction + half-open
window query, the highest-stakes adapter). Sequencing STORY-080 first would stop the
recurring gate false-red from taxing every subsequent sprint's close.
