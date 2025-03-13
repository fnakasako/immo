# app/models/enums.py
from enum import Enum

class ContentStatus(str, Enum):
    """Simplified status for content generation"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"  # Generic processing state
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class SectionStatus(str, Enum):
    """Simplified status for section generation"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"  # Generic processing state
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class SceneStatus(str, Enum):
    """Simplified status for scene generation"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"  # Generic processing state
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

# Keep the original enums for backward compatibility during migration
class GenerationStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING_OUTLINE = "PROCESSING_OUTLINE"
    OUTLINE_COMPLETED = "OUTLINE_COMPLETED"
    PROCESSING_SECTIONS = "PROCESSING_SECTIONS"
    SECTIONS_COMPLETED = "SECTIONS_COMPLETED"
    PROCESSING_SCENES = "PROCESSING_SCENES"
    SCENES_COMPLETED = "SCENES_COMPLETED"
    PROCESSING_PROSE = "PROCESSING_PROSE"
    COMPLETED = "COMPLETED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"
    FAILED = "FAILED"
