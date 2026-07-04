# Sprint 33 — Review

**Goal:** the Check History tab (STORY-015e) + the Publications tab (STORY-015g) — the two
read-only audit surfaces. **Five of the six tabs are now real** (Maintenance is the last
placeholder).
**Branch:** `sprint-33` (from main @ `350e928`). Committed 5 pts; both stories Done, both
first-pass clean — zero fix loops this sprint.
**DoD surface:** three frontend gates; backend untouched all sprint (empty diff, six-gate
baseline holds).
**Wiki compile pass:** 13/13 articles CURRENT at review HEAD, 0 broken links.

## STORY-015e — Check History tab (3 pts) — recommend ACCEPT

What was built: signal selector (topology enumeration) + 24h/7d/30d window selector driving
tz-aware refetches; dense observation table (timestamp mono, health badge, latency mono,
location); a NEW `observationHealth` mapper for the observation vocabulary; 1,000-row render cap
with a visible count note. Commits `e84f4cc..a2163ca` + wiki `f8b525e`/`ead0819`.

AC evidence (spec reviewer RAN 177/177 and read test bodies):
- **AC1:** signal picked from the STORY-044 enumeration; newest-first rows with all four fields;
  render order proven equal to response order (no re-sort).
- **AC2:** both selectors drive refetches; tests assert the ACTUAL `signal_key` and tz-aware
  `since`/`until` MSW received on change.
- **AC3:** machine values mono; badges dot+label. The planning-time vocabulary check paid off:
  observation `health` is `up|down|degraded` (NOT ComponentStatus) — unhandled, "up" would have
  rendered as *unknown*; the dedicated mapper renders it correctly (verified live).
- **AC4:** loading/empty/error+retry for BOTH fetches; volume strategy explicit — a 1,500-row
  test asserts "showing latest 1,000 of 1,500 observations".

Pipeline: spec PASS + quality APPROVE, both first-pass (identity chain traced; zero-signal edge
safe; `windowToRange` reused not duplicated; fixtures derive from the pinned live sample).
Gate: 177/177 + build + lint at clean `a2163ca`. **Live render-vs-wire spot check (new
agreement): rendered first row exactly matches wire row[0]** (`…13:29:17.931000Z / Up / 571 ms /
SYNTHETIC_LOCATION-…0060`).

Open minors (non-blocking): row key includes the index (style); on a selector switch the
previous rows show until the new fetch resolves — shared `useFetch` behavior across all tabs,
awareness only.

## STORY-015g — Publications tab (2 pts) — recommend ACCEPT

What was built: plain read tab — `PublicationDTO` + `getPublications()`, thin
`usePublications`, table of published-at (mono) / component / single StatusBadge / proposal_id
(mono, null → em-dash), permanent "Showing the latest 50 publications" header copy (the backend
caps server-side, so the client never learns a true total — permanent copy is the honest form).
Commits `e7d04e0`, `b7811cf`, `2b0f2a6` + wiki `4f787bc`/`5230f59`.

AC evidence:
- **AC1:** newest-first render of all four fields; `status` verified as the ComponentStatus
  vocabulary → the EXISTING `toHealthStatus` correctly reused (contrast 015e).
- **AC2:** loading / empty ("Nothing published yet") / error+retry all MSW-tested.
- **AC3:** per-tab pattern followed; badges dot+label; the 50-cap visible, tested.
- Fixtures derive from named backend test fixtures (`test_publications_endpoint.py:39-50,70-76`,
  `test_publication_domain.py:39-46`) per the real-sample agreement — statuses
  operational/degraded/major_outage, proposal_id 5/42/null.

Pipeline: 2 pts → gate-only. Gate: 188/188 + build + lint at clean `2b0f2a6`. **Live spot
check:** the endpoint returns `[]` and the tab renders the honest empty state + cap copy.

## Demo steps (stack is running)

1. http://localhost:5173/check-history — 120 real observations; switch signals/windows.
2. http://localhost:5173/publications — honest empty state. To see rows appear live: flip
   Sample mode ON (Dashboard) → wait for the degrade proposal (Approvals) → approve → the
   publication lands here with its proposal_id.
3. `curl "http://localhost:8000/api/v1/history?signal_key=http-check"` — wire rows the tab
   renders 1:1.

## Notes for retro / next planning

- Zero fix loops, zero stalls, zero reviewer re-dispatches — cleanest sprint since 27; both
  2026-07-04 agreements (units/scale check, live spot check) were exercised and useful.
- Observed: Dynatrace has produced no new synthetic executions since 2026-07-03 ~13:29 UTC (the
  loop polls healthily; the tenant-side monitor may be paused — PO to check the Dynatrace UI).
- Remaining: 015f Maintenance tab (3, ready) — the last placeholder; STORY-043 (.env, 2,
  ready); STORY-047 (1, ready); STORY-017 + STORY-050 need refinement.

## Verdicts (PO, 2026-07-04)

- STORY-015e (3 pts): **ACCEPT**
- STORY-015g (2 pts): **ACCEPT**

Velocity recorded: 5 committed / 5 accepted. No follow-up stories.
