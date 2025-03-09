# app/api/routes/content.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.api.dependencies import get_db, get_generation_coordinator
from app.models.schemas import (
    ContentGenerationRequest, 
    ContentGenerationResponse,
    SectionResponse,
    SectionListResponse,
    SceneResponse,
    SceneListResponse
)
from app.models.enums import GenerationStatus
from app.services.generation import GenerationCoordinator

router = APIRouter(tags=["content"])

@router.post("/content", 
             response_model=ContentGenerationResponse, 
             status_code=status.HTTP_201_CREATED)
async def create_content(
    request: ContentGenerationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    coordinator: GenerationCoordinator = Depends(get_generation_coordinator)
):
    """Initiate content generation process"""
    try:
        # Create content record and return ID
        content_id = await coordinator.create_story(request)
        
        # Schedule processing in background
        background_tasks.add_task(
            coordinator.process_content,
            content_id=content_id
        )
        
        # Return initial content info
        return await coordinator.get_content_info(content_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate content generation: {str(e)}"
        )

@router.get("/content/{content_id}", 
            response_model=ContentGenerationResponse)
async def get_content(
    content_id: UUID,
    coordinator: GenerationCoordinator = Depends(get_generation_coordinator)
):
    """Get content generation status and outline"""
    try:
        return await coordinator.get_content_info(content_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving content: {str(e)}"
        )

@router.get("/content/{content_id}/sections",
            response_model=SectionListResponse)
async def get_sections(
    content_id: UUID,
    coordinator: GenerationCoordinator = Depends(get_generation_coordinator)
):
    """Get all sections for content"""
    try:
        return await coordinator.get_sections(content_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )

@router.get("/content/{content_id}/sections/{section_number}",
            response_model=SectionResponse)
async def get_section(
    content_id: UUID,
    section_number: int,
    coordinator: GenerationCoordinator = Depends(get_generation_coordinator)
):
    """Get specific section by number"""
    try:
        return await coordinator.get_section(content_id, section_number)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section {section_number} not found"
        )

@router.get("/content/{content_id}/sections/{section_number}/scenes",
            response_model=SceneListResponse)
async def get_scenes(
    content_id: UUID,
    section_number: int,
    coordinator: GenerationCoordinator = Depends(get_generation_coordinator)
):
    """Get all scenes for a section"""
    try:
        return await coordinator.get_scenes(content_id, section_number)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section {section_number} not found"
        )

@router.get("/content/{content_id}/sections/{section_number}/scenes/{scene_number}",
            response_model=SceneResponse)
async def get_scene(
    content_id: UUID,
    section_number: int,
    scene_number: int,
    coordinator: GenerationCoordinator = Depends(get_generation_coordinator)
):
    """Get specific scene by number"""
    try:
        return await coordinator.get_scene(content_id, section_number, scene_number)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scene {scene_number} not found"
        )