from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.api.dependencies import get_db, get_generation_service
from app.models.schemas import (
    StoryGenerationRequest,
    StoryGenerationResponse,
    SectionList,
    SectionResponse
)
from app.models.orm.story import StoryGenerationRecord
from app.models.orm import StorySection
from app.services.generation import GenerationCoordinator
from app.core.logging import logger

router = APIRouter(tags=["stories"])

@router.post("/stories",
             response_model=StoryGenerationResponse,
             status_code=status.HTTP_201_CREATED)
async def create_story(
    request: StoryGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    generation_service: GenerationCoordinator = Depends(get_generation_service)
):
    """
    Initiate story generation process
    
    This endpoint will:
    1. Create a story record in the database
    2. trigger the asynchronous generation process
    3. Return the initial story record"""
    try:
        # Create story record and trigger the processing
        story_id = await generation_service.create_story(request)

        # Sechedule outline generation in the background
        background_tasks.add_task(
            generation_service.process_outline,
            story_id = story_id
        )

        # Retrieve the created story to return
        story = db.query(StoryGenerationRecord).filter(
            StoryGenerationRecord.id == story_id
        ).first()

        if not story:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create story record"
            )
        
        return story
    except ValueError as e:
        # Handle validation errors
        if "credentials" in str(e).lower() or "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials. Please check your username and password."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request: {str(e)}"
            )
    except Exception as e:
        logger.error(f"Error creating story: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate story generation: {str(e)}"
        )
    
@router.get("/stories/{story_id}",
            response_model = StoryGenerationResponse)
async def get_story(
    story_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get story generation status.
    
    Returns the curent state of the story generation process including:
    - Overall status
    - Progress percentage
    - Title and outline (if available)
    """
    try:
        story = db.query(StoryGenerationRecord).filter(
            StoryGenerationRecord.id == story_id
        ).first()

        if not story:
            raise ValueError("Story not found")
        
        return story
    except ValueError as e:
        if "credentials" in str(e).lower() or "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials. Please check your username and password."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving story: {str(e)}"
        )

@router.get("/stories/{story_id}/sections",
            response_model=SectionList)
async def get_sections(
    story_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get all chapters for a story.
    
    Returns all chapters associated with the story, including:
    - Chapter status
    - Title and summary
    - Content (if available)
    """
    try:
        # First verify story exists 
        story = db.query(StoryGenerationRecord).filter(
            StoryGenerationRecord.id == story_id
        ).first()

        if not story:
            raise ValueError("Story not found")
        
        # Get chapters
        chapters = db.query(StorySection).filter(
            StorySection.story_id == story_id
        ).order_by(StorySection.number).all()

        # Map story_id to content_id for frontend compatibility
        mapped_sections = []
        for section in chapters:
            mapped_sections.append({
                "id": section.id,
                "content_id": section.story_id,  # Map story_id to content_id
                "number": section.number,
                "title": section.title,
                "summary": section.summary,
                "content": section.content,
                "status": section.status,
                "created_at": section.created_at,
                "updated_at": section.updated_at
            })

        return {
            "sections": mapped_sections,
            "total": len(chapters)
        }
    except ValueError as e:
        if "credentials" in str(e).lower() or "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials. Please check your username and password."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving sections: {str(e)}"
        )

@router.get("/stories/{story_id}/sections/{section_number}",
            response_model=SectionResponse)
async def get_chapter(
    story_id: UUID,
    chapter_number: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific section by number.

    REturns a single section with all details.
    """
    try:
        section = db.query(StorySection).filter(
            StorySection.story_id == story_id,
            StorySection.number == chapter_number
        ).first()

        if not section:
            raise ValueError(f"Chapter {chapter_number} not found")
        
        # Map story_id to content_id for frontend compatibility
        section_dict = {
            "id": section.id,
            "content_id": section.story_id,  # Map story_id to content_id
            "number": section.number,
            "title": section.title,
            "summary": section.summary,
            "content": section.content,
            "status": section.status,
            "created_at": section.created_at,
            "updated_at": section.updated_at
        }
        
        return section_dict
    except ValueError as e:
        if "credentials" in str(e).lower() or "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials. Please check your username and password."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapter {chapter_number} not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving chapter: {str(e)}"
        )

@router.get("/stories",
            response_model=List[StoryGenerationResponse])
async def list_stories(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    List all story generation records.
    
    Returns a paginated list of stories ordered by creation date.
    """
    try:
        stories = db.query(StoryGenerationRecord).order_by(
            StoryGenerationRecord.created_at.desc()
        ).offset(skip).limit(limit).all()

        return stories
    except ValueError as e:
        if "credentials" in str(e).lower() or "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials. Please check your username and password."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request: {str(e)}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving stories: {str(e)}"
        )
