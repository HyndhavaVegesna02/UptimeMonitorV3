# Sprint 52 Retro — 2026-07-17

Process inspection (product judgments live in review.md).

## What happened worth learning from

1. **Gate pytest wiped the live local stack** (the sprint's one real incident). The
   orchestrator ran the baseline full gate with `DYNAMO_ENDPOINT_URL` exported for the
   live local stack; the suite's `clean_dynamo_tables` fixture (which honors that var)
   wiped topology/observations mid-sprint and left a fixture component behind. Surfaced
   confusingly later — as "Topo Comp / No data" during a reality-gate pass — and cost a
   diagnose/restore cycle (container restart + reseed). Sprint-51's STORY-094 had already
   modeled correct isolation (own container, own port) and yourteam 2.1.0 names the
   stateful-resource-isolation pattern; the mistake was not applying it to gate runs.
2. **The reality gate caught what green tests structurally missed** — drawer covered the
   destination page after nav-link navigation; 400 jsdom tests could not see it, one live
   Playwright pass did. Validates the PO's "verify every change with Playwright" directive.
3. **Brief vs agent definition drift on wiki ownership**: the STORY-096 brief said "do NOT
   edit wiki" (implementer obeyed, flagged only); STORY-097's implementer followed the
   yt-implementer definition's report schema (which has a `wiki.updated` field) and updated
   the two articles itself. Content was verified accurate and accepted, but two stories in
   one sprint handled the same obligation two different ways.
4. **Vite HMR artifacts twice looked like real defects** during live verification (hook-order
   console errors after 10+ hot patches; a stale-composite "white sidebar" in full-viewport
   headless screenshots). Both disproven the same way: hard reload for console truth,
   element-scoped screenshot / computed styles for color truth.

## Amendments (PO-delegated approval, routed down the enforcement ladder)

- **A1 — Gate runs never point at a live stateful endpoint.** Full or scoped gate runs that
  include `pytest` MUST run with `DYNAMO_ENDPOINT_URL` (and any future stateful-endpoint var)
  unset, letting the suite manage its own throwaway resources; the live dev stack's endpoint
  is exported only in the dev-stack terminals, never in the gate shell. (Rung: checklist —
  added to `.scrum/checklists/implementer.md` §gates; candidate for a `yt_gate.py`
  hard-warning at the script rung next time the skill is versioned, kept project-generic via
  the existing `(requires-env: ...)` DoD annotation mechanism, e.g. a `(forbid-env: ...)`
  counterpart. Motivated by: this sprint's wipe incident.)
- **A2 — Live-verification false-alarm protocol.** During browser-based verification: any
  console error after hot patches → hard reload before filing; any full-viewport screenshot
  color/theme anomaly on sticky/fixed elements → re-verify with an element screenshot +
  computed styles before filing. (Rung: checklist — added to the orchestrator's reality-gate
  practice via this retro record + journal lesson; motivated by: two false alarms this
  sprint.)
- **A3 — Wiki ownership follows the agent definition, not per-brief improvisation.**
  Implementer briefs must not override wiki ownership ad hoc: the yt-implementer definition's
  contract (update blast-radius articles, report `wiki.updated`/`flagged`) is the single
  source; the orchestrator's job is to REVIEW those updates at story close, not to forbid
  them. (Rung: prose here + brief-writing practice; motivated by: the 096/097 divergence.)

## Tooling friction
None new. Playwright MCP + ui-ux-pro-max both pulled their weight; no mid-sprint tooling
changes requested.
