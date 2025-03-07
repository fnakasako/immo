from enum import Enum

class GenerationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING_OUTLINE = "processing_outline"
    GENERATING_SECTIONS = "generating_sections"
    COMPLETED = "completed"
    FAILED = "failed"

class ChapterStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"