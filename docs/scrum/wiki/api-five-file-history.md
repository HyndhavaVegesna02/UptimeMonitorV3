---
title: API five-file convention — the compile record (history of [[api-five-file-convention]])
tier: reference
verified_sprint: sprint-69
# tier: reference (2026-08-12). Split out of `api-five-file-convention.md`, where the History
# was 127 of 198 lines — the same shape `zone-rules.md` had, and the same clean boundary. This
# half is the append-only compile record: which sprint added which feature to the
# `api-feature-independence` contract, which stories touched the five-file shape and which
# explicitly did not, what each `verified_sha` was bumped to back when that field existed.
#
# It cannot rot. Every entry is anchored to the sprint and story it describes, and a later
# change cannot make "sprint-42 created api/v1/_shared/ with errors.py" untrue. The
# `verified_sha → <sha>` lines throughout are a record of PAST bookkeeping under a field
# retired 2026-08-12, kept because the sequence is the evidence — not live frontmatter.
#
# No code_refs and no `## Facts` section, per the reference tier. Any claim about the API zone
# as it stands NOW lives in [[api-five-file-convention]], which is swept. Nothing machine-reads
# this file (checked: no test, tool or source module references it).
---

This is the history half of [[api-five-file-convention]]. Read that article for what the
convention IS and which half of it a standing test enforces; read this one for how the API zone
arrived at its current shape and which stories deliberately left it alone.

## History
- sprint-25: re-verified (STORY-015a). The only `pyproject.toml` change was adding `"frontend"` to
  `[tool.ruff] exclude` — a ruff-scope tweak for the new frontend SPA, unrelated to the
  `api-feature-independence` contract or the five-file convention this article describes. 5 contracts
  kept / 0 broken, unchanged. verified_sha → 08d91e7.
- sprint-28: re-verified (STORY-042). The only `pyproject.toml` change was adding `uvicorn[standard]`
  to the dev extras (a local ASGI dev server) — no bearing on the `api-feature-independence` contract
  or the five-file convention. 5 contracts kept / 0 broken, unchanged. verified_sha → 6303247.
- sprint-30 (STORY-044): added the NEW `topology` feature (five files, `GET /topology`, D3/AC1) and
  `src.api.v1.topology` to the `api-feature-independence` contract's `modules` list (the contract
  COUNT stays 5 — `lint-imports` still reports "5 kept / 0 broken"; only that one contract's module
  list grew). Extended the `availability` feature: `GET /availability/component/{component_id}`
  (D4/AC2) and the D5/AC3 per-signal default-interval fix (audit finding H2) —
  `AvailabilityService` gained required `component_repo`/`signal_repo` ctor deps (contract change,
  rewrote every call site). `signal_repo` added to `create_app`'s params/`app.state`;
  `get_signal_repo` added to `api/dependencies.py`. verified_sha → 280c1e3.
- sprint-31 (STORY-048, a TEMPORARY feature — see [[sample-mode]]): added the NEW `sample_mode`
  feature (five files, `GET`/`PUT /sample-mode`, D3) and `src.api.v1.sample_mode` to the
  `api-feature-independence` contract's `modules` list (contract COUNT stays 5 — `lint-imports`
  still reports "5 kept / 0 broken"; only that one contract's module list grew, same shape as
  sprint-30's `topology` addition). `create_app`/`app.state`/`api/dependencies.py`/
  `api/v1/__init__.py` each gained a marked STORY-048 seam. verified_sha → 0ea652e.
- sprint-36 (STORY-043, mechanical staleness sweep only): the only `pyproject.toml` edit was
  adding `python-dotenv` to `[project.dependencies]` (a `.env`-loading defect fix, unrelated to
  the API layer) — the `api-feature-independence` contract's `modules` list and the five-file
  convention are untouched. 5 contracts kept / 0 broken, unchanged. verified_sha → 6a33edb.
- sprint-36 (STORY-047, quality-review minors chore): AC1 fixed `create_app`'s injected-fakes
  path — see the updated bullet above (a `component_repo` without a `publication_repo` now still
  gets write-back). AC4 changed `AvailabilityService.get_component_availability` to build each
  `SignalAvailabilityDTO` via the shared `_to_dto` helper instead of spelling out all nine fields
  inline — no behavior change, no new fact to record. Five-file convention and
  `api-feature-independence` contract untouched. verified_sha → d441468.
