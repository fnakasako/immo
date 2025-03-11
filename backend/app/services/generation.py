# app/services/generation.py
from uuid import UUID
import asyncio
from typing import List, Dict, Any
from app.models.orm.content import ContentGenerationRecord, Scene, Section as ContentSection
from app.models.enums import GenerationStatus, SectionStatus, SceneStatus
from app.ai.service import AIService, AIServiceException

class GenerationCoordinator:
    """Coordinates the multi-stage content generation process"""
    
    def __init__(self, db_session, ai_service: AIService):
        self.db_session = db_session
        self.ai_service = ai_service
        
    async def _get_session(self):
        """Get a new database session for background tasks"""
        from app.core.database import SessionLocal
        return SessionLocal()
        
    async def _run_background_task(self, task_func, *args, **kwargs):
        """Run a task in the background with its own database session
        
        Args:
            task_func: The async function to run
            *args, **kwargs: Arguments to pass to the task function
            
        Returns:
            The result of the task function
        """
        from app.core.database import SessionLocal
        
        async with SessionLocal() as session:
            try:
                return await task_func(session, *args, **kwargs)
            except Exception as e:
                # Log the error
                import logging
                logging.error(f"Error in background task: {str(e)}")
                raise
        
    async def create_story(self, request):
        """Create a new content generation record"""
        # Create a new content record
        content = ContentGenerationRecord(
            description=request.description,
            sections_count=request.sections_count,
            style=request.style,
            status=GenerationStatus.PENDING
        )
        
        # Add to database and commit
        self.db_session.add(content)
        await self.db_session.commit()
        await self.db_session.refresh(content)
        
        return content.id
    
    
    async def _generate_outline_task(self, session, content_id: UUID):
        """Background task to generate outline for content"""
        from sqlalchemy import select
        from app.models.orm.content import ContentGenerationRecord
        
        # Get content record
        query = select(ContentGenerationRecord).where(ContentGenerationRecord.id == content_id)
        result = await session.execute(query)
        content = result.scalars().first()
        
        if not content:
            raise ValueError(f"Content with ID {content_id} not found")
        
        # Update status
        content.status = GenerationStatus.PROCESSING_OUTLINE
        await session.commit()
        
        # Generate outline
        outline = await self.ai_service.generate_outline(
            description=content.description,
            style=content.style,
            sections_count=content.sections_count
        )
        
        # Update content with outline only
        content.title = outline['title']
        content.outline = outline['outline']
        content.status = GenerationStatus.OUTLINE_COMPLETED
        await session.commit()
        
        return outline
    
    async def generate_outline(self, content_id: UUID):
        """Generate only the outline for a piece of content"""
        try:
            # Run the task in the background with its own session
            return await self._run_background_task(
                self._generate_outline_task,
                content_id
            )
        except Exception as e:
            # Log the error
            import logging
            logging.error(f"Error generating outline for content {content_id}: {str(e)}")
            
            # Try to update the content status if possible
            try:
                content = await self._get_content(content_id)
                content.status = GenerationStatus.FAILED
                content.error = str(e)
                await self.db_session.commit()
            except:
                # If we can't update the content status, just continue with the original error
                pass
            
            raise
    
    async def _generate_sections_task(self, session, content_id: UUID):
        """Background task to generate sections for content"""
        from sqlalchemy import select
        from app.models.orm.content import ContentGenerationRecord, Section as ContentSection
        
        # Get content record
        query = select(ContentGenerationRecord).where(ContentGenerationRecord.id == content_id)
        result = await session.execute(query)
        content = result.scalars().first()
        
        if not content:
            raise ValueError(f"Content with ID {content_id} not found")
        
        # Ensure outline exists
        if not content.title or not content.outline:
            raise ValueError("Content must have a title and outline before generating sections")
        
        # Update content status
        content.status = GenerationStatus.PROCESSING_SECTIONS
        await session.commit()
        
        # Generate sections using the AI service
        sections_data = await self.ai_service.generate_sections(
            content_title=content.title,
            content_outline=content.outline,
            style=content.style,
            sections_count=content.sections_count
        )
        
        # Create section records
        for i, section_data in enumerate(sections_data):
            section = ContentSection(
                content_id=content_id,
                number=i+1,
                title=section_data['title'],
                summary=section_data['summary'],
                style_description=section_data.get('style_description', 'Standard style'),
                status=SectionStatus.PENDING
            )
            session.add(section)
        
        await session.commit()
        
        # Update content status
        content.status = GenerationStatus.SECTIONS_COMPLETED
        await session.commit()
        
        # Get sections to return
        query = select(ContentSection).where(ContentSection.content_id == content_id).order_by(ContentSection.number)
        result = await session.execute(query)
        sections = list(result.scalars().all())
        
        # Convert Section objects to dictionaries for serialization
        section_dicts = []
        for section in sections:
            section_dicts.append({
                "id": section.id,
                "content_id": section.content_id,
                "number": section.number,
                "title": section.title,
                "summary": section.summary,
                "status": section.status.value,
                "created_at": section.created_at,
                "updated_at": section.updated_at
            })
        
        return {
            "sections": section_dicts,
            "total": len(sections)
        }
    
    async def generate_sections(self, content_id: UUID):
        """Generate section summaries and details"""
        try:
            # Run the task in the background with its own session
            return await self._run_background_task(
                self._generate_sections_task,
                content_id
            )
        except Exception as e:
            # Log the error
            import logging
            logging.error(f"Error generating sections for content {content_id}: {str(e)}")
            
            # Try to update the content status if possible
            try:
                content = await self._get_content(content_id)
                content.status = GenerationStatus.FAILED
                content.error = str(e)
                await self.db_session.commit()
            except:
                # If we can't update the content status, just continue with the original error
                pass
            
            raise
    
    async def _generate_scenes_for_section_task(self, session, content_id: UUID, section_number: int):
        """Background task to generate scenes for a section"""
        from sqlalchemy import select
        from app.models.orm.content import ContentGenerationRecord, Scene, Section as ContentSection
        
        # Get section record
        query = select(ContentSection).where(
            ContentSection.content_id == content_id,
            ContentSection.number == section_number
        )
        result = await session.execute(query)
        section = result.scalars().first()
        
        if not section:
            raise ValueError(f"Section {section_number} not found")
        
        # Update section status
        section.status = SectionStatus.GENERATING_SCENES
        await session.commit()
        
        # Get content record for context
        query = select(ContentGenerationRecord).where(ContentGenerationRecord.id == content_id)
        result = await session.execute(query)
        content = result.scalars().first()
        
        if not content:
            raise ValueError(f"Content with ID {content_id} not found")
        
        # Generate scenes for this section
        scenes = await self.ai_service.generate_scenes({
            'content_title': content.title,
            'content_outline': content.outline,
            'section_number': section_number,
            'section_title': section.title,
            'section_summary': section.summary
        })
        
        # Create scene records
        for i, scene_data in enumerate(scenes):
            scene = Scene(
                content_id=content_id,
                section_id=section.id,
                number=i+1,
                heading=scene_data['scene_heading'],
                setting=scene_data['setting'],
                characters=str(scene_data.get('characters', [])),
                key_events=scene_data['key_events'],
                emotional_tone=scene_data['emotional_tone'],
                status=SceneStatus.PENDING
            )
            session.add(scene)
        
        await session.commit()
        
        # Mark section as scenes completed
        section.status = SectionStatus.SCENES_COMPLETED
        await session.commit()
        
        # Get scenes to return
        query = select(Scene).where(
            Scene.section_id == section.id
        ).order_by(Scene.number)
        result = await session.execute(query)
        scenes = list(result.scalars().all())
        
        # Convert Scene objects to dictionaries for serialization
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
            "total": len(scenes)
        }
    
    async def generate_scenes_for_section(self, content_id: UUID, section_number: int):
        """Generate scenes for a specific section"""
        try:
            # Run the task in the background with its own session
            return await self._run_background_task(
                self._generate_scenes_for_section_task,
                content_id,
                section_number
            )
        except Exception as e:
            # Log the error
            import logging
            logging.error(f"Error generating scenes for section {section_number}: {str(e)}")
            
            # Try to update the section status if possible
            try:
                section = await self._get_section(content_id, section_number)
                section.status = SectionStatus.FAILED
                section.error = str(e)
                await self.db_session.commit()
            except:
                # If we can't update the section status, just continue with the original error
                pass
            
            raise
    
    async def _generate_prose_for_scene_task(self, session, content_id: UUID, section_number: int, scene_number: int):
        """Background task to generate prose for a scene"""
        from sqlalchemy import select
        from app.models.orm.content import ContentGenerationRecord, Scene, Section as ContentSection
        
        # Get section record
        query = select(ContentSection).where(
            ContentSection.content_id == content_id,
            ContentSection.number == section_number
        )
        result = await session.execute(query)
        section = result.scalars().first()
        
        if not section:
            raise ValueError(f"Section {section_number} not found")
        
        # Get scene record
        query = select(Scene).where(
            Scene.content_id == content_id,
            Scene.section_id == section.id,
            Scene.number == scene_number
        )
        result = await session.execute(query)
        scene = result.scalars().first()
        
        if not scene:
            raise ValueError(f"Scene {scene_number} not found")
        
        # Update scene status
        scene.status = SceneStatus.GENERATING
        await session.commit()
        
        # Get content record for context
        query = select(ContentGenerationRecord).where(ContentGenerationRecord.id == content_id)
        result = await session.execute(query)
        content = result.scalars().first()
        
        if not content:
            raise ValueError(f"Content with ID {content_id} not found")
        
        # Get scene data
        scene_data = {
            'scene_heading': scene.heading,
            'setting': scene.setting,
            'characters': eval(scene.characters) if isinstance(scene.characters, str) else scene.characters,
            'key_events': scene.key_events,
            'emotional_tone': scene.emotional_tone
        }
        
        # Build previous context
        context = []
        
        # Get previous sections
        query = select(ContentSection).where(
            ContentSection.content_id == content_id,
            ContentSection.number < section_number
        ).order_by(ContentSection.number)
        result = await session.execute(query)
        prev_sections = list(result.scalars().all())
        
        # Add section summaries
        for prev_section in prev_sections:
            context.append(f"Section {prev_section.number}: {prev_section.title}")
            context.append(prev_section.summary)
        
        # Get scenes from current section
        if scene_number > 1:
            query = select(Scene).where(
                Scene.section_id == section.id,
                Scene.number < scene_number
            ).order_by(Scene.number)
            result = await session.execute(query)
            prev_scenes = list(result.scalars().all())
            
            # Add scene content
            for prev_scene in prev_scenes:
                if prev_scene.content:
                    context.append(f"Scene {prev_scene.number}: {prev_scene.heading}")
                    context.append(prev_scene.content)
        
        previous_context = "\n\n".join(context)
        
        # Generate prose for this scene
        prose = await self.ai_service.generate_prose({
            'content_title': content.title,
            'content_outline': content.outline,
            'section_title': section.title,
            'section_number': section_number,
            'scene_heading': scene_data['scene_heading'],
            'setting': scene_data['setting'],
            'characters': scene_data['characters'],
            'key_events': scene_data['key_events'],
            'emotional_tone': scene_data['emotional_tone'],
            'previous_context': previous_context,
            'style': content.style
        })
        
        # Update scene with generated prose
        scene.content = prose
        scene.status = SceneStatus.COMPLETED
        await session.commit()
        
        # Return scene data
        return {
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
        }
    
    async def generate_prose_for_scene(self, content_id: UUID, section_number: int, scene_number: int):
        """Generate prose for a specific scene"""
        try:
            # Run the task in the background with its own session
            return await self._run_background_task(
                self._generate_prose_for_scene_task,
                content_id,
                section_number,
                scene_number
            )
        except Exception as e:
            # Log the error
            import logging
            logging.error(f"Error generating prose for scene {section_number}.{scene_number}: {str(e)}")
            
            # Try to update the scene status if possible
            try:
                scene = await self._get_scene(content_id, section_number, scene_number)
                scene.status = SceneStatus.FAILED
                scene.error = str(e)
                await self.db_session.commit()
            except:
                # If we can't update the scene status, just continue with the original error
                pass
            
            raise
    
    # Legacy methods kept for reference but no longer used directly
    async def _process_section(self, content_id: UUID, section_number: int, section_data: Dict[str, str]):
        """Legacy method - Process a single section including scenes and prose"""
        await self.generate_scenes_for_section(content_id, section_number)
        
        # Process each scene to generate prose
        scenes_result = await self.get_scenes(content_id, section_number)
        for scene in scenes_result['scenes']:
            await self.generate_prose_for_scene(content_id, section_number, scene['number'])
    
    async def _process_scene(self, content_id: UUID, section_number: int, 
                           scene_number: int, scene_data: Dict[str, Any]):
        """Legacy method - Generate prose for a single scene"""
        await self.generate_prose_for_scene(content_id, section_number, scene_number)
    
    async def get_content_info(self, content_id: UUID):
        """Get content generation info"""
        content = await self._get_content(content_id)
        
        # Calculate progress
        progress = 0.0
        if content.status == GenerationStatus.COMPLETED:
            progress = 100.0
        elif content.status == GenerationStatus.FAILED:
            progress = 0.0
        elif content.status == GenerationStatus.PROCESSING_SECTIONS:
            # Calculate based on sections
            sections = await self._get_sections(content_id)
            if sections:
                completed = sum(1 for s in sections if s.status == SectionStatus.COMPLETED)
                progress = (completed / len(sections)) * 100.0
        
        # Return response
        return {
            "id": content.id,
            "description": content.description,
            "sections_count": content.sections_count,
            "style": content.style,
            "model": "default",
            "status": content.status.value,
            "progress": progress,
            "title": content.title,
            "outline": content.outline,
            "created_at": content.created_at,
            "updated_at": content.updated_at
        }
    
    async def _get_content(self, content_id: UUID) -> ContentGenerationRecord:
        """Get content record by ID"""
        content = await self.db_session.get(ContentGenerationRecord, content_id)
        if not content:
            raise ValueError(f"Content with ID {content_id} not found")
        return content
    
    async def _get_sections(self, content_id: UUID) -> List[ContentSection]:
        """Get all sections for content"""
        from sqlalchemy import select
        
        query = select(ContentSection).where(ContentSection.content_id == content_id).order_by(ContentSection.number)
        result = await self.db_session.execute(query)
        return list(result.scalars().all())
    
    async def _get_section(self, content_id: UUID, section_number: int) -> ContentSection:
        """Get section by content ID and number"""
        from sqlalchemy import select
        
        query = select(ContentSection).where(
            ContentSection.content_id == content_id,
            ContentSection.number == section_number
        )
        result = await self.db_session.execute(query)
        section = result.scalars().first()
        
        if not section:
            raise ValueError(f"Section {section_number} not found")
        
        return section
    
    async def _get_scene(self, content_id: UUID, section_number: int, scene_number: int) -> Scene:
        """Get scene by content ID, section number, and scene number"""
        from sqlalchemy import select
        
        # First get section ID
        section = await self._get_section(content_id, section_number)
        
        # Then get scene
        query = select(Scene).where(
            Scene.content_id == content_id,
            Scene.section_id == section.id,
            Scene.number == scene_number
        )
        result = await self.db_session.execute(query)
        scene = result.scalars().first()
        
        if not scene:
            raise ValueError(f"Scene {scene_number} not found")
        
        return scene
    
    async def _create_section_records(self, content_id: UUID, sections_data: List[Dict[str, str]]):
        """Create section records from outline data"""
        for i, section_data in enumerate(sections_data):
            section = ContentSection(
                content_id=content_id,
                number=i+1,
                title=section_data['title'],
                summary=section_data['summary'],
                style_description=section_data.get('style_description', 'Standard style'),
                status=SectionStatus.PENDING
            )
            self.db_session.add(section)
        
        await self.db_session.commit()
    
    async def _create_scene_records(self, content_id: UUID, section_number: int, scenes_data: List[Dict[str, Any]]):
        """Create scene records from scene breakdown data"""
        # Get section ID
        section = await self._get_section(content_id, section_number)
        
        for i, scene_data in enumerate(scenes_data):
            scene = Scene(
                content_id=content_id,
                section_id=section.id,
                number=i+1,
                heading=scene_data['scene_heading'],
                setting=scene_data['setting'],
                characters=str(scene_data.get('characters', [])),
                key_events=scene_data['key_events'],
                emotional_tone=scene_data['emotional_tone'],
                status=SceneStatus.PENDING
            )
            self.db_session.add(scene)
        
        await self.db_session.commit()
    
    async def _build_previous_context(self, content_id: UUID, section_number: int, scene_number: int) -> str:
        """Build context from previous sections and scenes"""
        # Get all sections up to current
        from sqlalchemy import select
        
        context = []
        
        # Get previous sections
        query = select(ContentSection).where(
            ContentSection.content_id == content_id,
            ContentSection.number < section_number
        ).order_by(ContentSection.number)
        result = await self.db_session.execute(query)
        prev_sections = list(result.scalars().all())
        
        # Add section summaries
        for section in prev_sections:
            context.append(f"Section {section.number}: {section.title}")
            context.append(section.summary)
        
        # Get scenes from current section
        if scene_number > 1:
            section = await self._get_section(content_id, section_number)
            query = select(Scene).where(
                Scene.section_id == section.id,
                Scene.number < scene_number
            ).order_by(Scene.number)
            result = await self.db_session.execute(query)
            prev_scenes = list(result.scalars().all())
            
            # Add scene content
            for scene in prev_scenes:
                if scene.content:
                    context.append(f"Scene {scene.number}: {scene.heading}")
                    context.append(scene.content)
        
        return "\n\n".join(context)
    
    async def get_sections(self, content_id: UUID):
        """Get all sections for content"""
        sections = await self._get_sections(content_id)
        
        # Convert Section objects to dictionaries for serialization
        section_dicts = []
        for section in sections:
            section_dicts.append({
                "id": section.id,
                "content_id": section.content_id,
                "number": section.number,
                "title": section.title,
                "summary": section.summary,
                "status": section.status.value,
                "created_at": section.created_at,
                "updated_at": section.updated_at
            })
        
        return {
            "sections": section_dicts,
            "total": len(sections)
        }
    
    async def get_section(self, content_id: UUID, section_number: int):
        """Get specific section by number"""
        section = await self._get_section(content_id, section_number)
        
        # Convert Section object to dictionary for serialization
        section_dict = {
            "id": section.id,
            "content_id": section.content_id,
            "number": section.number,
            "title": section.title,
            "summary": section.summary,
            "status": section.status.value,
            "created_at": section.created_at,
            "updated_at": section.updated_at
        }
        
        return section_dict
    
    async def get_scenes(self, content_id: UUID, section_number: int):
        """Get all scenes for a section"""
        from sqlalchemy import select
        
        # Get section ID
        section = await self._get_section(content_id, section_number)
        
        # Get scenes
        query = select(Scene).where(
            Scene.section_id == section.id
        ).order_by(Scene.number)
        result = await self.db_session.execute(query)
        scenes = list(result.scalars().all())
        
        # Convert Scene objects to dictionaries for serialization
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
            "total": len(scenes)
        }
    
    async def get_scene(self, content_id: UUID, section_number: int, scene_number: int):
        """Get specific scene by number"""
        scene = await self._get_scene(content_id, section_number, scene_number)
        
        # Convert Scene object to dictionary for serialization
        scene_dict = {
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
        }
        
        return scene_dict
        
    async def get_section_by_id(self, section_id: UUID):
        """Get section by ID"""
        from sqlalchemy import select
        
        query = select(ContentSection).where(ContentSection.id == section_id)
        result = await self.db_session.execute(query)
        section = result.scalars().first()
        
        if not section:
            raise ValueError(f"Section with ID {section_id} not found")
        
        # Convert Section object to dictionary for serialization
        section_dict = {
            "id": section.id,
            "content_id": section.content_id,
            "number": section.number,
            "title": section.title,
            "summary": section.summary,
            "status": section.status.value,
            "created_at": section.created_at,
            "updated_at": section.updated_at
        }
        
        return section_dict
