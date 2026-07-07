# Sprint 37 — Review

**Goal:** Close the two remaining console-free maintenance gaps: the maintenance ordering
violation returns a clean, form-mappable 422 instead of a leaked Pydantic blob
(STORY-052), and the Dashboard visibly marks components under maintenance right now
(STORY-046).

**Committed:** 3 points (STORY-052 = 1, STORY-046 = 2). **Both Done.**
**Branch:** `sprint-37` (cut from main @ `b64a122`, tag `sprint-37-start`). Unmerged —
merge is the last step, only after PO acceptance.

---

## STORY-052 — Maintenance ordering 422: clean edge message + inline frontend mapping (1 pt) — DONE

**What was built.** The `ends_at <= starts_at` ordering check moved to the edge validator
(`backend/src/api/v1/maintenance/validation.py::validate_maintenance_request`), so a clean
one-line 422 (`"ends_at must be strictly greater than starts_at."`) fires in
`service.py` step 1 BEFORE domain construction — replacing the raw multi-line Pydantic blob
that `str(domain ValueError)` produced. `service.py` unchanged; the domain
`MaintenanceWindow` validator stays as defense in depth. On the frontend,
`fieldError.ts::fieldErrorFromDetail` now checks the "strictly greater than" phrase FIRST →
maps to `ends_at` (before the generic substring scan, which would else mis-map to
`starts_at`/`component_id`); its stale "two real backend 422 cases" doc rewritten to the
three cases; both sprint-34 quality-review minors folded in. `MaintenancePage.tsx` source
unchanged — it already consumed `fieldErrorFromDetail`; only its MSW test was added.

**AC checklist.**
- **AC1** ✅ ordering check in the edge validator → clean 422 for both `ends_at < starts_at`
  and `ends_at == starts_at`; endpoint tests assert the exact clean detail (and that it
  contains no "validation error for"/"input_value"/"pydantic"). Domain validator retained.
- **AC2** ✅ frontend maps the ordering message inline on `ends_at`; MSW test on the
  Maintenance tab uses the REAL new detail string; multi-field-determinism test added;
  stale doc comment rewritten.
- **AC3** ✅ six-gate backend + three-gate frontend DoD green (evidence below).

**Commits:** `c2c6651` (t1) · `b3efd95` (t2) · `1134799` (t3) · `ea2e5bc` (t4) ·
`27f904b` (t5) · `240666e`+`127c8fb` (wiki sweep).
*Note:* the Sonnet 5 implementer committed all seven tasks clean, then the process was
interrupted before its final report; the orchestrator verified crash-recovery invariants
(coherent committed work, clean tree, no scraps) and ran all nine gates itself.

**DoD evidence @ `127c8fb`** (orchestrator-run): backend pytest **513 passed** (+2:
end-before-start + equal-timestamp clean-detail tests), lint-imports 5 kept/0 broken, FK
11/0, alembic OK, ruff check + format clean; frontend 225 passed, build OK, lint clean;
wiki sweep all current.

---

## STORY-046 — Dashboard maintenance indicator (frontend overlay, Dashboard-only) (2 pts) — DONE

**What was built.** The Dashboard now ALSO fetches `GET /api/v1/maintenance` (new thin hook
`features/dashboard/useMaintenanceWindows.ts` = `useFetch(getMaintenance)`, mirroring
`useComponents`) and overlays a maintenance indicator per component. Per component,
`isUnderActiveMaintenance()` filters windows by `component_id` and ORs
`deriveWindowState(...) === 'active'` (reusing the existing half-open `windowState.ts` — a
window is active iff `starts_at <= now < ends_at`). The indicator is a SECOND `StatusBadge`
(`status="maintenance"`, label "Under maintenance") in a `.dashboard-status-cell` flex
wrapper ALONGSIDE the health badge — never replacing it, never color-only. No backend
change; `statusMapping.ts` / `ComponentStatus` untouched. Graceful degradation: any
non-`success` maintenance-fetch state → treated as no active windows → the primary
components table still renders (proven by a 500-response test).

**AC checklist.**
- **AC1** ✅ active window marks its component (existing maintenance tokens); upcoming/past
  and no-window do not. MSW-tested with active/upcoming/past + exact `starts_at`
  (active) / `ends_at` (not) boundary instants.
- **AC2** ✅ maintenance indicator coexists with the health badge (degraded + under
  maintenance shows both); non-color-only (label text). Tested.
- **AC3** ✅ three-gate frontend DoD green; backend diff empty; per-tab pattern respected.

**Commits:** `7e0f4fd` (t1) · `d08a2a1` (t2) · `8dbcc1d` (t3, hook) · `0f42798` (t4,
overlay) · `9f16880`+`a518c45` (wiki sweep).

**DoD evidence @ `a518c45`:** frontend VALID signal **230 passed / 34 files** (`vitest run
--no-file-parallelism`, exit 0 — +8 over the 222 baseline across both stories); build OK;
lint clean. Backend six-gate carried by empty backend diff `127c8fb..HEAD`.

> ⚠️ **Gate note (not a defect in this story).** The canonical `npm test` (default file
> parallelism) intermittently exits 1 on ONE pre-existing, unrelated test —
> `CheckHistoryPage.test.tsx`'s 1500-row 1000-cap render hits Vitest's 5000ms default
> timeout under CPU contention. Proven a contention false-red: empty diff since
> `sprint-37-start`, passes in isolation (11 passed, 3.6s), passes single-threaded (230),
> and passed green during STORY-052's own `npm test` run. Handled per the binding
> 2026-07-02 contention-false-red agreement (re-run cleanly for the real signal). Filed as
> **STORY-054** (defect) so the gate itself becomes deterministic. Retro input.

---

## Demo steps (local)
1. Start the stack (throwaway DB + API + frontend) per CLAUDE.md "Run the app locally".
2. **STORY-052:** on the Maintenance tab, submit a window with `ends_at <= starts_at` →
   the error renders inline on the *Ends* field reading "ends_at must be strictly greater
   than starts_at." (no Pydantic blob). Or `curl -X POST /api/v1/maintenance` with an
   inverted window → `422 {"detail":"ends_at must be strictly greater than starts_at."}`.
3. **STORY-046:** with an active maintenance window for a component, the Dashboard row
   shows both its health badge AND an "Under maintenance" badge; upcoming/past windows do
   not mark it.

## Sprint-close state
- Wiki compile pass: **0 stale, 0 broken links** at HEAD `4e3a4e7`.
- Velocity to record on acceptance: 3 points.
- Follow-ups filed: **STORY-054** (flaky frontend gate). STORY-053 refined (proxy-shim,
  console-gated, draft). STORY-017 remains parked on `sprint-35`.
