"""Postgres-backed `PublicationRepository` (dossier §9, §12/T1.1, §17, STORY-072)."""

from __future__ import annotations

from datetime import timezone

import sqlalchemy as sa
from sqlalchemy.engine import Engine

from src.core.domain.publication import Publication, PublicationOutcome
from src.core.domain.status import ComponentStatus
from src.core.ports.publication_repository import PublicationRepository

_PUBLICATIONS = sa.table(
    "publications",
    sa.column("id"),
    sa.column("component_id"),
    sa.column("proposal_id"),
    sa.column("status"),
    sa.column("published_at"),
    sa.column("outcome"),
)

_APPROVAL_EVENTS = sa.table(
    "approval_events",
    sa.column("proposal_id"),
    sa.column("action"),
    sa.column("actor"),
)


class PostgresPublicationRepository(PublicationRepository):
    """Concrete Postgres adapter for recording and listing publications (dossier §9, §12/T1.1, §17, STORY-072).

    Records every publish ATTEMPT (STORY-072) — `outcome` distinguishes a
    successful publish from a raising delegate; the `ck_publications_outcome`
    CHECK constraint (STORY-072 migration) enforces the closed
    `succeeded`/`failed` vocabulary at the DB level. list_recent returns
    most-recent-first (published_at DESC) to back the Publications tab (§17).
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def record(self, publication: Publication) -> Publication:
        """INSERT a new publication row and return it with the database-assigned id.

        Called on EVERY publish attempt (STORY-072) — `publication.outcome`
        carries whether the delegate publish succeeded or raised.
        """
        stmt = (
            sa.insert(_PUBLICATIONS)
            .values(
                {
                    "component_id": publication.component_id,
                    "proposal_id": publication.proposal_id,
                    "status": publication.status.value,
                    "published_at": publication.published_at,
                    "outcome": publication.outcome.value,
                }
            )
            .returning(
                _PUBLICATIONS.c.id,
                _PUBLICATIONS.c.component_id,
                _PUBLICATIONS.c.proposal_id,
                _PUBLICATIONS.c.status,
                _PUBLICATIONS.c.published_at,
                _PUBLICATIONS.c.outcome,
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
            outcome=PublicationOutcome(row.outcome),
        )

    def list_recent(self, limit: int = 50) -> list[Publication]:
        """SELECT up to `limit` publications ordered by published_at DESC.

        Returns `[]` when none exist (§17 Publications tab: empty state is valid).
        """
        subq = (
            sa.select(_APPROVAL_EVENTS.c.actor)
            .where(
                _APPROVAL_EVENTS.c.proposal_id == _PUBLICATIONS.c.proposal_id,
                _APPROVAL_EVENTS.c.action == "approved",
            )
            .limit(1)
            .scalar_subquery()
            .label("author")
        )

        stmt = (
            sa.select(
                _PUBLICATIONS.c.id,
                _PUBLICATIONS.c.component_id,
                _PUBLICATIONS.c.proposal_id,
                _PUBLICATIONS.c.status,
                _PUBLICATIONS.c.published_at,
                _PUBLICATIONS.c.outcome,
                subq,
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
                outcome=PublicationOutcome(row.outcome),
                author=row.author,
            )
            for row in rows
        ]
