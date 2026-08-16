---
title: Zone 1 — the canonical vocabulary and the core ports
code_refs: [backend/src/core/domain/signal.py, backend/src/core/domain/status.py, backend/src/core/domain/verdict.py, backend/src/core/domain/proposal.py, backend/src/core/domain/component.py, backend/src/core/domain/maintenance.py, backend/src/core/domain/publication.py, backend/src/core/domain/topology.py, backend/src/core/ports/__init__.py, backend/src/core/ports/clock.py, backend/src/core/ports/observation_repository.py, backend/src/core/ports/proposal_repository.py, backend/src/core/ports/rejected_observation_repository.py, backend/src/core/ports/signal_ingest.py, backend/src/core/ports/signal_repository.py, backend/src/core/ports/status_publisher.py, backend/src/core/ports/watermark.py, backend/src/core/ports/component_repository.py, backend/src/core/ports/maintenance_repository.py, backend/src/core/ports/publication_repository.py, backend/src/core/services/pipeline.py, backend/src/core/services/approval.py, backend/tests/fakes.py, backend/tests/test_ingest_service.py]
tier: map
verified_sprint: sprint-67
status: verified
# tier: map, `verified_sha` dropped 2026-08-12 (yourteam 2.3.0): the staleness baseline is now
# this article's own last commit, derived by git, so there is no stamp to keep current.
# WHAT THIS EDIT DID AND DID NOT VERIFY: it did not re-read these Facts against code. It
# established, per-article, that NO code_ref has moved since this article's last commit
# (`git diff <that commit>..HEAD -- <code_refs>` -> empty, and the sweep is CLEAN at HEAD),
# so the verification earned at sprint 67 is not invalidated by anything since. That is
# the same guarantee `status: verified` has always carried here; the frontmatter migration
# adds no new claim. Articles nobody could make that statement for were demoted to `stale`
# in the same pass, not laundered.
---

## Facts (verified against code)

### Canonical domain types (`core/domain/`, frozen Pydantic v2)
- `SignalObservation` is the vendor-neutral spine — one synthetic monitor execution
  from one location (`signal.py::SignalObservation`). Frozen via `model_config = ConfigDict(frozen=True)`
  (`signal.py::SignalObservation`). Fields: `signal_key:str`, `observed_at:datetime`,
  `health:Health`, `source_event_id:str`, `source:Provenance`,
  `location:str`, `latency_ms:int|None=None`, `response_status_code:int|None=None` (STORY-064 —
  optional HTTP response status code; `None` when the vendor row omits it or it is unparsable),
  `raw_ref:str|None=None` (`signal.py::SignalObservation`).
- `observed_at` is validated to be tz-aware **UTC** — a naive datetime AND any non-zero
  UTC offset are both rejected (`signal.py::SignalObservation._require_utc`). Strict reading of §5
  "UTC run time"; keeps unnormalized wall-clock values out of the core.
- `Health(str, Enum)` is a closed enum: exactly `up` / `down` / `degraded` (`signal.py::Health`).
  Not pass/fail — so a partial outage is expressible.
- `Provenance` (frozen) is the SOLE home of vendor identifiers: `{system, native_id,
  native_kind}` (`signal.py::Provenance`). `native_id`/`native_kind` are the vendor's own id and
  monitor type. No vendor id appears anywhere else on `SignalObservation`.
- `ComponentStatus(str, Enum)` closed enum: `operational` / `degraded` / `partial_outage`
  / `major_outage` (`status.py::ComponentStatus`). The canonical component status; the
  ComponentStatus→Statuspage-string mapping is a Zone 5 adapter concern, not here.
- `StatusChange` (frozen) `{component_id:str, status:ComponentStatus}` (`status.py::StatusChange`).
  `component_id` is the canonical component id the core owns — never a Statuspage id
  (`status.py::StatusChange`).
- `IngestResult` (frozen) `{accepted:int, rejected:int}` (`status.py::IngestResult`) — the outcome
  of ingesting one batch.
