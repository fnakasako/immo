from fastapi import APIRouter
from app.api.routes.stories import router as stories_router
from app.api.routes.content import router as content_router
from app.api.routes.sections import router as sections_router

router = APIRouter()
router.include_router(stories_router, prefix="/api/v1")
router.include_router(content_router, prefix="/api/v1")
router.include_router(sections_router, prefix="/api/v1")
