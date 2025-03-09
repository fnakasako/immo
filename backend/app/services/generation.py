# app/services/generation.py
from uuid import UUID
import asyncio
from typing import List, Dict, Any
from app.models.orm.content import ContentGenerationRecord, Section, Scene
from app.models.enums import GenerationStatus, SectionStatus, SceneStatus
from app.ai.service import AIService, AIServiceException

class GenerationCoordinator:
    """Coordinates the multi-stage content generation process"""
    
    def __init__(self, db_session, ai_service: AIService):
        self.db_session = db_session
        self.ai_service = ai_service
    
    async def process_content(self, content_id: UUID):
        """Main generation pipeline for a piece of content"""
        try:
            # 1. Generate overall outline
            content = await self._get_content(content_id)
            outline = await self.ai_service.generate_outline(
                description=content.description,
                style=content.style,
                sections_count=content.sections_count
            )
            
            # Update content with outline
            content.title = outline['title']
            content.outline = outline['outline']
            content.status = GenerationStatus.PROCESSING_SECTIONS
            await self.db_session.commit()
            
            # 2. Create section records and process each section
            await self._create_section_records(content_id, outline['sections'])
            
            # 3. Process each section in sequence
            for i, section_data in enumerate(outline['sections']):
                await self._process_section(content_id, i+1, section_data)
            
            # 4. Mark content as completed
            content.status = GenerationStatus.COMPLETED
            await self.db_session.commit()
            
        except Exception as e:
            # Handle failures
            content = await self._get_content(content_id)
            content.status = GenerationStatus.FAILED
            content.error = str(e)
            await self.db_session.commit()
            raise
    
    async def _process_section(self, content_id: UUID, section_number: int, section_data: Dict[str, str]):
        """Process a single section including scenes and prose"""
        try:
            # 1. Get section record
            section = await self._get_section(content_id, section_number)
            section.status = SectionStatus.GENERATING_SCENES
            await self.db_session.commit()
            
            # 2. Generate scenes for this section
            content = await self._get_content(content_id)
            scenes = await self.ai_service.generate_scenes({
                'content_title': content.title,
                'content_outline': content.outline,
                'section_number': section_number,
                'section_title': section.title,
                'section_summary': section.summary
            })
            
            # 3. Create scene records
            await self._create_scene_records(content_id, section_number, scenes)
            
            # 4. Process each scene to generate prose
            for i, scene_data in enumerate(scenes):
                await self._process_scene(content_id, section_number, i+1, scene_data)
            
            # 5. Mark section as completed
            section.status = SectionStatus.COMPLETED
            await self.db_session.commit()
            
        except Exception as e:
            # Handle section failure
            section = await self._get_section(content_id, section_number)
            section.status = SectionStatus.FAILED
            section.error = str(e)
            await self.db_session.commit()
            raise
    
    async def _process_scene(self, content_id: UUID, section_number: int, 
                           scene_number: int, scene_data: Dict[str, Any]):
        """Generate prose for a single scene"""
        try:
            # 1. Get scene record
            scene = await self._get_scene(content_id, section_number, scene_number)
            scene.status = SceneStatus.GENERATING
            await self.db_session.commit()
            
            # 2. Build context for prose generation
            content = await self._get_content(content_id)
            section = await self._get_section(content_id, section_number)
            
            # Get summaries of previous sections and scenes for context
            previous_context = await self._build_previous_context(
                content_id, section_number, scene_number
            )
            
            # 3. Generate prose for this scene
            prose = await self.ai_service.generate_prose({
                'content_title': content.title,
                'content_outline': content.outline,
                'section_title': section.title,
                'section_number': section_number,
                'scene_heading': scene_data['scene_heading'],
                'setting': scene_data['setting'],
                'characters': scene_data.get('characters', []),
                'key_events': scene_data['key_events'],
                'emotional_tone': scene_data['emotional_tone'],
                'previous_context': previous_context,
                'style': content.style
            })
            
            # 4. Update scene with generated prose
            scene.content = prose
            scene.status = SceneStatus.COMPLETED
            await self.db_session.commit()
            
        except Exception as e:
            # Handle scene failure
            scene = await self._get_scene(content_id, section_number, scene_number)
            scene.status = SceneStatus.FAILED
            scene.error = str(e)
            await self.db_session.commit()
            raise
    
    # Helper methods omitted for brevity