- `STATUS_SEVERITY` severity-ordering helpers (`status.py::STATUS_SEVERITY`): mapping and comparison functions (`status.py::severity_rank`, `status.py::is_worse`) to order and compare component status severity (operational < degraded < partial_outage < major_outage) (STORY-024).
- `Verdict` (frozen, `verdict.py::Verdict`) — STORY-010's pipeline output type: one cycle's
  collapsed verdict for one signal. Fields: `signal_key:str`, `observed_at:datetime`
  (the cycle instant — `max(observed_at)` across the cycle's observations, tz-aware
  UTC via the same `_require_utc` validator pattern as `SignalObservation`),
  `health:Health|None=None`, `under_maintenance:bool=False`. Represents BOTH a normal
  health verdict (`under_maintenance=False`, `health` set) AND a maintenance marker
  (`under_maintenance=True`, `health=None`) in one type, so `streak` can skip
  maintenance verdicts without a second type.
- STORY-025: that maintenance<->health shape is now ENFORCED, not just documented — a
  `model_validator(mode="after")` (`verdict.py::Verdict._require_maintenance_health_coherence`)
  rejects both incoherent shapes at construction (`under_maintenance=True` with a set `health`;
  `under_maintenance=False` with `health=None`), raising `ValueError` (wrapped as Pydantic `ValidationError`).
  Mirrors `signal.py`'s `_require_utc` validate-at-construction pattern. `collapse`
  (`pipeline.py::collapse`) already only ever builds the two coherent shapes, so this is
  unreachable from the existing pipeline today — it guards future hand-built `Verdict`s.
- `ProposalState(str, Enum)` is a closed enum representing the workflow states of a status
  proposal: `open` / `approved` / `rejected` / `superseded` / `obsoleted` (`proposal.py::ProposalState`).
- `StatusProposal` (frozen) models a proposal to transition a component's status (`proposal.py::StatusProposal`).
  Fields: `component_id:str`, `from_status:ComponentStatus|None`, `to_status:ComponentStatus`,
  `state:ProposalState`, `reason:str|None=None`, `proposed_at:datetime`, `resolved_at:datetime|None=None`,
  `id:int|None=None`. Timezones for proposed_at/resolved_at are validated to be UTC (`proposal.py::StatusProposal`).
- `Component` (frozen) models a component and its display status (`component.py::Component`).
  Fields: `id:str`, `name:str`, `status:ComponentStatus`, `app_id:str` (STORY-014b),
  `group:str|None=None`, `description:str|None=None` (STORY-147) — both additive/optional
  display metadata (a decorative sub-label and a one-line operator-facing description),
  sourced from `composition/config.py::ComponentConfig` via topology seeding
  (`composition/seed_dynamo.py`) and read back with `.get()` by
  `DynamoComponentRepository._map_item` (see [[persistence-adapters]]) so a component item
  seeded before STORY-147, carrying neither key at all, still reads back as `None` rather
  than raising `KeyError`. `None` is a legitimate state — a component not yet categorized —
  never a placeholder value.
- STORY-045: `ComponentNotFoundError` (`component.py::ComponentNotFoundError`, a `ValueError` subclass)
  mirrors `proposal.py::ProposalNotFoundError`'s pattern. Raised by `ComponentRepository.set_status`
  when the conditional write affects zero rows (2026-06-28 check-then-act agreement: never a bare
  `ValueError`) — both `DynamoComponentRepository` and `FakeComponentRepository` raise it identically
  (2026-06-26 fake/adapter parity agreement). See [[persistence-adapters]] for the adapter Facts.
