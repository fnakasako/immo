from sqlalchemy import Column, String, Integer, Enum, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base
from app.models.enums import GenerationStatus

class StoryGenerationRecord(Base):
    __tablename__ = "story_generations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    description = Column(Text, nullable=False)
    chapters_count = Column(Integer, nullable=False)
    style = Column(String)
    model = Column(String, nullable=False)
    status = Column(String, nullable =False, default =GenerationStatus.PENDING.value)
    title = Column(String)
    outline = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate =datetime.utcnow)

    sections = relationship("app.models.orm.section.Section", back_populates="story", cascade="all, delete-orphan")

    def calculate_progress(self) -> float:
        """Calculate generation progress percentage"""
        from app.models.enums import SectionStatus, GenerationStatus

        if self.status == GenerationStatus.COMPLETED.value:
            return 100.0
        if self.status == GenerationStatus.PENDING.value:
            return 0.0
        
        # Count completed chapters
        completed = sum(1 for c in self.sections if c.status == SectionStatus.COMPLETED.value)
        if not self.chapters_count or self.chapters_count == 0:
            return 0.0
        
        return (completed / self.chapters_count) * 100
