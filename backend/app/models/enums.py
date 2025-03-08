# app/models/enums.py
from enum import Enum

class GenerationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING_OUTLINE = "processing_outline"
    PROCESSING_SECTIONS = "processing_sections"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"

class SectionStatus(str, Enum):
    PENDING = "pending"
    GENERATING_SCENES = "generating_scenes"
    PROCESSING_SCENES = "processing_scenes"
    COMPLETED = "completed"
    FAILED = "failed"

class SceneStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"