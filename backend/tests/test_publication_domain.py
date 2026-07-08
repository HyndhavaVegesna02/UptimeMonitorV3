"""Tests for the Publication domain type (STORY-037, Phase A; STORY-072).

Verifies: frozen, UTC-validated published_at, correct fields/defaults,
and the STORY-072 `outcome` field (default + explicit succeeded/failed).
AC1 (domain type) — dossier §9, §12/T1.1, §17.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError


def _utc_now() -> datetime:
    return datetime(2026, 6, 29, 12, 0, 0, tzinfo=timezone.utc)


def test_publication_valid_construction():
    """AC1/STORY-072: A Publication with valid UTC published_at constructs
    successfully, defaulting outcome to SUCCEEDED."""
    from src.core.domain.publication import Publication, PublicationOutcome
    from src.core.domain.status import ComponentStatus

    pub = Publication(
        component_id="checkout",
        status=ComponentStatus.OPERATIONAL,
        published_at=_utc_now(),
    )
    assert pub.component_id == "checkout"
    assert pub.status == ComponentStatus.OPERATIONAL
    assert pub.published_at == _utc_now()
    assert pub.proposal_id is None
    assert pub.outcome == PublicationOutcome.SUCCEEDED
    assert pub.id is None


def test_publication_outcome_explicit_failed():
    """STORY-072 AC1: outcome=FAILED can be set explicitly (the raising-delegate path)."""
    from src.core.domain.publication import Publication, PublicationOutcome
    from src.core.domain.status import ComponentStatus

    pub = Publication(
        component_id="checkout",
        status=ComponentStatus.DEGRADED,
        published_at=_utc_now(),
        outcome=PublicationOutcome.FAILED,
    )
    assert pub.outcome == PublicationOutcome.FAILED


def test_publication_outcome_values():
    """STORY-072 AC2: PublicationOutcome is a closed succeeded/failed vocabulary."""
    from src.core.domain.publication import PublicationOutcome

    assert PublicationOutcome.SUCCEEDED.value == "succeeded"
    assert PublicationOutcome.FAILED.value == "failed"
    assert {o.value for o in PublicationOutcome} == {"succeeded", "failed"}


def test_publication_with_all_fields():
    """AC1: Optional proposal_id and id are accepted."""
    from src.core.domain.publication import Publication
    from src.core.domain.status import ComponentStatus

    pub = Publication(
        component_id="checkout",
        status=ComponentStatus.DEGRADED,
        published_at=_utc_now(),
        proposal_id=42,
        id=7,
    )
    assert pub.proposal_id == 42
    assert pub.id == 7


def test_publication_is_frozen():
    """AC1: Publication is immutable (frozen)."""
    from src.core.domain.publication import Publication
    from src.core.domain.status import ComponentStatus

    pub = Publication(
        component_id="checkout",
        status=ComponentStatus.OPERATIONAL,
        published_at=_utc_now(),
    )
    with pytest.raises(ValidationError):
        pub.component_id = "other"  # type: ignore[misc]


def test_publication_naive_datetime_rejected():
    """AC1: A naive (tz-unaware) published_at must be rejected."""
    from src.core.domain.publication import Publication
    from src.core.domain.status import ComponentStatus

    with pytest.raises(
        ValidationError, match="published_at must be a tz-aware UTC datetime"
    ):
        Publication(
            component_id="checkout",
            status=ComponentStatus.OPERATIONAL,
            published_at=datetime(2026, 6, 29, 12, 0, 0),  # naive
        )


def test_publication_non_utc_datetime_rejected():
    """AC1: A tz-aware but non-UTC published_at must be rejected."""
    import zoneinfo

    from src.core.domain.publication import Publication
    from src.core.domain.status import ComponentStatus

    est = zoneinfo.ZoneInfo("America/New_York")
    with pytest.raises(
        ValidationError, match="published_at must be a tz-aware UTC datetime"
    ):
        Publication(
            component_id="checkout",
            status=ComponentStatus.OPERATIONAL,
            published_at=datetime(2026, 6, 29, 12, 0, 0, tzinfo=est),
        )


def test_publication_exported_from_domain_init():
    """AC1: Publication is exported from core/domain/__init__.py."""
    from src.core.domain import Publication  # noqa: F401


def test_publication_outcome_exported_from_domain_init():
    """STORY-072: PublicationOutcome is exported from core/domain/__init__.py."""
    from src.core.domain import PublicationOutcome  # noqa: F401
