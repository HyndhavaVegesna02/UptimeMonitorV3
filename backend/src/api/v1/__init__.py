from fastapi import APIRouter

from src.api.v1.approvals import router as approvals_router
from src.api.v1.components import router as components_router
from src.api.v1.decisions import router as decisions_router
from src.api.v1.health import router as health_router

router = APIRouter()
router.include_router(health_router)
router.include_router(decisions_router)
router.include_router(components_router)
router.include_router(approvals_router)
