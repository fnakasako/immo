"""
API Dependencies Module

This module provides dependency injection for FastAPI routes.
"""
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.services.content import ContentService
from app.services.generation import GenerationService, LLMService

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency"""
    async for session in get_async_session():
        yield session

async def get_content_service(db: AsyncSession = Depends(get_db)) -> ContentService:
    """Get content service dependency"""
    return ContentService(db)

async def get_llm_service() -> LLMService:
    """Get LLM service dependency"""
    return LLMService()

async def get_generation_service(db: AsyncSession = Depends(get_db)) -> GenerationService:
    """Get generation service dependency"""
    llm_service = await get_llm_service()
    return GenerationService(db, llm_service)