- STORY-044: `Signal` (`topology.py::Signal`, frozen) is the seeded-topology read model — distinct
  from `signal.py::SignalObservation` (a runtime observation). Fields: `signal_key:str`, `name:str`,
  `component_id:str|None` (`None` for an orphan signal), `interval_seconds:int|None` (`None` when the
  D1 migration's backfill hasn't run yet for this row). A `model_validator(mode="after")`
  (`topology.py::Signal._require_positive_interval_when_set`) enforces `interval_seconds > 0` when not
  `None` (2026-06-26 coherence agreement; both-shapes tested). Two domain errors, deliberately plain
  `Exception` subclasses (NOT `ValueError`, unlike `ComponentNotFoundError`/`ProposalNotFoundError`):
  `SignalNotFoundError` (`topology.py::SignalNotFoundError`) and `SignalIntervalUnconfiguredError`
  (`topology.py::SignalIntervalUnconfiguredError`) — both raised by the EDGE SERVICE
  (`api/v1/availability/service.py`, see [[api-five-file-convention]]), never by `SignalRepository`
  itself, when the default-interval resolution path needs a signal that is absent from the topology
  or seeded without a configured interval, respectively.
- `MaintenanceWindow` (frozen) models a scheduled maintenance window for a component (`maintenance.py::MaintenanceWindow`).
  Fields: `component_id:str`, `starts_at:datetime`, `ends_at:datetime`, `reason:str|None=None`, `title:str|None=None` (STORY-065, sprint-45), `id:int|None=None`. Timezones for starts_at and ends_at are validated to be UTC (`maintenance.py::MaintenanceWindow`). Enforces `ends_at > starts_at` invariant via a `model_validator(mode="after")` (`maintenance.py::MaintenanceWindow._require_ends_after_starts`) (STORY-036).
- `Publication` (frozen) records a Statuspage publish ATTEMPT (§9, §12/T1.1, §17, STORY-037; STORY-072
  changed it to record-always) (`publication.py::Publication`).
  Fields: `component_id:str`, `status:ComponentStatus` (the status attempted, not necessarily
  published), `published_at:datetime` (UTC-validated via `field_validator`, same pattern as
  `MaintenanceWindow`), `proposal_id:int|None=None`, `outcome:PublicationOutcome=SUCCEEDED` (STORY-072
  — whether the Statuspage call itself succeeded or raised; defaults to `SUCCEEDED` matching the
  migration backfill, but production code always sets it explicitly), `id:int|None=None`, `author:str|None=None` (STORY-066, sprint-45) derived on read from approval events. Naive or
  non-UTC `published_at` is rejected at construction (`publication.py::Publication._require_published_at_utc`).
  `PublicationOutcome` (`publication.py::PublicationOutcome`, STORY-072) is a closed `str, Enum` —
  `SUCCEEDED = "succeeded"` / `FAILED = "failed"` — DISTINCT from `ComponentStatus` (which health
  status was attempted vs. whether the publish call itself succeeded).
- STORY-012: status proposal cross-field coherence is ENFORCED at construction: a
  `model_validator(mode="after")` (`proposal.py::StatusProposal._require_resolved_at_coherence`)
  enforces that `resolved_at` is set if and only if the state is terminal (i.e. not `open`).
  Raises `ValueError` (wrapped as `ValidationError`) if violated.
- A transition rule helper `is_valid_transition(from_state, to_state) -> bool` (`proposal.py::is_valid_transition`)
  and `StatusProposal.terminal` property (`proposal.py::StatusProposal.terminal`) define allowed transitions:
  from `open` to any terminal state only; terminal states are final and cannot transition.
- STORY-014: two proposal-lifecycle domain errors live in the domain (both `ValueError` subclasses):
  `ProposalNotFoundError` (`proposal.py::ProposalNotFoundError`) and `ProposalNotOpenError`
  (`proposal.py::ProposalNotOpenError`, raised when a proposal is missing or no longer `open` and so
  cannot be resolved — e.g. a lost-race concurrent resolve). `core/services/approval.py` re-exports
  them for callers that import from the service. See [[persistence-adapters]] for the repository
  contract that raises them.

