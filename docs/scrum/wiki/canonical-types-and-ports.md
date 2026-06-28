---
title: Zone 1 — the canonical vocabulary and the core ports
code_refs: [backend/src/core/domain/signal.py, backend/src/core/domain/status.py, backend/src/core/domain/verdict.py, backend/src/core/domain/proposal.py, backend/src/core/domain/component.py, backend/src/core/domain/maintenance.py, backend/src/core/ports/__init__.py, backend/src/core/ports/clock.py, backend/src/core/ports/observation_repository.py, backend/src/core/ports/proposal_repository.py, backend/src/core/ports/rejected_observation_repository.py, backend/src/core/ports/signal_ingest.py, backend/src/core/ports/status_publisher.py, backend/src/core/ports/watermark.py, backend/src/core/ports/component_repository.py, backend/src/core/ports/maintenance_repository.py, backend/src/core/services/pipeline.py]
verified_sha: 19eefc8
verified_sprint: sprint-18
status: verified          # verified | stale | archived
---

## Facts (verified against code)

### Canonical domain types (`core/domain/`, frozen Pydantic v2)
- `SignalObservation` is the vendor-neutral spine — one synthetic monitor execution
  from one location (`signal.py::SignalObservation`). Frozen via `model_config = ConfigDict(frozen=True)`
  (`signal.py::SignalObservation`). Fields: `signal_key:str`, `observed_at:datetime`,
  `health:Health`, `source_event_id:str`, `source:Provenance`,
  `location:str`, `latency_ms:int|None=None`, `raw_ref:str|None=None` (`signal.py::SignalObservation`).
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
  Fields: `id:str`, `name:str`, `status:ComponentStatus`, `app_id:str` (STORY-014b).
- `MaintenanceWindow` (frozen) models a scheduled maintenance window for a component (`maintenance.py::MaintenanceWindow`).
  Fields: `component_id:str`, `starts_at:datetime`, `ends_at:datetime`, `reason:str|None=None`, `id:int|None=None`. Timezones for starts_at and ends_at are validated to be UTC (`maintenance.py::MaintenanceWindow`). Enforces `ends_at > starts_at` invariant via a `model_validator(mode="after")` (`maintenance.py::MaintenanceWindow._require_ends_after_starts`) (STORY-036).
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

### The nine core ports (`core/ports/`, ABCs)
Ports are interfaces the core OWNS but does not implement (dossier §6); adapters implement
them, the composition root injects them. All nine are `abc.ABC` with `@abstractmethod`,
signatures in canonical vocabulary only (no vendor/HTTP/SQL types):
- `SignalIngestPort.ingest_observations(batch: Sequence[SignalObservation]) -> IngestResult`
  — inbound front door (`signal_ingest.py::SignalIngestPort.ingest_observations`).
- `StatusPublisherPort.publish(change: StatusChange) -> None` — outbound
  (`status_publisher.py::StatusPublisherPort.publish`).
- `ObservationRepository.save_new(batch: Sequence[SignalObservation]) -> int` — outbound
  persistence; returns insert count (ON CONFLICT DO NOTHING semantics) (`observation_repository.py::ObservationRepository.save_new`).
  STORY-011 adds `ObservationRepository.in_window(signal_key: str, since: datetime, until:
  datetime) -> Sequence[SignalObservation]` (`observation_repository.py::ObservationRepository.in_window`) — the READ
  side: returns `signal_key`'s observations with `observed_at` in the half-open range
  `[since, until)`, so adjacent windows never double-count the boundary instant. This is the
  only read path the availability engine uses; ALL SQL for it stays behind the Postgres
  adapter (see [[persistence-adapters]]).
- `WatermarkRepository.get(signal_key: str) -> datetime | None` + `advance(signal_key: str,
  to: datetime) -> None` — core-owned per-signal ingestion cursor (`watermark.py::WatermarkRepository.get` / `watermark.py::WatermarkRepository.advance`).
- `ClockPort.now() -> datetime` — injected, returns tz-aware UTC, so time is controllable
  in tests (`clock.py::ClockPort.now`).
- `RejectedObservationRepository.save(*, signal_key: str | None, reason: str, payload: dict,
  rejected_at: datetime) -> None` — the quarantine sink for observations the ingest
  validation gate refuses (STORY-009, dossier §8). `signal_key` is `str | None` deliberately:
  an unknown/absent signal_key is often exactly *why* a row was rejected
  (`rejected_observation_repository.py::RejectedObservationRepository.save`).
- `ComponentRepository` — read persistence interface for listing and looking up components (`component_repository.py::ComponentRepository`).
  Provides `list_components() -> list[Component]` (STORY-014b) and `get(component_id) -> Component | None` (STORY-016a: returns `None` on not-found).
- `MaintenanceRepository` — persistence interface for managing maintenance windows (`maintenance_repository.py::MaintenanceRepository`).
  Provides `list_windows() -> list[MaintenanceWindow]` (ordered by starts_at), `create(window) -> MaintenanceWindow`, and `is_under_maintenance(component_id, at) -> bool` (inclusive start / exclusive end bounds) (STORY-036).
- `ProposalRepository` — outbound and read persistence for status proposals (`proposal_repository.py::ProposalRepository`).
  Provides `create_open(proposal) -> StatusProposal | None` (persists open proposal, returns None on
  one-open-per-component conflict), `get_open(component_id) -> StatusProposal | None`,
  `get(proposal_id) -> StatusProposal | None` (STORY-014: lookup by id, returns None if absent),
  `resolve(proposal_id, *, to_state, reason, resolved_at) -> None` (moves open proposal to a terminal
  state; raises `ProposalNotOpenError` if it is missing or no longer open),
  `record_approval_event(proposal_id, *, actor, action, notes, occurred_at) -> None`, and
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
  FakeObservationRepository, RecordingStatusPublisher, FakeSignalIngestPort) — never in
  `src/adapters`, keeping the production edge clean. STORY-009's `IngestService` test
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
  implementation in [[persistence-adapters]]) and `core/services/availability.py`'s
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

