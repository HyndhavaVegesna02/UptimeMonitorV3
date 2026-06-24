---
title: Zone 1 — the canonical vocabulary and the core ports
code_refs: [backend/src/core/domain/signal.py, backend/src/core/domain/status.py, backend/src/core/ports/]
verified_sha: d7d3b18
verified_sprint: sprint-1
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

### The five core ports (`core/ports/`, ABCs)
Ports are interfaces the core OWNS but does not implement (dossier §6); adapters implement
them, the composition root injects them. All five are `abc.ABC` with `@abstractmethod`,
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

### Boundary status
- `core/ports` imports `core/domain` but NOT `core/services`; the `core-internal-layering`
  contract (`services → ports → domain`) now actually bites and is KEPT. `core-independence`
  KEPT (no adapter / sqlalchemy / httpx in core). See [[architecture-boundary]].
- Fakes for every port live under `backend/tests/fakes.py` (FakeClock, FakeWatermarkRepository,
  FakeObservationRepository, RecordingStatusPublisher, FakeSignalIngestPort) — never in
  `src/adapters`, keeping the production edge clean.

## Inference (synthesis, not verified)
- The deliberately small repository surface (`save_new`, `get`, `advance` only) reflects a
  refinement decision to defer richer query methods to the zones that consume them
  (Zone 2 repos / Zone 4 pipeline), avoiding speculative interface design.
- ABCs (not Protocols) were chosen to match the §6 "strongest OO seam" framing — concrete
  adapter classes injected by composition.

## History
- sprint-1: created (STORY-004 canonical types, STORY-005 core ports).
