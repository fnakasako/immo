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
from app.models.orm.story import StoryGenerationRecord, Section
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
    except Exception as e:
        logger.error(f"Error creating story: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_ITNERNAL_SERVER_ERROR,
            detail=f"Failed to initiate story generation: {str(e)}"

        )
    
@router.get("/stories/{story_id}",
            response_model = StoryGenerationResponse)
async def get_story(
    story_id: UUID,
    db: Session = Depends(gets_db)
):
    """
    Get story generation status.
    
    Returns the curent state of the story generation process including:
    - Overall status
    - Progress percentage
    - Title and outline (if available)
    """
    story = db.query(StoryGenerationRecord).filter(
        StoryGenerationRecord.id == story_id
    ).first()

    if not story:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail= "Story not found"
        )
    
    return story

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
    # First verify story exists 
    story = db.query(StoryGenerationRecord).filter(
        StoryGenerationRecord.id == story_id
    ).first()

    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found"
        )
    
    # Get chapters
    chapters = db.query(Section).filter(
        Section.story_id == story_id
    ).order_by(Section.number).all()

    return {
        "sections": "sections",
        "total": len(chapters)
    }

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
    section = db.query(Section)/filter(
        Section.story_id == story_id,
        Section.number == section_number
    ).first()

    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_number} not found"
        )
    
    return chapter

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
    stories = db.query(StoryGenerationRecord).order_by(
        StoryGenerationRecord.created_at.desc()
    ).offset(skip).limit(limit).all()

    return stories