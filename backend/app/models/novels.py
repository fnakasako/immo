from pydantic import BaseModel, Field
from typing import List, Optional, Dict, any
from enum import Enum

class StoryStyle(str, Enum):
    LITERARY = "literary"
    COMMERCIAL = "commercial"
    EXPIERMENTAL = "experimental"

class ChapterCOntent(BaseModel):
    number: int
    title: str
    content: str
    word_count: int

class StoryGenerationRequest(BaseModel):
    title: Optional[str]= None
    description: str = Field(..., min_length=10, max_length=1000)
    chatpers: int = Field(default-3, ge=1, le=10)
    style: Optional[StoryStyle] = None
    genre: Optional[str] = None
    additional_instructions: Optional[str] = None

class StoryGenerationResponse(BaseModel):
    id: str
    title: str
    chapters: List[ChapterContent]
    metadata: Dict[str, Any] = Field(default_factory=dict) 