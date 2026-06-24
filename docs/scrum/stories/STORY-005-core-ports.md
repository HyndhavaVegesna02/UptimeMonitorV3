---
id: STORY-005
title: The core ports
type: feature
---

## Context
Spec: dossier §6 (Ports & interfaces) + §8 (ingest contract). Zone 1. Ports are
interfaces the core OWNS but does not implement — the inversion that lets the core
depend on nothing. Depends on STORY-004 (port signatures import the canonical domain
types).

## Description
Define in `src/core/ports/`, in canonical vocabulary only, the interfaces the core owns:
`SignalIngestPort` (inbound — batches, idempotent + validating by contract),
`StatusPublisherPort` (outbound — sends a canonical `StatusChange` with a canonical
`component_id`), `ObservationRepository` + `WatermarkRepository` (outbound persistence),
and `ClockPort` (injected `now()`). A reader who has never heard of Dynatrace must
understand every signature.

**Implementation decisions (refinement):**
- **Style:** ABCs (`abc.ABC` + `@abstractmethod`), per the §6 OOP note ("ports *are*
  abstract interfaces, adapters *are* their concrete classes").
- **Port set (this story):** `SignalIngestPort`, `StatusPublisherPort`,
  `ObservationRepository`, `WatermarkRepository`, `ClockPort`. Richer read/query methods
  on the repositories are deliberately DEFERRED to the zones that consume them
  (Zone 2 repos / Zone 4 pipeline) — defining them now would be speculative.
- **Supporting canonical types** introduced minimally into `core/domain` to satisfy
  signatures (ports may import domain): `IngestResult` (accepted/rejected counts),
  `StatusChange` (`{component_id:str, status:ComponentStatus}`), and `ComponentStatus`
  (closed enum: `operational`/`degraded`/`partial_outage`/`major_outage`). The
  ComponentStatus→Statuspage-string mapping stays in the Zone 5 adapter; Zone 5 owns
  *producing* a StatusChange — this story only defines the type the port needs.

## Acceptance Criteria
- [ ] AC1: All five ports defined in `src/core/ports/` as ABCs, signatures in canonical
      vocabulary only (no vendor/HTTP/SQL types in any signature):
      `SignalIngestPort.ingest_observations(batch: Sequence[SignalObservation]) -> IngestResult`;
      `StatusPublisherPort.publish(change: StatusChange) -> None`;
      `ObservationRepository.save_new(batch) -> int`;
      `WatermarkRepository.get(signal_key) -> datetime | None` and
      `advance(signal_key, to: datetime) -> None`;
      `ClockPort.now() -> datetime`.
- [ ] AC2: A fake/in-memory implementation of each port exists UNDER `tests/` (not in
      `src/adapters` — keeps the production edge clean), satisfies the interface, and is
      exercised in at least one test.
- [ ] AC3: `ClockPort.now()` returns tz-aware UTC; the fake clock returns an injected
      fixed time (time is controllable in tests).
- [ ] AC4: `WatermarkRepository.get` returns `None` when unset; the fake demonstrates an
      `advance` then `get` round-trip.
- [ ] AC5: `lint-imports` exits 0 — `core` imports no adapter and no `sqlalchemy`/`httpx`;
      `core/ports` imports `core/domain` but NOT `core/services` (layering contract green).
- [ ] Every AC carries at least one test (DoD standing rule).

## Open Questions
- None — resolved at refinement (2026-06-24): style = ABCs; port set fixed (richer repo
  queries deferred to consuming zones); `StatusChange`/`ComponentStatus`/`IngestResult`
  shapes defined; fakes live under `tests/`; estimate = 3.

## Review notes (Sprint 1 — non-blocking minors from quality review)
- `test_core_ports.py` uses bare `from fakes import ...` (sibling-helper idiom via pytest
  rootdir sys.path) rather than `src.`-qualified imports, repeated per-test. Cosmetic;
  works correctly.
- `RecordingStatusPublisher` lacks the `Fake*` prefix the other doubles use — intentional
  ("recording" is the precise name; the dossier itself calls it a recording fake). Left.
- `raise NotImplementedError` after each `@abstractmethod` is redundant (the decorator
  already blocks instantiation) but is a deliberate defensive idiom, not dead code.

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §6/§8. Status: draft.
- 2026-06-24: refined for Sprint 1 — AC finalized, port set + StatusChange shape + ABC
  style decided, open questions resolved. Status: ready.
- 2026-06-24: implemented (commits ad6e085..ce4c7c7), spec review PASS (5/5 AC MET),
  quality review APPROVE (0 critical/major). Full DoD gate green. Status: done (board).
