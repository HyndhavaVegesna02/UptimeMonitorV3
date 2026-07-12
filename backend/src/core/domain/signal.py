"""The canonical signal vocabulary (dossier §5).

`SignalObservation` is the spine of the system: the flattened, vendor-neutral
form of one synthetic monitor execution from one location. Vendor identifiers
live ONLY inside `Provenance`; every other field reads to someone who has never
heard of Dynatrace (vocabulary rule P3, dossier §6).
"""

from datetime import datetime, timedelta
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator


class Health(str, Enum):
    """Closed health verdict for one observation.

    Not pass/fail — `degraded` lets a partial outage be expressed (dossier §5).
    """

    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"


class Provenance(BaseModel):
    """Where an observation came from — the ONLY home for vendor identifiers.

    The core never reads these for logic; they exist for audit and traceability.
    `native_id` and `native_kind` are the vendor's own id and monitor type
    (e.g. http / clickpath / browser / nam), quarantined here so the rest of the
    canonical shape stays vendor-neutral (dossier §5, §6).
    """

    model_config = ConfigDict(frozen=True)

    system: str
    native_id: str
    native_kind: str


class SignalObservation(BaseModel):
    """One synthetic monitor execution from one location, vendor-neutral (dossier §5).

    The canonical spine of the system. Frozen and validated at construction so a
    bad upstream payload surfaces immediately rather than corrupting core logic.
    Every field below makes sense to a reader who has never heard of Dynatrace;
    the vendor's own identifiers live solely inside `source` (Provenance).
    """

    model_config = ConfigDict(frozen=True)

    signal_key: str
    """Stable name we choose — never a vendor id. The shock absorber for churn."""

    observed_at: datetime
    """UTC run time of the execution (tz-aware; naive is rejected, see validator)."""

    health: Health
    """Closed verdict: up / down / degraded."""

    source_event_id: str
    """Idempotency key for exactly-once ingestion."""

    source: Provenance
    """Provenance only — the sole home of vendor identifiers."""

    location: str
    """The probe location for this execution (enables COUNT(DISTINCT location))."""

    latency_ms: int | None = None
    """Optional measured latency in milliseconds."""

    response_status_code: int | None = None
    """Optional HTTP response status code (e.g. 200); `None` when the vendor
    row omits it or it is unparsable (STORY-064)."""

    raw_ref: str | None = None
    """Optional pointer to the archived raw payload; the core never reads it."""

    @field_validator("observed_at")
    @classmethod
    def _require_utc(cls, value: datetime) -> datetime:
        """Reject naive or non-UTC timestamps rather than silently coercing them.

        A naive datetime carries no instant; a non-UTC offset means the upstream
        adapter failed to normalize. Surfacing it here keeps bad data out of the
        core (dossier §5; AC3).
        """
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("observed_at must be a tz-aware UTC datetime")
        return value
