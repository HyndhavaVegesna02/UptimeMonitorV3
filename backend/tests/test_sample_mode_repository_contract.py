"""Contract test for `SampleModeRepository` (STORY-048 D1/D2, dossier §6/§17).

TEMPORARY feature — see docs/scrum/wiki/sample-mode.md for the REMOVAL
inventory; this whole file is deleted when sample-mode is removed.

Fake/adapter parity agreement (2026-06-26): `FakeSampleModeRepository` and
`PostgresSampleModeRepository` must behave IDENTICALLY: never-set -> False;
set/read round-trips; setting the same value twice is idempotent (no error);
and the state survives a FRESH repository instance bound to the same
underlying store (proves persistence, not Python instance memory) — the
"fresh instance" check is why the shared assertion body takes a `make_repo`
FACTORY rather than a single repo instance.
"""

from __future__ import annotations

import psycopg
import pytest


def _assert_sample_mode_repository_contract(make_repo) -> None:
    """Shared assertion body run against BOTH the fake and Postgres impls.

    `make_repo` is a zero-arg factory returning a NEW repository instance
    bound to the same underlying persistent store on each call.
    """
    repo = make_repo()

    # Never-set -> False (the PO's default-OFF lives in the port, not a seed).
    assert repo.is_enabled() is False

    # Set/read round-trip.
    repo.set_enabled(True)
    assert repo.is_enabled() is True

    repo.set_enabled(False)
    assert repo.is_enabled() is False

    # Idempotent: setting the same value twice succeeds silently.
    repo.set_enabled(False)
    assert repo.is_enabled() is False

    repo.set_enabled(True)
    repo.set_enabled(True)
    assert repo.is_enabled() is True

    # Persistence across a FRESH repository instance on the same store —
    # proves the state lives in the store, not in this Python object.
    fresh = make_repo()
    assert fresh.is_enabled() is True


def test_fake_sample_mode_repository_never_set_defaults_false():
    from tests.fakes import FakeSampleModeRepository

    repo = FakeSampleModeRepository()
    assert repo.is_enabled() is False


def test_fake_sample_mode_repository_contract():
    from tests.fakes import FakeSampleModeRepository

    shared_store: dict = {}
    _assert_sample_mode_repository_contract(
        lambda: FakeSampleModeRepository(store=shared_store)
    )


@pytest.fixture
def clean_sample_mode(migrated_db):
    """Truncate `sample_mode` before and after the test (no FK; shared DB)."""
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE sample_mode;")
        conn.commit()
    yield
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE sample_mode;")
        conn.commit()


def test_postgres_sample_mode_repository_never_set_defaults_false(
    migrated_db, engine, clean_sample_mode
):
    from src.adapters.persistence.sample_mode_repository import (
        PostgresSampleModeRepository,
    )

    repo = PostgresSampleModeRepository(engine)
    assert repo.is_enabled() is False


def test_postgres_sample_mode_repository_contract(
    migrated_db, engine, clean_sample_mode
):
    from src.adapters.persistence.sample_mode_repository import (
        PostgresSampleModeRepository,
    )

    _assert_sample_mode_repository_contract(
        lambda: PostgresSampleModeRepository(engine)
    )
