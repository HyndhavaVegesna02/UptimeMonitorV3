# Sprint 40 Retro

**Outcome:** 1 story (STORY-072, publication outcome), 5/5 pts accepted, merged to `main`.

## What went well
- Systematic debugging pinned the record-successes-only design gap from the log + publisher-chain read;
  the fix was designed with the PO (AskUserQuestion: record-with-outcome + defer publish) before coding.
- The Sprint 39 retro lesson was applied proactively: the new `outcome` CHECK constraint shipped with a
  DB-gated allowed-and-rejected test, so the STORY-071 class can't recur on this column.
- Record-always verified by driving the REAL publisher chain against real Postgres on both success and
  failing-publish paths — reproduction, not assertion.

## What dragged
- A first orchestrator gate run gave 78 DB-gated "alembic upgrade head failed" errors — proven
  ENVIRONMENTAL (the session-hammered throwaway DB had leftover state/connections colliding with the
  migration round-trip test; a fresh `dev_db down+up` → 522 green, matching the implementer + spec
  reviewer). Handled per the 2026-07-02 / 2026-07-06 contention agreements (reset DB, re-run for the
  valid signal). Cost one wasted ~6-min run.

## Amendment decision
No NEW working-agreement proposed. The environmental false-red is already covered by the
2026-07-02 (single-invocation DB) + 2026-07-06 (prove-contention, re-run isolated) agreements — the
corrective action here (reset the throwaway DB when it has been used by a long-running local stack
before running the gate) is an application of those, not a new rule. Recorded as reinforcement.

## Follow-ups
- MINOR: `publish_helper` failure path masks the original delegate error if `record()` itself raises
  (benign; best-effort still swallows). Optional follow-up.
- Standing: STORY-066 (publication author/incident) — outcome delivered here; author/incident remain.
  STORY-070 (vendor-id drift health check) still open. The Statuspage 401 credential is the PO's to
  refresh (`STATUSPAGE_API_KEY`).