### The ten STABLE core ports (`core/ports/`, ABCs)
Ports are interfaces the core OWNS but does not implement (dossier §6); adapters implement
them, the composition root injects them. All ten are `abc.ABC` with `@abstractmethod`,
signatures in canonical vocabulary only (no vendor/HTTP/SQL types). (A TEMPORARY eleventh,
`SampleModeRepository`, existed alongside these from STORY-048 through STORY-155b, which
removed it along with the feature it supported; see [[sample-mode]] (archived).)
- `SignalIngestPort.ingest_observations(batch: Sequence[SignalObservation]) -> IngestResult`
  — inbound front door (`signal_ingest.py::SignalIngestPort.ingest_observations`).
- `StatusPublisherPort.publish(change: StatusChange) -> None` — outbound
  (`status_publisher.py::StatusPublisherPort.publish`).
- `ObservationRepository.save_new(batch: Sequence[SignalObservation]) -> int` — outbound
  persistence; idempotent insert, never a duplicate on replay (the DynamoDB adapter implements
  this via an `EVT#<event_id>`/`DEDUPE` marker item, `dynamo_observation_repository.py:58-62`)
  (`observation_repository.py::ObservationRepository.save_new`).
  STORY-011 adds `ObservationRepository.in_window(signal_key: str, since: datetime, until:
  datetime) -> Sequence[SignalObservation]` (`observation_repository.py::ObservationRepository.in_window`) — the READ
  side: returns `signal_key`'s observations with `observed_at` in the half-open range
  `[since, until)`, so adjacent windows never double-count the boundary instant. This is the
  only read path the availability engine uses; the adapter's persistence mechanism stays
  entirely behind the port (see [[persistence-adapters]]).
- `WatermarkRepository.get(signal_key: str) -> datetime | None` + `advance(signal_key: str,
  to: datetime) -> None` — core-owned per-signal ingestion cursor (`watermark.py::WatermarkRepository.get` / `watermark.py::WatermarkRepository.advance`).
- `ClockPort.now() -> datetime` — injected, returns tz-aware UTC, so time is controllable
  in tests (`clock.py::ClockPort.now`).
- `RejectedObservationRepository.save(*, signal_key: str | None, reason: str, payload: dict,
  rejected_at: datetime) -> None` — the quarantine sink for observations the ingest
  validation gate refuses (STORY-009, dossier §8). `signal_key` is `str | None` deliberately:
  an unknown/absent signal_key is often exactly *why* a row was rejected
  (`rejected_observation_repository.py::RejectedObservationRepository.save`).
- `ComponentRepository` — persistence interface for listing, looking up, and writing back components (`component_repository.py::ComponentRepository`).
  Provides `list_components() -> list[Component]` (STORY-014b), `get(component_id) -> Component | None` (STORY-016a: returns `None` on not-found), and `set_status(component_id, status) -> None` (STORY-045: writes the published status back; raises `ComponentNotFoundError` on an unknown id — see [[persistence-adapters]] for the adapter implementation and the shared fake/Postgres parity contract test).
- `MaintenanceRepository` — persistence interface for managing maintenance windows (`maintenance_repository.py::MaintenanceRepository`).
  Provides `list_windows() -> list[MaintenanceWindow]` (ordered by starts_at), `create(window) -> MaintenanceWindow`, `is_under_maintenance(component_id, at) -> bool` (inclusive start / exclusive end bounds) (STORY-036), and `delete(window_id: int) -> None` (STORY-065, sprint-45) which deletes a scheduled window or raises `MaintenanceWindowNotFoundError`.
- `PublicationRepository` — persistence interface for recording and listing publish attempts (`publication_repository.py::PublicationRepository`, STORY-037; STORY-072 record-always).
  Provides `record(publication) -> Publication` (INSERTs a new row, returns it with the db-assigned id; called on EVERY publish ATTEMPT — `publication.outcome` distinguishes success from a raising delegate) and `list_recent(limit: int = 50) -> list[Publication]` (most-recent-first by `published_at DESC`; `[]` when none exist).
