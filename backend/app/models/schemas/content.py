from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime

from app.models.enums import GenerationStatus, SceneStatus

class ContentGenerationRequest(BaseModel):
    """Schema for requesting content generation"""
    description: str = Field(..., min_length=10, max_length=1000,
                             description="Detailed description of the content to generate")
    sections_count: int = Field(..., ge=1, le=20,
                                description="Number of sections to generate")
    style: Optional[str] = Field(None,
                                 description="Optional writing style for the content")
    model: str = Field("default",
                       description="AI model to use for generation")

class ContentGenerationResponse(BaseModel):
    """Schema for content generation response"""
    id: UUID
    description: str
    sections_count: int
    style: Optional[str]
    model: str
    status: str
    progress: float = Field(..., ge=0, le=100,
                            description="Generation progress percentage (0-100)")
    title: Optional[str] = None
    outline: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class SceneResponse(BaseModel):
    """Schema for scene response"""
    id: UUID
    content_id: UUID
    section_id: UUID
    number: int
    heading: Optional[str]
    setting: Optional[str]
    characters: Optional[str]
    key_events: Optional[str]
    emotional_tone: Optional[str]
    content: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class SceneListResponse(BaseModel):
    """Schema for listing multiple scenes"""
    scenes: List[SceneResponse]
    total: int

class SectionListResponse(BaseModel):
    """Schema for listing multiple sections"""
    sections: List[Dict]
    total: int
