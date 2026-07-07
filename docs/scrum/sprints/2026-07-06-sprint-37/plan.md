# Sprint 37 — Plan

**Goal:** Close the two remaining console-free maintenance gaps: the maintenance ordering
violation returns a clean, form-mappable 422 instead of a leaked Pydantic blob
(STORY-052), and the Dashboard visibly marks components that are under maintenance right
now (STORY-046).

**Committed:** 3 points — STORY-052 (1) → STORY-046 (2). Deliberate under-commit vs.
velocity ~5: these are the only two console-free `ready` stories (STORY-017 and STORY-053
both need PO console time, deferred).

**Branch:** `sprint-37` · **Start tag:** `sprint-37-start` · **Cut from main @ `b64a122`**

**Baseline:** code unchanged since the last green gate (`8237962`) — sprint-36 evidence
holds: backend 511 passed, frontend 222 passed.

---

## Standing conventions checklist (every step is held to these at the DoD gate)

Both stories are gate-only (≤2 pts, no reviewer pipeline), so this checklist is the quality
floor — the implementer applies it, the DoD gate + orchestrator tree-inspection enforce it.

- **(a) Docstrings citing the dossier §** on any new/changed module, public class, or public
  function — mirror the peer modules (`maintenance/validation.py`, `windowState.ts`,
  `fieldError.ts` all carry them).
- **(b) Frozen value/result types enforce cross-field coherence** with a
  `model_validator(mode="after")` + test. (N/A this sprint — no new value types.)
- **(c) Empty-input AND non-aligned-boundary tests** where a function takes a
  collection/window/range. STORY-046's active-window derivation reuses
  `deriveWindowState` (half-open `starts_at <= now < ends_at`), which already pins both
  boundary instants — 046's tests must cover the boundary at `starts_at` (active) and at
  `ends_at` (past/not-active) for the per-component marking.
- **(d) Scoped staging** — stage only the files the step created/changed; never `git add -A`.
- **(e) Follow existing import/naming/structure patterns** — no new style. Frontend: match
  the existing feature-folder + hook + MSW-handler shape; backend: match the edge-validator
  one-line-message style.
- **(f) Commit after every green step** — the commit cadence IS crash recovery. The wiki
  blast-radius pass commits article-by-article (2026-07-03 agreement).
- **(g) DoD counts only on a CLEAN committed tree** (2026-06-29) — leave the tree clean when
  reporting green; `ruff format` output must be COMMITTED, not left in the working tree.
- **(h) Timezone-aware datetime inputs** at the edge (2026-06-28) — N/A for new inputs this
  sprint (052 adds an ordering check on already-tz-checked datetimes; 046 adds no API input).
- **(i) Wiki blast radius = the MECHANICAL sweep** (2026-06-28), never eyeballed:
  `git diff <each article's verified_sha>..HEAD -- <its code_refs>` over all
  `docs/scrum/wiki/*.md`; update or re-verify EVERY flagged article before the story is Done.
  AC never pre-declares which articles (2026-07-03) — the sweep decides.

---

## STORY-052 — Maintenance ordering 422: clean edge message + inline frontend mapping (1 pt)

**Defect (live wire sample, 2026-07-06):** `POST /api/v1/maintenance` with
`ends_at <= starts_at` DOES return 422 — but the `detail` is the raw Pydantic blob
(`"1 validation error for MaintenanceWindow\n  Value error, ends_at must be strictly
greater than starts_at [type=value_error, input_value={...}] ... errors.pydantic.dev ..."`).
Root cause: `maintenance/service.py::MaintenanceService.create_window` step 2 catches the
domain `ValueError` and sets `detail=str(e)`, and `str()` of the Pydantic `ValidationError`
is that multi-line blob. Step 1's syntactic validator
(`maintenance/validation.py::validate_maintenance_request`) never checks ordering, so the
clean one-liner path is never taken. Downstream, the Maintenance tab's
`fieldError.ts::fieldErrorFromDetail` maps by substring in order (component_id → starts_at
→ ends_at); the blob's `input_value={...}` echo contains a `component_id` token, so today
the ordering error MIS-MAPS to the component_id field.

