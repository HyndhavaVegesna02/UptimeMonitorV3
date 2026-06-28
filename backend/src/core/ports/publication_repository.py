"""The publication repository port (dossier §9, §12/T1.1, §17).

Records SUCCESSFUL Statuspage publishes and provides the read path for the
Publications tab (§17). The table has no error column — failed publishes are
logged and swallowed by BestEffortPublisher; only successes are recorded.
"""

from abc import ABC, abstractmethod

from src.core.domain.publication import Publication


class PublicationRepository(ABC):
    """Port for recording and listing successful Statuspage publishes (dossier §9, §12/T1.1, §17).

    The core owns this interface; adapters implement it. Signatures speak in
    canonical vocabulary only (Publication domain type, not SQL or HTTP types).
    """

    @abstractmethod
    def record(self, publication: Publication) -> Publication:
        """Persist a new publication record and return it with the database-assigned id.

        Called ONLY after a successful Statuspage publish (the table has no error
        column — do not call this on a failed publish).

        Args:
            publication: The Publication to persist (id should be None).

        Returns:
            Publication: The persisted record with its database-assigned id set.
        """
        raise NotImplementedError

    @abstractmethod
    def list_recent(self, limit: int = 50) -> list[Publication]:
        """Return up to `limit` most-recent publications ordered by published_at DESC.

        Args:
            limit: Maximum number of records to return (default 50).

        Returns:
            list[Publication]: Publications most-recent-first. Returns `[]` when none exist.
        """
        raise NotImplementedError