- `SignalRepository` — read-only persistence for the seeded-topology signal read model
  (`signal_repository.py::SignalRepository`, STORY-044). Provides `list_signals() -> list[Signal]`
  (ordered by `signal_key`, `[]` when none exist, never raises) and `get(signal_key) ->
  Signal | None` (`None` on unknown — mirrors `ComponentRepository.get`, 2026-06-26 parity
  agreement). Read-only: the seed (`composition/seed.py::seed_topology`) is the only writer of
  `signals`. See [[persistence-adapters]] for the adapter/fake implementations and the shared
  parity contract test.
- `ProposalRepository` — outbound and read persistence for status proposals (`proposal_repository.py::ProposalRepository`).
  Provides `create_open(proposal) -> StatusProposal | None` (persists open proposal, returns None on
  one-open-per-component conflict), `get_open(component_id) -> StatusProposal | None`,
  `get(proposal_id) -> StatusProposal | None` (STORY-014: lookup by id, returns None if absent),
  `resolve(proposal_id, *, to_state, reason, resolved_at) -> None` (moves open proposal to a terminal
  state; raises `ProposalNotOpenError` if it is missing or no longer open),
  `record_approval_event(proposal_id, *, actor, action: ProposalState, notes, occurred_at) -> None`
  — `action` is domain-typed `ProposalState` (STORY-200, sprint-67; was a bare `str` before, ZR-6),
  matching `resolve`'s `to_state: ProposalState` above it. Only `APPROVED`/`REJECTED` are ever legal;
  the caller (`backend/src/core/services/approval.py::ApprovalService._decide`) enforces that
  2-member subset, raising `InvalidApprovalActionError`
  (`core/domain/proposal.py::InvalidApprovalActionError`) for
  any other value — `is_valid_transition` does not cover this, since it admits any non-OPEN target.
  `FakeProposalRepository.record_approval_event` (`backend/tests/fakes.py`) types `action` to match
  but only appends a dict — it does NOT denormalize `approved_actor`, so the adapter's identity-
  comparison branch (`action is ProposalState.APPROVED`) is unobservable through the fake; see
  [[persistence-adapters]] for the adapter side and its real-DynamoDB proving test. Also provides
  `list_open() -> list[StatusProposal]` (STORY-014b: returns all open proposals, or `[]` if none exist).

