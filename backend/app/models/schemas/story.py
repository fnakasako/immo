from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime

from app.models.enums import GenerationStatus

class StoryGenerationRequest(BaseModel):
    """Schema for requesting story generation"""
    description: str = Field(..., min_length=10, max_length=1000,
                             description= "Detailed description of the story to generate")
    sections_count: int = Field(..., ge=1, le=20,
                                description = "Number of chapters to generate")
    style: Optional[str] = Field(none,
                                 description = "Optional writing style for the story")
    model: str = Field("default",
                       description = "AI model to use for generation")

    @validator('description')
    def description_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip()
    
class StoryOutline(BaseModel):
    """Schema for story outline structure"""
    title: str
    outline: str
    section_summaries: List[Dict[str, str]]

class StoryGenerationResponse(BaseModel):
    """Schema for story generation resposne"""
    id: UUID
    description: str
    sections_count: int
    style: Optional[str]
    model: str
    status: str
    progress: float = Field(..., ge=0, le=100,
                            description="Generation progress percentage (0-100)")
    title: Optional[str] = None
    outline: Optiona[str] = None
    created_at: datetime
    updated_at: datetime

    class COnfig:
        orm_mode = True
    
    @classmethod
    def from_orm(cls, obj):
        # Create a dict from the ORM model instance
        data = {
            c.name: getattr(obj, c.name)
            for c in obj.__table__.columns
        }
        # Add calculated fields
        data['progress'] = obj.calculate_progress()
        return cls(**data)
    
class StoryGenerationList(BaseModel):
    """Schema for listing multiple story generations"""
    stories: List[StoryGenerationResponse]
    total: int

    