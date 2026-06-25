---
title: Zone 1 — the canonical vocabulary and the core ports
code_refs: [backend/src/core/domain/signal.py, backend/src/core/domain/status.py, backend/src/core/domain/verdict.py, backend/src/core/ports/]
verified_sha: fc74e53
verified_sprint: sprint-6
status: verified          # verified | stale | archived
---

## Facts (verified against code)

### Canonical domain types (`core/domain/`, frozen Pydantic v2)
- `SignalObservation` is the vendor-neutral spine — one synthetic monitor execution
  from one location (`signal.py:42`). Frozen via `model_config = ConfigDict(frozen=True)`
  (`signal.py:51`). Fields: `signal_key:str` (`:53`), `observed_at:datetime` (`:56`),
  `health:Health` (`:59`), `source_event_id:str` (`:62`), `source:Provenance` (`:65`),
  `location:str` (`:68`), `latency_ms:int|None=None` (`:71`), `raw_ref:str|None=None` (`:74`).
- `observed_at` is validated to be tz-aware **UTC** — a naive datetime AND any non-zero
  UTC offset are both rejected (`_require_utc`, `signal.py:79`). Strict reading of §5
  "UTC run time"; keeps unnormalized wall-clock values out of the core.
- `Health(str, Enum)` is a closed enum: exactly `up` / `down` / `degraded` (`signal.py:15`).
  Not pass/fail — so a partial outage is expressible.
- `Provenance` (frozen) is the SOLE home of vendor identifiers: `{system, native_id,
  native_kind}` (`signal.py:26-39`). `native_id`/`native_kind` are the vendor's own id and
  monitor type. No vendor id appears anywhere else on `SignalObservation`.
- `ComponentStatus(str, Enum)` closed enum: `operational` / `degraded` / `partial_outage`
  / `major_outage` (`status.py:15`). The canonical component status; the
  ComponentStatus→Statuspage-string mapping is a Zone 5 adapter concern, not here.
- `StatusChange` (frozen) `{component_id:str, status:ComponentStatus}` (`status.py:29-42`).
  `component_id` is the canonical component id the core owns — never a Statuspage id
  (`status.py:32`).
- `IngestResult` (frozen) `{accepted:int, rejected:int}` (`status.py:46-59`) — the outcome
  of ingesting one batch.
- `Verdict` (frozen, `verdict.py:14`) — STORY-010's pipeline output type: one cycle's
  collapsed verdict for one signal. Fields: `signal_key:str`, `observed_at:datetime`
  (the cycle instant — `max(observed_at)` across the cycle's observations, tz-aware
  UTC via the same `_require_utc` validator pattern as `SignalObservation`),
  `health:Health|None=None`, `under_maintenance:bool=False`. Represents BOTH a normal
  health verdict (`under_maintenance=False`, `health` set) AND a maintenance marker
  (`under_maintenance=True`, `health=None`) in one type, so `streak` can skip
  maintenance verdicts without a second type.

### The six core ports (`core/ports/`, ABCs)
Ports are interfaces the core OWNS but does not implement (dossier §6); adapters implement
them, the composition root injects them. All six are `abc.ABC` with `@abstractmethod`,
signatures in canonical vocabulary only (no vendor/HTTP/SQL types):
- `SignalIngestPort.ingest_observations(batch: Sequence[SignalObservation]) -> IngestResult`
  — inbound front door (`signal_ingest.py:17-22`).
- `StatusPublisherPort.publish(change: StatusChange) -> None` — outbound
  (`status_publisher.py:14-18`).
- `ObservationRepository.save_new(batch: Sequence[SignalObservation]) -> int` — outbound
  persistence; returns insert count (ON CONFLICT DO NOTHING semantics) (`observation_repository.py:16-20`).
- `WatermarkRepository.get(signal_key: str) -> datetime | None` + `advance(signal_key: str,
  to: datetime) -> None` — core-owned per-signal ingestion cursor (`watermark.py:15-24`).
- `ClockPort.now() -> datetime` — injected, returns tz-aware UTC, so time is controllable
  in tests (`clock.py:12-21`).
- `RejectedObservationRepository.save(*, signal_key: str | None, reason: str, payload: dict,
  rejected_at: datetime) -> None` — the quarantine sink for observations the ingest
  validation gate refuses (STORY-009, dossier §8). `signal_key` is `str | None` deliberately:
  an unknown/absent signal_key is often exactly *why* a row was rejected
  (`rejected_observation_repository.py:17-33`).

### Core pipeline stages 1-2 (`core/services/pipeline.py`, STORY-010)
- `collapse(observations: Sequence[SignalObservation], *, under_maintenance: bool) ->
  Verdict` (`pipeline.py:36`) — stage 1 (dossier §10). Assumes all observations belong
  to one signal + one cycle (the caller groups; collapse does not). `under_maintenance`
  is an INJECTED boolean, never a DB/table lookup, so the function stays pure. When
  `True`, returns a `Verdict(under_maintenance=True, health=None)` immediately —
  maintenance short-circuits before health is ever computed (AC2). Otherwise delegates
  to `_collapse_health`: all `up` -> `up`; all `down` -> `down`; any mix (including
  all-`degraded`) -> `degraded` (AC1).
- `Streak` (frozen, `pipeline.py:22`) `{health:Health, length:int}` — the current
  streak's health and consecutive count.
- `streak(verdicts: Sequence[Verdict]) -> Streak | None` (`pipeline.py:88`) — stage 2
  (dossier §10). `verdicts` is ordered oldest-to-newest; filters out every
  `under_maintenance` verdict first, then reads the remaining sequence backward from
  the most recent, counting while health matches and stopping at the first change
  (AC3). Maintenance verdicts are excluded from the sequence entirely — they neither
  count nor break a surrounding run (AC2). Returns `None` if every verdict supplied is
  maintenance (no non-maintenance verdict to start from).
- Stages 3-4 (anti-flap + decide) are explicitly OUT OF SCOPE here — STORY-024.

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
- `core/services/` now has its first concrete implementation: `IngestService`
  (`core/services/ingest_service.py`), the concrete `SignalIngestPort` (STORY-009). It is
  constructed with all four ports injected (`observation_repo`, `watermark_repo`,
  `rejected_repo`, `clock`) and implements the dossier §8 ordering: validate (a
  future-timestamp gate against the injected clock, `FUTURE_TOLERANCE = timedelta(minutes=5)`)
  → dedupe+persist via `save_new`'s true newly-inserted count → advance the watermark to
  `max(observed_at)` over ACCEPTED observations only, after `save_new` returns (so a raise
  never leaves the watermark ahead of persisted data). It imports only `src.core.*` — no SQL,
  no vendor types.

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
