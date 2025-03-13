# app/api/routes/content.py
import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.api.dependencies import get_db, get_generation_service, get_content_service
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
from app.models.enums import GenerationStatus, ContentStatus
from app.services.generation import GenerationService
from app.services.content import ContentService

router = APIRouter(tags=["content"])

@router.post("/content", 
             response_model=ContentGenerationResponse, 
             status_code=status.HTTP_201_CREATED)
async def create_content(
    request: ContentGenerationRequest,
    db: AsyncSession = Depends(get_db),
    generation_service: GenerationService = Depends(get_generation_service),
    content_service: ContentService = Depends(get_content_service)
):
    """Create a new content record without starting generation"""
    try:
        # Create content record and return ID
        content_id = await generation_service.create_content(request)
        
        # Get content info
        content = await content_service.get_content(content_id)
        
        # Convert to response format
        return {
            "id": content.id,
            "description": content.description,
            "sections_count": content.sections_count,
            "style": content.style,
            "model": "default",
            "status": content.status.value if hasattr(content, 'status') else "PENDING",
            "progress": 0.0,
            "title": content.title,
            "outline": content.outline,
            "created_at": content.created_at,
            "updated_at": content.updated_at
        }
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
    content_service: ContentService = Depends(get_content_service)
):
    """
    List all content generation records.
    
    Returns a paginated list of content ordered by creation date.
    """
    try:
        return await content_service.list_content(skip, limit)
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
    generation_service: GenerationService = Depends(get_generation_service),
    content_service: ContentService = Depends(get_content_service)
):
    """Generate outline for content"""
    try:
        # Schedule outline generation in background
        background_tasks.add_task(
            generation_service.generate_outline,
            content_id=content_id
        )
        
        # Get content info
        content = await content_service.get_content(content_id)
        
        # Convert to response format
        return {
            "id": content.id,
            "description": content.description,
            "sections_count": content.sections_count,
            "style": content.style,
            "model": "default",
            "status": content.status.value if hasattr(content, 'status') else "PENDING",
            "progress": await content_service._calculate_progress(content),
            "title": content.title,
            "outline": content.outline,
            "created_at": content.created_at,
            "updated_at": content.updated_at
        }
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
    content_service: ContentService = Depends(get_content_service)
):
    """Update content outline"""
    try:
        # Prepare update data
        update_data = {}
        if request.title is not None:
            update_data["title"] = request.title
        if request.outline is not None:
            update_data["outline"] = request.outline
        
        # Update content
        content = await content_service.update_content(content_id, update_data)
        
        # Convert to response format
        return {
            "id": content.id,
            "description": content.description,
            "sections_count": content.sections_count,
            "style": content.style,
            "model": "default",
            "status": content.status.value if hasattr(content, 'status') else "PENDING",
            "progress": await content_service._calculate_progress(content),
            "title": content.title,
            "outline": content.outline,
            "created_at": content.created_at,
            "updated_at": content.updated_at
        }
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
    generation_service: GenerationService = Depends(get_generation_service),
    content_service: ContentService = Depends(get_content_service)
):
    """Generate sections for content with summaries and styling descriptions"""
    try:
        # Schedule section generation in background
        background_tasks.add_task(
            generation_service.generate_sections,
            content_id=content_id,
            num_sections=numSections
        )
        
        # Return current sections
        return await content_service.list_sections(content_id)
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
    generation_service: GenerationService = Depends(get_generation_service),
    content_service: ContentService = Depends(get_content_service)
):
    """Generate scenes for selected sections"""
    try:
        # Schedule scene generation for each selected section in background
        for section_number in request.items:
            background_tasks.add_task(
                generation_service.generate_scenes_for_section,
                content_id=content_id,
                section_number=section_number
            )
        
        # Return current sections
        return await content_service.list_sections(content_id)
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
    generation_service: GenerationService = Depends(get_generation_service),
    content_service: ContentService = Depends(get_content_service)
):
    """Generate prose for selected scenes in a section"""
    try:
        # Get section first to validate it exists
        section = await content_service.get_section_by_number(content_id, section_number)
        
        # Schedule prose generation for each selected scene in background
        for scene_number in request.items:
            background_tasks.add_task(
                generation_service.generate_prose_for_scene,
                content_id=content_id,
                section_number=section_number,
                scene_number=scene_number
            )
        
        # Return current scenes
        return await content_service.list_scenes(section.id)
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
    content_service: ContentService = Depends(get_content_service)
):
    """Get content generation status and outline"""
    try:
        # Get content
        content = await content_service.get_content(content_id)
        
        # Calculate progress
        progress = await content_service._calculate_progress(content)
        
        # Convert to response format
        return {
            "id": content.id,
            "description": content.description,
            "sections_count": content.sections_count,
            "style": content.style,
            "model": "default",
            "status": content.status.value if hasattr(content, 'status') else "PENDING",
            "progress": progress,
            "title": content.title,
            "outline": content.outline,
            "created_at": content.created_at,
            "updated_at": content.updated_at
        }
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
    content_service: ContentService = Depends(get_content_service)
):
    """Get all sections for content"""
    try:
        return await content_service.list_sections(content_id)
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
    content_service: ContentService = Depends(get_content_service)
):
    """Update section details"""
    try:
        # Get section
        section = await content_service.get_section_by_number(content_id, section_number)
        
        # Prepare update data
        update_data = {}
        if request.title is not None:
            update_data["title"] = request.title
        if request.summary is not None:
            update_data["summary"] = request.summary
        if request.content is not None:
            update_data["content"] = request.content
        
        # Update section
        updated_section = await content_service.update_section(section.id, update_data)
        
        # Return updated section
        return updated_section
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
    content_service: ContentService = Depends(get_content_service)
):
    """Get specific section by number"""
    try:
        return await content_service.get_section_by_number(content_id, section_number)
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
    content_service: ContentService = Depends(get_content_service)
):
    """Get all scenes for a section"""
    try:
        # Get section first to validate it exists
        section = await content_service.get_section_by_number(content_id, section_number)
        
        # Get scenes for the section
        return await content_service.list_scenes(section.id)
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
    content_service: ContentService = Depends(get_content_service)
):
    """Update scene details"""
    try:
        # Get section first to validate it exists
        section = await content_service.get_section_by_number(content_id, section_number)
        
        # Get scene by number
        scene = await content_service.get_scene_by_number(section.id, scene_number)
        
        # Prepare update data
        update_data = {}
        if request.heading is not None:
            update_data["heading"] = request.heading
        if request.setting is not None:
            update_data["setting"] = request.setting
        if request.characters is not None:
            update_data["characters"] = str(request.characters)
        if request.key_events is not None:
            update_data["key_events"] = request.key_events
        if request.emotional_tone is not None:
            update_data["emotional_tone"] = request.emotional_tone
        if request.content is not None:
            update_data["content"] = request.content
        
        # Update scene
        updated_scene = await content_service.update_scene(scene.id, update_data)
        
        # Return updated scene
        return updated_scene
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
    content_service: ContentService = Depends(get_content_service)
):
    """Get specific scene by number"""
    try:
        # Get section first to validate it exists
        section = await content_service.get_section_by_number(content_id, section_number)
        
        # Get scene by number
        return await content_service.get_scene_by_number(section.id, scene_number)
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

