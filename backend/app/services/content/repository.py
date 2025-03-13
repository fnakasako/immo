"""
Content Repository Module

This module provides data access layer functionality for content, sections, and scenes.
It abstracts database operations and provides a clean interface for the service layer.
"""
from uuid import UUID
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm.content import ContentGenerationRecord, Section, Scene
from app.models.enums import ContentStatus, GenerationStatus, SectionStatus, SceneStatus

class ContentRepository:
    """Repository for content-related database operations"""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize with a database session"""
        self.db_session = db_session
    
    # Content operations
    
    async def create_content(self, content_data: Dict[str, Any]) -> ContentGenerationRecord:
        """Create a new content record"""
        content = ContentGenerationRecord(**content_data)
        self.db_session.add(content)
        await self.db_session.commit()
        await self.db_session.refresh(content)
        return content
    
    async def get_content(self, content_id: UUID) -> Optional[ContentGenerationRecord]:
        """Get content by ID"""
        return await self.db_session.get(ContentGenerationRecord, content_id)
    
    async def list_content(self, skip: int = 0, limit: int = 10) -> List[ContentGenerationRecord]:
        """List content with pagination"""
        query = select(ContentGenerationRecord).order_by(
            desc(ContentGenerationRecord.created_at)
        ).offset(skip).limit(limit)
        result = await self.db_session.execute(query)
        return list(result.scalars().all())
    
    async def update_content(self, content_id: UUID, update_data: Dict[str, Any]) -> Optional[ContentGenerationRecord]:
        """Update content fields"""
        content = await self.get_content(content_id)
        if not content:
            return None
        
        for key, value in update_data.items():
            setattr(content, key, value)
        
        await self.db_session.commit()
        await self.db_session.refresh(content)
        return content
    
    async def update_content_status(self, content_id: UUID, status: ContentStatus) -> Optional[ContentGenerationRecord]:
        """Update content status"""
        content = await self.get_content(content_id)
        if not content:
            return None
        
        content.new_status = status
        await self.db_session.commit()
        await self.db_session.refresh(content)
        return content
    
    async def delete_content(self, content_id: UUID) -> bool:
        """Delete content (soft delete by setting deleted_at)"""
        content = await self.get_content(content_id)
        if not content:
            return False
        
        # If we had a deleted_at column, we would set it here
        # For now, we'll do a hard delete
        await self.db_session.delete(content)
        await self.db_session.commit()
        return True
    
    # Section operations
    
    async def create_section(self, section_data: Dict[str, Any]) -> Section:
        """Create a new section record"""
        section = Section(**section_data)
        self.db_session.add(section)
        await self.db_session.commit()
        await self.db_session.refresh(section)
        return section
    
    async def create_sections(self, content_id: UUID, sections_data: List[Dict[str, Any]]) -> List[Section]:
        """Create multiple section records for a content"""
        sections = []
        for i, data in enumerate(sections_data):
            section = Section(
                content_id=content_id,
                number=i+1,
                **data
            )
            self.db_session.add(section)
            sections.append(section)
        
        await self.db_session.commit()
        for section in sections:
            await self.db_session.refresh(section)
        
        return sections
    
    async def get_section(self, section_id: UUID) -> Optional[Section]:
        """Get section by ID"""
        return await self.db_session.get(Section, section_id)
    
    async def get_section_by_number(self, content_id: UUID, section_number: int) -> Optional[Section]:
        """Get section by content ID and section number"""
        query = select(Section).where(
            Section.content_id == content_id,
            Section.number == section_number
        )
        result = await self.db_session.execute(query)
        return result.scalars().first()
    
    async def list_sections(self, content_id: UUID) -> List[Section]:
        """List all sections for a content"""
        query = select(Section).where(
            Section.content_id == content_id
        ).order_by(Section.number)
        result = await self.db_session.execute(query)
        return list(result.scalars().all())
    
    async def update_section(self, section_id: UUID, update_data: Dict[str, Any]) -> Optional[Section]:
        """Update section fields"""
        section = await self.get_section(section_id)
        if not section:
            return None
        
        for key, value in update_data.items():
            setattr(section, key, value)
        
        await self.db_session.commit()
        await self.db_session.refresh(section)
        return section
    
    async def update_section_status(self, section_id: UUID, status: ContentStatus) -> Optional[Section]:
        """Update section status"""
        section = await self.get_section(section_id)
        if not section:
            return None
        
        section.new_status = status
        await self.db_session.commit()
        await self.db_session.refresh(section)
        return section
    
    # Scene operations
    
    async def create_scene(self, scene_data: Dict[str, Any]) -> Scene:
        """Create a new scene record"""
        scene = Scene(**scene_data)
        self.db_session.add(scene)
        await self.db_session.commit()
        await self.db_session.refresh(scene)
        return scene
    
    async def create_scenes(self, section_id: UUID, content_id: UUID, scenes_data: List[Dict[str, Any]]) -> List[Scene]:
        """Create multiple scene records for a section"""
        scenes = []
        for i, data in enumerate(scenes_data):
            scene = Scene(
                section_id=section_id,
                content_id=content_id,
                number=i+1,
                **data
            )
            self.db_session.add(scene)
            scenes.append(scene)
        
        await self.db_session.commit()
        for scene in scenes:
            await self.db_session.refresh(scene)
        
        return scenes
    
    async def get_scene(self, scene_id: UUID) -> Optional[Scene]:
        """Get scene by ID"""
        return await self.db_session.get(Scene, scene_id)
    
    async def get_scene_by_number(self, section_id: UUID, scene_number: int) -> Optional[Scene]:
        """Get scene by section ID and scene number"""
        query = select(Scene).where(
            Scene.section_id == section_id,
            Scene.number == scene_number
        )
        result = await self.db_session.execute(query)
        return result.scalars().first()
    
    async def list_scenes(self, section_id: UUID) -> List[Scene]:
        """List all scenes for a section"""
        query = select(Scene).where(
            Scene.section_id == section_id
        ).order_by(Scene.number)
        result = await self.db_session.execute(query)
        return list(result.scalars().all())
    
    async def update_scene(self, scene_id: UUID, update_data: Dict[str, Any]) -> Optional[Scene]:
        """Update scene fields"""
        scene = await self.get_scene(scene_id)
        if not scene:
            return None
        
        for key, value in update_data.items():
            setattr(scene, key, value)
        
        await self.db_session.commit()
        await self.db_session.refresh(scene)
        return scene
    
    async def update_scene_status(self, scene_id: UUID, status: ContentStatus) -> Optional[Scene]:
        """Update scene status"""
        scene = await self.get_scene(scene_id)
        if not scene:
            return None
        
        scene.new_status = status
        await self.db_session.commit()
        await self.db_session.refresh(scene)
        return scene
