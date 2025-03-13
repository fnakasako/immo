"""
Content Service Module

This module provides business logic for content operations.
It uses the repository layer for data access and implements domain-specific logic.
"""
from uuid import UUID
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm.content import ContentGenerationRecord, Section, Scene
from app.models.enums import ContentStatus, GenerationStatus, SectionStatus, SceneStatus
from app.services.content.repository import ContentRepository

class ContentService:
    """Service for content-related business logic"""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize with a database session"""
        self.db_session = db_session
        self.repository = ContentRepository(db_session)
    
    # Content operations
    
    async def create_content(self, content_data: Dict[str, Any]) -> ContentGenerationRecord:
        """Create a new content record"""
        # Set default values if not provided
        if 'status' not in content_data:
            content_data['status'] = GenerationStatus.PENDING
        if 'new_status' not in content_data:
            content_data['new_status'] = ContentStatus.PENDING
        
        return await self.repository.create_content(content_data)
    
    async def get_content(self, content_id: UUID) -> Optional[ContentGenerationRecord]:
        """Get content by ID"""
        content = await self.repository.get_content(content_id)
        if not content:
            raise ValueError(f"Content with ID {content_id} not found")
        return content
    
    async def list_content(self, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """List content with pagination and convert to response format"""
        content_list = await self.repository.list_content(skip, limit)
        
        # Convert to response format
        result = []
        for content in content_list:
            result.append({
                "id": content.id,
                "description": content.description,
                "sections_count": content.sections_count,
                "style": content.style,
                "model": "default",
                "status": content.status.value,
                "progress": await self._calculate_progress(content),
                "title": content.title,
                "outline": content.outline,
                "created_at": content.created_at,
                "updated_at": content.updated_at
            })
        
        return result
    
    async def update_content(self, content_id: UUID, update_data: Dict[str, Any]) -> ContentGenerationRecord:
        """Update content fields"""
        content = await self.repository.update_content(content_id, update_data)
        if not content:
            raise ValueError(f"Content with ID {content_id} not found")
        return content
    
    async def update_content_status(self, content_id: UUID, status: ContentStatus) -> ContentGenerationRecord:
        """Update content status"""
        content = await self.repository.update_content_status(content_id, status)
        if not content:
            raise ValueError(f"Content with ID {content_id} not found")
        return content
    
    async def delete_content(self, content_id: UUID) -> bool:
        """Delete content"""
        success = await self.repository.delete_content(content_id)
        if not success:
            raise ValueError(f"Content with ID {content_id} not found")
        return True
    
    async def _calculate_progress(self, content: ContentGenerationRecord) -> float:
        """Calculate progress percentage based on completed sections and scenes"""
        if content.new_status == ContentStatus.COMPLETED:
            return 100.0
        if content.new_status == ContentStatus.PENDING:
            return 0.0
        
        # Get all sections
        sections = await self.repository.list_sections(content.id)
        if not sections:
            return 0.0
        
        # Count completed sections
        completed_sections = sum(1 for s in sections if s.new_status == ContentStatus.COMPLETED)
        
        # Calculate progress
        return (completed_sections / len(sections)) * 100.0
    
    # Section operations
    
    async def create_section(self, section_data: Dict[str, Any]) -> Section:
        """Create a new section record"""
        # Set default values if not provided
        if 'status' not in section_data:
            section_data['status'] = SectionStatus.PENDING
        if 'new_status' not in section_data:
            section_data['new_status'] = ContentStatus.PENDING
        
        return await self.repository.create_section(section_data)
    
    async def create_sections(self, content_id: UUID, sections_data: List[Dict[str, Any]]) -> List[Section]:
        """Create multiple section records for a content"""
        # Ensure content exists
        await self.get_content(content_id)
        
        # Process each section data
        for data in sections_data:
            if 'status' not in data:
                data['status'] = SectionStatus.PENDING
            if 'new_status' not in data:
                data['new_status'] = ContentStatus.PENDING
        
        return await self.repository.create_sections(content_id, sections_data)
    
    async def get_section(self, section_id: UUID) -> Optional[Section]:
        """Get section by ID"""
        section = await self.repository.get_section(section_id)
        if not section:
            raise ValueError(f"Section with ID {section_id} not found")
        return section
    
    async def get_section_by_number(self, content_id: UUID, section_number: int) -> Optional[Section]:
        """Get section by content ID and section number"""
        # Ensure content exists
        await self.get_content(content_id)
        
        section = await self.repository.get_section_by_number(content_id, section_number)
        if not section:
            raise ValueError(f"Section {section_number} not found for content {content_id}")
        return section
    
    async def list_sections(self, content_id: UUID) -> Dict[str, Any]:
        """List all sections for a content"""
        # Ensure content exists
        await self.get_content(content_id)
        
        sections = await self.repository.list_sections(content_id)
        
        # Convert to response format
        section_dicts = []
        for section in sections:
            section_dicts.append({
                "id": section.id,
                "content_id": section.content_id,
                "number": section.number,
                "title": section.title,
                "summary": section.summary,
                "style_description": section.style_description,
                "status": section.status.value,
                "created_at": section.created_at,
                "updated_at": section.updated_at
            })
        
        return {
            "sections": section_dicts,
            "total": len(section_dicts)
        }
    
    async def update_section(self, section_id: UUID, update_data: Dict[str, Any]) -> Section:
        """Update section fields"""
        section = await self.repository.update_section(section_id, update_data)
        if not section:
            raise ValueError(f"Section with ID {section_id} not found")
        return section
    
    async def update_section_status(self, section_id: UUID, status: ContentStatus) -> Section:
        """Update section status"""
        section = await self.repository.update_section_status(section_id, status)
        if not section:
            raise ValueError(f"Section with ID {section_id} not found")
        return section
    
    # Scene operations
    
    async def create_scene(self, scene_data: Dict[str, Any]) -> Scene:
        """Create a new scene record"""
        # Set default values if not provided
        if 'status' not in scene_data:
            scene_data['status'] = SceneStatus.PENDING
        if 'new_status' not in scene_data:
            scene_data['new_status'] = ContentStatus.PENDING
        
        return await self.repository.create_scene(scene_data)
    
    async def create_scenes(self, section_id: UUID, content_id: UUID, scenes_data: List[Dict[str, Any]]) -> List[Scene]:
        """Create multiple scene records for a section"""
        # Ensure section exists
        await self.get_section(section_id)
        
        # Process each scene data
        for data in scenes_data:
            if 'status' not in data:
                data['status'] = SceneStatus.PENDING
            if 'new_status' not in data:
                data['new_status'] = ContentStatus.PENDING
        
        return await self.repository.create_scenes(section_id, content_id, scenes_data)
    
    async def get_scene(self, scene_id: UUID) -> Optional[Scene]:
        """Get scene by ID"""
        scene = await self.repository.get_scene(scene_id)
        if not scene:
            raise ValueError(f"Scene with ID {scene_id} not found")
        return scene
    
    async def get_scene_by_number(self, section_id: UUID, scene_number: int) -> Optional[Scene]:
        """Get scene by section ID and scene number"""
        # Ensure section exists
        await self.get_section(section_id)
        
        scene = await self.repository.get_scene_by_number(section_id, scene_number)
        if not scene:
            raise ValueError(f"Scene {scene_number} not found for section {section_id}")
        return scene
    
    async def list_scenes(self, section_id: UUID) -> Dict[str, Any]:
        """List all scenes for a section"""
        # Ensure section exists
        await self.get_section(section_id)
        
        scenes = await self.repository.list_scenes(section_id)
        
        # Convert to response format
        scene_dicts = []
        for scene in scenes:
            scene_dicts.append({
                "id": scene.id,
                "content_id": scene.content_id,
                "section_id": scene.section_id,
                "number": scene.number,
                "heading": scene.heading,
                "setting": scene.setting,
                "characters": scene.characters,
                "key_events": scene.key_events,
                "emotional_tone": scene.emotional_tone,
                "content": scene.content,
                "status": scene.status.value,
                "created_at": scene.created_at,
                "updated_at": scene.updated_at
            })
        
        return {
            "scenes": scene_dicts,
            "total": len(scene_dicts)
        }
    
    async def update_scene(self, scene_id: UUID, update_data: Dict[str, Any]) -> Scene:
        """Update scene fields"""
        scene = await self.repository.update_scene(scene_id, update_data)
        if not scene:
            raise ValueError(f"Scene with ID {scene_id} not found")
        return scene
    
    async def update_scene_status(self, scene_id: UUID, status: ContentStatus) -> Scene:
        """Update scene status"""
        scene = await self.repository.update_scene_status(scene_id, status)
        if not scene:
            raise ValueError(f"Scene with ID {scene_id} not found")
        return scene
