"""Smoke test: the four backend zones import cleanly (STORY-001, AC1/AC2)."""


def test_zones_import():
    import src.core
    import src.core.domain
    import src.core.ports
    import src.core.services
    import src.adapters
    import src.adapters.inbound
    import src.adapters.outbound
    import src.adapters.persistence
    import src.composition
    import src.api

    assert src.core is not None
    assert src.adapters is not None
    assert src.composition is not None
    assert src.api is not None
