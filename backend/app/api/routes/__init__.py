from fastapi import APIRouter
from app.api.routes.stories import router as stories_router

router = APIRouter()
router.include_router(stories_router, predix="/api/v1")