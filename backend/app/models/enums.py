# app/models/enums.py
from enum import Enum

class GenerationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING_OUTLINE = "processing_outline"
    OUTLINE_COMPLETED = "outline_completed"
    PROCESSING_SECTIONS = "processing_sections"
    SECTIONS_COMPLETED = "sections_completed"
    PROCESSING_SCENES = "processing_scenes"
    SCENES_COMPLETED = "scenes_completed"
    PROCESSING_PROSE = "processing_prose"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"

class SectionStatus(str, Enum):
    PENDING = "pending"
    READY_FOR_SCENES = "ready_for_scenes"
    GENERATING_SCENES = "generating_scenes"
    SCENES_COMPLETED = "scenes_completed"
    PROCESSING_SCENES = "processing_scenes"
    COMPLETED = "completed"
    FAILED = "failed"

class SceneStatus(str, Enum):
    PENDING = "pending"
    READY_FOR_PROSE = "ready_for_prose"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
