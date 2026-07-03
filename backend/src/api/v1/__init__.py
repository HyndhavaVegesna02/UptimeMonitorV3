from fastapi import APIRouter

from src.api.v1.approvals import router as approvals_router
from src.api.v1.availability import router as availability_router
from src.api.v1.components import router as components_router
from src.api.v1.decisions import router as decisions_router
from src.api.v1.health import router as health_router
from src.api.v1.history import router as history_router
from src.api.v1.maintenance import router as maintenance_router
from src.api.v1.publications import router as publications_router

# STORY-048 sample-mode seam (temporary — see docs/scrum/wiki/sample-mode.md)
from src.api.v1.sample_mode import router as sample_mode_router
from src.api.v1.topology import router as topology_router

router = APIRouter()
router.include_router(health_router)
router.include_router(decisions_router)
router.include_router(components_router)
router.include_router(approvals_router)
router.include_router(maintenance_router)
router.include_router(availability_router)
router.include_router(history_router)
router.include_router(publications_router)
router.include_router(topology_router)
router.include_router(sample_mode_router)