### Zone 4 core logic — moved
- The pipeline (`collapse`/`streak`, STORY-010) and the availability engine
  (`AvailabilityCalculator`/`rollup_group`, STORY-011) — both in `core/services/` and both
  CONSUMERS of the `Verdict` type + the `ObservationRepository` port catalogued here — are
  documented in [[core-pipeline-and-availability]] (extracted sprint-7 so their `core/services/`
  Facts are covered by that article's `code_refs`). The ingest service (`IngestService`, STORY-009)
  is in [[ingest-service-and-pull-loop]].

### Boundary status
- `core/ports` imports `core/domain` but NOT `core/services`; the `core-internal-layering`
  contract (`services → ports → domain`) now actually bites and is KEPT. `core-independence`
  KEPT (no adapter / sqlalchemy / httpx in core). See [[architecture-boundary]].
- Fakes for every port live under `backend/tests/fakes.py` (FakeClock, FakeWatermarkRepository,
  FakeObservationRepository, RecordingStatusPublisher, FakeSignalIngestPort, FakePublicationRepository,
  FakeSignalRepository) — never in `src/adapters`, keeping the production edge clean. STORY-009's `IngestService` test
  (`backend/tests/test_ingest_service.py`) additionally defines its own local fakes
  (`DedupingObservationRepository`, `FakeWatermarkRepository`,
  `FakeRejectedObservationRepository`, `FakeClock`) rather than extending `tests/fakes.py`,
  because it needs a `save_new` that actually honors `source_event_id` dedupe (AC3) — the
  shared `tests/fakes.py` fake from STORY-005 only had to prove the interface shape.
- `core/services/` concrete implementations are documented in their own articles (so their
  `code_refs` cover them): `IngestService` (STORY-009) in [[ingest-service-and-pull-loop]];
  `collapse`/`streak` (STORY-010) + the availability engine (STORY-011) in
  [[core-pipeline-and-availability]].

## Inference (synthesis, not verified)
- The deliberately small repository surface (`save_new`, `get`, `advance` only) reflects a
  refinement decision to defer richer query methods to the zones that consume them
  (Zone 2 repos / Zone 4 pipeline), avoiding speculative interface design.
- ABCs (not Protocols) were chosen to match the §6 "strongest OO seam" framing — concrete
  adapter classes injected by composition.

## History
- sprint-1: created (STORY-004 canonical types, STORY-005 core ports).
- sprint-5: STORY-009 adds the sixth port (`RejectedObservationRepository`) and the first
  `core/services/` implementation (`IngestService`), the concrete `SignalIngestPort`.
- sprint-6: STORY-010 adds the `Verdict` domain type (`core/domain/verdict.py`) and the
  first two core-logic-pipeline stages (`core/services/pipeline.py`: `collapse`,
  `Streak`, `streak`) — dossier §10 stages 1-2 only; stages 3-4 (anti-flap + decide) are
  STORY-024.
- sprint-6: fix loop 1 (quality review MAJOR) — `collapse` now raises a plain
  `ValueError` ("collapse requires at least one observation for a cycle") on an
  empty `observations` sequence instead of leaking a stdlib `max()`/`IndexError`;
  re-verified, Fact text above was already accurate (made no empty-input claim).
- sprint-7: STORY-011 adds `ObservationRepository.in_window` (the read side; Postgres
  implementation in [[persistence-adapters]]) and `core/queries/availability.py`'s
  `AvailabilityResult`/`AvailabilityCalculator`/`rollup_group` — the two-grain
  availability/completeness calculator and min-of-children group rollup (dossier §11).
  The skew flag is split to STORY-026 (out of scope here).
- sprint-7: fix loop 1 (quality review CRITICAL) — `expected_cycles` now takes the CEILING
  of `(until - since) / interval` instead of the floor, so a non-divisible window's partial
  trailing cycle no longer makes `gap_verdicts` go negative / `total_verdicts` overcount.
- sprint-7 (compile pass): EXTRACTED the Zone 4 service-logic Facts (the pipeline
  `collapse`/`streak` and the availability engine) to the new [[core-pipeline-and-availability]]
  article, and re-scoped this article's `code_refs` to `core/domain/` + `core/ports/` only. This
  article had grown into a catch-all whose `code_refs` did not even list `pipeline.py`, so its
  collapse/streak Facts were not staleness-covered — the extraction restores coverage. This
  article is now back to its title scope: the canonical vocabulary + the core ports.
- sprint-7: STORY-025 (Sprint 6 review follow-up) adds a `model_validator(mode="after")`
  to `Verdict` enforcing the maintenance<->health invariant at construction (previously
  documented only); see Fact above.
- sprint-9: STORY-012 adds `ProposalState` and `StatusProposal` canonical domain types,
  the `ProposalRepository` port, and enforces proposal resolved_at coherence at construction.
- sprint-10: added STATUS_SEVERITY helpers to status.py (STORY-024). Verified at 75674b7.
- sprint-12: STORY-014 adds the `ProposalRepository.get(proposal_id)` lookup and the
  `ProposalNotFoundError`/`ProposalNotOpenError` domain errors to `proposal.py`. Re-verified at eb147ef.
- sprint-19: STORY-037 adds `Publication` domain type (`core/domain/publication.py`, frozen, UTC-validated `published_at` via `field_validator`) and `PublicationRepository` port (`core/ports/publication_repository.py`, `record` + `list_recent`). `FakePublicationRepository` added to `backend/tests/fakes.py`. Both exported from their respective `__init__.py` modules. verified_sha → cc7f0ce.
- sprint-29 (STORY-045): adds `ComponentNotFoundError` (`core/domain/component.py`) and the `ComponentRepository.set_status` abstract method — the status write-back the approve and recovery publish paths now use (see [[statuspage-publish]]'s `StatusWritebackPublisher` and [[persistence-adapters]]'s adapter/fake implementations). verified_sha → 7cabee7.
- sprint-30 (STORY-044): adds the tenth port, `SignalRepository` (`core/ports/signal_repository.py`),
  and its domain type `Signal` + two domain errors `SignalNotFoundError`/`SignalIntervalUnconfiguredError`
  (`core/domain/topology.py`) — the seeded-topology signal read model the new `/topology` and
  `/availability/component/{id}` endpoints consume (see [[api-five-file-convention]]) and the D5
  per-signal default-interval fix (audit finding H2) reads. `FakeSignalRepository` added to
  `backend/tests/fakes.py`; `PostgresSignalRepository` added (see [[persistence-adapters]]). Both
  exported from their respective `__init__.py` modules. verified_sha → 280c1e3.
- sprint-40 (STORY-072, record-always publication outcome): `Publication` gains `outcome:
  PublicationOutcome = SUCCEEDED` and the new closed `PublicationOutcome` enum (`succeeded`/`failed`)
  — DISTINCT from `status` (Facts updated above); `PublicationRepository.record` is now called on
  EVERY publish attempt, not only successes. Both exported from `core/domain/__init__.py`. See
  [[statuspage-publish]] for the `RecordingPublisher` behavior change and the new migration, and
  [[persistence-adapters]] for the adapter/fake implementations. verified_sha → a1bacab.
- sprint-43 (STORY-078): Relocated availability read-model to a new core/queries/ package. verified_sha → 05f640e.
- sprint-43 (quality-review fix loop, M2): `core/ports/observation_repository.py`'s `in_window`
  docstring repointed its `core/services/availability.py` reference to
  `core/queries/availability.py` (STORY-078 follow-up). No port signature or Fact changed.
  verified_sha -> 10a2d73.
- sprint-44 (STORY-064, pilot): `SignalObservation` gains an optional frozen
  `response_status_code: int | None = None` field (Facts updated above), mirroring the existing
  `latency_ms` optional-field style; no cross-field invariant, no new validator. Caught by manual
  re-verification, not the mechanical sweep: this article's (and [[dynatrace-adapter]]'s)
  frontmatter carried a trailing inline comment on the `status:` line
  (`status: verified` followed by `# verified | stale | archived`) that `yt_wiki.py`'s frontmatter
  parser reads as PART of the value, so `status != "verified"` and the sweep silently SKIPPED both
  articles instead of reporting them stale; normalized both articles' `status:` lines to the plain
  form other articles already use so future sweeps actually cover them (flagged as a candidate
  backlog item: `yt_wiki.py`'s frontmatter parser should strip trailing `#` comments). See
  [[persistence-adapters]]/[[migrations-and-db]] for the paired persistence/migration Facts and
  [[api-five-file-convention]] for the DTO/service side. verified_sha -> 0da9568.
- sprint-44 (STORY-079, Facts-coverage cleanup): the new `yt_wiki.py facts` lint flagged this
  article's Facts citing `backend/tests/fakes.py` (the per-port fakes catalog) and
  `backend/tests/test_ingest_service.py` (cited as the exception that defines its OWN local
  fakes rather than extending `tests/fakes.py`) — neither was in `code_refs`, so the mechanical
  sweep could never have caught either drifting. Both are genuinely defining test files for the
  ports/fakes contract this article documents (2026-06-25 scoping rule: test files pinning a
  documented contract qualify); added to `code_refs`. No Fact text changed. verified_sha -> 678ff0d.
- sprint-45 (STORY-065/STORY-066): verified after implementing Maintenance title + DELETE endpoint and Publication author metadata. MaintenanceWindow gained optional `title`, Publication gained optional `author` derived on read, and MaintenanceRepository gained `delete(window_id: int)`. verified_sha -> f6f589fd4dcb6e3a2a565453c43b0fb95d7e5787.
- 2026-07-13 (sprint-45 gate closure): re-stale was the trailing ruff/lint commit 48fba51 (behavior-neutral — trailing-blank trims; MaintenancePage dropped the now-unused formatReason helper + added a type import). Facts unchanged. Re-verified; verified_sha -> 2db6c70.
- sprint-62 (STORY-149): RE-VERIFIED, no content change. Went stale on `pipeline.py`, this article's
  only overlap with the anti-flap fix. The single claim it makes about that file is that `collapse`
  "already only ever builds the two coherent shapes" of `Verdict` (line 49) — STORY-149's diff is
  confined to `anti_flap`'s `DEGRADED` branch and its docstring; `collapse` is byte-identical, so the
  claim was re-read against the code rather than bulk-stamped. verified_sha -> 40e2a2c.
- sprint-63 (STORY-181): the sweep flagged `component.py`, `publication.py`, `ports/__init__.py`,
  `ports/component_repository.py`, `ports/observation_repository.py`. Two Facts above directly
  paraphrased the phantom-class/SQL prose this story retired: `ComponentNotFoundError`'s note now
  names `DynamoComponentRepository` (was `PostgresComponentRepository`, a class that does not
  exist), and `ObservationRepository.save_new`'s note now describes the idempotent-insert
  guarantee via the real `EVT#.../DEDUPE` marker item instead of "ON CONFLICT DO NOTHING" SQL that
  never ran here. No port signature, contract, or test changed. verified_sha -> b272c32.
- sprint-67 (STORY-200): `ProposalRepository.record_approval_event`'s Fact above now describes
  `action: ProposalState` (was `str`) — the port SIGNATURE itself changed, not just a comment. Added
  the `InvalidApprovalActionError` guard and the fake's non-denormalizing-so-unobservable-branch note
  (both new claims). `ProposalState`/`StatusProposal` themselves are unchanged; ZR-6's fix is scoped
  to this one port method. verified_sha -> d469d2c.
- sprint-67 (STORY-200 fix round, quality review): **MAJOR — the new `_decide` citation used the
  abbreviated `core/services/approval.py` form, and `backend/src/core/services/approval.py` was not
  in this article's `code_refs`**, so the fact-checker's citation resolver silently skipped it (it
  only resolves paths from the repo root) and no future edit to that frequently-touched file would
  ever flag this article stale. Corrected the citation to the full `backend/src/...` path and added
  the file to `code_refs`. Also bumped `verified_sprint` from the stale `sprint-63` left over from an
  earlier partial re-stamp to `sprint-67`, matching `verified_sha`. **Known pre-existing instance of
  the same abbreviated-path pattern, left unfixed as out of this round's scope and flagged as a
  candidate:** line 99's `core/services/approval.py` re-exports... citation has the identical
  problem and predates STORY-200. verified_sha -> 013f344.
- sprint-73 (STORY-147): `Component`'s Fact above gains two new fields, `group:str|None=None` and
  `description:str|None=None` — additive/optional operator-cockpit display metadata, sourced from
  `ComponentConfig` (see [[config-layer]]) via topology seeding and read back with `.get()` (never
  bracket access) so a pre-STORY-147 component item, carrying neither key, still reads back as
  `None`. No other Fact in this article changed — `ComponentNotFoundError`, the port signatures, and
  every other domain type are untouched by this story.
- sprint-73 (STORY-155b): removed the `SampleModeRepository` port Fact, `sample_mode_repository.py`
  from `code_refs`, and the `FakeSampleModeRepository` mention in the fakes list — the port, its
  DynamoDB adapter, and its fake no longer exist. "The ten STABLE core ports + one TEMPORARY
  eleventh" heading corrected to "the ten STABLE core ports" (a parenthetical points at the archived
  [[sample-mode]] for what the eleventh was). Every other Fact — the ten stable ports themselves,
  the domain types, the boundary status — is untouched.