@router.post("/content/{content_id}/stream-outline")
async def stream_outline(
    content_id: UUID,
    content_service: ContentService = Depends(get_content_service),
    generation_service: GenerationService = Depends(get_generation_service)
):
    """Stream outline generation for content"""
    try:
        # Get content record
        content = await content_service.get_content(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Update status to processing
        await content_service.update_content(content_id, {"status": ContentStatus.PROCESSING})
        
        # Get LLM service
        llm_service = generation_service.llm_service
        
        async def stream_generator():
            try:
                # Format for SSE (Server-Sent Events)
                yield "data: {\"status\": \"started\"}\n\n"
                
                # Stream the outline generation
                outline_text = ""
                async for chunk in llm_service.stream_outline(
                    description=content.description,
                    style=content.style,
                    sections_count=content.sections_count
                ):
                    outline_text += chunk
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                
                # Try to parse the JSON response
                try:
                    outline_data = json.loads(outline_text)
                    
                    # Update content with outline data
                    update_data = {
                        "title": outline_data.get('title', 'Untitled'),
                        "outline": outline_data.get('outline', ''),
                        "status": ContentStatus.COMPLETED
                    }
                    await content_service.update_content(content_id, update_data)
                    
                    # Send completion message
                    yield f"data: {json.dumps({'status': 'completed', 'title': update_data['title']})}\n\n"
                except json.JSONDecodeError:
                    # If we can't parse the JSON, just store the raw text
                    update_data = {
                        "outline": outline_text,
                        "status": ContentStatus.COMPLETED
                    }
                    await content_service.update_content(content_id, update_data)
                    
                    # Send completion message
                    yield f"data: {json.dumps({'status': 'completed', 'note': 'Could not parse JSON response'})}\n\n"
                
                yield "data: [DONE]\n\n"
            except Exception as e:
                # Update status to failed
                await content_service.update_content(content_id, {
                    "status": ContentStatus.FAILED,
                    "error": str(e)
                })
                
                # Send error message
                yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
                yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error streaming outline: {str(e)}"
        )