**Files:** backend `backend/src/api/v1/maintenance/validation.py` +
`backend/tests/test_maintenance_endpoint.py`; frontend
`frontend/src/features/maintenance/fieldError.ts` + `fieldError.test.ts`, and the
Maintenance tab MSW/error path (`frontend/src/pages/MaintenancePage.*` /
`features/maintenance/useMaintenance.*` — implementer confirms the exact seam).

### Tasks

- [x] **1. Backend — failing test for the clean ordering 422.** In
  `test_maintenance_endpoint.py`, add a test posting `ends_at < starts_at` asserting
  `status_code == 422` AND `response.json()["detail"] == "ends_at must be strictly greater
  than starts_at."` (a clean one-liner, no `"validation error for"`, no `"input_value"`,
  no `"pydantic"`). Add a sibling asserting the SAME clean detail for `ends_at == starts_at`
  (equal timestamps — the domain rule is strictly-greater). Run; see both fail (today's
  detail is the blob). Commit the test.
- [x] **2. Backend — add the ordering check to the edge validator.** In
  `validate_maintenance_request`, after the tz-aware checks, add:
  `if ends_at <= starts_at: raise SyntacticValidationError("ends_at must be strictly
  greater than starts_at.")`. This fires in service step 1 → mapped to a clean 422 BEFORE
  domain construction. The domain validator stays (defense in depth). Update the function
  docstring. Run the two tests green + the existing `test_post_maintenance_invalid_times`
  (still 422). Commit.
