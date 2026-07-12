"""Pydantic DTOs for the history API feature (dossier §13, §17).

`ObservationDTO` is a client-facing subset of `SignalObservation` — it omits
`source`, `raw_ref`, and `source_event_id`, which are internal provenance /
idempotency fields not relevant to the dashboard consumer.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ObservationDTO(BaseModel):
    """Data Transfer Object for one signal observation (dossier §13, §17).

    Client-facing subset of SignalObservation: omits source/raw_ref/source_event_id.
    """

    model_config = ConfigDict(frozen=True)

    signal_key: str
    """Stable signal identifier."""

    observed_at: datetime
    """UTC time of the synthetic monitor execution."""

    health: str
    """Closed verdict: up / down / degraded."""

    location: str
    """Probe location for this execution."""

    latency_ms: int | None
    """Optional measured latency in milliseconds."""

    response_status_code: int | None
    """Optional HTTP response status code (STORY-064); `None` when the
    normalizer's source row omitted it or it was unparsable."""

    check_type: str
    """The monitor's check type (STORY-064), mapped verbatim from the
    persisted provenance `native_kind` (e.g. `"http"`). Always present —
    provenance is mandatory on every observation."""
