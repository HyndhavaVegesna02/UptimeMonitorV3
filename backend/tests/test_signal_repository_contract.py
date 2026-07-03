"""Contract test for `SignalRepository` (STORY-044 D2, dossier §7/§9).

Fake/adapter parity agreement (2026-06-26): `FakeSignalRepository` and
`PostgresSignalRepository` must behave IDENTICALLY — empty topology → `[]`;
`list_signals` ordered by `signal_key`; `get` on an unknown key → `None`; `get`
on a known key returns all four fields, including a NULL `interval_seconds`
surfacing as `None`. ONE shared assertion body is exercised against both
implementations so the two can never silently drift (mirrors
`test_component_repository_contract.py`'s pattern).
"""

from __future__ import annotations

import psycopg
import pytest
from src.core.domain.topology import Signal


def _sample_signals() -> list[Signal]:
    return [
        Signal(
            signal_key="z-http-check",
            name="Z HTTP Check",
            component_id="checkout",
            interval_seconds=120,
        ),
        Signal(
            signal_key="a-http-check",
            name="A HTTP Check",
            component_id=None,
            interval_seconds=None,
        ),
    ]


def _seed_signals_raw(
    database_url: str, signals: list[Signal], app_id: str = "app-1"
) -> None:
    """Insert `apps` (+ `components` for any non-None component_id) + `signals`
    rows via raw psycopg (test arrangement only, not the repository under test).
    """
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
            for signal in signals:
                if signal.component_id is not None:
                    cur.execute(
                        """
                        INSERT INTO components (id, app_id, name)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                        """,
                        (signal.component_id, app_id, signal.component_id),
                    )
            for signal in signals:
                cur.execute(
                    """
                    INSERT INTO signals
                        (signal_key, app_id, name, component_id, interval_seconds)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (signal_key) DO NOTHING
                    """,
                    (
                        signal.signal_key,
                        app_id,
                        signal.name,
                        signal.component_id,
                        signal.interval_seconds,
                    ),
                )
        conn.commit()


def _assert_signal_repository_contract(repo) -> None:
    """Shared assertion body run against BOTH the fake and Postgres impls."""
    signals = repo.list_signals()
    assert [s.signal_key for s in signals] == ["a-http-check", "z-http-check"]

    orphan = next(s for s in signals if s.signal_key == "a-http-check")
    assert orphan.component_id is None
    assert orphan.interval_seconds is None
    assert orphan.name == "A HTTP Check"

    mapped = next(s for s in signals if s.signal_key == "z-http-check")
    assert mapped.component_id == "checkout"
    assert mapped.interval_seconds == 120
    assert mapped.name == "Z HTTP Check"

    assert repo.get("does-not-exist") is None
    got = repo.get("z-http-check")
    assert got is not None
    assert got.signal_key == "z-http-check"
    assert got.component_id == "checkout"
    assert got.interval_seconds == 120


def test_fake_signal_repository_empty():
    from tests.fakes import FakeSignalRepository

    repo = FakeSignalRepository()
    assert repo.list_signals() == []
    assert repo.get("anything") is None


def test_fake_signal_repository_contract():
    from tests.fakes import FakeSignalRepository

    repo = FakeSignalRepository(signals=_sample_signals())
    _assert_signal_repository_contract(repo)


@pytest.fixture
def clean_topology(migrated_db):
    """Truncate topology tables before and after the test to keep the shared
    session-scoped database clean (mirrors `test_seed.py::clean_topology`)."""
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE apps, components, signals CASCADE;")
        conn.commit()
    yield
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE apps, components, signals CASCADE;")
        conn.commit()


def test_postgres_signal_repository_empty(migrated_db, engine, clean_topology):
    from src.adapters.persistence.signal_repository import PostgresSignalRepository

    repo = PostgresSignalRepository(engine)
    assert repo.list_signals() == []
    assert repo.get("anything") is None


def test_postgres_signal_repository_contract(migrated_db, engine, clean_topology):
    from src.adapters.persistence.signal_repository import PostgresSignalRepository

    _seed_signals_raw(migrated_db.database_url, _sample_signals())
    repo = PostgresSignalRepository(engine)
    _assert_signal_repository_contract(repo)
