"""The signal ingest port (dossier §6, §8) — the core's front door.

Adapters push BATCHES of canonical observations here; the port is idempotent and
validating BY CONTRACT (dossier §8). Because validation, deduplication, and the
watermark advance all live on the core side of this boundary, any adapter that
ever feeds the core inherits those guarantees and cannot bypass them — the
adapter's only job is to translate into canonical observations. `ingest_observations`
returns an `IngestResult` summarizing accepted vs rejected counts.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from src.core.domain import IngestResult, SignalObservation


class SignalIngestPort(ABC):
    """Accepts batches of canonical observations into the core (dossier §6, §8)."""

    @abstractmethod
    def ingest_observations(
        self, batch: Sequence[SignalObservation]
    ) -> IngestResult:
        """Validate, deduplicate, and persist `batch`; advance the watermark.

        Returns an `IngestResult` with the accepted and rejected counts. Rejected
        observations are quarantined, never silently dropped (dossier §8).
        """
        raise NotImplementedError
