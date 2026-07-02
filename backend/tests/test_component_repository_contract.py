"""Contract test for `ComponentRepository.set_status` (STORY-045, dossier §9/§17).

Fake/adapter parity agreement (2026-06-26): `FakeComponentRepository` and
`PostgresComponentRepository` must behave IDENTICALLY for `set_status` — a
known id updates and the change is visible via `get`; an unknown id raises
`ComponentNotFoundError` from BOTH. One shared assertion body
(`_assert_set_status_contract`) is exercised against both implementations so
the two can never silently drift (mirrors the `ComponentRepository.get`
parity convention already documented in [[persistence-adapters]]).
"""

from __future__ import annotations

import psycopg
import pytest
from src.core.domain.component import ComponentNotFoundError
from src.core.domain.status import ComponentStatus


def _seed_component(
    database_url: str, component_id: str, app_id: str = "app-1"
) -> None:
    """Insert a minimal `apps` row + `components` row (test arrangement only)."""
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO apps (id, name, config)
                VALUES (%s, %s, '{}'::jsonb)
                ON CONFLICT (id) DO NOTHING
                """,
                (app_id, app_id),
            )
            cur.execute(
                """
                INSERT INTO components (id, app_id, name, status)
                VALUES (%s, %s, %s, 'operational')
                ON CONFLICT (id) DO NOTHING
                """,
                (component_id, app_id, component_id),
            )
        conn.commit()


def _assert_set_status_contract(repo, *, known_id: str) -> None:
    """Shared assertion body run against BOTH the fake and Postgres impls.

    Proves: (1) a known id's status update is visible via `get`; (2) an
    unknown id raises `ComponentNotFoundError` — from both implementations.
    """
    # Known id: update visible via get().
    repo.set_status(known_id, ComponentStatus.DEGRADED)
    updated = repo.get(known_id)
    assert updated is not None
    assert updated.status == ComponentStatus.DEGRADED

    # Unknown id: raises the named domain error in BOTH implementations
    # (never a bare ValueError — 2026-06-28 check-then-act agreement).
    with pytest.raises(ComponentNotFoundError):
        repo.set_status("does-not-exist-xyz", ComponentStatus.MAJOR_OUTAGE)


def test_fake_component_repository_set_status_contract():
    from src.core.domain.component import Component
    from tests.fakes import FakeComponentRepository

    comp = Component(
        id="checkout",
        name="Checkout",
        status=ComponentStatus.OPERATIONAL,
        app_id="app-1",
    )
    repo = FakeComponentRepository(components=[comp])

    _assert_set_status_contract(repo, known_id="checkout")


def test_postgres_component_repository_set_status_contract(migrated_db, engine):
    from src.adapters.persistence.component_repository import (
        PostgresComponentRepository,
    )

    _seed_component(migrated_db.database_url, "set-status-comp", "app-1")

    repo = PostgresComponentRepository(engine)

    _assert_set_status_contract(repo, known_id="set-status-comp")
