# Sprint 34 — review (2026-07-06)

**Goal:** Land the ingestion-stall fix on main and complete the second mutating tab.
**Committed:** STORY-051 (2) + STORY-015f (3) = 5. **Delivered for verdict:** both, 5/5.
Branch `sprint-34` (cut `c5a90f8`, tag `sprint-34-start`), HEAD at review prep includes the
lock-merged debug lineage (STORY-051 fix + records) + 015f's TDD commits.

---

## STORY-051 — DQL watermark bare-string stall (defect, 2 pts) — verdict requested

**What:** `build_dql_query` emitted `timestamp >= "<ISO>"`; DQL silently matches nothing on
a bare-string timestamp compare, so every post-backfill cycle fetched 0 rows and the
watermark never advanced — a permanent, invisible ingestion stall. Fix (`c1839e4`): wrap
the bound in `toTimestamp()`; the covering test pins the new form AND forbids the
bare-string regression.

**AC evidence:**
- AC1 (query form pinned + regression-forbidden): `backend/tests/test_dynatrace_adapter.py`
  (committed with the fix).
- AC2 (live: new observations persist, watermark advances): verified TWICE against real
  Grail — 2026-07-04 fix session, and the 2026-07-06 debug sprint (watermark
  `06:13:54 → 06:15:54` across consecutive cycles; 120+2 rows;
  `docs/scrum/sprints/2026-07-06-debug-sample-mode/report.md`).
- AC3 (six-command backend DoD, clean committed tree): @ `362fb52` — pytest **498 passed**,
  lint-imports **5 kept / 0 broken**, FK-direction **11 FKs / 0 violations**,
  `alembic upgrade head` OK, ruff check + format clean. All exit 0.
- Wiki sweep at gate: 0 stale (the debug-session commits already updated
  `dynatrace-adapter.md` + `sample-mode.md`).

**Demo:** the live loop against real Dynatrace now ingests fresh rows every 120s cycle and
advances the watermark — shown end-to-end in the debug-sprint report (both sample-mode ON
→ forced-down rows and OFF → genuine up rows).

## STORY-015f — Maintenance tab (feature, 3 pts) — verdict requested

**What:** the sixth and final tab goes real: maintenance windows list (component, mono
start/end, reason with em-dash for null, upcoming/active/past badge derived client-side by
the backend's half-open rule `starts_at <= now < ends_at`) + a schedule form (component
select from the shared topology source, datetime-local inputs submitted tz-aware, inline
422 field errors, refresh-on-success). Implementer: Sonnet 5, single clean dispatch, 10
TDD commits (`9681432..a65de00`), no fix loop.

**AC evidence (spec reviewer: PASS, all four MET; quality reviewer: APPROVE, 0C/0M):**
- AC1: table renders all fields; `windowState.ts` pure helper with BOTH boundary instants
  unit-tested (`now === starts_at` → active; `now === ends_at` → past); tokens-only badge.
- AC2: MSW test asserts the HANDLER-RECEIVED payload is tz-aware (`endsWith('Z')`,
  round-trips) driven through the real form; success refetches (call-count + new row).
- AC3: both real 422 cases (naive datetime → Starts field; empty component_id → Component
  field) asserted INSIDE the field container — not toast/console.
- AC4: labels via htmlFor (getByLabelText all four), Tab-order test, loading/empty/
  error+retry each driven.
- DoD gate (orchestrator, clean HEAD `53ad5a1`): npm test **222 passed** (33 files), build
  OK, lint clean. Backend paths untouched (`362fb52..HEAD` empty).
- LIVE render-vs-wire spot check (2026-07-04 agreement): two real windows POSTed to the
  real API; rendered rows match the wire field-by-field; a window spanning "now" badges
  **Active**, the future one **Upcoming**, null reason renders **—**.

**Demo steps:** stack up (`dev_db.py up` → uvicorn :8000 → `cd frontend && npm run dev`),
open `/maintenance`: two seeded windows visible; schedule a new window via the form and
watch the list refresh; submit a naive datetime via devtools to see the inline field error.

**Open minors (recorded, non-blocking — accept + follow-up per process):** ordering-422
Pydantic blob mis-maps to the Component field (folded into STORY-052 AC2 with the stale
doc comment); inline-error JSX duplicated 4×; no aria-describedby association (peer-tab
consistent); `new Date().toISOString()` relies on native `required`; `select` lacks the
accent focus ring.

## Disclosure — mid-sprint planning-check correction (no scope impact)

The planning-time consumer-DTO check WRONGLY concluded the backend does not 422
end-before-start windows (it read only the edge validator and live-probed only the happy
path). The 015f implementer flagged the contradiction; live re-probe confirmed the DOMAIN
layer rejects end-before-start AND equal timestamps (422) — but with a raw multi-line
Pydantic blob as the `detail`. Records corrected same-day (`8b46295`): STORY-052 re-scoped
from "missing 422" (false) to "clean edge message + inline frontend mapping" (real). The
amended AC3 the PO approved remains narrower-but-true; the story was built and reviewed
against it as locked. Retro input: planning contract checks must probe failure paths live.

## Blocked stories
None.

## Velocity on acceptance
Both accepted → record `{sprint: 34, committed: 5, accepted: 5}`.
