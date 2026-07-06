# Sprint 34 — plan (locked 2026-07-06)

**Goal:** Land the ingestion-stall fix on main and complete the second mutating tab: the
live loop ingests reliably past its first cycle (STORY-051), and operators can view and
schedule maintenance windows from the dashboard (STORY-015f).

**Committed:** STORY-051 (2) + STORY-015f (3) = 5 points, at measured velocity 5.
**Order:** 051 first (backend correctness, mostly pre-written — an honest live demo for
015f's review depends on a loop that actually ingests), then 015f.

**Branch mechanics:** `sprint-34` cut from main @ `c5a90f8` (tag `sprint-34-start`), then
fast-forwarded to `6b34c1a` by merging `debug/sample-mode-forced-down-not-applied` — the
PO-directed debug lineage carrying STORY-051's fix + records. Done at lock, before this
plan was written.

---

## STORY-051 — DQL watermark bare-string stall (defect, 2 pts, gate-only)

The fix (`c1839e4`: `build_dql_query` wraps the watermark bound in `toTimestamp()`;
covering test pins the new form AND forbids the bare-string regression) and its wiki/story
records are already on this branch via the lock merge. AC1 is pinned by the committed
test; AC2 was live-verified twice (2026-07-04 fix session; 2026-07-06 debug sprint —
watermark advanced `06:13:54 → 06:15:54` across consecutive cycles against real Grail).
Remaining work is the mechanical close-out:

- [ ] 1. Confirm clean committed tree (`git status` empty) at `6b34c1a`-or-later.
- [ ] 2. Run the six-command backend DoD gate (single, non-concurrent invocation against
      the throwaway DB per the 2026-07-02 agreement): `pytest`, `lint-imports`,
      `python scripts/check_fk_direction.py`, `alembic upgrade head`, `ruff check .`,
      `ruff format --check .` — all exit 0.
- [ ] 3. Run the mechanical wiki staleness sweep over ALL articles (2026-06-28 agreement)
      — the merged commits touch `query.py` + `test_dynatrace_adapter.py` +
      `sample-mode.md`/`dynatrace-adapter.md`; the sweep decides what (if anything) still
      needs a re-verify bump. Commit article-by-article if updates emerge.
- [ ] 4. Record dod_evidence + board `done` in `sprint-current.yaml`; tick story AC3.

No implementer dispatch expected. Any fix loop that DOES emerge → fresh Sonnet 5
implementer at HIGH effort with a focused brief (2026-06-25 fresh-agent rule).

## STORY-015f — Maintenance tab (feature, 3 pts, full pipeline)

Second mutating tab (pattern precedent: Approvals 015c for mutation + list refresh;
Check History 015e for selector/tab conventions). Dossier §17; DESIGN-linear.app.md
guides, never copies. AC as amended at planning (AC3 trimmed, PO-approved — see the
story file's 2026-07-06 History entry; producer gap filed as STORY-052).

### Verified API contracts (pinned at planning, live wire + producing code)

`GET /api/v1/maintenance` → `MaintenanceWindowDTO[]`; `POST /api/v1/maintenance` with
`{component_id, starts_at, ends_at, reason?}` → the created DTO. Real wire sample
(live round-trip, 2026-07-06 — MSW fixtures MUST derive from this shape, real-sample
rule):

```json
[{"id": 1, "component_id": "http-check", "starts_at": "2026-07-07T10:00:00Z",
  "ends_at": "2026-07-07T11:00:00Z", "reason": "planning-time wire probe"}]
```

- **Units/formats:** `id` int; `component_id` raw string id; datetimes ISO-8601 UTC `Z`;
  `reason` `string | null` (render null as an em-dash, never "null"/empty-looking).
- **NO `state` field on the wire.** upcoming/active/past is derived CLIENT-SIDE with the
  backend's half-open rule — active ⟺ `starts_at <= now < ends_at`
  (`core/ports/maintenance_repository.py::is_under_maintenance`; Postgres adapter
  `starts_at <= at AND ends_at > at` agrees). A window is NOT active at exactly
  `ends_at`. Derivation lives in one pure, unit-tested helper (e.g.
  `features/maintenance/windowState.ts`) — not inline in the component.
- **Real 422 cases only:** tz-naive `starts_at`/`ends_at`; empty/whitespace
  `component_id`. End-before-start is NOT rejected by the backend (STORY-052) — the form
  must not claim otherwise; a client-side ordering hint is allowed only as a
  non-blocking warning, and only if cheap (optional, not AC).
- **Submission:** the form takes local time (`<input type="datetime-local">`) and
  submits tz-aware ISO (`new Date(value).toISOString()`); the MSW test asserts the
  payload received by the handler is tz-aware and well-formed (AC2).
- Component options for the form's component field: reuse the existing components/
  topology source the other tabs use (see `frontend-zone.md`) rather than a new fetch
  shape.

### Task breakdown (TDD, commit after every green step)

- [x] 1. `mocks/handlers/maintenance.ts` — GET/POST handlers + fixtures derived from the
      wire sample above; register in `handlers/index.ts` (additive spread, mirroring
      peers).
- [x] 2. `api/types.ts::MaintenanceWindowDTO` + `api/client.ts::getMaintenance` /
      `postMaintenance` (reuse `putJson`-style helper conventions; error-wrapping per
      STORY-041) — client tests: happy path + ApiError wrap + the POST body shape.
- [x] 3. `features/maintenance/windowState.ts` — pure derivation (upcoming/active/past),
      unit tests including BOTH boundary instants (`now === starts_at` → active;
      `now === ends_at` → past) per the half-open rule and the non-aligned-boundary
      agreement.
- [x] 4. `features/maintenance/useMaintenance.ts` — list via shared `useFetch`; create
      mutation with in-flight flag + refresh-on-success (015c Approvals precedent);
      mutation error kept for inline rendering; tests via MSW.
- [x] 5. `pages/MaintenancePage.tsx` (+ `.css`) — windows list (component, start/end in
      mono, reason, state badge via tokens-only dot+label) + schedule form (labeled
      inputs, text-input spec, focus ring, keyboard operable); replace the placeholder.
- [x] 6. AC3 test: MSW 422 (naive datetime / empty component_id shapes as FastAPI emits
      them) → error renders INLINE on the relevant field(s), not toast/console-only.
- [x] 7. Loading / empty ("No maintenance scheduled") / error+retry states — tested (AC4).
- [ ] 8. Wiki blast radius: run the mechanical sweep; expected minimum `frontend-zone.md`
      (+ whatever the sweep flags); commit article-by-article.
- [ ] 9. Frontend DoD gate on the clean committed tree: `npm test`, `npm run build`,
      `npm run lint` — all exit 0. Verify backend untouched: diff from STORY-051's gate
      SHA over backend/ scripts/ pyproject.toml alembic.ini migrations/ config/ is EMPTY.

### Conventions checklist (standing, self-contained — quality review holds code to it)

(a) module/public-symbol doc comments citing the dossier §/story, mirroring peer tabs;
(b) empty-input AND non-aligned/boundary tests where applicable (windowState boundaries);
(c) scoped staging — never `git add -A`; (d) follow existing import/naming/structure
patterns (tokens.css variables only — no hardcoded colors; shared primitives; per-tab
feature dir); (e) MSW is the only mocked edge; fixtures derive from the pinned real
sample; (f) tests DRIVE the AC's named scenario and assert its outcome — no
name-matching; contract changes rewrite covering tests, never delete to a gap;
(g) DTO fields map directly — no sentinel fallbacks; (h) rendered null/absent values get
an explicit visual (em-dash), tested.

### Review prep (orchestrator)

- Live render-vs-wire spot check (2026-07-04 agreement): with the local stack up, load
  /maintenance, schedule a real window, compare at least one rendered row field-by-field
  against `curl /api/v1/maintenance`, and confirm the state badge matches the half-open
  rule for a window spanning "now".
