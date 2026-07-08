"""The publication repository port (dossier §9, §12/T1.1, §17, STORY-072).

Records EVERY approve publish ATTEMPT and provides the read path for the
Publications tab (§17). Each row carries an `outcome` (`succeeded`/`failed`,
STORY-072) — a raising delegate still gets recorded (with `outcome='failed'`)
before `BestEffortPublisher` logs+swallows the error for the caller.
"""

from abc import ABC, abstractmethod

from src.core.domain.publication import Publication


class PublicationRepository(ABC):
    """Port for recording and listing publish attempts (dossier §9, §12/T1.1, §17, STORY-072).

    The core owns this interface; adapters implement it. Signatures speak in
    canonical vocabulary only (Publication domain type, not SQL or HTTP types).
    """

    @abstractmethod
    def record(self, publication: Publication) -> Publication:
        """Persist a new publication record and return it with the database-assigned id.

        Called on EVERY publish attempt (STORY-072) — `publication.outcome`
        distinguishes a successful publish from a raising delegate.

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