- sprint-37 (STORY-052, defect fix + mechanical staleness sweep): `api/v1/maintenance/validation.py::validate_maintenance_request`
  gained the `ends_at <= starts_at` ordering check (see the updated `maintenance` feature bullet
  above) — `service.py` itself is UNCHANGED (the fix is entirely which layer's exception the
  existing step-1/step-2 try/except in `service.py::MaintenanceService.create_window` catches
  first). Five-file convention and `api-feature-independence` contract untouched. verified_sha → 27f904b.
- sprint-39 (STORY-071, defect fix, mechanical staleness sweep): `core/services/approval.py::ApprovalService._decide`
  was recording the present-tense verb (`action="approve"`/`"reject"`) into `approval_events.action`,
  violating the spine's `ck_approval_events_action` constraint (`action IN ('approved', 'rejected')`)
  on every real approve/reject — a 500 on `POST /api/v1/decisions/{id}`. Fixed by deriving
  `action=to_state.value` inside `_decide` instead of a separately-hard-coded literal (the `action`
  param was dropped from `approve`/`reject`'s calls into `_decide` entirely). `test_approval.py` and
  `test_decisions.py` assertions that pinned the old (wrong) `'approve'`/`'reject'` literal were
  updated to `'approved'`/`'rejected'`. No change to the five-file shape, DTOs, or the
  `api-feature-independence` contract. verified_sha → 06cf232.
  **SUPERSEDED at sprint-67 (STORY-200) — see below: `_decide` now passes `to_state` itself, not
  `to_state.value`, because `record_approval_event`'s port parameter is `ProposalState`, not `str`.**
- sprint-40 (STORY-072, record-always publication outcome): `PublicationDTO`
  (`api/v1/publications/models.py`) gains `outcome: str`; `service.py::PublicationsService.list_recent`
  now also maps `p.outcome.value` (Facts updated above). No change to the five-file shape or the
  `api-feature-independence` contract; `test_publications_endpoint.py` (see [[persistence-adapters]]
  for the paired repository/migration change) gained an assertion on `outcome` in the DTO shape test
  plus a defaulting-to-`succeeded` case. verified_sha → 144bcc0.
- sprint-42 (STORY-075): Created `api/v1/_shared/` with `errors.py` (registry and exception handlers installer) and empty `middleware.py` seam. Wired `install_error_handlers(app)` into `create_app` (`composition/app.py`). Stripped local try/except exception mapping logic from availability and history controllers, and decisions and maintenance services. Added `api-shared-no-feature-imports` contract in `pyproject.toml`. verified_sha → d967acc.
- sprint-42 (STORY-076): Consolidated read-window defaulting policy in `api/v1/_shared/windowing.py` (24h constant + `resolve_window` function). Updated availability and history services to consume it and delete their private defaulting copies. Added direct unit tests in `test_shared_windowing.py`. verified_sha → fd9e706.
- sprint-42 (STORY-075, code-quality review fix loop): MAJOR-2 converted `_shared/errors.py` from seven copy-pasted per-exception closures to the `_STATUS_BY_EXCEPTION` dict + `_make_handler` factory (Facts updated above), pure refactor, no behavior change. MAJOR-1 hoisted `SyntacticValidationError` out of four per-feature duplicate definitions into a NEW `_shared/validation.py` (Facts updated above) — each feature `validation.py` (`availability`, `decisions`, `history`, `maintenance`) now imports and re-exports the shared class instead of defining its own; this is legal under `api-shared-no-feature-imports` because the forbidden direction is `_shared`→feature, and this is feature→`_shared`. The base `ValueError`→422 catch-all was then removed from the registry entirely, since it silently downgraded genuine server-side `ValueError`s (and `pydantic.ValidationError`, a `ValueError` subclass) to 422 instead of 500. Removing it opened a regression: a tz-aware-but-non-UTC `starts_at`/`ends_at` (e.g. `+05:30`) used to reach the domain `MaintenanceWindow` validators and get caught by the (now-gone) base handler; closed by adding UTC-offset checks to `api/v1/maintenance/validation.py::validate_maintenance_request` (Facts updated above) so it stays a clean 422 at the edge. New tests: `test_shared_errors.py::test_shared_errors_bare_value_error_500` (bare `ValueError` → 500) and `test_maintenance_endpoint.py::test_post_maintenance_non_utc_starts_at_clean_detail`/`test_post_maintenance_non_utc_ends_at_clean_detail` (non-UTC offset → clean 422). All pre-existing tests pass unmodified. `lint-imports`: 8 kept / 0 broken, unchanged (contract list/count untouched — only `_shared`'s own import set grew, which the contract still permits since it points at `_shared/validation.py`, not a feature). Entirely within the `api` zone — no core/adapters/composition changes. verified_sha → f21ae5a.
- sprint-43 (STORY-078): Repointed availability rollup reference from core/services/ to core/queries/. verified_sha → 05f640e.
- sprint-43 (STORY-077): Documented decisions concurrency nuance (ProposalNotOpenError -> 409 covers both up-front guard and lost-race resolve) in decisions/service.py and core/services/approval.py. verified_sha → be886af.
- sprint-43 (quality-review fix loop, M2): re-verified after `availability/models.py`'s docstring
  repointed its `core/services/availability.py::AvailabilityResult` mirror-reference to
  `core/queries/availability.py::AvailabilityResult` (STORY-078 follow-up). No five-file-convention
  Fact or contract count changed. verified_sha -> 10a2d73.
- sprint-44 (STORY-064, pilot): `history` feature's `ObservationDTO` (`api/v1/history/models.py`)
  gained `response_status_code: int | None` and `check_type: str`; `HistoryService.get_history`
  (`api/v1/history/service.py`) now also maps `o.response_status_code` and `o.source.native_kind`
  (Facts updated above). No five-file-convention shape or `api-feature-independence` contract
  change; existing history validation tests (tz-naive 422, five-file shape) stay green. See
  [[canonical-types-and-ports]] for the paired `SignalObservation.response_status_code` domain
  field and [[persistence-adapters]]/[[migrations-and-db]] for the persistence/migration side.
  verified_sha -> 0da9568.
- sprint-45 (STORY-065/STORY-066): verified after implementing Maintenance title + DELETE endpoint and Publication author metadata. Added `MaintenanceWindowNotFoundError` -> 404 mapping in `errors.py`. Added optional `title` to `MaintenanceWindowDTO`/`CreateMaintenanceRequest` and exposed `DELETE /api/v1/maintenance/{window_id}` in `controller.py`. Added optional `author` to `PublicationDTO` in `publications/models.py` (Facts updated above). verified_sha -> f6f589fd4dcb6e3a2a565453c43b0fb95d7e5787.



- 2026-07-13 (sprint-45 gate closure): re-stale was the trailing ruff/lint commit 48fba51 (behavior-neutral — trailing-blank trims; MaintenancePage dropped the now-unused formatReason helper + added a type import). Facts unchanged. Re-verified; verified_sha -> 2db6c70.
- sprint-46 (STORY-082): Re-verified after pyproject.toml changes. verified_sha -> abd8609.
- sprint-51 (STORY-094, defect/enhancement): added optional `limit` query param to `GET /history` (Facts updated above) — `api/v1/history/controller.py::get_history` gained `limit: int | None = Query(None, ge=1, ...)`; `api/v1/history/service.py::HistoryService.get_history` applies the cap as `sorted_obs[:limit]` after the existing most-recent-first sort. `ObservationRepository.in_window` port signature unchanged (no port churn); `models.py` (`ObservationDTO`) unchanged. No change to the five-file shape or the `api-feature-independence` contract. verified_sha -> c6f6916.
- sprint-63 (STORY-181): the sweep flagged `middleware.py` and `pyproject.toml`. `middleware.py`'s
  docstring no longer names the archived STORY-017; it now states no CORS middleware is required
  (dev: Vite proxy; prod: same-origin behind CloudFront, STORY-089) and remains an unassigned seam
  for future middleware — Fact above corrected to match. `pyproject.toml`'s change was a comment-only
  fix to the vendor-subpackage note (unrelated to this article's contract-count Facts). No other Fact
  or contract count changed. verified_sha -> b272c32.
- sprint-67 (STORY-200): the sweep flagged `core/services/approval.py` and `test_approval.py`
  (`ProposalRepository.record_approval_event` gained a domain-typed `action: ProposalState`
  parameter — see [[canonical-types-and-ports]] and [[persistence-adapters]] for the port/adapter
  side). `ApprovalService._decide` (`approval.py::ApprovalService._decide`) now passes `action=to_state`
  directly instead of `to_state.value` (the Fact above marked SUPERSEDED), and gained a NEW guard —
  raising `InvalidApprovalActionError` for any `to_state` outside `{APPROVED, REJECTED}` before any
  repository access — proven by
  `test_approval.py::test_approval_service_decide_rejects_action_outside_approved_or_rejected`.
  `test_decisions.py`'s HTTP-level assertions (`event["action"] == "approved"`) are unchanged: they
  run against `FakeProposalRepository`, which appends `action` verbatim to a dict, and
  `ProposalState.APPROVED == "approved"` still holds (`ProposalState` is a str-mixin `Enum`). No
  change to the five-file shape, DTOs, or the `api-feature-independence` contract. verified_sha -> d469d2c.
- sprint-67 (STORY-200 fix round, quality review — ALSO FIX): re-verified after the fix round's
  `_decide` docstring correction (it no longer claims a nonexistent Postgres-era
  `ck_approval_events_action` CHECK constraint backs this guard — that constraint was retired with
  the relational layer at STORY-087 and this DynamoDB-only repo enforces nothing datastore-side; the
  `_decide` guard is the sole enforcement) and the last bare-string `record_approval_event` call site
  fix in `test_core_ports.py` (unrelated to this article's `code_refs`). No Fact above changed. Also
  corrected `verified_sprint`, left at the stale `sprint-63` in the previous re-stamp despite
  `verified_sha` already reading `d469d2c` — a within-diff inconsistency the reviewer caught.
  verified_sha -> 013f344.
- sprint-69 (STORY-206, verified_sha bumped `013f344` -> `f3319cb`): `pyproject.toml` (a
  `code_ref`) gained a ninth `lint-imports` contract, `inbound-adapters-dont-persist` (ZR-1's guard
  — see [[zone-rules]]), unrelated to `_shared`/feature fencing. The `_shared`-fencing Fact's quoted
  `lint-imports: 8 kept / 0 broken` is corrected to 9 kept; no other Fact, the five-file shape, or
  the `api-feature-independence`/`api-shared-no-feature-imports` contracts changed.
- sprint-69 (STORY-206 rework, quality review MINOR): the trailing clause on that same Fact —
  "this particular Fact's own contract count is unchanged by this article's own subject matter" —
  contradicted the count it had just corrected. Reworded to say what was meant: the
  `api-shared-no-feature-imports` CONTRACT this Fact describes is itself unchanged by STORY-206;
  the overall count moved only because a different, unrelated contract was added elsewhere. The
  same rework also fixed the maintenance-note referent and attribution above `pyproject.toml`'s
  `inbound-adapters-dont-persist` contract (a `code_ref` of this article) — comment-only, no
  contract structure changed. verified_sha bumped `f3319cb` -> `c34e193` (the `pyproject.toml`
  comment-fix commit) to reflect that `code_ref` moving; the sweep would otherwise flag this
  article STALE against it.
- sprint-69 (STORY-206, QM-5 fix / wiki sweep at resume 2026-08-12): the sweep flagged this
  article STALE a third time — `pyproject.toml` (a `code_ref`) moved at `13bbb07`. Comment-only
  above `[tool.importlinter]` (module-form invocation + a `sys.path` warning — see
  [[architecture-boundary]]). The two contracts this article is about,
  `api-shared-no-feature-imports` and `api-feature-independence`, are byte-for-byte unchanged, as
  is the 9 kept / 0 broken figure quoted in the `_shared`-fencing Fact. Re-verified only.
  verified_sha bumped `c34e193` -> `13bbb07`.
