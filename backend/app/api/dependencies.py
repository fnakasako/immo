from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.generation import GenerationCoordinator

async def get_generation_service(db: AsyncSession = Depends(get_db)) -> GenerationCoordinator:
    """Generation service dependency"""
    from app.ai.service import AIService
    from app.core.config import settings
    
    # Create AI service with API key from settings
    ai_service = AIService(api_key=settings.ANTHROPIC_API_KEY)
    
    # Create and return the coordinator with dependencies
    return GenerationCoordinator(db_session=db, ai_service=ai_service)
