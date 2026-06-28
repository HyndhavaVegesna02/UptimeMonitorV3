"""Postgres-backed `PublicationRepository` (dossier §9, §12/T1.1, §17)."""

from __future__ import annotations

from datetime import timezone

import sqlalchemy as sa
from sqlalchemy.engine import Engine

from src.core.domain.publication import Publication
from src.core.domain.status import ComponentStatus
from src.core.ports.publication_repository import PublicationRepository

_PUBLICATIONS = sa.table(
    "publications",
    sa.column("id"),
    sa.column("component_id"),
    sa.column("proposal_id"),
    sa.column("status"),
    sa.column("published_at"),
)


class PostgresPublicationRepository(PublicationRepository):
    """Concrete Postgres adapter for recording and listing publications (dossier §9, §12/T1.1, §17).

    Records SUCCESSFUL Statuspage publishes only — the table has no error column.
    list_recent returns most-recent-first (published_at DESC) to back the Publications
    tab (§17).
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def record(self, publication: Publication) -> Publication:
        """INSERT a new publication row and return it with the database-assigned id.

        Called only after a successful Statuspage publish (§12/T1.1 — record
        SUCCESSES only; a raising delegate records nothing).
        """
        stmt = (
            sa.insert(_PUBLICATIONS)
            .values(
                {
                    "component_id": publication.component_id,
                    "proposal_id": publication.proposal_id,
                    "status": publication.status.value,
                    "published_at": publication.published_at,
                }
            )
            .returning(
                _PUBLICATIONS.c.id,
                _PUBLICATIONS.c.component_id,
                _PUBLICATIONS.c.proposal_id,
                _PUBLICATIONS.c.status,
                _PUBLICATIONS.c.published_at,
            )
        )

        with self._engine.begin() as conn:
            row = conn.execute(stmt).fetchone()

        assert row is not None
        return Publication(
            id=row.id,
            component_id=row.component_id,
            proposal_id=row.proposal_id,
            status=ComponentStatus(row.status),
            published_at=row.published_at.astimezone(timezone.utc),
        )

    def list_recent(self, limit: int = 50) -> list[Publication]:
        """SELECT up to `limit` publications ordered by published_at DESC.

        Returns `[]` when none exist (§17 Publications tab: empty state is valid).
        """
        stmt = (
            sa.select(
                _PUBLICATIONS.c.id,
                _PUBLICATIONS.c.component_id,
                _PUBLICATIONS.c.proposal_id,
                _PUBLICATIONS.c.status,
                _PUBLICATIONS.c.published_at,
            )
            .order_by(_PUBLICATIONS.c.published_at.desc())
            .limit(limit)
        )

        with self._engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()

        return [
            Publication(
                id=row.id,
                component_id=row.component_id,
                proposal_id=row.proposal_id,
                status=ComponentStatus(row.status),
                published_at=row.published_at.astimezone(timezone.utc),
            )
            for row in rows
        ]
