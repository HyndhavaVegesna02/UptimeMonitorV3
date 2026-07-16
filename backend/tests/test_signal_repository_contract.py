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
