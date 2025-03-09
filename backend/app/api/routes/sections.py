# app/api/routes/sections.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.api.dependencies import get_db, get_generation_service
from app.models.schemas import SectionResponse, SectionList
from app.services.generation import GenerationCoordinator

router = APIRouter(tags=["sections"])

@router.get("/sections/{section_id}", response_model=SectionResponse)
async def get_section_by_id(
    section_id: UUID,
    db: Session = Depends(get_db),
    generation_service: GenerationCoordinator = Depends(get_generation_service)
):
    """Get section by ID"""
    try:
        return await generation_service.get_section_by_id(section_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section not found: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving section: {str(e)}"
        )
