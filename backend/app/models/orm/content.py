# app/models/orm/content.py
from sqlalchemy import Column, String, Integer, ForeignKey, Text, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base
from app.models.enums import GenerationStatus, SectionStatus, SceneStatus

class ContentGenerationRecord(Base):
    __tablename__ = "content_generations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    description = Column(Text, nullable=False)
    sections_count = Column(Integer, nullable=False, default=5)
    style = Column(String, nullable=True)
    status = Column(Enum(GenerationStatus), nullable=False, default=GenerationStatus.PENDING)
    title = Column(String, nullable=True)
    outline = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sections = relationship("Section", back_populates="content_record", cascade="all, delete-orphan")
    
    def calculate_progress(self) -> float:
        """Calculate progress percentage based on completed sections and scenes"""
        # Calculation logic here
        pass

class Section(Base):
    __tablename__ = "sections"
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(UUID(as_uuid=True), ForeignKey("content_generations.id"), nullable=False)
    number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    status = Column(Enum(SectionStatus), nullable=False, default=SectionStatus.PENDING)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    content_record = relationship("ContentGenerationRecord", back_populates="sections")
    scenes = relationship("Scene", back_populates="section", cascade="all, delete-orphan")

class Scene(Base):
    __tablename__ = "scenes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(UUID(as_uuid=True), ForeignKey("content_generations.id"), nullable=False)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.id"), nullable=False)
    number = Column(Integer, nullable=False)
    heading = Column(String, nullable=True)
    setting = Column(Text, nullable=True)
    characters = Column(Text, nullable=True)  # JSON string of character names
    key_events = Column(Text, nullable=True)
    emotional_tone = Column(String, nullable=True)
    content = Column(Text, nullable=True)  # The generated prose
    status = Column(Enum(SceneStatus), nullable=False, default=SceneStatus.PENDING)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    section = relationship("Section", back_populates="scenes")
