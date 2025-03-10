from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base
from app.models.enums import SectionStatus


class Section(Base):
    __tablename__= "sections"



    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    story_id = Column(UUID(as_uuid=True), ForeignKey("story_generations.id"))
    number = Column(Integer, nullable = False)
    title = Column(String, nullable = False)
    summary = Column(Text, nullable=True)
    content = Column(Text)
    status = Column(String, nullable=False, default=SectionStatus.PENDING.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default = datetime.utcnow)

    story = relationship("app.models.orm.story.StoryGenerationRecord", back_populates="sections")

    class Config:
        orm_mode = True
