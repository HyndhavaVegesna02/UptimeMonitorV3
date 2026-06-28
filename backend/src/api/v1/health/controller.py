"""HTTP controller for the health feature (api/v1/health zone).

Cites dossier §13. A minimal liveness probe; it also gives the
``api-feature-independence`` import-linter contract a second feature so the
contract is non-vacuous.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def get_health() -> dict[str, str]:
    """Return a static liveness payload (200 OK)."""
    return {"status": "ok"}
