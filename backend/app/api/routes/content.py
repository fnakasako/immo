# app/api/routes/content.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.api.dependencies import get_db, get_generation_service
from app.models.schemas import (
    ContentGenerationRequest, 
    ContentGenerationResponse,
    SectionResponse,
    SectionListResponse,
    SceneResponse,
    SceneListResponse
)
from app.models.orm.content import ContentGenerationRecord
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
    coordinator: GenerationCoordinator = Depends(get_generation_service)
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
    except ValueError as e:
        # Handle validation errors
        if "credentials" in str(e).lower() or "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key. Please check your Anthropic API key configuration."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request: {str(e)}"
            )
    except Exception as e:
        import traceback
        print(f"Error in create_content: {str(e)}")
        print(traceback.format_exc())
        
        # Check if the error is related to authentication
        error_str = str(e).lower()
        if "credentials" in error_str or "authentication" in error_str or "unauthorized" in error_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key. Please check your Anthropic API key configuration."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initiate content generation: {str(e)}"
            )

@router.get("/content", 
            response_model=List[ContentGenerationResponse])
async def list_content(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    List all content generation records.
    
    Returns a paginated list of content ordered by creation date.
    """
    try:
        from sqlalchemy import select, desc
        
        query = select(ContentGenerationRecord).order_by(
            desc(ContentGenerationRecord.created_at)
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        content_list = result.scalars().all()
        
        # Convert ORM objects to dictionaries for serialization
        content_dicts = []
        for content in content_list:
            content_dicts.append({
                "id": content.id,
                "description": content.description,
                "sections_count": content.sections_count,
                "style": content.style,
                "model": "default",
                "status": content.status.value,
                "progress": 100.0 if content.status == GenerationStatus.COMPLETED else 0.0,
                "title": content.title,
                "outline": content.outline,
                "created_at": content.created_at,
                "updated_at": content.updated_at
            })
        
        return content_dicts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving content list: {str(e)}"
        )

@router.get("/content/{content_id}", 
            response_model=ContentGenerationResponse)
async def get_content(
    content_id: UUID,
    coordinator: GenerationCoordinator = Depends(get_generation_service)
):
    """Get content generation status and outline"""
    try:
        return await coordinator.get_content_info(content_id)
    except ValueError as e:
        if "credentials" in str(e).lower() or "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key. Please check your Anthropic API key configuration."
            )
        else:
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
    coordinator: GenerationCoordinator = Depends(get_generation_service)
):
    """Get all sections for content"""
    try:
        return await coordinator.get_sections(content_id)
    except ValueError as e:
        if "credentials" in str(e).lower() or "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key. Please check your Anthropic API key configuration."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving sections: {str(e)}"
        )

@router.get("/content/{content_id}/sections/{section_number}",
            response_model=SectionResponse)
async def get_section(
    content_id: UUID,
    section_number: int,
    coordinator: GenerationCoordinator = Depends(get_generation_service)
):
    """Get specific section by number"""
    try:
        return await coordinator.get_section(content_id, section_number)
    except ValueError as e:
        if "credentials" in str(e).lower() or "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key. Please check your Anthropic API key configuration."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Section {section_number} not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving section: {str(e)}"
        )

@router.get("/content/{content_id}/sections/{section_number}/scenes",
            response_model=SceneListResponse)
async def get_scenes(
    content_id: UUID,
    section_number: int,
    coordinator: GenerationCoordinator = Depends(get_generation_service)
):
    """Get all scenes for a section"""
    try:
        return await coordinator.get_scenes(content_id, section_number)
    except ValueError as e:
        if "credentials" in str(e).lower() or "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key. Please check your Anthropic API key configuration."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Section {section_number} not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving scenes: {str(e)}"
        )

@router.get("/content/{content_id}/sections/{section_number}/scenes/{scene_number}",
            response_model=SceneResponse)
async def get_scene(
    content_id: UUID,
    section_number: int,
    scene_number: int,
    coordinator: GenerationCoordinator = Depends(get_generation_service)
):
    """Get specific scene by number"""
    try:
        return await coordinator.get_scene(content_id, section_number, scene_number)
    except ValueError as e:
        if "credentials" in str(e).lower() or "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key. Please check your Anthropic API key configuration."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scene {scene_number} not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving scene: {str(e)}"
        )
