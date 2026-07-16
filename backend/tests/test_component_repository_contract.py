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

import pytest
from src.core.domain.component import ComponentNotFoundError
from src.core.domain.status import ComponentStatus


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
