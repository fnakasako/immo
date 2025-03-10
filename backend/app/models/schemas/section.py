from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.models.enums import SectionStatus

class SectionResponse(BaseModel):
    """Schema for chapter response"""
    id: UUID
    content_id: UUID
    number: int
    title: str
    summary: Optional[str]
    content: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config: 
        orm_mode = True

class SectionList(BaseModel):
    """Schema for listing multiple sections"""
    sections: List[SectionResponse]
    total: int