- [x] **3. Frontend — failing test for ends_at mapping + multi-field determinism.** In
  `fieldError.test.ts`, add: (a) `fieldErrorFromDetail("ends_at must be strictly greater
  than starts_at.")` returns `'ends_at'` (NOT `starts_at` — the ordering violation is the
  user's `ends_at` input); (b) a multi-field-detail determinism test proving a detail
  naming several fields resolves deterministically and never throws. Run; see (a) fail
  (current order returns `starts_at`). Commit the test.
- [x] **4. Frontend — fix the mapping + refresh the stale doc comment.** Make the ordering
  message map to `ends_at` (e.g. an explicit early check for the strictly-greater phrase →
  `ends_at`, placed before the generic substring scan; keep the generic scan for the other
  cases). Rewrite `fieldError.ts`'s stale `"two real backend 422 cases"` doc comment to
  reflect the THREE cases now (component_id empty, tz-aware, ordering) and cite
  `maintenance/validation.py`. Run the fieldError tests green. Commit.
- [x] **5. Frontend — Maintenance tab renders the ordering error inline on ends_at.** Add
  an MSW-backed test on the Maintenance tab: submitting `ends_at <= starts_at` gets the
  REAL new detail string (`"ends_at must be strictly greater than starts_at."`) from a
  mocked 422 and renders it INLINE next to the `ends_at` field (not a toast/console-only,
  not on component_id). Wire the page if needed to consume `fieldErrorFromDetail`'s result
  for this case. Run green. Commit.
- [x] **6. Gates + wiki sweep.** Run the full six-gate backend DoD (pytest on an ISOLATED
  throwaway DB — unset DATABASE_URL; lint-imports; check_fk_direction; alembic upgrade head;
  ruff check; ruff format --check) and the three-gate frontend DoD (npm test, npm run build,
  npm run lint). Run the mechanical wiki staleness sweep over all `docs/scrum/wiki/*.md`
  (`maintenance/validation.py` may be a `code_ref` of a maintenance/api article); update or
  re-verify each flagged article, committing article-by-article. Leave the tree clean.
  Report DoD evidence (command, output tail, exit code, commit SHA) in the final message —
  do NOT edit sprint-current.yaml (orchestrator writes the board).

**Edge behavior pinned:** ordering violation → clean `SyntacticValidationError` →
HTTP 422, for both `ends_at < starts_at` and `ends_at == starts_at`. Frontend maps that
message to the `ends_at` field deterministically.

---

## STORY-046 — Dashboard maintenance indicator (frontend overlay, Dashboard-only) (2 pts)

**Gap (audit M3):** the frontend health vocabulary has a `maintenance` value with tokens in
both themes, but `core/domain/status.py::ComponentStatus` is a closed 4-value set with NO
maintenance value, so `statusMapping.ts::toHealthStatus` can never produce `maintenance`
from `GET /api/v1/components` — the Dashboard's maintenance badge is dead code. Maintenance
state lives in maintenance WINDOWS (`GET /api/v1/maintenance`), derived client-side.

**Chosen design (PO, Option A + Dashboard-only):** the Dashboard ALSO fetches
`/api/v1/maintenance`, derives active windows client-side via the EXISTING
`features/maintenance/windowState.ts::deriveWindowState` (half-open `starts_at <= now <
ends_at`) keyed by `component_id`, and overlays a maintenance indicator per component. NO
backend change — `ComponentDTO` stays `{id, name, status}`. The indicator coexists with,
never replaces, the health status (a degraded component under maintenance shows both), and
is not color-only.

**Files:** frontend only — `frontend/src/pages/DashboardPage.*`,
`frontend/src/features/dashboard/*` (a maintenance-windows fetch hook alongside
`useComponents.ts`), reusing `features/maintenance/windowState.ts` and the existing
`maintenance` StatusBadge tokens; MSW handler for `/maintenance` on the Dashboard test.
Backend untouched.

### Tasks

- [x] **1. Failing test — active window marks its component.** In `DashboardPage.test.tsx`,
  add an MSW handler returning `/api/v1/maintenance` windows derived from the REAL wire
  shape (`{id, component_id, starts_at, ends_at, reason}`, tz-aware ISO). Assert: a
  component with an ACTIVE window (`starts_at <= now < ends_at`) shows the maintenance
  indicator; components with only UPCOMING or PAST windows, and components with NO window,
  do NOT. Pin `now` deterministically (fixtures relative to a fixed instant, or inject as
  `windowState` allows). Run; see fail. Commit.
- [x] **2. Failing test — coexistence with health + non-color-only.** Assert a component
  that is BOTH degraded (health status) AND under active maintenance renders BOTH signals —
  the maintenance indicator does not replace or hide the health badge — and the indicator
  carries a non-color cue (text/label/icon), not color alone (accessibility rule). Run; see
  fail. Commit.
- [x] **3. Fetch maintenance windows on the Dashboard.** Add a hook (e.g.
  `features/dashboard/useMaintenanceWindows.ts`) mirroring `useComponents.ts`'s
  shape/error-wrapping, using the typed client. Docstring cites dossier §6/§11 (health vs
  maintenance kept separate) + §17. Handle loading/error per the existing per-tab pattern
  (the Dashboard already renders Loading/Error states). Commit once its own unit test is
  green.
- [x] **4. Overlay the indicator.** In the Dashboard, for each component compute
  `isUnderMaintenance = windows for that component_id .some(w => deriveWindowState(...) ===
  'active')` and render the maintenance indicator alongside the existing StatusBadge using
  the existing `maintenance` tokens. Do not alter `statusMapping.ts` / `ComponentStatus`.
  Run tasks 1–2 tests green. Commit.
- [x] **5. Gates + wiki sweep.** Run the three-gate frontend DoD (npm test, build, lint).
  Run the six-gate backend DoD too and CONFIRM an empty backend diff (frontend/ change only)
  — record that. Run the mechanical wiki sweep; frontend files are unlikely to be in any
  article's `code_refs`, but run it and update/re-verify anything flagged, committing
  article-by-article. Leave the tree clean. Report DoD evidence in the final message.

**Edge behavior pinned:** active = `starts_at <= now < ends_at` (half-open, reusing
`deriveWindowState` — boundary at `starts_at` is active, at `ends_at` is not); upcoming and
past windows never mark; no window never marks; multiple windows on one component → active
if ANY is active. Maintenance and health are independent and both displayed.

---

## Sprint-close sequence (orchestrator, after both stories Done)

1. Blocking wiki compile pass — mechanical staleness sweep over ALL articles until ALL
   CURRENT at branch HEAD + internal links resolve.
2. Record DoD evidence + board transitions in `sprint-current.yaml`; write `review.md`.
3. Commit those on `sprint-37`.
4. Call the review. Merge to main is the LAST step, only after PO acceptance
   (2026-06-29 agreement).
