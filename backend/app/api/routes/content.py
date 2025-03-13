# app/api/routes/content.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.api.dependencies import get_db, get_generation_service
from app.models.schemas import (
    ContentGenerationRequest, 
    ContentGenerationResponse,
    ContentUpdateRequest,
    SectionResponse,
    SectionListResponse,
    SectionUpdateRequest,
    SceneResponse,
    SceneListResponse,
    SceneUpdateRequest,
    GenerationSelectionRequest
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
    db: AsyncSession = Depends(get_db),
    coordinator: GenerationCoordinator = Depends(get_generation_service)
):
    """Create a new content record without starting generation"""
    try:
        # Create content record and return ID
        content_id = await coordinator.create_story(request)
        
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

@router.post("/content/{content_id}/generate-outline", 
             response_model=ContentGenerationResponse)
async def generate_outline(
    content_id: UUID,
    background_tasks: BackgroundTasks,
    coordinator: GenerationCoordinator = Depends(get_generation_service)
):
    """Generate outline for content"""
    try:
        # Schedule outline generation in background
        background_tasks.add_task(
            coordinator.generate_outline,
            content_id=content_id
        )
        
        # Return current content info
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
            detail=f"Error generating outline: {str(e)}"
        )

@router.put("/content/{content_id}/outline", 
            response_model=ContentGenerationResponse)
async def update_outline(
    content_id: UUID,
    request: ContentUpdateRequest,
    db: AsyncSession = Depends(get_db),
    coordinator: GenerationCoordinator = Depends(get_generation_service)
):
    """Update content outline"""
    try:
        # Get content record
        content = await coordinator._get_content(content_id)
        
        # Update fields if provided
        if request.title is not None:
            content.title = request.title
        if request.outline is not None:
            content.outline = request.outline
        
        # Save changes
        await db.commit()
        
        # Return updated content info
        return await coordinator.get_content_info(content_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating outline: {str(e)}"
        )

@router.post("/content/{content_id}/generate-sections", 
             response_model=SectionListResponse)
async def generate_sections(
    content_id: UUID,
    background_tasks: BackgroundTasks,
    numSections: int = None,
    coordinator: GenerationCoordinator = Depends(get_generation_service)
):
    """Generate sections for content with summaries and styling descriptions"""
    try:
        # Schedule section generation in background
        background_tasks.add_task(
            coordinator.generate_sections,
            content_id=content_id,
            num_sections=numSections
        )
        
        # Return current sections
        return await coordinator.get_sections(content_id)
    except ValueError as e:
        if "credentials" in str(e).lower() or "authentication" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key."
            )
        elif "outline" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Outline must be generated before creating sections."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating sections: {str(e)}"
        )

@router.post("/content/{content_id}/generate-scenes", 
             response_model=SectionListResponse)
async def generate_scenes_for_sections(
    content_id: UUID,
    request: GenerationSelectionRequest,
    background_tasks: BackgroundTasks,
    coordinator: GenerationCoordinator = Depends(get_generation_service)
):
    """Generate scenes for selected sections"""
    try:
        # Schedule scene generation for each selected section in background
        for section_number in request.items:
            background_tasks.add_task(
                coordinator.generate_scenes_for_section,
                content_id=content_id,
                section_number=section_number
            )
        
        # Return current sections
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
                detail="Content or section not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating scenes: {str(e)}"
        )

@router.post("/content/{content_id}/sections/{section_number}/generate-prose", 
             response_model=SceneListResponse)
async def generate_prose_for_scenes(
    content_id: UUID,
    section_number: int,
    request: GenerationSelectionRequest,
    background_tasks: BackgroundTasks,
    coordinator: GenerationCoordinator = Depends(get_generation_service)
):
    """Generate prose for selected scenes in a section"""
    try:
        # Schedule prose generation for each selected scene in background
        for scene_number in request.items:
            background_tasks.add_task(
                coordinator.generate_prose_for_scene,
                content_id=content_id,
                section_number=section_number,
                scene_number=scene_number
            )
        
        # Return current scenes
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
                detail="Content, section, or scene not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating prose: {str(e)}"
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

@router.put("/content/{content_id}/sections/{section_number}",
            response_model=SectionResponse)
async def update_section(
    content_id: UUID,
    section_number: int,
    request: SectionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    coordinator: GenerationCoordinator = Depends(get_generation_service)
):
    """Update section details"""
    try:
        # Get section record
        section = await coordinator._get_section(content_id, section_number)
        
        # Update fields if provided
        if request.title is not None:
            section.title = request.title
        if request.summary is not None:
            section.summary = request.summary
        if request.content is not None:
            section.content = request.content
        
        # Save changes
        await db.commit()
        
        # Return updated section
        return await coordinator.get_section(content_id, section_number)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section {section_number} not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating section: {str(e)}"
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

@router.put("/content/{content_id}/sections/{section_number}/scenes/{scene_number}",
            response_model=SceneResponse)
async def update_scene(
    content_id: UUID,
    section_number: int,
    scene_number: int,
    request: SceneUpdateRequest,
    db: AsyncSession = Depends(get_db),
    coordinator: GenerationCoordinator = Depends(get_generation_service)
):
    """Update scene details"""
    try:
        # Get scene record
        scene = await coordinator._get_scene(content_id, section_number, scene_number)
        
        # Update fields if provided
        if request.heading is not None:
            scene.heading = request.heading
        if request.setting is not None:
            scene.setting = request.setting
        if request.characters is not None:
            scene.characters = str(request.characters)
        if request.key_events is not None:
            scene.key_events = request.key_events
        if request.emotional_tone is not None:
            scene.emotional_tone = request.emotional_tone
        if request.content is not None:
            scene.content = request.content
        
        # Save changes
        await db.commit()
        
        # Return updated scene
        return await coordinator.get_scene(content_id, section_number, scene_number)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scene {scene_number} not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating scene: {str(e)}"
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
